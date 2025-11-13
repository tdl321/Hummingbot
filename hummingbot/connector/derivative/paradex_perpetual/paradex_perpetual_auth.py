import time
import json
import base64
from typing import Any, Dict, Optional

from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class ParadexPerpetualAuth(AuthBase):
    """
    Authentication handler for Paradex Perpetual API.

    Supports two authentication methods:
    1. API Key (recommended): Pre-generated JWT token from Paradex UI
       - Simple, long-lived token
       - No SDK required
       - Best for most users

    2. L2 Subkey: Generate JWTs dynamically using paradex_py SDK
       - Uses L2 private key to sign and generate JWTs
       - Tokens expire in 5 minutes
       - More complex but gives full control

    Auto-detects method based on api_secret format:
    - Starts with "eyJ": API key (JWT token)
    - Starts with "0x": L2 subkey private key
    """

    def __init__(
        self,
        api_secret: str,  # API key (JWT) OR L2 subkey private key
        account_address: str,  # L1 Ethereum address
        environment: str = "mainnet",
        domain: Optional[str] = None
    ):
        """
        Initialize Paradex authentication.

        Args:
            api_secret: Either a JWT API key (starts with "eyJ") OR L2 subkey private key (starts with "0x")
            account_address: L1 Ethereum account address (hex string, 0x...)
            environment: "mainnet" or "testnet"
            domain: Domain string for determining environment

        Raises:
            RuntimeError: If Paradex client initialization fails

        Note:
            Authentication method is auto-detected:
            - API key: api_secret starts with "eyJ" (base64-encoded JWT)
            - L2 subkey: api_secret starts with "0x" (hex private key)
        """
        self._api_secret: str = api_secret
        self._account_address: str = account_address
        self._environment_str: str = environment
        self._domain: Optional[str] = domain

        # Detect authentication method
        self._is_api_key: bool = api_secret.startswith("eyJ")

        # JWT token management
        self._jwt_token: Optional[str] = None
        self._jwt_expires_at: Optional[float] = None  # Unix timestamp

        # For L2 subkey auth: lazy-initialize SDK client when needed
        self._paradex_client: Optional[Any] = None  # Paradex instance

        # For API key auth: parse token immediately to get expiry
        if self._is_api_key:
            self._jwt_token = api_secret
            self._parse_jwt_expiry()

    def _parse_jwt_expiry(self):
        """
        Parse JWT token to extract expiry time.

        JWT format: header.payload.signature (all base64-encoded)
        Payload contains "exp" field with Unix timestamp.
        """
        try:
            # Split JWT into parts
            parts = self._jwt_token.split(".")
            if len(parts) != 3:
                # Invalid JWT format, use default expiry (1 hour)
                self._jwt_expires_at = time.time() + 3600
                return

            # Decode payload (add padding if needed for base64)
            payload = parts[1]
            # Add padding for base64 decoding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            payload_bytes = base64.urlsafe_b64decode(payload)
            payload_dict = json.loads(payload_bytes.decode("utf-8"))

            # Extract expiry timestamp
            exp = payload_dict.get("exp")
            if exp:
                self._jwt_expires_at = float(exp)
            else:
                # No expiry in token, assume 1 hour
                self._jwt_expires_at = time.time() + 3600

        except Exception:
            # Failed to parse, use default expiry (1 hour)
            self._jwt_expires_at = time.time() + 3600

    def _initialize_client(self):
        """
        Initialize Paradex client for trading operations.

        This is done lazily to avoid importing paradex_py during module load
        and to handle SDK import errors gracefully.
        """
        if self._paradex_client is None:
            try:
                # Import paradex_py SDK (lazy import)
                from paradex_py import Paradex
            except ImportError as e:
                raise RuntimeError(
                    "Failed to import paradex_py SDK. "
                    "Please install: pip install paradex-py>=0.4.6\n"
                    f"Error: {str(e)}"
                ) from e

            try:
                # Determine environment from domain or environment string
                if self._domain and "testnet" in self._domain:
                    env = "testnet"
                elif self._environment_str == "testnet":
                    env = "testnet"
                else:
                    env = "prod"

                # Initialize Paradex client
                self._paradex_client = Paradex(
                    env=env,
                    l2_private_key=self._api_secret,  # L2 subkey private key
                )

                # Initialize account with L1 address
                # For subkey authentication:
                #   - l1_address: Main account's Ethereum L1 address
                #   - l2_private_key: Already set in Paradex() constructor
                self._paradex_client.init_account(
                    l1_address=self._account_address,  # L1 Ethereum address
                    l2_private_key=self._api_secret,   # L2 subkey private key
                )

            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize Paradex client. "
                    f"Verify credentials are correct:\n"
                    f"  - account_address should be L1 Ethereum address (0x...)\n"
                    f"  - api_secret should be L2 subkey private key (0x...)\n"
                    f"Error: {str(e)}"
                ) from e

    async def get_jwt_token(self) -> str:
        """
        Get valid JWT token.

        For API key auth: Returns the long-lived API key directly.
        For L2 subkey auth: Generates/refreshes JWT tokens via SDK (expire every 5 minutes).

        Returns:
            Valid JWT token string

        Raises:
            Exception: If token generation fails (L2 subkey auth only)
        """
        # API key authentication: just return the API key (already a JWT)
        if self._is_api_key:
            # Check if API key is expired
            if self._jwt_expires_at and time.time() >= self._jwt_expires_at:
                raise Exception(
                    "API key has expired. Please generate a new API key from Paradex UI:\n"
                    "1. Go to https://paradex.trade\n"
                    "2. Settings → API Management\n"
                    "3. Generate new API key\n"
                    "4. Update configuration with new key"
                )
            return self._jwt_token

        # L2 subkey authentication: generate JWT via SDK
        # Check if token exists and is not expired
        if self._jwt_token and self._jwt_expires_at:
            # Refresh 1 minute (60 seconds) before expiry
            # Paradex docs recommend refreshing early for retry attempts
            if time.time() < (self._jwt_expires_at - 60):
                return self._jwt_token

        # Generate new token via paradex_py SDK
        self._initialize_client()

        try:
            # Get authentication headers from SDK
            # This method generates/refreshes JWT token automatically
            # Note: auth_headers() is synchronous, safe to call in async context
            auth_headers = self._paradex_client.account.auth_headers()

            # Extract JWT token from Authorization header
            # Expected format: "Bearer <jwt_token>"
            auth_header = auth_headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                self._jwt_token = auth_header[7:]  # Remove "Bearer " prefix
            else:
                raise ValueError(f"Unexpected Authorization header format: {auth_header}")

            # JWT tokens expire in 5 minutes (300 seconds) per Paradex docs
            # Set expiry time to 5 minutes from now
            self._jwt_expires_at = time.time() + 300

            if not self._jwt_token:
                raise ValueError("Failed to extract JWT token from SDK auth headers")

            return self._jwt_token

        except Exception as e:
            raise Exception(f"Failed to generate JWT token: {str(e)}") from e

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Add authentication headers to REST requests.

        Paradex requires:
        - Authorization: Bearer {jwt_token}
        - PARADEX-STARKNET-ACCOUNT: {main_account_address} (for subkeys)

        Args:
            request: The REST request to authenticate

        Returns:
            Authenticated REST request with headers
        """
        if request.headers is None:
            request.headers = {}

        # Get valid JWT token (auto-refresh if needed)
        jwt_token = await self.get_jwt_token()

        # Add authentication headers (exact format from Paradex documentation)
        request.headers["Authorization"] = f"Bearer {jwt_token}"
        request.headers["PARADEX-STARKNET-ACCOUNT"] = self._account_address

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket requests.

        Paradex WebSocket authentication sends JWT token in subscription message.

        Args:
            request: The WebSocket request to authenticate

        Returns:
            Authenticated WebSocket request

        Note:
            The exact WebSocket authentication format should be verified from
            Paradex documentation. This implementation follows common patterns.
        """
        # Get valid JWT token
        jwt_token = await self.get_jwt_token()

        # Add authentication to WebSocket payload
        # Note: Exact format may differ - verify from Paradex docs
        if request.payload is None:
            request.payload = {}

        request.payload["jwt_token"] = jwt_token
        request.payload["account"] = self._account_address

        return request

    def get_paradex_client(self) -> Any:
        """
        Get ParadexSubkey client for direct SDK method calls.

        This is used for operations that require SDK signing:
        - Place orders (submit_order)
        - Cancel orders (cancel_order)
        - Modify orders (modify_order)

        Returns:
            ParadexSubkey instance for trading operations

        Usage:
            client = auth.get_paradex_client()
            order = await client.submit_order(market="BTC-USD-PERP", ...)
        """
        self._initialize_client()
        return self._paradex_client

    @property
    def account_address(self) -> str:
        """Get the main account address."""
        return self._account_address

    async def get_rest_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for REST requests.

        Returns:
            Dictionary with Authorization and PARADEX-STARKNET-ACCOUNT headers
        """
        jwt_token = await self.get_jwt_token()
        return {
            "Authorization": f"Bearer {jwt_token}",
            "PARADEX-STARKNET-ACCOUNT": self._account_address
        }

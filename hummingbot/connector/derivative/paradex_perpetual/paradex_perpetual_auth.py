import time
from typing import Any, Dict, Optional

from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class ParadexPerpetualAuth(AuthBase):
    """
    Authentication handler for Paradex Perpetual API.

    Uses paradex_py SDK for:
    - JWT token generation and auto-refresh
    - Order signing (via SDK methods)
    - Subkey authentication (L2-only, trading restrictions for security)

    This implementation uses ParadexSubkey for trading operations, which:
    - Cannot withdraw funds (security feature)
    - Can only place/cancel orders and read account data
    - Requires: subkey L2 private key + main account address
    """

    def __init__(
        self,
        api_secret: str,  # Starknet subkey private key (L2)
        account_address: str,  # Main account address
        environment: str = "mainnet"
    ):
        """
        Initialize Paradex authentication with paradex_py SDK integration.

        Args:
            api_secret: Starknet subkey private key (hex string, 0x...)
            account_address: Main Paradex account address (hex string, 0x...)
            environment: "mainnet" or "testnet"

        Raises:
            RuntimeError: If ParadexSubkey initialization fails
        """
        self._api_secret: str = api_secret
        self._account_address: str = account_address
        self._environment_str: str = environment

        # JWT token management
        self._jwt_token: Optional[str] = None
        self._jwt_expires_at: Optional[float] = None  # Unix timestamp

        # Lazy-initialize SDK client when needed
        self._paradex_client: Optional[Any] = None  # ParadexSubkey instance

    def _initialize_client(self):
        """
        Initialize ParadexSubkey client for trading operations.

        This is done lazily to avoid importing paradex_py during module load
        and to handle SDK import errors gracefully.
        """
        if self._paradex_client is None:
            try:
                # Import paradex_py SDK (lazy import)
                from paradex_py import ParadexSubkey, Environment
            except ImportError as e:
                raise RuntimeError(
                    "Failed to import paradex_py SDK. "
                    "Please install: pip install paradex-py\n"
                    f"Error: {str(e)}"
                ) from e

            try:
                # Determine environment
                env = Environment.PROD if self._environment_str == "mainnet" else Environment.TESTNET

                # Initialize ParadexSubkey for subkey-based authentication
                self._paradex_client = ParadexSubkey(
                    env=env,
                    l2_private_key=self._api_secret,  # Subkey private key
                    l2_account_address=self._account_address  # Main account address
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize ParadexSubkey client. "
                    f"Verify credentials are correct. Error: {str(e)}"
                ) from e

    async def get_jwt_token(self) -> str:
        """
        Get valid JWT token, refreshing if expired.

        JWT tokens are required for all authenticated API requests.
        Tokens are auto-refreshed 5 minutes before expiry.

        Returns:
            Valid JWT token string

        Raises:
            Exception: If token generation fails
        """
        # Check if token exists and is not expired
        if self._jwt_token and self._jwt_expires_at:
            # Refresh 5 minutes (300 seconds) before expiry
            if time.time() < (self._jwt_expires_at - 300):
                return self._jwt_token

        # Generate new token via paradex_py SDK
        self._initialize_client()

        try:
            # Get JWT token from SDK
            # Note: Actual SDK method may differ - verify from paradex_py documentation
            token_response = await self._paradex_client.auth.get_jwt_token()

            # Extract token and expiry
            # Note: Response format may differ - adjust based on actual SDK response
            if isinstance(token_response, dict):
                self._jwt_token = token_response.get("jwt_token")
                self._jwt_expires_at = token_response.get("expires_at")  # Unix timestamp
            else:
                # If SDK returns token string directly
                self._jwt_token = str(token_response)
                # Assume 1 hour expiry if not provided
                self._jwt_expires_at = time.time() + 3600

            if not self._jwt_token:
                raise ValueError("Failed to extract JWT token from SDK response")

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

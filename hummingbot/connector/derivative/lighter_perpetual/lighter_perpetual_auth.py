import time
from typing import Any, Dict, Optional

from lighter import SignerClient, Configuration

from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


class LighterPerpetualAuth(AuthBase):
    """
    Authentication handler for Lighter Perpetual API.

    Lighter uses API key authentication for read operations and
    requires transaction signing for write operations via the lighter SDK SignerClient.

    This implementation integrates the lighter Python SDK for transaction signing.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        api_key_index: int = 0,
        account_index: int = 0
    ):
        """
        Initialize Lighter authentication with lighter SDK integration.

        Args:
            api_key: Lighter API key (public) - not directly used by SignerClient
            api_secret: Ethereum private key (hex string) for signing transactions
            api_key_index: API key index (default 0, Lighter supports up to 256 per sub-account)
            account_index: Sub-account index (default 0)
        """
        self._api_key: str = api_key
        self._api_secret: str = api_secret
        self._api_key_index: int = api_key_index
        self._account_index: int = account_index

        # Get Lighter mainnet URL from Configuration
        config = Configuration()
        self._url: str = config.host  # https://mainnet.zklighter.elliot.ai

        # Lazy-initialize SignerClient when needed
        self._signer_client: Optional[SignerClient] = None

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Add authentication headers to REST requests.

        Lighter typically uses API key in query params or headers for authenticated endpoints.

        Args:
            request: The REST request to authenticate

        Returns:
            Authenticated REST request with required headers/params
        """
        if request.headers is None:
            request.headers = {}

        # Add API key header (if Lighter uses header-based auth)
        # Note: Lighter may use different auth methods - verify with API docs
        request.headers["X-API-Key"] = self._api_key

        # For POST requests that modify account state (orders, transactions, etc.),
        # Lighter requires transaction signing. This will be implemented in a future iteration.
        if request.method == RESTMethod.POST:
            # TODO: Implement transaction signing
            # This requires:
            # 1. ZK proof generation or similar cryptography
            # 2. Message hashing according to Lighter's specification
            # 3. Signature generation using api_secret
            pass

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket requests.

        Lighter WebSocket authentication may require sending API key
        in the initial subscription message.

        Args:
            request: The WebSocket request to authenticate

        Returns:
            Authenticated WebSocket request
        """
        # WebSocket authentication will be implemented when WebSocket support is added
        # Typically requires sending auth message after connection:
        # {"type": "auth", "apiKey": "..."}
        return request

    def get_signer_client(self) -> SignerClient:
        """
        Get or create SignerClient for transaction signing.

        The SignerClient handles all transaction signing and submission internally.

        Returns:
            SignerClient instance
        """
        if self._signer_client is None:
            # Create SignerClient with mainnet URL and credentials
            self._signer_client = SignerClient(
                url=self._url,
                private_key=self._api_secret,  # Ethereum private key
                api_key_index=self._api_key_index,
                account_index=self._account_index
            )

        return self._signer_client

    def close(self):
        """
        Close the SignerClient connection if open.
        """
        if self._signer_client is not None:
            try:
                self._signer_client.close()
            except Exception:
                pass
            self._signer_client = None

    @staticmethod
    def _get_timestamp() -> float:
        """
        Get current Unix timestamp.

        Returns:
            Current time as float
        """
        return time.time()

    @staticmethod
    def _get_timestamp_ms() -> int:
        """
        Get current Unix timestamp in milliseconds.

        Returns:
            Current time in milliseconds
        """
        return int(time.time() * 1000)

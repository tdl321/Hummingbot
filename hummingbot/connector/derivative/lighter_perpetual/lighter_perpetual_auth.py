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

        Raises:
            RuntimeError: If Configuration initialization fails
        """
        self._api_key: str = api_key
        self._api_secret: str = api_secret
        self._api_key_index: int = api_key_index
        self._account_index: int = account_index

        # Get Lighter mainnet URL from Configuration
        try:
            config = Configuration()
            self._url: str = config.host  # https://mainnet.zklighter.elliot.ai
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Lighter Configuration. "
                f"Ensure lighter SDK is properly installed. Error: {str(e)}"
            ) from e

        # Lazy-initialize SignerClient when needed
        self._signer_client: Optional[SignerClient] = None

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Add authentication headers to REST requests.

        Lighter uses API key header for authenticated endpoints.

        Note: Order signing and transaction submission are handled by the
        lighter SDK (SignerClient) via get_signer_client(), not through
        this method. This method only adds the API key header for read-only
        account data endpoints.

        Args:
            request: The REST request to authenticate

        Returns:
            Authenticated REST request with X-API-Key header
        """
        if request.headers is None:
            request.headers = {}

        # Add API key header for read-only endpoints
        request.headers["X-API-Key"] = self._api_key

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket requests.

        Note: WebSocket authentication for private channels (user orders, positions)
        is not currently implemented. Public market data channels do not require
        authentication.

        When needed, Lighter WebSocket auth typically requires sending an auth
        message after connection with the API key.

        Args:
            request: The WebSocket request to authenticate

        Returns:
            WebSocket request (currently unmodified)
        """
        return request

    def get_signer_client(self) -> SignerClient:
        """
        Get or create SignerClient for transaction signing.

        The SignerClient handles all transaction signing and submission internally
        using the lighter SDK.

        Returns:
            SignerClient instance

        Raises:
            ValueError: If private key format is invalid
            RuntimeError: If client initialization fails
        """
        if self._signer_client is None:
            try:
                # Create SignerClient with mainnet URL and credentials
                self._signer_client = SignerClient(
                    url=self._url,
                    private_key=self._api_secret,  # Ethereum private key
                    api_key_index=self._api_key_index,
                    account_index=self._account_index
                )
            except ValueError as e:
                raise ValueError(
                    f"Invalid Ethereum private key format. "
                    f"Expected hex string (with or without '0x' prefix). Error: {str(e)}"
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize Lighter SignerClient. "
                    f"Ensure network connectivity to {self._url} and valid credentials. "
                    f"Error: {str(e)}"
                ) from e

        return self._signer_client

    def close(self):
        """
        Close the SignerClient connection if open.

        This method safely closes the SignerClient, catching and suppressing
        any exceptions during cleanup.
        """
        if self._signer_client is not None:
            try:
                self._signer_client.close()
            except Exception as e:
                # Suppress errors during cleanup, but could log them if logger available
                pass
            finally:
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

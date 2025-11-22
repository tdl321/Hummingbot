import time
from typing import Any, Dict, Optional

import fast_stark_crypto
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient

from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


class ExtendedPerpetualAuth(AuthBase):
    """
    Authentication handler for Extended Perpetual API.

    Extended uses:
    - X-Api-Key header for API authentication
    - Stark signatures for order placement and account operations (via x10 SDK)

    This implementation integrates the x10 Python SDK for Stark signature generation.
    """

    def __init__(self, api_key: str, api_secret: str, vault_id: Optional[str] = None):
        """
        Initialize Extended authentication with x10 SDK integration.

        Args:
            api_key: Extended API key (public)
            api_secret: Stark private key (hex string) for signing transactions
            vault_id: Vault/account identifier on Extended (optional, can be fetched from API)
        """
        self._api_key: str = api_key.strip() if api_key else api_key
        # Stark private key as hex string - normalize by stripping whitespace
        self._api_secret: str = api_secret.strip() if api_secret and isinstance(api_secret, str) else api_secret
        self._vault_id: Optional[str] = vault_id

        # Derive public key from private key
        try:
            # Convert hex private key to integer
            # Handle both '0x' prefixed and unprefixed hex strings
            if isinstance(self._api_secret, str):
                clean_secret = self._api_secret[2:] if self._api_secret.startswith('0x') else self._api_secret
                private_key_int = int(clean_secret, 16)
            else:
                raise ValueError("API secret must be a hex string")

            # Derive public key using Stark curve
            public_key_int = fast_stark_crypto.get_public_key(private_key_int)
            self._public_key = hex(public_key_int)
        except ValueError as e:
            self._public_key = None
            raise ValueError(
                f"Invalid Stark private key format. Expected hex string (with or without '0x' prefix). "
                f"Error: {str(e)}"
            ) from e
        except Exception as e:
            self._public_key = None
            raise RuntimeError(
                f"Failed to derive Stark public key from private key. "
                f"Ensure your api_secret is a valid Stark private key. Error: {str(e)}"
            ) from e

        # Lazy-initialize StarkPerpetualAccount and TradingClient when needed
        self._stark_account: Optional[StarkPerpetualAccount] = None
        self._trading_client: Optional[PerpetualTradingClient] = None

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Add authentication headers to REST requests.

        Extended requires X-Api-Key header for authenticated endpoints.

        Note: Order signing and state-modifying operations are handled by the
        x10 SDK (PerpetualTradingClient) via get_trading_client(), not through
        this method. This method only adds the API key header for read-only
        account data endpoints.

        Args:
            request: The REST request to authenticate

        Returns:
            Authenticated REST request with X-Api-Key header
        """
        if request.headers is None:
            request.headers = {}

        # Add API key header for read-only endpoints
        request.headers["X-Api-Key"] = self._api_key

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket requests.

        Note: WebSocket authentication for private channels (user orders, positions)
        is not currently implemented. Public market data channels do not require
        authentication.

        When needed, Extended WebSocket auth typically requires sending an auth
        message after connection with the API key.

        Args:
            request: The WebSocket request to authenticate

        Returns:
            WebSocket request (currently unmodified)
        """
        return request

    def _initialize_stark_account(self):
        """
        Initialize StarkPerpetualAccount if not already created.

        Requires vault_id to be set (either during init or fetched from API).

        Raises:
            ValueError: If vault_id is not set or public key derivation failed
            RuntimeError: If StarkPerpetualAccount initialization fails
        """
        if self._stark_account is None:
            if self._vault_id is None:
                raise ValueError(
                    "Cannot initialize Stark account: vault_id not set. "
                    "Fetch vault_id from Extended API using connector._ensure_vault_id() first."
                )
            if self._public_key is None:
                raise ValueError(
                    "Cannot initialize Stark account: public key derivation failed. "
                    "Check that api_secret is a valid Stark private key (hex string)."
                )

            try:
                self._stark_account = StarkPerpetualAccount(
                    vault=self._vault_id,
                    private_key=self._api_secret,
                    public_key=self._public_key,
                    api_key=self._api_key
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize StarkPerpetualAccount with vault={self._vault_id}. "
                    f"Error: {str(e)}"
                ) from e

    def get_trading_client(self) -> PerpetualTradingClient:
        """
        Get or create PerpetualTradingClient for order operations.

        The trading client handles all order signing and submission internally
        using the x10 SDK.

        Returns:
            PerpetualTradingClient instance

        Raises:
            ValueError: If vault_id or public key is not available
            RuntimeError: If client initialization fails
        """
        if self._trading_client is None:
            # Ensure Stark account is initialized
            self._initialize_stark_account()

            try:
                # Create trading client with mainnet config and Stark account
                self._trading_client = PerpetualTradingClient(
                    endpoint_config=MAINNET_CONFIG,
                    stark_account=self._stark_account
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize PerpetualTradingClient. "
                    f"Ensure network connectivity and valid credentials. Error: {str(e)}"
                ) from e

        return self._trading_client

    def set_vault_id(self, vault_id: str):
        """
        Set the vault ID after fetching from API.

        Args:
            vault_id: Vault/account identifier from Extended
        """
        self._vault_id = vault_id
        # Reset Stark account and trading client to reinitialize with new vault
        self._stark_account = None
        self._trading_client = None

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

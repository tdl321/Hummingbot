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
        self._api_key: str = api_key
        self._api_secret: str = api_secret  # Stark private key as hex string
        self._vault_id: Optional[str] = vault_id

        # Derive public key from private key
        try:
            # Convert hex private key to integer
            private_key_int = int(api_secret, 16) if isinstance(api_secret, str) and api_secret.startswith('0x') else int(api_secret, 16)
            # Derive public key
            public_key_int = fast_stark_crypto.get_public_key(private_key_int)
            self._public_key = hex(public_key_int)
        except Exception as e:
            self._public_key = None
            # Will raise error when trying to sign if public key derivation failed

        # Lazy-initialize StarkPerpetualAccount and TradingClient when needed
        self._stark_account: Optional[StarkPerpetualAccount] = None
        self._trading_client: Optional[PerpetualTradingClient] = None

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Add authentication headers to REST requests.

        Extended requires X-Api-Key header for all authenticated endpoints.

        Args:
            request: The REST request to authenticate

        Returns:
            Authenticated REST request with required headers
        """
        if request.headers is None:
            request.headers = {}

        # Add API key header (required for all private endpoints)
        request.headers["X-Api-Key"] = self._api_key

        # For POST requests that modify account state (orders, leverage, etc.),
        # Extended requires Stark signatures. This will be implemented in a future iteration.
        # For now, this provides read-only access to account data.
        if request.method == RESTMethod.POST:
            # TODO: Implement Stark signature for order placement
            # This requires:
            # 1. Stark curve cryptography (starknet.py or similar library)
            # 2. Message hashing according to Extended's specification
            # 3. Signature generation using api_secret
            pass

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket requests.

        Extended WebSocket authentication typically uses a connection token
        or API key in the initial subscription message.

        Args:
            request: The WebSocket request to authenticate

        Returns:
            Authenticated WebSocket request
        """
        # WebSocket authentication will be implemented when WebSocket support is added
        # Typically requires sending auth message after connection:
        # {"type": "subscribe", "channel": "user", "apiKey": "..."}
        return request

    def _initialize_stark_account(self):
        """
        Initialize StarkPerpetualAccount if not already created.

        Requires vault_id to be set (either during init or fetched from API).
        """
        if self._stark_account is None:
            if self._vault_id is None:
                raise ValueError("Cannot initialize Stark account: vault_id not set. "
                                 "Fetch vault_id from Extended API first.")
            if self._public_key is None:
                raise ValueError("Cannot initialize Stark account: public key derivation failed. "
                                 "Check that api_secret is a valid Stark private key.")

            self._stark_account = StarkPerpetualAccount(
                vault=self._vault_id,
                private_key=self._api_secret,
                public_key=self._public_key,
                api_key=self._api_key
            )

    def get_trading_client(self) -> PerpetualTradingClient:
        """
        Get or create PerpetualTradingClient for order operations.

        The trading client handles all order signing and submission internally.

        Returns:
            PerpetualTradingClient instance
        """
        if self._trading_client is None:
            # Ensure Stark account is initialized
            self._initialize_stark_account()

            # Create trading client with mainnet config and Stark account
            self._trading_client = PerpetualTradingClient(
                endpoint_config=MAINNET_CONFIG,
                stark_account=self._stark_account
            )

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

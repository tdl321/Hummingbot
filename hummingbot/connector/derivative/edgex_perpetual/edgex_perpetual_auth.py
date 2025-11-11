"""
EdgeX Perpetual Authentication

Handles ECDSA signature-based authentication for EdgeX API.

EdgeX uses per-request signature authentication (NOT JWT tokens like Paradex):
- Each request requires fresh ECDSA signature
- Signature includes: timestamp + HTTP method + path + sorted parameters
- SHA3 hashing before ECDSA signing
- Headers: X-edgeX-Api-Timestamp and X-edgeX-Api-Signature

Reference: https://edgex-1.gitbook.io/edgeX-documentation/api/authentication
"""

import hashlib
import time
from typing import Any, Dict
from urllib.parse import urlencode

from eth_account import Account
from eth_account.messages import encode_defunct

from hummingbot.connector.derivative.edgex_perpetual import edgex_perpetual_constants as CONSTANTS
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


class EdgexPerpetualAuth(AuthBase):
    """
    Authentication handler for EdgeX Perpetual API.

    EdgeX uses ECDSA signature authentication where each request must be signed
    with the user's private key. The signature is generated from:
    - Timestamp (milliseconds)
    - HTTP method (GET, POST, etc.)
    - Request path
    - Sorted query parameters or request body

    The message is hashed with SHA3-256, then signed with ECDSA.
    """

    def __init__(
        self,
        api_secret: str,
        account_id: str,
    ):
        """
        Initialize EdgeX authentication handler.

        Args:
            api_secret: Private key for signing requests (hex string with or without 0x prefix)
            account_id: EdgeX account ID
        """
        self._api_secret = api_secret
        self._account_id = account_id

        # Initialize eth_account for ECDSA signing
        # Remove '0x' prefix if present
        private_key = api_secret if not api_secret.startswith('0x') else api_secret[2:]
        self._account = Account.from_key(private_key)

    def _get_timestamp_ms(self) -> int:
        """
        Get current timestamp in milliseconds.

        Returns:
            Current Unix timestamp in milliseconds
        """
        return int(time.time() * 1000)

    def _generate_signature_message(
        self,
        timestamp: int,
        method: str,
        path: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate signature message string according to EdgeX specification.

        Format: {timestamp}{METHOD}{path}{sorted_params}

        Example from EdgeX docs:
        1735542383256GET/api/v1/private/account/getPositionTransactionPageaccountId=543429922991899150&filterTypeList=SETTLE_FUNDING_FEE&size=10

        Args:
            timestamp: Request timestamp in milliseconds
            method: HTTP method in uppercase (GET, POST, etc.)
            path: Request path (e.g., "/api/v1/private/order/createOrder")
            params: Query parameters (GET) or request body (POST) as dict

        Returns:
            Signature message string
        """
        # Sort parameters alphabetically by key
        if params:
            sorted_params = urlencode(sorted(params.items()))
        else:
            sorted_params = ""

        # Construct signature message
        message = f"{timestamp}{method.upper()}{path}{sorted_params}"
        return message

    def _sign_message(self, message: str) -> str:
        """
        Sign message with ECDSA after SHA3-256 hashing.

        Args:
            message: Message string to sign

        Returns:
            Hex signature string
        """
        # Hash message with SHA3-256
        message_hash = hashlib.sha3_256(message.encode('utf-8')).digest()

        # Sign with ECDSA using eth_account
        # Note: eth_account expects messages in specific format
        signable_message = encode_defunct(primitive=message_hash)
        signed_message = self._account.sign_message(signable_message)

        # Return signature as hex string (without 0x prefix)
        return signed_message.signature.hex()

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Add authentication headers to REST request.

        EdgeX requires two headers:
        - X-edgeX-Api-Timestamp: Request timestamp in milliseconds
        - X-edgeX-Api-Signature: ECDSA signature of request

        Args:
            request: REST request to authenticate

        Returns:
            Request with authentication headers added
        """
        if request.headers is None:
            request.headers = {}

        # Generate timestamp
        timestamp = self._get_timestamp_ms()

        # Extract method and path
        method = request.method.name  # RESTMethod enum to string (GET, POST, etc.)
        path = request.url if request.url.startswith('/') else f"/{request.url}"

        # Get parameters
        params = {}
        if method == "GET" and request.params:
            params = request.params
        elif method == "POST" and request.data:
            # For POST requests, use request body
            params = request.data if isinstance(request.data, dict) else {}

        # Generate signature message
        message = self._generate_signature_message(timestamp, method, path, params)

        # Sign message
        signature = self._sign_message(message)

        # Add authentication headers
        request.headers[CONSTANTS.HEADER_TIMESTAMP] = str(timestamp)
        request.headers[CONSTANTS.HEADER_SIGNATURE] = signature

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket request.

        EdgeX private WebSocket authentication method needs to be verified.
        Likely similar to REST API with signature in connection headers or
        initial message.

        Args:
            request: WebSocket request to authenticate

        Returns:
            Request with authentication added

        TODO: Verify EdgeX private WebSocket authentication method
        - Check if auth headers needed in connection
        - Check if auth message sent after connection
        - Implement based on EdgeX WebSocket documentation
        """
        # TODO: Implement WebSocket authentication
        # Placeholder for now
        return request

    @property
    def account_id(self) -> str:
        """Get EdgeX account ID."""
        return self._account_id

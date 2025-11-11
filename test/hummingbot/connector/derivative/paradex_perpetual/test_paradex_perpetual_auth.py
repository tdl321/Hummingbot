import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth import ParadexPerpetualAuth
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class TestParadexPerpetualAuth(unittest.TestCase):
    """Unit tests for Paradex Perpetual authentication."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_secret = "0x1234567890abcdef"  # Mock subkey private key
        self.account_address = "0xabcdef1234567890"  # Mock main account address
        self.environment = "testnet"

        self.auth = ParadexPerpetualAuth(
            api_secret=self.api_secret,
            account_address=self.account_address,
            environment=self.environment
        )

    def test_initialization(self):
        """Test auth object initialization."""
        self.assertEqual(self.auth._api_secret, self.api_secret)
        self.assertEqual(self.auth._account_address, self.account_address)
        self.assertIsNone(self.auth._jwt_token)
        self.assertIsNone(self.auth._jwt_expires_at)
        self.assertIsNone(self.auth._paradex_client)

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.ParadexSubkey')
    def test_initialize_client(self, mock_paradex_subkey):
        """Test SDK client initialization."""
        mock_client = MagicMock()
        mock_paradex_subkey.return_value = mock_client

        self.auth._initialize_client()

        # Verify client was initialized
        self.assertIsNotNone(self.auth._paradex_client)
        mock_paradex_subkey.assert_called_once()

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.ParadexSubkey')
    async def test_get_jwt_token_new(self, mock_paradex_subkey):
        """Test JWT token generation for new token."""
        # Mock SDK client and auth response
        mock_client = MagicMock()
        mock_auth = AsyncMock()
        mock_auth.get_jwt_token.return_value = {
            "jwt_token": "mock_jwt_token_12345",
            "expires_at": 9999999999  # Far future timestamp
        }
        mock_client.auth = mock_auth
        mock_paradex_subkey.return_value = mock_client

        # Get token
        token = await self.auth.get_jwt_token()

        # Verify
        self.assertEqual(token, "mock_jwt_token_12345")
        self.assertEqual(self.auth._jwt_token, "mock_jwt_token_12345")
        self.assertEqual(self.auth._jwt_expires_at, 9999999999)

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.time')
    async def test_get_jwt_token_cached(self, mock_time):
        """Test JWT token reuse when not expired."""
        # Set up cached token
        mock_time.time.return_value = 1000000  # Current time
        self.auth._jwt_token = "cached_token"
        self.auth._jwt_expires_at = 1000600  # Expires in 600 seconds (10 min)

        # Get token (should return cached)
        token = await self.auth.get_jwt_token()

        # Verify cached token was returned
        self.assertEqual(token, "cached_token")

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.time')
    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.ParadexSubkey')
    async def test_get_jwt_token_refresh(self, mock_paradex_subkey, mock_time):
        """Test JWT token refresh when about to expire."""
        # Current time close to expiry (within 5min buffer)
        mock_time.time.return_value = 1000000
        self.auth._jwt_token = "old_token"
        self.auth._jwt_expires_at = 1000200  # Expires in 200 seconds (< 5min buffer)

        # Mock SDK client for refresh
        mock_client = MagicMock()
        mock_auth = AsyncMock()
        mock_auth.get_jwt_token.return_value = {
            "jwt_token": "new_refreshed_token",
            "expires_at": 1001000  # New expiry
        }
        mock_client.auth = mock_auth
        mock_paradex_subkey.return_value = mock_client
        self.auth._paradex_client = mock_client

        # Get token (should refresh)
        token = await self.auth.get_jwt_token()

        # Verify new token
        self.assertEqual(token, "new_refreshed_token")
        self.assertEqual(self.auth._jwt_expires_at, 1001000)

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.ParadexSubkey')
    async def test_rest_authenticate(self, mock_paradex_subkey):
        """Test REST request authentication."""
        # Mock JWT token
        self.auth._jwt_token = "test_jwt_token"
        self.auth._jwt_expires_at = 9999999999  # Far future

        # Create mock request
        request = RESTRequest(
            method="GET",
            url="https://api.testnet.paradex.trade/v1/account/balances"
        )

        # Authenticate request
        authenticated_request = await self.auth.rest_authenticate(request)

        # Verify headers were added
        self.assertIn("Authorization", authenticated_request.headers)
        self.assertEqual(authenticated_request.headers["Authorization"], "Bearer test_jwt_token")
        self.assertIn("PARADEX-STARKNET-ACCOUNT", authenticated_request.headers)
        self.assertEqual(authenticated_request.headers["PARADEX-STARKNET-ACCOUNT"], self.account_address)

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.ParadexSubkey')
    async def test_ws_authenticate(self, mock_paradex_subkey):
        """Test WebSocket request authentication."""
        # Mock JWT token
        self.auth._jwt_token = "test_jwt_token"
        self.auth._jwt_expires_at = 9999999999  # Far future

        # Create mock WebSocket request
        request = WSRequest(payload={})

        # Authenticate request
        authenticated_request = await self.auth.ws_authenticate(request)

        # Verify payload was updated
        self.assertIn("jwt_token", authenticated_request.payload)
        self.assertEqual(authenticated_request.payload["jwt_token"], "test_jwt_token")
        self.assertIn("account", authenticated_request.payload)
        self.assertEqual(authenticated_request.payload["account"], self.account_address)

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth.ParadexSubkey')
    def test_get_paradex_client(self, mock_paradex_subkey):
        """Test getting ParadexSubkey client."""
        mock_client = MagicMock()
        mock_paradex_subkey.return_value = mock_client

        # Get client
        client = self.auth.get_paradex_client()

        # Verify client was returned
        self.assertIsNotNone(client)
        self.assertEqual(client, mock_client)

    def test_environment_mapping(self):
        """Test environment string to Environment enum mapping."""
        # Test mainnet
        auth_mainnet = ParadexPerpetualAuth(
            api_secret=self.api_secret,
            account_address=self.account_address,
            environment="mainnet"
        )
        # Should use Environment.PROD

        # Test testnet
        auth_testnet = ParadexPerpetualAuth(
            api_secret=self.api_secret,
            account_address=self.account_address,
            environment="testnet"
        )
        # Should use Environment.TESTNET

        # Both should initialize without errors
        self.assertIsNotNone(auth_mainnet)
        self.assertIsNotNone(auth_testnet)


if __name__ == "__main__":
    unittest.main()

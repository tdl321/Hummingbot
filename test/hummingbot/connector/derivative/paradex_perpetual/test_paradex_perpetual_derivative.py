import asyncio
import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict

from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative import ParadexPerpetualDerivative
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder


class TestParadexPerpetualDerivative(unittest.TestCase):
    """Unit tests for Paradex Perpetual main connector."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_secret = "0x1234567890abcdef"
        self.account_address = "0xabcdef1234567890"
        self.trading_pairs = ["BTC-USD-PERP", "ETH-USD-PERP"]

        # Create connector instance
        self.connector = ParadexPerpetualDerivative(
            paradex_perpetual_api_secret=self.api_secret,
            paradex_perpetual_account_address=self.account_address,
            trading_pairs=self.trading_pairs,
            trading_required=False,
            domain="paradex_perpetual_testnet"
        )

    def test_initialization(self):
        """Test connector initialization."""
        self.assertEqual(self.connector.name, "paradex_perpetual_testnet")
        self.assertEqual(self.connector._trading_pairs, self.trading_pairs)
        self.assertFalse(self.connector._trading_required)

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative.ParadexPerpetualDerivative._api_get')
    async def test_update_balances(self, mock_api_get):
        """Test balance update from API."""
        # Mock API response
        mock_api_get.return_value = {
            "balances": [
                {
                    "asset": "USDC",
                    "total": "1000.50",
                    "available": "950.00",
                    "locked": "50.50"
                },
                {
                    "asset": "BTC",
                    "total": "0.5",
                    "available": "0.5",
                    "locked": "0"
                }
            ]
        }

        # Update balances
        await self.connector._update_balances()

        # Verify balances were updated
        self.assertEqual(self.connector._account_balances["USDC"], Decimal("1000.50"))
        self.assertEqual(self.connector._account_available_balances["USDC"], Decimal("950.00"))
        self.assertEqual(self.connector._account_balances["BTC"], Decimal("0.5"))
        self.assertEqual(self.connector._account_available_balances["BTC"], Decimal("0.5"))

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative.ParadexPerpetualDerivative._api_get')
    async def test_update_positions(self, mock_api_get):
        """Test position update from API."""
        # Mock API response
        mock_api_get.return_value = {
            "positions": [
                {
                    "market": "BTC-USD-PERP",
                    "side": "LONG",
                    "size": "1.5",
                    "entry_price": "49500.00",
                    "mark_price": "50000.00",
                    "liquidation_price": "45000.00",
                    "unrealized_pnl": "750.00",
                    "leverage": "10"
                }
            ]
        }

        # Update positions
        await self.connector._update_positions()

        # Verify positions were updated
        self.assertIn("BTC-USD-PERP", self.connector.account_positions)
        position = self.connector.account_positions["BTC-USD-PERP"]
        self.assertEqual(position.amount, Decimal("1.5"))
        self.assertEqual(position.position_side.name, "LONG")

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative.ParadexPerpetualDerivative._api_get')
    async def test_update_trading_rules(self, mock_api_get):
        """Test trading rules update from API."""
        # Mock API response (corrected to use "results" key)
        mock_api_get.return_value = {
            "results": [
                {
                    "market": "BTC-USD-PERP",
                    "status": "ACTIVE",
                    "min_order_size": "0.001",
                    "max_order_size": "100.0",
                    "tick_size": "0.1",
                    "step_size": "0.001"
                },
                {
                    "market": "ETH-USD-PERP",
                    "status": "ACTIVE",
                    "min_order_size": "0.01",
                    "max_order_size": "1000.0",
                    "tick_size": "0.01",
                    "step_size": "0.01"
                }
            ]
        }

        # Update trading rules
        await self.connector._update_trading_rules()

        # Verify trading rules were updated
        self.assertIn("BTC-USD-PERP", self.connector._trading_rules)
        btc_rule = self.connector._trading_rules["BTC-USD-PERP"]
        self.assertEqual(btc_rule.min_order_size, Decimal("0.001"))
        self.assertEqual(btc_rule.max_order_size, Decimal("100.0"))
        self.assertEqual(btc_rule.min_price_increment, Decimal("0.1"))
        self.assertEqual(btc_rule.min_base_amount_increment, Decimal("0.001"))

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative.ParadexPerpetualAuth.get_paradex_client')
    async def test_place_order(self, mock_get_client):
        """Test order placement via SDK."""
        # Mock SDK client
        mock_client = AsyncMock()
        mock_client.submit_order.return_value = {
            "id": "ORDER_123456",
            "created_at": 1699564800000  # Milliseconds
        }
        mock_get_client.return_value = mock_client

        # Place order
        order_id = "HBOT_BUY_BTC_123"
        exchange_order_id, created_at = await self.connector._place_order(
            order_id=order_id,
            trading_pair="BTC-USD-PERP",
            amount=Decimal("0.1"),
            trade_type=TradeType.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000.0")
        )

        # Verify order was placed
        self.assertEqual(exchange_order_id, "ORDER_123456")
        self.assertEqual(created_at, 1699564800.0)  # Converted to seconds

        # Verify SDK was called correctly
        mock_client.submit_order.assert_called_once()
        call_kwargs = mock_client.submit_order.call_args[1]
        self.assertEqual(call_kwargs["market"], "BTC-USD-PERP")
        self.assertEqual(call_kwargs["side"], "BUY")
        self.assertEqual(call_kwargs["size"], "0.1")
        self.assertEqual(call_kwargs["order_type"], "LIMIT")
        self.assertEqual(call_kwargs["price"], "50000.0")
        self.assertEqual(call_kwargs["client_id"], order_id)

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative.ParadexPerpetualAuth.get_paradex_client')
    async def test_place_cancel(self, mock_get_client):
        """Test order cancellation via SDK."""
        # Mock SDK client
        mock_client = AsyncMock()
        mock_client.cancel_order.return_value = {"status": "CANCELLED"}
        mock_get_client.return_value = mock_client

        # Create tracked order
        order = InFlightOrder(
            client_order_id="HBOT_BUY_BTC_123",
            exchange_order_id="ORDER_123456",
            trading_pair="BTC-USD-PERP",
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("0.1"),
            price=Decimal("50000.0"),
            creation_timestamp=1699564800.0
        )

        # Cancel order
        await self.connector._place_cancel("ORDER_123456", order)

        # Verify SDK was called
        mock_client.cancel_order.assert_called_once_with(order_id="ORDER_123456")

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative.ParadexPerpetualDerivative._api_get')
    async def test_update_funding_rates(self, mock_api_get):
        """Test funding rate updates."""
        # Mock API responses for each trading pair
        mock_api_get.side_effect = [
            {
                "funding_rate": "0.0001",
                "next_funding_time": 1699564800
            },
            {
                "funding_rate": "-0.0002",
                "next_funding_time": 1699564800
            }
        ]

        # Update funding rates
        await self.connector._update_funding_rates()

        # Verify funding rates were updated
        self.assertEqual(self.connector._funding_rates["BTC-USD-PERP"], Decimal("0.0001"))
        self.assertEqual(self.connector._funding_rates["ETH-USD-PERP"], Decimal("-0.0002"))

    def test_supported_order_types(self):
        """Test supported order types."""
        supported_types = self.connector.supported_order_types()

        # Verify basic order types are supported
        self.assertIn(OrderType.LIMIT, supported_types)
        self.assertIn(OrderType.MARKET, supported_types)

    def test_is_order_not_found_during_status_update(self):
        """Test order not found detection."""
        # Create mock exception with 404 status
        exception_with_404 = Exception("404 Not Found")

        # Verify detection
        is_not_found = self.connector._is_order_not_found_during_status_update_error(exception_with_404)
        self.assertTrue(is_not_found)

    def test_is_order_not_found_during_cancelation(self):
        """Test order not found during cancellation detection."""
        # Create mock exception
        exception_with_404 = Exception("Order not found: 404")

        # Verify detection
        is_not_found = self.connector._is_order_not_found_during_cancelation_error(exception_with_404)
        self.assertTrue(is_not_found)


if __name__ == "__main__":
    unittest.main()

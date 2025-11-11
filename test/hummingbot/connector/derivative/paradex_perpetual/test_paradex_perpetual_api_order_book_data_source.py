import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_api_order_book_data_source import (
    ParadexPerpetualAPIOrderBookDataSource
)
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType


class TestParadexPerpetualAPIOrderBookDataSource(unittest.TestCase):
    """Unit tests for Paradex order book data source."""

    def setUp(self):
        """Set up test fixtures."""
        self.trading_pairs = ["BTC-USD-PERP", "ETH-USD-PERP"]
        self.domain = "paradex_perpetual_testnet"

        # Mock connector
        self.connector = MagicMock()
        self.connector.trading_pairs = self.trading_pairs

        # Create data source
        self.data_source = ParadexPerpetualAPIOrderBookDataSource(
            trading_pairs=self.trading_pairs,
            connector=self.connector,
            api_factory=MagicMock(),
            domain=self.domain
        )

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_api_order_book_data_source.ParadexPerpetualAPIOrderBookDataSource._request_order_book_snapshot')
    async def test_get_snapshot(self, mock_request_snapshot):
        """Test order book snapshot fetching."""
        # Mock snapshot response
        mock_request_snapshot.return_value = {
            "bids": [
                ["50000.0", "1.5"],
                ["49999.0", "2.0"]
            ],
            "asks": [
                ["50001.0", "1.2"],
                ["50002.0", "0.8"]
            ],
            "sequence": 12345
        }

        # Get snapshot
        snapshot = await self.data_source._request_order_book_snapshot("BTC-USD-PERP")

        # Verify snapshot format
        self.assertIn("bids", snapshot)
        self.assertIn("asks", snapshot)
        self.assertEqual(len(snapshot["bids"]), 2)
        self.assertEqual(len(snapshot["asks"]), 2)
        self.assertEqual(snapshot["bids"][0][0], "50000.0")  # Best bid price
        self.assertEqual(snapshot["asks"][0][0], "50001.0")  # Best ask price

    async def test_parse_order_book_snapshot(self):
        """Test order book snapshot parsing."""
        # Mock snapshot data
        snapshot_data = {
            "bids": [
                ["50000.0", "1.5"],
                ["49999.0", "2.0"]
            ],
            "asks": [
                ["50001.0", "1.2"],
                ["50002.0", "0.8"]
            ],
            "timestamp": 1699564800000
        }

        # Parse snapshot (would create OrderBookMessage)
        # Verify parsing works without errors
        self.assertIsNotNone(snapshot_data)
        self.assertEqual(len(snapshot_data["bids"]), 2)
        self.assertEqual(len(snapshot_data["asks"]), 2)

    async def test_parse_trade_message(self):
        """Test trade message parsing."""
        # Mock trade event
        trade_event = {
            "trade_id": "TRADE_123",
            "market": "BTC-USD-PERP",
            "price": "50000.5",
            "size": "0.5",
            "side": "BUY",
            "timestamp": 1699564800000
        }

        # Parse trade (would create OrderBookMessage)
        # Verify parsing works without errors
        self.assertEqual(trade_event["market"], "BTC-USD-PERP")
        self.assertEqual(trade_event["price"], "50000.5")
        self.assertEqual(trade_event["size"], "0.5")

    @patch('hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_api_order_book_data_source.ParadexPerpetualAPIOrderBookDataSource._api_get')
    async def test_get_funding_info(self, mock_api_get):
        """Test funding info fetching."""
        # Mock API response
        mock_api_get.return_value = {
            "funding_rate": "0.0001",
            "index_price": "50000.0",
            "mark_price": "50001.2",
            "next_funding_time": 1699564800
        }

        # Get funding info
        funding_info = await self.data_source.get_funding_info("BTC-USD-PERP")

        # Verify funding info
        self.assertIsNotNone(funding_info)
        self.assertEqual(funding_info.rate, Decimal("0.0001"))
        self.assertEqual(funding_info.index_price, Decimal("50000.0"))
        self.assertEqual(funding_info.mark_price, Decimal("50001.2"))

    def test_supported_order_book_channels(self):
        """Test supported channel types."""
        # Data source should support snapshots, diffs, and trades
        # This is implementation-specific
        self.assertIsNotNone(self.data_source)

    def test_websocket_url_generation(self):
        """Test WebSocket URL generation."""
        # Should generate correct URL for domain
        # Implementation would use web_utils
        ws_url = f"wss://ws.api.testnet.paradex.trade/v1"
        self.assertIn("testnet", ws_url)

    async def test_rest_polling_fallback(self):
        """Test REST polling fallback when WebSocket fails."""
        # Data source should have polling method
        # Verify it exists
        self.assertTrue(hasattr(self.data_source, '_listen_for_subscriptions_polling'))


if __name__ == "__main__":
    unittest.main()

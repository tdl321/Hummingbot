"""
EdgeX Perpetual API Order Book Data Source

Handles market data streaming via WebSocket and REST API including:
- Order book snapshots and updates
- Public trade feed
- Funding rate data

WebSocket channels (verified from EdgeX docs):
- depth.{contractId}.200 - Order book with 200 levels
- trades.{contractId} - Public trades
- ticker.{contractId} - Ticker data (includes funding rates)
"""

import asyncio
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from hummingbot.connector.derivative.edgex_perpetual import (
    edgex_perpetual_constants as CONSTANTS,
    edgex_perpetual_web_utils as web_utils,
)
from hummingbot.core.data_type.funding_info import FundingInfo
from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.core.data_type.perpetual_api_order_book_data_source import PerpetualAPIOrderBookDataSource
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant

if TYPE_CHECKING:
    from hummingbot.connector.derivative.edgex_perpetual.edgex_perpetual_derivative import EdgexPerpetualDerivative


class EdgexPerpetualAPIOrderBookDataSource(PerpetualAPIOrderBookDataSource):
    """
    Order book data source for EdgeX Perpetual.

    Manages WebSocket subscriptions for market data:
    - Order book depth (snapshots and updates)
    - Public trades
    - Funding rates (via ticker channel)

    Implements REST API fallback for reliability.
    """

    def __init__(
        self,
        trading_pairs: List[str],
        connector: "EdgexPerpetualDerivative",
        api_factory: WebAssistantsFactory,
        domain: str = CONSTANTS.DOMAIN,
    ):
        """
        Initialize order book data source.

        Args:
            trading_pairs: List of trading pairs to track
            connector: Parent connector instance
            api_factory: Web assistants factory
            domain: Domain (mainnet or testnet)
        """
        super().__init__(trading_pairs)
        self._connector = connector
        self._api_factory = api_factory
        self._domain = domain
        self._ws_assistant: Optional[WSAssistant] = None

        # Message queues for different data types
        self._message_queue: Dict[str, asyncio.Queue] = {}
        self._snapshot_messages_queue_key = "order_book_snapshots"
        self._diff_messages_queue_key = "order_book_diffs"
        self._trade_messages_queue_key = "trades"
        self._funding_info_messages_queue_key = "funding_info"

    async def get_last_traded_prices(
        self, trading_pairs: List[str], domain: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        Get last traded prices for trading pairs.

        Args:
            trading_pairs: List of trading pairs
            domain: Domain (uses instance domain if None)

        Returns:
            Dict mapping trading pair to last traded price

        TODO: Implement in Phase 4
        - Fetch from ticker API or recent trades
        - Parse response and extract last price
        """
        raise NotImplementedError("get_last_traded_prices to be implemented in Phase 4")

    async def _request_order_book_snapshot(self, trading_pair: str) -> Dict[str, Any]:
        """
        Request order book snapshot via REST API.

        Args:
            trading_pair: Trading pair

        Returns:
            Order book snapshot data

        TODO: Implement in Phase 4
        - Fetch from order book REST endpoint
        - Parse bids and asks
        - Return in standard format
        """
        raise NotImplementedError("_request_order_book_snapshot to be implemented in Phase 4")

    async def _subscribe_channels(self, ws_assistant: WSAssistant):
        """
        Subscribe to WebSocket channels for market data.

        EdgeX WebSocket subscription format (verified from docs):
        {
          "type": "subscribe",
          "channel": "channel_name"
        }

        Channels to subscribe:
        - depth.{contractId}.200 - Order book with 200 levels
        - trades.{contractId} - Public trades
        - ticker.{contractId} - Ticker (includes funding rates)

        Args:
            ws_assistant: WebSocket assistant

        TODO: Implement in Phase 4
        - Get contractId for each trading pair
        - Send subscription messages for all channels
        - Handle subscription confirmations
        """
        raise NotImplementedError("_subscribe_channels to be implemented in Phase 4")

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """
        Create and connect WebSocket assistant for public data.

        Uses EdgeX public WebSocket URL (no authentication needed).

        Returns:
            Connected WSAssistant instance

        TODO: Implement in Phase 4
        - Get public WebSocket URL
        - Create WSAssistant
        - Connect to WebSocket
        - Subscribe to channels
        """
        raise NotImplementedError("_connected_websocket_assistant to be implemented in Phase 4")

    async def _parse_order_book_diff_message(
        self, raw_message: Dict[str, Any], message_queue: asyncio.Queue
    ):
        """
        Parse order book diff/update message from WebSocket.

        EdgeX WebSocket message format (from docs):
        {
          "type": "message",
          "channel": "depth.{contractId}.200",
          "dataType": "Changed",  // "Snapshot" or "Changed"
          "data": [...]
        }

        Args:
            raw_message: Raw WebSocket message
            message_queue: Queue to put parsed message

        TODO: Implement in Phase 4
        - Check message type and channel
        - Parse bid/ask updates
        - Convert to OrderBookMessage
        - Put in queue
        """
        pass  # Placeholder for Phase 4

    async def _parse_order_book_snapshot_message(
        self, raw_message: Dict[str, Any], message_queue: asyncio.Queue
    ):
        """
        Parse order book snapshot message from WebSocket.

        Args:
            raw_message: Raw WebSocket message
            message_queue: Queue to put parsed message

        TODO: Implement in Phase 4
        - Check for "Snapshot" dataType
        - Parse full order book
        - Convert to OrderBookMessage
        - Put in queue
        """
        pass  # Placeholder for Phase 4

    async def _parse_trade_message(
        self, raw_message: Dict[str, Any], message_queue: asyncio.Queue
    ):
        """
        Parse trade message from WebSocket.

        Channel: trades.{contractId}

        Args:
            raw_message: Raw WebSocket message
            message_queue: Queue to put parsed message

        TODO: Implement in Phase 4
        - Parse trade data (price, size, side, timestamp)
        - Convert to OrderBookMessage
        - Put in queue
        """
        pass  # Placeholder for Phase 4

    async def _parse_funding_info_message(
        self, raw_message: Dict[str, Any], message_queue: asyncio.Queue
    ):
        """
        Parse funding rate info from ticker channel.

        Channel: ticker.{contractId}

        Args:
            raw_message: Raw WebSocket message
            message_queue: Queue to put parsed FundingInfo

        TODO: Implement in Phase 4
        - Extract funding rate from ticker data
        - Extract next funding time
        - Create FundingInfo object
        - Put in queue
        """
        pass  # Placeholder for Phase 4

    async def listen_for_subscriptions(self):
        """
        Main WebSocket listener loop.

        Connects to EdgeX public WebSocket, subscribes to channels,
        and routes messages to appropriate parsers.

        Implements reconnection logic with exponential backoff.

        TODO: Implement in Phase 4
        - Connect to WebSocket
        - Subscribe to channels
        - Listen for messages
        - Route to appropriate parser
        - Handle ping/pong (EdgeX requires pong within 5 attempts)
        - Reconnect on disconnect
        """
        raise NotImplementedError("listen_for_subscriptions to be implemented in Phase 4")

    async def listen_for_order_book_diffs(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        """
        Listen for order book diff messages and output to queue.

        Args:
            ev_loop: Event loop
            output: Output queue

        TODO: Implement in Phase 4
        """
        raise NotImplementedError("listen_for_order_book_diffs to be implemented in Phase 4")

    async def listen_for_order_book_snapshots(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        """
        Listen for order book snapshot messages and output to queue.

        Args:
            ev_loop: Event loop
            output: Output queue

        TODO: Implement in Phase 4
        """
        raise NotImplementedError("listen_for_order_book_snapshots to be implemented in Phase 4")

    async def listen_for_trades(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        """
        Listen for trade messages and output to queue.

        Args:
            ev_loop: Event loop
            output: Output queue

        TODO: Implement in Phase 4
        """
        raise NotImplementedError("listen_for_trades to be implemented in Phase 4")

    async def listen_for_funding_info(self, output: asyncio.Queue):
        """
        Listen for funding info updates and output to queue.

        Args:
            output: Output queue

        TODO: Implement in Phase 4
        """
        raise NotImplementedError("listen_for_funding_info to be implemented in Phase 4")

    async def get_funding_info(self, trading_pair: str) -> FundingInfo:
        """
        Get current funding info for trading pair.

        Args:
            trading_pair: Trading pair

        Returns:
            FundingInfo with current funding rate and next funding time

        TODO: Implement in Phase 4
        - Fetch from REST API or cached WebSocket data
        - Parse funding rate and timing
        - Return FundingInfo object
        """
        raise NotImplementedError("get_funding_info to be implemented in Phase 4")

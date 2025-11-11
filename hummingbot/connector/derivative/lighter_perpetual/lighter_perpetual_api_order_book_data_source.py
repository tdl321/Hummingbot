import asyncio
import time
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_web_utils as web_utils
from hummingbot.core.data_type.common import TradeType
from hummingbot.core.data_type.funding_info import FundingInfo, FundingInfoUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.perpetual_api_order_book_data_source import PerpetualAPIOrderBookDataSource
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_derivative import (
        LighterPerpetualDerivative,
    )


class LighterPerpetualAPIOrderBookDataSource(PerpetualAPIOrderBookDataSource):
    """
    Order book data source for Lighter Perpetual.

    Handles:
    - Fetching order books from REST API
    - Listening to order book updates via WebSocket
    - Fetching and monitoring funding rates (CRITICAL for arbitrage strategy!)
    - Trade data streaming
    """

    _bpobds_logger: Optional[HummingbotLogger] = None

    def __init__(
            self,
            trading_pairs: List[str],
            connector: 'LighterPerpetualDerivative',
            api_factory: WebAssistantsFactory,
            domain: str = CONSTANTS.DOMAIN
    ):
        super().__init__(trading_pairs)
        self._connector = connector
        self._api_factory = api_factory
        self._domain = domain
        self._trading_pairs: List[str] = trading_pairs
        self._message_queue: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._snapshot_messages_queue_key = "order_book_snapshot"
        self._market_id_map: Dict[str, int] = {}  # trading_pair -> market_id

    async def _initialize_market_mappings(self):
        """
        Fetch market mappings from Lighter API.

        Lighter uses integer market IDs (e.g., 33 for KAITO).
        This method populates the _market_id_map.
        """
        if self._market_id_map:
            return  # Already initialized

        # GET /api/v1/orderBooks
        response = await self._connector._api_get(
            path_url=CONSTANTS.ORDER_BOOKS_URL,
            limit_id=CONSTANTS.ORDER_BOOKS_URL
        )

        if isinstance(response, dict) and 'order_books' in response:
            order_books = response['order_books']
            for book in order_books:
                symbol = book.get('symbol', '').upper()
                market_id = book.get('market_id')
                if symbol and market_id is not None:
                    # Create trading pair format: "KAITO-USD"
                    trading_pair = f"{symbol}-{CONSTANTS.CURRENCY}"
                    self._market_id_map[trading_pair] = market_id
                    self.logger().debug(f"Lighter market mapping: {trading_pair} -> market_id {market_id}")

        self.logger().info(f"Initialized {len(self._market_id_map)} Lighter market mappings")

    def _get_market_id(self, trading_pair: str) -> Optional[int]:
        """Get market ID for a trading pair."""
        return self._market_id_map.get(trading_pair)

    async def get_last_traded_prices(self,
                                     trading_pairs: List[str],
                                     domain: Optional[str] = None) -> Dict[str, float]:
        """Get last traded prices for trading pairs."""
        return await self._connector.get_last_traded_prices(trading_pairs=trading_pairs)

    async def get_funding_info(self, trading_pair: str) -> FundingInfo:
        """
        Fetch current funding rate information for a trading pair.

        This is CRITICAL for the funding rate arbitrage strategy!

        Lighter API: GET /api/v1/fundings
        Parameters: market_id, resolution, start_timestamp, end_timestamp, count_back

        Args:
            trading_pair: Trading pair (e.g., "KAITO-USD")

        Returns:
            FundingInfo object with rate, index/mark prices, next funding time
        """
        # Ensure market mappings are loaded
        if not self._market_id_map:
            await self._initialize_market_mappings()

        market_id = self._get_market_id(trading_pair)
        if market_id is None:
            self.logger().warning(f"Market ID not found for {trading_pair}")
            return FundingInfo(
                trading_pair=trading_pair,
                index_price=Decimal("0"),
                mark_price=Decimal("0"),
                next_funding_utc_timestamp=self._next_funding_time(),
                rate=Decimal("0"),
            )

        # Get latest funding rate
        # Lighter: GET /api/v1/fundings?market_id={id}&resolution=1h&count_back=1
        end_time = int(time.time())
        start_time = end_time - 3600  # 1 hour ago

        params = {
            "market_id": market_id,
            "resolution": "1h",
            "start_timestamp": start_time,
            "end_timestamp": end_time,
            "count_back": 1  # Only get the most recent
        }

        funding_response = await self._connector._api_get(
            path_url=CONSTANTS.FUNDING_RATES_URL,
            params=params
        )

        # Parse Lighter response: {"code": 200, "resolution": "1h", "fundings": [...]}
        funding_rate = Decimal("0")
        if isinstance(funding_response, dict) and 'fundings' in funding_response:
            fundings = funding_response['fundings']
            if fundings and len(fundings) > 0:
                latest = fundings[-1]  # Most recent
                value = latest.get('value', '0')
                direction = latest.get('direction', '')

                funding_rate = Decimal(str(value))

                # Apply direction: "long" means longs pay shorts (positive rate)
                # "short" means shorts pay longs (negative rate)
                if direction == "long":
                    funding_rate = -funding_rate

        # Get mark/index prices from order book or recent trades
        # Lighter doesn't have a direct mark price endpoint, so we use last traded price
        mark_price = Decimal(str(await self._connector._get_last_traded_price(trading_pair)))
        index_price = mark_price  # Use same as mark for now

        # Calculate next funding time
        # Lighter has 1-hour funding intervals (every hour on the hour)
        next_funding_timestamp = self._next_funding_time()

        funding_info = FundingInfo(
            trading_pair=trading_pair,
            index_price=index_price,
            mark_price=mark_price,
            next_funding_utc_timestamp=next_funding_timestamp,
            rate=funding_rate,
        )
        return funding_info

    def _next_funding_time(self) -> int:
        """
        Calculate next funding time.

        Lighter funding occurs every 1 hour on the hour (00:00, 01:00, 02:00, etc. UTC).

        Returns:
            Unix timestamp of next funding time
        """
        current_time = int(time.time())
        current_hour_start = (current_time // 3600) * 3600
        next_funding_time = current_hour_start + 3600  # Next hour
        return next_funding_time

    async def listen_for_funding_info(self, output: asyncio.Queue):
        """
        Continuously monitor and update funding rate information.

        Polls every FUNDING_RATE_UPDATE_INTERNAL_SECOND (1 hour for Lighter).
        """
        while True:
            try:
                for trading_pair in self._trading_pairs:
                    funding_info = await self.get_funding_info(trading_pair)
                    funding_info_update = FundingInfoUpdate(
                        trading_pair=trading_pair,
                        index_price=funding_info.index_price,
                        mark_price=funding_info.mark_price,
                        next_funding_utc_timestamp=funding_info.next_funding_utc_timestamp,
                        rate=funding_info.rate,
                    )
                    output.put_nowait(funding_info_update)
                await self._sleep(CONSTANTS.FUNDING_RATE_UPDATE_INTERNAL_SECOND)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().exception("Unexpected error when processing funding info updates from Lighter")
                await self._sleep(CONSTANTS.FUNDING_RATE_UPDATE_INTERNAL_SECOND)

    async def _request_order_book_snapshot(self, trading_pair: str) -> Dict[str, Any]:
        """Fetch order book snapshot from REST API."""
        # Ensure market mappings are loaded
        if not self._market_id_map:
            await self._initialize_market_mappings()

        market_id = self._get_market_id(trading_pair)
        if market_id is None:
            self.logger().warning(f"Market ID not found for {trading_pair}")
            return {}

        # Lighter: GET /api/v1/orderbook?market_id={id}
        params = {"market_id": market_id}
        data = await self._connector._api_get(
            path_url=CONSTANTS.ORDER_BOOK_URL,
            params=params,
            limit_id=CONSTANTS.ORDER_BOOK_URL
        )
        return data

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        """Parse order book snapshot into OrderBookMessage."""
        snapshot_response: Dict[str, Any] = await self._request_order_book_snapshot(trading_pair)

        # Lighter response format: {"code": 200, "bids": [...], "asks": [...], ...}
        timestamp = int(time.time() * 1000)
        bids = snapshot_response.get('bids', [])
        asks = snapshot_response.get('asks', [])

        snapshot_msg: OrderBookMessage = OrderBookMessage(
            OrderBookMessageType.SNAPSHOT,
            {
                "trading_pair": trading_pair,
                "update_id": timestamp,
                "bids": [[float(bid[0]), float(bid[1])] for bid in bids],
                "asks": [[float(ask[0]), float(ask[1])] for ask in asks],
            },
            timestamp=timestamp
        )
        return snapshot_msg

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """Connect to Lighter WebSocket."""
        url = f"{web_utils.wss_url(self._domain)}"
        ws: WSAssistant = await self._api_factory.get_ws_assistant()
        await ws.connect(ws_url=url, ping_timeout=CONSTANTS.HEARTBEAT_TIME_INTERVAL)
        return ws

    async def _subscribe_channels(self, ws: WSAssistant):
        """
        Subscribe to WebSocket channels for order book and trade data.

        Lighter WebSocket channels (to be verified with actual API):
        - Order book updates
        - Trade updates
        """
        try:
            # Ensure market mappings are loaded
            if not self._market_id_map:
                await self._initialize_market_mappings()

            for trading_pair in self._trading_pairs:
                market_id = self._get_market_id(trading_pair)
                if market_id is None:
                    self.logger().warning(f"Cannot subscribe to {trading_pair}: market ID not found")
                    continue

                # Subscribe to order book (format TBD - verify with Lighter docs)
                orderbook_payload = {
                    "type": "subscribe",
                    "channel": "orderbook",
                    "market_id": market_id
                }
                subscribe_orderbook_request: WSJSONRequest = WSJSONRequest(payload=orderbook_payload)
                await ws.send(subscribe_orderbook_request)

                # Subscribe to trades (format TBD)
                trades_payload = {
                    "type": "subscribe",
                    "channel": "trades",
                    "market_id": market_id
                }
                subscribe_trade_request: WSJSONRequest = WSJSONRequest(payload=trades_payload)
                await ws.send(subscribe_trade_request)

                self.logger().info(f"Subscribed to Lighter public channels for {trading_pair} (market_id: {market_id})")
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().error("Unexpected error subscribing to Lighter order book streams.")
            raise

    def _channel_originating_message(self, event_message: Dict[str, Any]) -> str:
        """Identify which channel a message came from."""
        channel = ""
        channel_type = event_message.get("channel", "")
        if "orderbook" in channel_type:
            channel = self._snapshot_messages_queue_key
        elif "trades" in channel_type:
            channel = self._trade_messages_queue_key
        return channel

    async def _parse_order_book_diff_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """Parse order book update (diff) message."""
        # Lighter format (to be verified): {"channel": "orderbook", "market_id": 33, "data": {...}}
        data = raw_message.get("data", {})
        market_id = raw_message.get("market_id")

        # Find trading pair from market_id
        trading_pair = None
        for tp, mid in self._market_id_map.items():
            if mid == market_id:
                trading_pair = tp
                break

        if not trading_pair:
            self.logger().warning(f"Trading pair not found for market_id {market_id}")
            return

        timestamp = int(data.get("timestamp", time.time() * 1000))

        order_book_message: OrderBookMessage = OrderBookMessage(
            OrderBookMessageType.DIFF,
            {
                "trading_pair": trading_pair,
                "update_id": timestamp,
                "bids": [[float(bid[0]), float(bid[1])] for bid in data.get("bids", [])],
                "asks": [[float(ask[0]), float(ask[1])] for ask in data.get("asks", [])],
            },
            timestamp=timestamp / 1000 if timestamp > 1e12 else timestamp
        )
        message_queue.put_nowait(order_book_message)

    async def _parse_trade_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """Parse trade message from WebSocket."""
        # Lighter format (to be verified): {"channel": "trades", "market_id": 33, "data": [{trade}, ...]}
        market_id = raw_message.get("market_id")

        # Find trading pair from market_id
        trading_pair = None
        for tp, mid in self._market_id_map.items():
            if mid == market_id:
                trading_pair = tp
                break

        if not trading_pair:
            return

        trades_data = raw_message.get("data", [])
        for trade in trades_data:
            trade_message: OrderBookMessage = OrderBookMessage(
                OrderBookMessageType.TRADE,
                {
                    "trading_pair": trading_pair,
                    "trade_type": TradeType.SELL.value if trade.get("side") == "sell" else TradeType.BUY.value,
                    "trade_id": trade.get("id", ""),
                    "update_id": int(trade.get("timestamp", time.time() * 1000)),
                    "price": float(trade.get("price", 0)),
                    "amount": float(trade.get("amount", 0)),
                },
                timestamp=int(trade.get("timestamp", time.time() * 1000)) / 1000
            )
            message_queue.put_nowait(trade_message)

    async def _request_complete_funding_info(self, trading_pair: str) -> List:
        """Request complete funding information (for compatibility)."""
        # This is a compatibility method for the base class
        funding_info = await self.get_funding_info(trading_pair)
        return [funding_info]

    async def _parse_funding_info_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """Parse funding info message from WebSocket."""
        # Lighter WebSocket funding info format (to be verified)
        # This is called when funding info updates come via WebSocket
        try:
            market_id = raw_message.get("market_id")
            # Find trading pair from market_id
            trading_pair = None
            for tp, mid in self._market_id_map.items():
                if mid == market_id:
                    trading_pair = tp
                    break

            if trading_pair:
                funding_info = await self.get_funding_info(trading_pair)
                funding_info_update = FundingInfoUpdate(
                    trading_pair=trading_pair,
                    index_price=funding_info.index_price,
                    mark_price=funding_info.mark_price,
                    next_funding_utc_timestamp=funding_info.next_funding_utc_timestamp,
                    rate=funding_info.rate,
                )
                message_queue.put_nowait(funding_info_update)
        except Exception as e:
            self.logger().error(f"Error parsing funding info message: {e}", exc_info=True)

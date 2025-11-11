import asyncio
import time
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_web_utils as web_utils
from hummingbot.core.data_type.common import TradeType
from hummingbot.core.data_type.funding_info import FundingInfo, FundingInfoUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.perpetual_api_order_book_data_source import PerpetualAPIOrderBookDataSource
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative import (
        ParadexPerpetualDerivative,
    )


class ParadexPerpetualAPIOrderBookDataSource(PerpetualAPIOrderBookDataSource):
    """
    Order book data source for Paradex Perpetual.

    Handles:
    - Fetching order books from REST API (fallback)
    - Listening to order book updates via WebSocket (if available)
    - Fetching and monitoring funding rates (CRITICAL for arbitrage strategy!)
    - Trade data streaming

    Note:
        WebSocket implementation depends on Paradex API availability.
        If WebSocket not available, falls back to REST polling.
        (Lessons learned #3.1: Always verify endpoints exist before implementing)
    """

    _bpobds_logger: Optional[HummingbotLogger] = None

    def __init__(
        self,
        trading_pairs: List[str],
        connector: 'ParadexPerpetualDerivative',
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
        self._diff_messages_queue_key = "order_book_diff"
        self._trade_messages_queue_key = "order_book_trade"
        self._funding_info_messages_queue_key = "funding_info"

    async def get_last_traded_prices(
        self,
        trading_pairs: List[str],
        domain: Optional[str] = None
    ) -> Dict[str, float]:
        """Get last traded prices for trading pairs."""
        return await self._connector.get_last_traded_prices(trading_pairs=trading_pairs)

    async def get_funding_info(self, trading_pair: str) -> FundingInfo:
        """
        Fetch current funding rate information for a trading pair.

        This is CRITICAL for the funding rate arbitrage strategy!

        Paradex API: GET /markets/{market}/funding
        """
        try:
            response = await self._connector._api_get(
                path_url=CONSTANTS.FUNDING_RATE_URL.format(market=trading_pair),
                limit_id=CONSTANTS.FUNDING_RATE_URL
            )

            if not isinstance(response, dict):
                raise ValueError(f"Invalid funding rate response: {response}")

            # Extract funding rate data (verify field names from Paradex API docs)
            index_price = Decimal(str(response.get("index_price", "0")))
            mark_price = Decimal(str(response.get("mark_price", "0")))
            funding_rate = Decimal(str(response.get("funding_rate", "0")))
            next_funding_time = response.get("next_funding_time", 0)

            funding_info = FundingInfo(
                trading_pair=trading_pair,
                index_price=index_price,
                mark_price=mark_price,
                next_funding_utc_timestamp=next_funding_time,
                rate=funding_rate,
            )

            return funding_info

        except Exception as e:
            self.logger().error(
                f"Error fetching funding info for {trading_pair}: {str(e)}",
                exc_info=True
            )
            # Return default funding info to avoid breaking strategies
            return FundingInfo(
                trading_pair=trading_pair,
                index_price=Decimal("0"),
                mark_price=Decimal("0"),
                next_funding_utc_timestamp=0,
                rate=Decimal("0"),
            )

    async def _request_order_book_snapshot(self, trading_pair: str) -> Dict[str, Any]:
        """
        Fetch order book snapshot from REST API.

        Paradex API: GET /markets/{market}/orderbook
        """
        try:
            response = await self._connector._api_get(
                path_url=CONSTANTS.ORDER_BOOK_URL.format(market=trading_pair),
                limit_id=CONSTANTS.ORDER_BOOK_URL
            )

            return response

        except Exception as e:
            self.logger().error(
                f"Error fetching order book snapshot for {trading_pair}: {str(e)}",
                exc_info=True
            )
            raise

    async def _parse_order_book_snapshot_message(
        self,
        raw_message: Dict[str, Any],
        message_queue: asyncio.Queue
    ):
        """Parse order book snapshot and add to queue."""
        try:
            trading_pair = raw_message.get("trading_pair")  # Injected by caller

            # Paradex order book format (verify from API docs):
            # {
            #   "bids": [["price", "size"], ...],
            #   "asks": [["price", "size"], ...]
            # }

            bids = []
            asks = []

            for bid in raw_message.get("bids", []):
                price = Decimal(str(bid[0]))
                size = Decimal(str(bid[1]))
                bids.append([price, size])

            for ask in raw_message.get("asks", []):
                price = Decimal(str(ask[0]))
                size = Decimal(str(ask[1]))
                asks.append([price, size])

            order_book_message = OrderBookMessage(
                message_type=OrderBookMessageType.SNAPSHOT,
                content={
                    "trading_pair": trading_pair,
                    "update_id": int(time.time() * 1000),
                    "bids": bids,
                    "asks": asks,
                },
                timestamp=time.time(),
            )

            message_queue.put_nowait(order_book_message)

        except Exception as e:
            self.logger().error(
                f"Error parsing order book snapshot: {str(e)}",
                exc_info=True
            )

    async def _subscribe_channels(self, ws: WSAssistant):
        """
        Subscribe to WebSocket channels.

        Note: This implementation depends on Paradex WebSocket availability.
        If WebSocket is not available, the connector will use REST polling fallback.

        Paradex channels:
        - orderbook.{market}: Order book updates
        - trades.{market}: Trade stream
        - markets_summary: Market data including funding rates
        """
        try:
            # Subscribe to order book and trades for each trading pair
            for trading_pair in self._trading_pairs:
                # Subscribe to order book
                subscribe_orderbook_request = WSJSONRequest({
                    "type": "subscribe",
                    "channels": [
                        f"orderbook.{trading_pair}",
                        f"trades.{trading_pair}"
                    ]
                })
                await ws.send(subscribe_orderbook_request)

            # Subscribe to markets summary for funding rates
            subscribe_markets_request = WSJSONRequest({
                "type": "subscribe",
                "channels": ["markets_summary"]
            })
            await ws.send(subscribe_markets_request)

            self.logger().info(f"Subscribed to Paradex channels for {len(self._trading_pairs)} trading pairs")

        except Exception as e:
            self.logger().error(
                f"Error subscribing to channels: {str(e)}",
                exc_info=True
            )
            raise

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """
        Create connected WebSocket assistant.

        Note: Verify WebSocket URL from Paradex documentation.
        If WebSocket endpoint returns 404, this will fail gracefully
        and connector should fall back to REST polling.
        (Lessons learned #3.1: Always verify endpoints exist)
        """
        ws_url = web_utils.wss_url(self._domain)

        try:
            ws: WSAssistant = await self._api_factory.get_ws_assistant()
            await ws.connect(ws_url=ws_url, ping_timeout=CONSTANTS.HEARTBEAT_TIME_INTERVAL)

            self.logger().info(f"Connected to Paradex WebSocket: {ws_url}")

            return ws

        except Exception as e:
            self.logger().warning(
                f"WebSocket connection failed: {str(e)}\n"
                f"Connector will use REST polling fallback."
            )
            raise

    async def _process_websocket_messages(self, websocket_assistant: WSAssistant):
        """
        Process incoming WebSocket messages.

        Paradex WebSocket message format (verify from docs):
        {
          "channel": "orderbook.BTC-USD-PERP",
          "type": "snapshot" | "update",
          "data": {...}
        }
        """
        async for ws_response in websocket_assistant.iter_messages():
            try:
                data = ws_response.data

                if isinstance(data, dict):
                    channel = data.get("channel", "")
                    message_type = data.get("type", "")
                    message_data = data.get("data", {})

                    # Order book updates
                    if channel.startswith("orderbook."):
                        trading_pair = channel.replace("orderbook.", "")

                        if message_type == "snapshot":
                            await self._parse_order_book_snapshot_message(
                                {"trading_pair": trading_pair, **message_data},
                                self._message_queue[self._snapshot_messages_queue_key]
                            )
                        elif message_type == "update":
                            await self._parse_order_book_diff_message(
                                {"trading_pair": trading_pair, **message_data},
                                self._message_queue[self._diff_messages_queue_key]
                            )

                    # Trade updates
                    elif channel.startswith("trades."):
                        trading_pair = channel.replace("trades.", "")
                        await self._parse_trade_message(
                            {"trading_pair": trading_pair, **message_data},
                            self._message_queue[self._trade_messages_queue_key]
                        )

                    # Markets summary (funding rates)
                    elif channel == "markets_summary":
                        await self._parse_funding_info_message(
                            message_data,
                            self._message_queue[self._funding_info_messages_queue_key]
                        )

            except Exception as e:
                self.logger().error(
                    f"Error processing WebSocket message: {str(e)}",
                    exc_info=True
                )

    async def _parse_order_book_diff_message(
        self,
        raw_message: Dict[str, Any],
        message_queue: asyncio.Queue
    ):
        """Parse order book diff (update) message."""
        try:
            trading_pair = raw_message.get("trading_pair")

            bids = []
            asks = []

            for bid in raw_message.get("bids", []):
                price = Decimal(str(bid[0]))
                size = Decimal(str(bid[1]))
                bids.append([price, size])

            for ask in raw_message.get("asks", []):
                price = Decimal(str(ask[0]))
                size = Decimal(str(ask[1]))
                asks.append([price, size])

            order_book_message = OrderBookMessage(
                message_type=OrderBookMessageType.DIFF,
                content={
                    "trading_pair": trading_pair,
                    "update_id": int(time.time() * 1000),
                    "bids": bids,
                    "asks": asks,
                },
                timestamp=time.time(),
            )

            message_queue.put_nowait(order_book_message)

        except Exception as e:
            self.logger().error(
                f"Error parsing order book diff: {str(e)}",
                exc_info=True
            )

    async def _parse_trade_message(
        self,
        raw_message: Dict[str, Any],
        message_queue: asyncio.Queue
    ):
        """Parse trade message."""
        try:
            trading_pair = raw_message.get("trading_pair")

            trade_id = raw_message.get("trade_id")
            price = Decimal(str(raw_message.get("price", "0")))
            size = Decimal(str(raw_message.get("size", "0")))
            side = raw_message.get("side", "BUY")  # Taker side
            timestamp = raw_message.get("timestamp", 0) / 1000  # Convert ms to seconds

            trade_type = TradeType.BUY if side == "BUY" else TradeType.SELL

            order_book_message = OrderBookMessage(
                message_type=OrderBookMessageType.TRADE,
                content={
                    "trading_pair": trading_pair,
                    "trade_type": trade_type.value,
                    "trade_id": trade_id,
                    "update_id": int(timestamp * 1000),
                    "price": price,
                    "amount": size,
                },
                timestamp=timestamp,
            )

            message_queue.put_nowait(order_book_message)

        except Exception as e:
            self.logger().error(
                f"Error parsing trade message: {str(e)}",
                exc_info=True
            )

    async def _parse_funding_info_message(
        self,
        raw_message: Dict[str, Any],
        message_queue: asyncio.Queue
    ):
        """Parse funding info from markets summary."""
        try:
            trading_pair = raw_message.get("market")
            if not trading_pair:
                return

            index_price = Decimal(str(raw_message.get("index_price", "0")))
            mark_price = Decimal(str(raw_message.get("mark_price", "0")))
            funding_rate = Decimal(str(raw_message.get("funding_rate", "0")))
            next_funding_time = raw_message.get("next_funding_time", 0)

            funding_info_update = FundingInfoUpdate(
                trading_pair=trading_pair,
                index_price=index_price,
                mark_price=mark_price,
                next_funding_utc_timestamp=next_funding_time,
                rate=funding_rate,
            )

            message_queue.put_nowait(funding_info_update)

        except Exception as e:
            self.logger().error(
                f"Error parsing funding info: {str(e)}",
                exc_info=True
            )

    async def listen_for_subscriptions(self):
        """
        Main listener for WebSocket subscriptions.

        Implements fallback to REST polling if WebSocket is unavailable.
        (Lessons learned #3.2: Always implement polling fallback)
        """
        try:
            # Try WebSocket connection
            ws = await self._connected_websocket_assistant()
            await self._subscribe_channels(ws)

            # Process messages
            await self._process_websocket_messages(ws)

        except Exception as e:
            self.logger().warning(
                f"WebSocket streaming failed: {str(e)}\n"
                f"Falling back to REST polling..."
            )

            # Fallback to REST polling
            await self._listen_for_subscriptions_polling()

    async def _listen_for_subscriptions_polling(self):
        """
        REST API polling fallback for order book and market data.

        This ensures connector works even if WebSocket is unavailable.
        (Lessons learned #3.1, #3.2: Always verify endpoints and implement fallback)
        """
        polling_interval = 2.0  # 2 seconds between polls

        self.logger().info(
            f"Using REST polling fallback (interval: {polling_interval}s)"
        )

        while True:
            try:
                # Poll order book snapshots for each trading pair
                for trading_pair in self._trading_pairs:
                    try:
                        # Fetch order book snapshot
                        snapshot = await self._request_order_book_snapshot(trading_pair)

                        # Parse and queue
                        await self._parse_order_book_snapshot_message(
                            {"trading_pair": trading_pair, **snapshot},
                            self._message_queue[self._snapshot_messages_queue_key]
                        )

                    except Exception as e:
                        self.logger().error(
                            f"Error polling order book for {trading_pair}: {str(e)}"
                        )

                # Poll funding rates
                for trading_pair in self._trading_pairs:
                    try:
                        funding_info = await self.get_funding_info(trading_pair)
                        funding_update = FundingInfoUpdate(
                            trading_pair=trading_pair,
                            index_price=funding_info.index_price,
                            mark_price=funding_info.mark_price,
                            next_funding_utc_timestamp=funding_info.next_funding_utc_timestamp,
                            rate=funding_info.rate,
                        )
                        self._message_queue[self._funding_info_messages_queue_key].put_nowait(
                            funding_update
                        )

                    except Exception as e:
                        self.logger().error(
                            f"Error polling funding info for {trading_pair}: {str(e)}"
                        )

                await asyncio.sleep(polling_interval)

            except Exception as e:
                self.logger().error(
                    f"Error in REST polling loop: {str(e)}",
                    exc_info=True
                )
                await asyncio.sleep(polling_interval)

    async def listen_for_order_book_diffs(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        """Listen for order book diff messages."""
        message_queue = self._message_queue[self._diff_messages_queue_key]
        while True:
            try:
                diff_message = await message_queue.get()
                output.put_nowait(diff_message)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Error in listen_for_order_book_diffs: {str(e)}", exc_info=True)

    async def listen_for_order_book_snapshots(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        """Listen for order book snapshot messages."""
        message_queue = self._message_queue[self._snapshot_messages_queue_key]
        while True:
            try:
                snapshot_message = await message_queue.get()
                output.put_nowait(snapshot_message)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Error in listen_for_order_book_snapshots: {str(e)}", exc_info=True)

    async def listen_for_trades(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        """Listen for trade messages."""
        message_queue = self._message_queue[self._trade_messages_queue_key]
        while True:
            try:
                trade_message = await message_queue.get()
                output.put_nowait(trade_message)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Error in listen_for_trades: {str(e)}", exc_info=True)

    async def listen_for_funding_info(self, output: asyncio.Queue):
        """Listen for funding info updates."""
        message_queue = self._message_queue[self._funding_info_messages_queue_key]
        while True:
            try:
                funding_info_update = await message_queue.get()
                output.put_nowait(funding_info_update)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Error in listen_for_funding_info: {str(e)}", exc_info=True)

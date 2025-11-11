import asyncio
import json
import time
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_web_utils as web_utils
from hummingbot.core.data_type.common import TradeType
from hummingbot.core.data_type.funding_info import FundingInfo, FundingInfoUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.perpetual_api_order_book_data_source import PerpetualAPIOrderBookDataSource
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTResponse, WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import (
        ExtendedPerpetualDerivative,
    )


class ExtendedPerpetualAPIOrderBookDataSource(PerpetualAPIOrderBookDataSource):
    """
    Order book data source for Extended Perpetual.

    Handles:
    - Fetching order books from REST API
    - Listening to order book updates via WebSocket
    - Fetching and monitoring funding rates
    - Trade data streaming
    """

    _bpobds_logger: Optional[HummingbotLogger] = None

    def __init__(
            self,
            trading_pairs: List[str],
            connector: 'ExtendedPerpetualDerivative',
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

    async def get_last_traded_prices(self,
                                     trading_pairs: List[str],
                                     domain: Optional[str] = None) -> Dict[str, float]:
        """Get last traded prices for trading pairs."""
        return await self._connector.get_last_traded_prices(trading_pairs=trading_pairs)

    async def get_funding_info(self, trading_pair: str) -> FundingInfo:
        """
        Fetch current funding rate information for a trading pair.

        This is CRITICAL for the funding rate arbitrage strategy!

        Args:
            trading_pair: Trading pair (e.g., "KAITO-USD")

        Returns:
            FundingInfo object with rate, index/mark prices, next funding time
        """
        ex_trading_pair = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
        market_name = ex_trading_pair  # Extended uses "KAITO-USD" format directly

        # Get market stats for mark/index prices
        stats_path = CONSTANTS.MARKET_STATS_URL.format(market=market_name)
        stats_response = await self._connector._api_get(
            path_url=stats_path,
            limit_id=CONSTANTS.MARKET_STATS_URL
        )

        # Get latest funding rate
        # Extended: GET /api/v1/info/{market}/funding
        # Returns: {"status": "OK", "data": [{"m": "KAITO-USD", "T": timestamp, "f": "0.0001"}, ...]}
        funding_path = CONSTANTS.FUNDING_RATE_URL.format(market=market_name)

        # Get last funding rate (most recent record)
        end_time = int(time.time() * 1000)
        start_time = end_time - (3600 * 1000)  # Last hour

        funding_response = await self._connector._api_get(
            path_url=funding_path,
            params={"startTime": start_time, "endTime": end_time, "limit": 1},
            limit_id=CONSTANTS.FUNDING_RATE_URL
        )

        # Parse response
        if isinstance(funding_response, dict) and 'data' in funding_response:
            funding_data = funding_response['data']
            if funding_data and len(funding_data) > 0:
                latest_funding = funding_data[-1]  # Most recent
                funding_rate = Decimal(latest_funding.get('f', '0'))
            else:
                funding_rate = Decimal('0')
        else:
            funding_rate = Decimal('0')

        # Parse stats for prices
        if isinstance(stats_response, dict) and 'data' in stats_response:
            stats = stats_response['data']
            mark_price = Decimal(stats.get('markPrice', '0'))
            index_price = Decimal(stats.get('indexPrice', mark_price))  # Fallback to mark if no index
        else:
            # Fallback: fetch last traded price
            mark_price = Decimal(str(await self._connector._get_last_traded_price(trading_pair)))
            index_price = mark_price

        # Calculate next funding time
        # Extended has 8-hour funding intervals (00:00, 08:00, 16:00 UTC)
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

        Extended funding occurs every 8 hours at 00:00, 08:00, 16:00 UTC.

        Returns:
            Unix timestamp of next funding time
        """
        current_time = int(time.time())
        current_hour = int((current_time % 86400) / 3600)  # Hour of day (0-23)

        # Find next funding hour (0, 8, or 16)
        if current_hour < 8:
            next_hour = 8
        elif current_hour < 16:
            next_hour = 16
        else:
            next_hour = 24  # Next day at 00:00

        # Calculate seconds until next funding
        hours_until_funding = next_hour - current_hour
        seconds_until_funding = hours_until_funding * 3600 - (current_time % 3600)

        return current_time + seconds_until_funding

    async def listen_for_funding_info(self, output: asyncio.Queue):
        """
        Continuously monitor and update funding rate information.

        Polls every FUNDING_RATE_UPDATE_INTERNAL_SECOND (8 hours for Extended).
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
                self.logger().exception("Unexpected error when processing funding info updates from Extended")
                await self._sleep(CONSTANTS.FUNDING_RATE_UPDATE_INTERNAL_SECOND)

    async def _request_order_book_snapshot(self, trading_pair: str) -> Dict[str, Any]:
        """Fetch order book snapshot from REST API."""
        ex_trading_pair = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)
        market_name = ex_trading_pair

        # Extended: GET /api/v1/info/markets/{market}/orderbook
        path = CONSTANTS.ORDER_BOOK_URL.format(market=market_name)
        data = await self._connector._api_get(path_url=path, limit_id=CONSTANTS.ORDER_BOOK_URL)
        return data

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        """Parse order book snapshot into OrderBookMessage."""
        snapshot_response: Dict[str, Any] = await self._request_order_book_snapshot(trading_pair)

        # Extended response format: {"status": "OK", "data": {"bids": [...], "asks": [...], "timestamp": ...}}
        if isinstance(snapshot_response, dict) and 'data' in snapshot_response:
            data = snapshot_response['data']
            timestamp = int(data.get('timestamp', time.time() * 1000))
            bids = data.get('bids', [])
            asks = data.get('asks', [])
        else:
            # Fallback
            timestamp = int(time.time() * 1000)
            bids = []
            asks = []

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

    async def _connect_orderbook_stream(self, market: str) -> RESTResponse:
        """
        Create HTTP streaming connection for orderbook updates.

        Extended uses HTTP GET streaming (Server-Sent Events) instead of WebSocket.

        Args:
            market: Market symbol (e.g., "KAITO-USD")

        Returns:
            RESTResponse with persistent connection for streaming
        """
        path_url = CONSTANTS.STREAM_ORDERBOOK_URL.format(market=market)
        url = web_utils.stream_url(path_url, self._domain)

        rest_assistant = await self._api_factory.get_rest_assistant()

        # Make GET request with streaming support
        response = await rest_assistant.execute_request_and_get_response(
            url=url,
            throttler_limit_id=CONSTANTS.STREAM_ORDERBOOK_URL,
            method=RESTMethod.GET,
            headers={"Accept": "text/event-stream"},
            timeout=None,  # Keep connection open indefinitely
        )
        return response

    async def _read_stream_messages(self, response: RESTResponse):
        """
        Read Server-Sent Events from HTTP streaming response.

        Yields JSON messages from the SSE stream line-by-line.

        Args:
            response: RESTResponse with persistent connection

        Yields:
            Dict[str, Any]: Parsed JSON message from stream
        """
        try:
            # Access underlying aiohttp response to read stream
            aiohttp_response = response._aiohttp_response

            while True:
                # Read one line from the stream
                line = await aiohttp_response.content.readline()

                if not line:
                    # Connection closed
                    break

                line = line.decode('utf-8').strip()

                # Skip empty lines and SSE comments
                if not line or line.startswith(':'):
                    continue

                # Parse SSE data format: "data: {json}"
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        message = json.loads(json_str)
                        yield message
                    except json.JSONDecodeError as e:
                        self.logger().error(f"Failed to parse SSE message: {line}", exc_info=True)
                        continue
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger().error(f"Error reading stream messages: {e}", exc_info=True)
            raise

    async def listen_for_subscriptions(self):
        """
        Listen to orderbook updates via HTTP streaming (Server-Sent Events).

        Overrides base class WebSocket implementation with HTTP streaming.
        Extended Exchange uses HTTP GET streaming instead of WebSocket.
        """
        # Create separate streaming tasks for each trading pair
        tasks = []
        for trading_pair in self._trading_pairs:
            task = asyncio.create_task(self._listen_for_orderbook_stream(trading_pair))
            tasks.append(task)

        # Wait for all streaming tasks
        await asyncio.gather(*tasks)

    async def _listen_for_orderbook_stream(self, trading_pair: str):
        """
        Listen to orderbook updates for a specific trading pair via HTTP streaming.

        Args:
            trading_pair: Trading pair to subscribe to (e.g., "KAITO-USD")
        """
        while True:
            stream_response = None
            try:
                # Get exchange symbol
                symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

                # Connect to HTTP stream
                stream_response = await self._connect_orderbook_stream(symbol)
                self.logger().info(f"Connected to orderbook stream for {trading_pair}")

                # Read and process streaming messages
                async for message in self._read_stream_messages(stream_response):
                    # Route message to appropriate queue based on type
                    channel = self._channel_originating_message(message)
                    if channel == self._snapshot_messages_queue_key:
                        await self._parse_order_book_diff_message(message, self._message_queue[channel])
                    elif channel == self._trade_messages_queue_key:
                        await self._parse_trade_message(message, self._message_queue[channel])

            except asyncio.CancelledError:
                raise
            except ConnectionError as e:
                self.logger().warning(f"Orderbook stream connection closed for {trading_pair}: {e}")
            except Exception:
                self.logger().exception(
                    f"Unexpected error in orderbook stream for {trading_pair}. Retrying in 5 seconds..."
                )
                await self._sleep(5.0)
            finally:
                # Close stream connection if open
                if stream_response is not None:
                    try:
                        await stream_response._aiohttp_response.close()
                    except Exception:
                        pass

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """
        DEPRECATED: Extended uses HTTP streaming, not WebSocket.

        This method is kept for compatibility but should not be used.
        """
        url = f"{web_utils.wss_url(self._domain)}"
        ws: WSAssistant = await self._api_factory.get_ws_assistant()
        await ws.connect(ws_url=url, ping_timeout=CONSTANTS.HEARTBEAT_TIME_INTERVAL)
        return ws

    async def _subscribe_channels(self, ws: WSAssistant):
        """
        Subscribe to WebSocket channels for order book and trade data.

        Extended WebSocket channels (to be verified with actual API):
        - Order book: {"type": "subscribe", "channel": "orderbook", "market": "KAITO-USD"}
        - Trades: {"type": "subscribe", "channel": "trades", "market": "KAITO-USD"}
        """
        try:
            for trading_pair in self._trading_pairs:
                symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=trading_pair)

                # Subscribe to order book
                orderbook_payload = {
                    "type": "subscribe",
                    "channel": "orderbook",
                    "market": symbol
                }
                subscribe_orderbook_request: WSJSONRequest = WSJSONRequest(payload=orderbook_payload)
                await ws.send(subscribe_orderbook_request)

                # Subscribe to trades
                trades_payload = {
                    "type": "subscribe",
                    "channel": "trades",
                    "market": symbol
                }
                subscribe_trade_request: WSJSONRequest = WSJSONRequest(payload=trades_payload)
                await ws.send(subscribe_trade_request)

                self.logger().info(f"Subscribed to Extended public channels for {trading_pair}")
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().error("Unexpected error subscribing to Extended order book streams.")
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
        # Extended format (to be verified): {"channel": "orderbook", "market": "KAITO-USD", "data": {...}}
        data = raw_message.get("data", {})
        market = raw_message.get("market", "")

        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(market)
        timestamp = int(data.get("timestamp", time.time() * 1000))

        order_book_message: OrderBookMessage = OrderBookMessage(
            OrderBookMessageType.DIFF,
            {
                "trading_pair": trading_pair,
                "update_id": timestamp,
                "bids": [[float(bid[0]), float(bid[1])] for bid in data.get("bids", [])],
                "asks": [[float(ask[0]), float(ask[1])] for bid in data.get("asks", [])],
            },
            timestamp=timestamp / 1000 if timestamp > 1e12 else timestamp
        )
        message_queue.put_nowait(order_book_message)

    async def _parse_trade_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """Parse trade message from WebSocket."""
        # Extended format (to be verified): {"channel": "trades", "market": "KAITO-USD", "data": [{trade}, ...]}
        market = raw_message.get("market", "")
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(market)

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
        # Return format similar to what base class expects
        funding_info = await self.get_funding_info(trading_pair)
        return [funding_info]

    async def _parse_funding_info_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """Parse funding info message from WebSocket."""
        # Extended WebSocket funding info format (to be verified)
        # This is called when funding info updates come via WebSocket
        try:
            market = raw_message.get("market", "")
            trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(market)

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

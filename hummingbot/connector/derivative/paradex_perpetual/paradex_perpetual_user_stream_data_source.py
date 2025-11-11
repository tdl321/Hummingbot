import asyncio
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_web_utils as web_utils
from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth import ParadexPerpetualAuth
from hummingbot.core.data_type.in_flight_order import OrderState
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative import (
        ParadexPerpetualDerivative,
    )


class ParadexPerpetualUserStreamDataSource(UserStreamTrackerDataSource):
    """
    User stream data source for Paradex Perpetual.

    Handles authenticated WebSocket channels for:
    - Order updates (orders channel)
    - Trade fills (fills channel)
    - Position changes (positions channel)
    - Balance updates (balance_events channel)

    All private channels require JWT authentication.
    """

    _bpobds_logger: Optional[HummingbotLogger] = None

    def __init__(
        self,
        auth: ParadexPerpetualAuth,
        trading_pairs: List[str],
        connector: 'ParadexPerpetualDerivative',
        api_factory: WebAssistantsFactory,
        domain: str = CONSTANTS.DOMAIN,
    ):
        super().__init__()
        self._auth: ParadexPerpetualAuth = auth
        self._trading_pairs: List[str] = trading_pairs
        self._connector: 'ParadexPerpetualDerivative' = connector
        self._api_factory: WebAssistantsFactory = api_factory
        self._domain: str = domain
        self._message_queue: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

    @property
    def last_recv_time(self) -> float:
        """Get last receive time."""
        # Note: Implement proper tracking if needed
        return 0.0

    async def listen_for_user_stream(self, output: asyncio.Queue):
        """
        Main listener for authenticated user stream.

        Connects to Paradex WebSocket with JWT authentication and
        subscribes to private channels for order/trade/position/balance updates.
        """
        while True:
            try:
                ws = await self._connected_websocket_assistant()
                await self._subscribe_to_channels(ws)

                # Process messages
                await self._process_websocket_messages(ws, output)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(
                    f"Unexpected error in user stream: {str(e)}",
                    exc_info=True
                )
                # Wait before reconnecting
                await asyncio.sleep(5.0)

    async def _connected_websocket_assistant(self) -> WSAssistant:
        """
        Create authenticated WebSocket connection.

        Paradex WebSocket authentication:
        - Connects to wss://ws.prod.paradex.trade/v1
        - Sends authentication message with JWT token
        - Receives confirmation before subscribing to channels
        """
        ws_url = web_utils.wss_url(self._domain)

        try:
            ws: WSAssistant = await self._api_factory.get_ws_assistant()
            await ws.connect(ws_url=ws_url, ping_timeout=CONSTANTS.HEARTBEAT_TIME_INTERVAL)

            # Authenticate WebSocket connection
            await self._authenticate_websocket(ws)

            self.logger().info(f"Connected to Paradex user stream: {ws_url}")

            return ws

        except Exception as e:
            self.logger().error(
                f"Failed to connect to Paradex user stream: {str(e)}",
                exc_info=True
            )
            raise

    async def _authenticate_websocket(self, ws: WSAssistant):
        """
        Authenticate WebSocket connection with JWT token.

        Paradex WebSocket authentication format (verify from docs):
        {
          "type": "auth",
          "jwt_token": "<token>",
          "account": "<main_account_address>"
        }
        """
        try:
            # Get valid JWT token
            jwt_token = await self._auth.get_jwt_token()

            # Send authentication message
            auth_message = WSJSONRequest({
                "type": "auth",
                "jwt_token": jwt_token,
                "account": self._auth.account_address
            })

            await ws.send(auth_message)

            # Wait for auth confirmation (may need adjustment based on actual protocol)
            # Note: Some exchanges send confirmation, others just accept subscriptions
            await asyncio.sleep(0.5)

            self.logger().info("Authenticated Paradex WebSocket connection")

        except Exception as e:
            self.logger().error(
                f"WebSocket authentication failed: {str(e)}",
                exc_info=True
            )
            raise

    async def _subscribe_to_channels(self, ws: WSAssistant):
        """
        Subscribe to private channels.

        Paradex private channels:
        - orders: Order state changes (created, filled, cancelled)
        - fills: Trade execution events
        - positions: Position changes
        - balance_events: Real-time balance updates
        """
        try:
            subscribe_request = WSJSONRequest({
                "type": "subscribe",
                "channels": [
                    CONSTANTS.WS_CHANNEL_ORDERS,
                    CONSTANTS.WS_CHANNEL_FILLS,
                    CONSTANTS.WS_CHANNEL_POSITIONS,
                    CONSTANTS.WS_CHANNEL_BALANCE_EVENTS,
                ]
            })

            await ws.send(subscribe_request)

            self.logger().info("Subscribed to Paradex private channels")

        except Exception as e:
            self.logger().error(
                f"Error subscribing to private channels: {str(e)}",
                exc_info=True
            )
            raise

    async def _process_websocket_messages(self, ws: WSAssistant, output: asyncio.Queue):
        """
        Process incoming WebSocket messages.

        Paradex private channel message format (verify from docs):
        {
          "channel": "orders" | "fills" | "positions" | "balance_events",
          "event": "created" | "filled" | "cancelled" | etc.,
          "data": {...}
        }
        """
        async for ws_response in ws.iter_messages():
            try:
                data = ws_response.data

                if isinstance(data, dict):
                    channel = data.get("channel", "")
                    event_type = data.get("event", "")
                    event_data = data.get("data", {})

                    # Route to appropriate handler
                    if channel == CONSTANTS.WS_CHANNEL_ORDERS:
                        await self._handle_order_update(event_data, output)

                    elif channel == CONSTANTS.WS_CHANNEL_FILLS:
                        await self._handle_fill_update(event_data, output)

                    elif channel == CONSTANTS.WS_CHANNEL_POSITIONS:
                        await self._handle_position_update(event_data, output)

                    elif channel == CONSTANTS.WS_CHANNEL_BALANCE_EVENTS:
                        await self._handle_balance_update(event_data, output)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(
                    f"Error processing user stream message: {str(e)}",
                    exc_info=True
                )

    async def _handle_order_update(self, event_data: Dict[str, Any], output: asyncio.Queue):
        """
        Handle order update events.

        Paradex order events:
        - created: Order placed
        - partially_filled: Partial fill
        - filled: Fully filled
        - cancelled: Order cancelled
        - rejected: Order rejected
        - failed: Order failed
        """
        try:
            # Convert to Hummingbot format
            order_update = {
                "type": "order_update",
                "data": event_data,
            }

            output.put_nowait(order_update)

        except Exception as e:
            self.logger().error(
                f"Error handling order update: {str(e)}",
                exc_info=True
            )

    async def _handle_fill_update(self, event_data: Dict[str, Any], output: asyncio.Queue):
        """
        Handle trade fill events.

        Paradex fill format:
        {
          "fill_id": "...",
          "order_id": "...",
          "trade_id": "...",
          "market": "BTC-USD-PERP",
          "side": "BUY",
          "price": "50000",
          "size": "0.5",
          "fee": "0",
          "fee_asset": "USDC",
          "liquidity": "taker",
          "timestamp": 1699564850000
        }
        """
        try:
            # Convert to Hummingbot format
            trade_update = {
                "type": "trade_update",
                "data": event_data,
            }

            output.put_nowait(trade_update)

        except Exception as e:
            self.logger().error(
                f"Error handling fill update: {str(e)}",
                exc_info=True
            )

    async def _handle_position_update(self, event_data: Dict[str, Any], output: asyncio.Queue):
        """
        Handle position change events.

        Paradex position format:
        {
          "market": "BTC-USD-PERP",
          "side": "LONG",
          "size": "1.5",
          "entry_price": "49500",
          "mark_price": "50000",
          "liquidation_price": "45000",
          "unrealized_pnl": "750",
          "leverage": "10",
          ...
        }
        """
        try:
            # Convert to Hummingbot format
            position_update = {
                "type": "position_update",
                "data": event_data,
            }

            output.put_nowait(position_update)

        except Exception as e:
            self.logger().error(
                f"Error handling position update: {str(e)}",
                exc_info=True
            )

    async def _handle_balance_update(self, event_data: Dict[str, Any], output: asyncio.Queue):
        """
        Handle balance change events.

        Paradex balance event format:
        {
          "asset": "USDC",
          "available": "8500.00",
          "locked": "1500.00",
          "total": "10000.00",
          "change": "+50.00",
          "reason": "trade_settled",
          "timestamp": 1699564900000
        }
        """
        try:
            # Convert to Hummingbot format
            balance_update = {
                "type": "balance_update",
                "data": event_data,
            }

            output.put_nowait(balance_update)

        except Exception as e:
            self.logger().error(
                f"Error handling balance update: {str(e)}",
                exc_info=True
            )

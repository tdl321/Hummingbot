import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_web_utils as web_utils
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import (
        ExtendedPerpetualDerivative,
    )


class ExtendedPerpetualUserStreamDataSource(UserStreamTrackerDataSource):
    """
    User stream data source for Extended Perpetual.

    Handles WebSocket connection for user-specific data:
    - Order updates
    - Position updates
    - Balance updates
    - Funding payments
    """

    _bpobds_logger: Optional[HummingbotLogger] = None

    def __init__(
            self,
            connector: 'ExtendedPerpetualDerivative',
            api_factory: WebAssistantsFactory,
            domain: str = CONSTANTS.DOMAIN
    ):
        super().__init__()
        self._connector = connector
        self._api_factory = api_factory
        self._domain = domain
        self._ws_assistant: Optional[WSAssistant] = None

    async def listen_for_user_stream(self, output: asyncio.Queue):
        """
        Main loop for listening to user stream WebSocket.

        Connects to Extended WebSocket and processes user events.
        """
        while True:
            try:
                ws = await self._get_ws_assistant()
                await self._subscribe_to_channels(ws)

                async for msg in ws.iter_messages():
                    if msg.data is None:
                        continue

                    # Extended WebSocket message format (to be verified):
                    # {"type": "order_update", "data": {...}}
                    # {"type": "position_update", "data": {...}}
                    # {"type": "balance_update", "data": {...}}
                    # {"type": "funding_payment", "data": {...}}

                    output.put_nowait(msg.data)

            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unexpected error in Extended user stream listener.", exc_info=True)
                await self._sleep(5.0)
            finally:
                await self._on_user_stream_interruption(ws)

    async def _get_ws_assistant(self) -> WSAssistant:
        """Get or create WebSocket assistant with authentication."""
        if self._ws_assistant is None:
            self._ws_assistant = await self._api_factory.get_ws_assistant()
        return self._ws_assistant

    async def _subscribe_to_channels(self, ws: WSAssistant):
        """
        Subscribe to user-specific WebSocket channels.

        Extended WebSocket authentication (to be verified):
        - May require sending API key in subscription message
        - Or may use authenticated WebSocket URL
        """
        try:
            # Subscribe to account updates
            subscribe_payload = {
                "type": "subscribe",
                "channel": "account",
                # May need to include API key or auth token
            }
            subscribe_request: WSJSONRequest = WSJSONRequest(payload=subscribe_payload)
            await ws.send(subscribe_request)

            self.logger().info("Subscribed to Extended user stream")
        except Exception:
            self.logger().error("Failed to subscribe to Extended user stream channels")
            raise

    async def _on_user_stream_interruption(self, ws: Optional[WSAssistant]):
        """Handle WebSocket interruption."""
        if ws is not None:
            await ws.disconnect()
        self._ws_assistant = None

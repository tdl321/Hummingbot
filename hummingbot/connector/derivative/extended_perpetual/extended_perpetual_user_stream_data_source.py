import asyncio
import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_web_utils as web_utils
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTResponse, WSJSONRequest
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
        Main loop for listening to user stream via WebSocket.

        Extended uses WebSocket for real-time account updates including:
        - Order updates
        - Position updates
        - Balance updates
        - Funding payments

        Args:
            output: Queue to put received messages
        """
        while True:
            ws: Optional[WSAssistant] = None
            try:
                # Connect to WebSocket
                ws = await self._get_ws_assistant()
                self.logger().info("Connected to Extended WebSocket account stream")

                # Listen for messages
                async for ws_response in ws.iter_messages():
                    data = ws_response.data

                    # Parse WebSocket message
                    if isinstance(data, str):
                        message = json.loads(data)
                    else:
                        message = data

                    # Extended sends messages with structure:
                    # {"type": "BALANCE/ORDER/POSITION/FUNDING", "data": {...}, "ts": ..., "seq": ...}
                    # Forward all messages to output queue
                    output.put_nowait(message)

            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Unexpected error in Extended WebSocket listener.", exc_info=True)
                await self._on_user_stream_interruption(ws)
                await self._sleep(5.0)

    async def _connect_account_stream(self) -> RESTResponse:
        """
        Create authenticated HTTP streaming connection for account updates.

        Extended uses HTTP GET streaming with X-Api-Key authentication.

        Returns:
            RESTResponse with persistent connection for streaming
        """
        path_url = CONSTANTS.STREAM_ACCOUNT_URL
        url = web_utils.stream_url(path_url, self._domain)

        rest_assistant = await self._api_factory.get_rest_assistant()

        # Make authenticated GET request with streaming support
        response = await rest_assistant.execute_request_and_get_response(
            url=url,
            throttler_limit_id=CONSTANTS.STREAM_ACCOUNT_URL,
            method=RESTMethod.GET,
            is_auth_required=True,  # Adds X-Api-Key header via auth handler
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

    async def _get_ws_assistant(self) -> WSAssistant:
        """
        Get or create WebSocket assistant for Extended account stream.

        Extended WebSocket authentication uses API key as query parameter.

        Returns:
            WSAssistant connected to Extended account stream
        """
        if self._ws_assistant is None:
            self._ws_assistant = await self._api_factory.get_ws_assistant()

            # Get API key from connector
            api_key = self._connector.extended_perpetual_api_key
            if not api_key:
                raise ValueError("API key required for WebSocket authentication")

            # Construct WebSocket URL with API key authentication
            # Format: wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account?X-API-KEY=...
            base_url = CONSTANTS.PERPETUAL_WS_URL
            ws_url = f"{base_url}?X-API-KEY={api_key}"

            # Connect to WebSocket
            await self._ws_assistant.connect(
                ws_url=ws_url,
                ping_timeout=CONSTANTS.HEARTBEAT_TIME_INTERVAL
            )

            self.logger().info("Extended WebSocket connected successfully")

        return self._ws_assistant

    async def _subscribe_to_channels(self, ws: WSAssistant):
        """
        DEPRECATED: Extended uses HTTP streaming, not WebSocket.

        Subscribe to user-specific WebSocket channels.

        Extended WebSocket authentication (to be verified):
        - May require sending API key in subscription message
        - Or may use authenticated WebSocket URL
        """
        try:
            # Subscribe to account updates
            # Extended uses "account_updates" channel for private user data
            subscribe_payload = {
                "type": "subscribe",
                "channel": "account_updates"
            }
            subscribe_request: WSJSONRequest = WSJSONRequest(payload=subscribe_payload)
            await ws.send(subscribe_request)

            self.logger().info("Subscribed to Extended user stream")
        except Exception:
            self.logger().error("Failed to subscribe to Extended user stream channels")
            raise

    async def _on_user_stream_interruption(self, ws: Optional[WSAssistant]):
        """
        Handle WebSocket interruption and cleanup.

        Args:
            ws: WebSocket assistant to disconnect
        """
        if ws is not None:
            await ws.disconnect()
        self._ws_assistant = None
        self.logger().info("Extended WebSocket disconnected, will reconnect...")

import time
from typing import Any, Dict, Optional

import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_constants as CONSTANTS
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest
from hummingbot.core.web_assistant.rest_pre_processors import RESTPreProcessorBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


class ExtendedPerpetualRESTPreProcessor(RESTPreProcessorBase):
    """Pre-processor for REST requests to Extended API."""

    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        """
        Add required headers to all Extended API requests.

        Extended requires:
        - Content-Type: application/json
        - User-Agent: (required by API)
        """
        if request.headers is None:
            request.headers = {}
        request.headers["Content-Type"] = "application/json"
        request.headers["User-Agent"] = "hummingbot-extended-connector"
        return request


def private_rest_url(path_url: str, domain: str = "extended_perpetual") -> str:
    """Build URL for private API endpoints."""
    return rest_url(path_url, domain)


def public_rest_url(path_url: str, domain: str = "extended_perpetual") -> str:
    """Build URL for public API endpoints."""
    return rest_url(path_url, domain)


def rest_url(path_url: str, domain: str = "extended_perpetual") -> str:
    """
    Build complete URL from path and domain.

    Args:
        path_url: API endpoint path (e.g., "/api/v1/info/markets")
        domain: Domain identifier (mainnet only)

    Returns:
        Complete URL string
    """
    base_url = CONSTANTS.PERPETUAL_BASE_URL
    return base_url + path_url


def stream_url(path_url: str, domain: str = "extended_perpetual") -> str:
    """
    Build complete URL for HTTP streaming endpoints.

    Extended uses HTTP GET streaming (Server-Sent Events) instead of WebSocket.

    Args:
        path_url: Streaming endpoint path (e.g., "/stream.extended.exchange/v1/account")
        domain: Domain identifier (mainnet only)

    Returns:
        Complete streaming URL string
    """
    base_url = CONSTANTS.PERPETUAL_STREAM_URL
    return base_url + path_url


def wss_url(domain: str = "extended_perpetual") -> str:
    """
    Get WebSocket URL for the domain.

    DEPRECATED: Extended uses HTTP streaming, not WebSocket.

    Args:
        domain: Domain identifier (mainnet only)

    Returns:
        WebSocket URL string
    """
    base_ws_url = CONSTANTS.PERPETUAL_WS_URL
    return base_ws_url


def build_api_factory(
        throttler: Optional[AsyncThrottler] = None,
        auth: Optional[AuthBase] = None) -> WebAssistantsFactory:
    """
    Build WebAssistantsFactory with throttler and auth.

    Args:
        throttler: Rate limiter instance
        auth: Authentication handler

    Returns:
        Configured WebAssistantsFactory
    """
    throttler = throttler or create_throttler()
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        rest_pre_processors=[ExtendedPerpetualRESTPreProcessor()],
        auth=auth)
    return api_factory


def build_api_factory_without_time_synchronizer_pre_processor(throttler: AsyncThrottler) -> WebAssistantsFactory:
    """Build API factory without time synchronizer (Extended doesn't need it)."""
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        rest_pre_processors=[ExtendedPerpetualRESTPreProcessor()])
    return api_factory


def create_throttler() -> AsyncThrottler:
    """Create throttler with Extended rate limits."""
    return AsyncThrottler(CONSTANTS.RATE_LIMITS)


async def get_current_server_time(
        throttler: AsyncThrottler,
        domain: str) -> float:
    """
    Get current server time.

    Extended doesn't require time synchronization, so we return local time.

    Args:
        throttler: Rate limiter (unused)
        domain: Domain identifier (unused)

    Returns:
        Current Unix timestamp
    """
    return time.time()


def is_exchange_information_valid(market: Dict[str, Any]) -> bool:
    """
    Verify if a trading pair is enabled to operate.

    Args:
        market: Market information dict from /api/v1/info/markets

    Returns:
        True if market is active and tradeable
    """
    # Check if market has required fields and is active
    if not isinstance(market, dict):
        return False

    # Extended markets should have 'name' and 'status'
    name = market.get('name')
    status = market.get('status', '').lower()

    # Market must have a name and be in active status
    if not name:
        return False

    # Check if market is active (status field may vary - adapt as needed)
    # Common statuses: "ACTIVE", "TRADING", "ONLINE", etc.
    if status and status not in ['active', 'trading', 'online', '']:
        return False

    return True

import time
from typing import Any, Dict, Optional

import hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_constants as CONSTANTS
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest
from hummingbot.core.web_assistant.rest_pre_processors import RESTPreProcessorBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


class LighterPerpetualRESTPreProcessor(RESTPreProcessorBase):
    """Pre-processor for REST requests to Lighter API."""

    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        """
        Add required headers to all Lighter API requests.

        Lighter requires:
        - Content-Type: application/json (for POST requests)
        """
        if request.headers is None:
            request.headers = {}
        request.headers["Content-Type"] = "application/json"
        return request


def private_rest_url(path_url: str, domain: str = "lighter_perpetual") -> str:
    """Build URL for private API endpoints."""
    return rest_url(path_url, domain)


def public_rest_url(path_url: str, domain: str = "lighter_perpetual") -> str:
    """Build URL for public API endpoints."""
    return rest_url(path_url, domain)


def rest_url(path_url: str, domain: str = "lighter_perpetual") -> str:
    """
    Build complete URL from path and domain.

    Args:
        path_url: API endpoint path (e.g., "/api/v1/orderBooks")
        domain: Domain identifier (lighter_perpetual or lighter_perpetual_testnet)

    Returns:
        Complete URL string
    """
    base_url = CONSTANTS.PERPETUAL_BASE_URL if domain == "lighter_perpetual" else CONSTANTS.TESTNET_BASE_URL
    return base_url + path_url


def wss_url(domain: str = "lighter_perpetual") -> str:
    """
    Get WebSocket URL for the domain.

    Args:
        domain: Domain identifier

    Returns:
        WebSocket URL string
    """
    base_ws_url = CONSTANTS.PERPETUAL_WS_URL if domain == "lighter_perpetual" else CONSTANTS.TESTNET_WS_URL
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
        rest_pre_processors=[LighterPerpetualRESTPreProcessor()],
        auth=auth)
    return api_factory


def build_api_factory_without_time_synchronizer_pre_processor(throttler: AsyncThrottler) -> WebAssistantsFactory:
    """Build API factory without time synchronizer (Lighter doesn't need it)."""
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        rest_pre_processors=[LighterPerpetualRESTPreProcessor()])
    return api_factory


def create_throttler() -> AsyncThrottler:
    """Create throttler with Lighter rate limits."""
    return AsyncThrottler(CONSTANTS.RATE_LIMITS)


async def get_current_server_time(
        throttler: AsyncThrottler,
        domain: str) -> float:
    """
    Get current server time.

    Lighter doesn't require time synchronization, so we return local time.

    Args:
        throttler: Rate limiter (unused)
        domain: Domain identifier (unused)

    Returns:
        Current Unix timestamp
    """
    return time.time()


def is_exchange_information_valid(order_book: Dict[str, Any]) -> bool:
    """
    Verify if a trading pair is enabled to operate.

    Args:
        order_book: Order book information dict from /api/v1/orderBooks

    Returns:
        True if market is active and tradeable
    """
    # Check if order book has required fields and is active
    if not isinstance(order_book, dict):
        return False

    # Lighter order books should have 'symbol' and 'market_id'
    symbol = order_book.get('symbol')
    market_id = order_book.get('market_id')
    status = order_book.get('status', '').lower()

    # Market must have symbol and market_id
    if not symbol or market_id is None:
        return False

    # Check if market is active
    # Status values may include: "ACTIVE", "TRADING", "ONLINE", etc.
    if status and status not in ['active', 'trading', 'online', '']:
        return False

    return True

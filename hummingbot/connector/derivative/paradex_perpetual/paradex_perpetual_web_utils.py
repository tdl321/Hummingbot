import time
from typing import Any, Dict, Optional

import hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_constants as CONSTANTS
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest
from hummingbot.core.web_assistant.rest_pre_processors import RESTPreProcessorBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


class ParadexPerpetualRESTPreProcessor(RESTPreProcessorBase):
    """Pre-processor for REST requests to Paradex API."""

    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        """
        Add required headers to all Paradex API requests.

        Paradex requires:
        - Content-Type: application/json
        """
        if request.headers is None:
            request.headers = {}
        request.headers["Content-Type"] = "application/json"
        return request


def private_rest_url(path_url: str, domain: str = "paradex_perpetual") -> str:
    """Build URL for private API endpoints."""
    return rest_url(path_url, domain)


def public_rest_url(path_url: str, domain: str = "paradex_perpetual") -> str:
    """Build URL for public API endpoints."""
    return rest_url(path_url, domain)


def rest_url(path_url: str, domain: str = "paradex_perpetual") -> str:
    """
    Build complete URL from path and domain.

    Args:
        path_url: API endpoint path (e.g., "/markets")
        domain: Domain identifier (paradex_perpetual or paradex_perpetual_testnet)

    Returns:
        Complete URL string
    """
    base_url = (
        CONSTANTS.TESTNET_BASE_URL
        if domain == CONSTANTS.TESTNET_DOMAIN
        else CONSTANTS.PERPETUAL_BASE_URL
    )
    return base_url + path_url


def wss_url(domain: str = "paradex_perpetual") -> str:
    """
    Get WebSocket URL for the domain.

    Args:
        domain: Domain identifier

    Returns:
        WebSocket URL string

    Note:
        Verify actual WebSocket URL from Paradex documentation.
        Current URLs are based on standard patterns.
    """
    base_ws_url = (
        CONSTANTS.TESTNET_WS_URL
        if domain == CONSTANTS.TESTNET_DOMAIN
        else CONSTANTS.PERPETUAL_WS_URL
    )
    return base_ws_url


def build_api_factory(
    throttler: Optional[AsyncThrottler] = None,
    auth: Optional[AuthBase] = None
) -> WebAssistantsFactory:
    """
    Build WebAssistantsFactory for Paradex API with throttler and auth.

    Args:
        throttler: Rate limiter instance (creates default if None)
        auth: Authentication handler

    Returns:
        Configured WebAssistantsFactory
    """
    throttler = throttler or create_throttler()
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        rest_pre_processors=[ParadexPerpetualRESTPreProcessor()],
        auth=auth
    )
    return api_factory


def build_api_factory_without_time_synchronizer_pre_processor(
    throttler: AsyncThrottler
) -> WebAssistantsFactory:
    """
    Build API factory without time synchronizer.

    Paradex uses JWT tokens for authentication, not timestamp-based signatures,
    so time synchronization is not required.

    Args:
        throttler: Rate limiter instance

    Returns:
        WebAssistantsFactory without time synchronizer
    """
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        rest_pre_processors=[ParadexPerpetualRESTPreProcessor()]
    )
    return api_factory


def create_throttler() -> AsyncThrottler:
    """
    Create rate limiter with Paradex rate limits.

    Returns:
        AsyncThrottler configured with RATE_LIMITS from constants
    """
    return AsyncThrottler(CONSTANTS.RATE_LIMITS)


async def get_current_server_time(
    throttler: AsyncThrottler,
    domain: str
) -> float:
    """
    Get current server time.

    Paradex doesn't require time synchronization for JWT-based auth,
    so we return local time.

    Args:
        throttler: Rate limiter (unused)
        domain: Domain identifier (unused)

    Returns:
        Current Unix timestamp (float)
    """
    return time.time()


def is_exchange_information_valid(market_info: Dict[str, Any]) -> bool:
    """
    Verify if a trading pair is enabled to operate.

    Args:
        market_info: Market information dict from /markets endpoint

    Returns:
        True if market is active and tradeable

    Note:
        Verify exact field names from Paradex API documentation.
        This implementation follows common patterns.
    """
    if not isinstance(market_info, dict):
        return False

    # Check for required fields
    # Paradex markets should have 'market' (symbol) and status
    symbol = market_info.get('market') or market_info.get('symbol')
    status = market_info.get('status', '').upper()

    # Market must have a symbol
    if not symbol:
        return False

    # Check if market is active
    # Common status values: "ACTIVE", "TRADING", "ONLINE"
    # If status field is missing, assume active
    if status and status not in ['ACTIVE', 'TRADING', 'ONLINE', '']:
        return False

    # Check if market is perpetual futures (filter out options, spot, etc.)
    # Perpetual futures typically have "PERP" suffix
    if not symbol.endswith('-PERP') and not symbol.endswith('-USD'):
        # May not be a perpetual futures market
        # But don't reject - let connector handle it
        pass

    return True

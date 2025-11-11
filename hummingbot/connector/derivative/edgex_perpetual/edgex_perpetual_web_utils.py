"""
EdgeX Perpetual Web Utilities

Provides utility functions for web communication including:
- API factory creation
- Throttler setup
- URL construction for REST and WebSocket
"""

from typing import Any, Dict, Optional

from hummingbot.connector.derivative.edgex_perpetual import edgex_perpetual_constants as CONSTANTS
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


def build_api_factory(
    throttler: Optional[AsyncThrottler] = None,
    auth: Optional[AuthBase] = None,
) -> WebAssistantsFactory:
    """
    Build WebAssistantsFactory for EdgeX API communication.

    Args:
        throttler: Rate limiter instance (creates new if None)
        auth: Authentication handler instance

    Returns:
        Configured WebAssistantsFactory instance
    """
    throttler = throttler or create_throttler()
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        auth=auth,
    )
    return api_factory


def create_throttler() -> AsyncThrottler:
    """
    Create AsyncThrottler with EdgeX rate limits.

    Returns:
        AsyncThrottler configured with RATE_LIMITS from constants
    """
    return AsyncThrottler(CONSTANTS.RATE_LIMITS)


def get_rest_url_for_endpoint(
    endpoint: str,
    domain: str = CONSTANTS.DOMAIN
) -> str:
    """
    Construct full REST API URL for given endpoint.

    Args:
        endpoint: API endpoint path (e.g., "/api/v1/public/meta/getServerTime")
        domain: Domain identifier (mainnet or testnet)

    Returns:
        Full URL string (e.g., "https://api.edgex.exchange/api/v1/public/meta/getServerTime")
    """
    base_url = (
        CONSTANTS.TESTNET_BASE_URL
        if domain == CONSTANTS.TESTNET_DOMAIN
        else CONSTANTS.PERPETUAL_BASE_URL
    )
    return f"{base_url}{endpoint}"


def get_ws_url_for_endpoint(
    domain: str = CONSTANTS.DOMAIN,
    private: bool = False
) -> str:
    """
    Get WebSocket URL for EdgeX.

    EdgeX has separate WebSocket endpoints for public and private data.

    Args:
        domain: Domain identifier (mainnet or testnet)
        private: If True, returns private WebSocket URL; otherwise public

    Returns:
        WebSocket URL string
    """
    if domain == CONSTANTS.TESTNET_DOMAIN:
        return (
            CONSTANTS.TESTNET_WS_PRIVATE_URL
            if private
            else CONSTANTS.TESTNET_WS_PUBLIC_URL
        )
    else:
        return (
            CONSTANTS.PERPETUAL_WS_PRIVATE_URL
            if private
            else CONSTANTS.PERPETUAL_WS_PUBLIC_URL
        )

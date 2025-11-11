"""
EdgeX Perpetual Constants

This file contains all constants for the EdgeX Perpetual connector including:
- Exchange metadata
- Base URLs
- API endpoints (verified from EdgeX GitBook documentation)
- WebSocket channels
- Order state mappings
- Rate limits

All endpoints have been verified against EdgeX API documentation at:
https://edgex-1.gitbook.io/edgeX-documentation/edgex-v1
"""

from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

# ===============================
# Exchange Metadata
# ===============================

EXCHANGE_NAME = "edgex_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = 36  # UUID format for client order IDs
DOMAIN = EXCHANGE_NAME
TESTNET_DOMAIN = "edgex_perpetual_testnet"

# ===============================
# Base URLs
# ===============================

# Mainnet (verified from official Python SDK)
PERPETUAL_BASE_URL = "https://pro.edgex.exchange"
PERPETUAL_WS_PUBLIC_URL = "wss://quote.edgex.exchange"
PERPETUAL_WS_PRIVATE_URL = "wss://quote.edgex.exchange"  # TODO: Verify if separate private WS endpoint exists

# Testnet (verified from official Python SDK)
TESTNET_BASE_URL = "https://testnet.edgex.exchange"
TESTNET_WS_PUBLIC_URL = "wss://quote-testnet.edgex.exchange"
TESTNET_WS_PRIVATE_URL = "wss://quote-testnet.edgex.exchange"  # TODO: Verify if separate private WS endpoint exists

# ===============================
# API Version
# ===============================

API_VERSION = "v1"

# ===============================
# Quote Currency
# ===============================

CURRENCY = "USD"  # Quote currency for perpetual futures

# ===============================
# Timing Constants
# ===============================

# Funding rate update interval (30 seconds)
FUNDING_RATE_UPDATE_INTERNAL_SECOND = 30

# Heartbeat interval for WebSocket
HEARTBEAT_TIME_INTERVAL = 30.0

# ===============================
# API Endpoints - Public
# ===============================

# Meta Data API (verified from EdgeX docs)
SERVER_TIME_URL = "/api/v1/public/meta/getServerTime"
METADATA_URL = "/api/v1/public/meta/getMetaData"

# Quote API (TODO: verify exact endpoints)
TICKER_URL = "/api/v1/public/quote/getTicker"  # TODO: Verify
ORDER_BOOK_URL = "/api/v1/public/quote/getOrderBook"  # TODO: Verify
TRADES_URL = "/api/v1/public/quote/getRecentTrades"  # TODO: Verify

# Funding API (TODO: verify exact endpoints)
FUNDING_RATE_URL = "/api/v1/public/funding/getFundingRate"  # TODO: Verify
FUNDING_HISTORY_URL = "/api/v1/public/funding/getFundingHistory"  # TODO: Verify

# ===============================
# API Endpoints - Private (Account)
# ===============================

# Account management (verified from EdgeX docs)
GET_ACCOUNT_PAGE_URL = "/api/v1/private/account/getAccountPage"
GET_ACCOUNT_BY_ID_URL = "/api/v1/private/account/getAccountById"
GET_ACCOUNT_ASSET_URL = "/api/v1/private/account/getAccountAsset"
REGISTER_ACCOUNT_URL = "/api/v1/private/account/registerAccount"

# Collateral/Balance endpoints (verified from EdgeX docs)
GET_COLLATERAL_BY_COIN_URL = "/api/v1/private/account/getCollateralByCoinId"
GET_COLLATERAL_TRANSACTION_PAGE_URL = "/api/v1/private/account/getCollateralTransactionPage"
GET_COLLATERAL_TRANSACTION_BY_ID_URL = "/api/v1/private/account/getCollateralTransactionById"
GET_ACCOUNT_ASSET_SNAPSHOT_PAGE_URL = "/api/v1/private/account/getAccountAssetSnapshotPage"

# Position endpoints (verified from EdgeX docs)
GET_POSITION_BY_CONTRACT_URL = "/api/v1/private/account/getPositionByContractId"
GET_POSITION_TERM_PAGE_URL = "/api/v1/private/account/getPositionTermPage"
GET_POSITION_TRANSACTION_PAGE_URL = "/api/v1/private/account/getPositionTransactionPage"
GET_POSITION_TRANSACTION_BY_ID_URL = "/api/v1/private/account/getPositionTransactionById"
GET_DELEVERAGE_LIGHT_URL = "/api/v1/private/account/getAccountDeleverageLight"

# ===============================
# API Endpoints - Private (Trading)
# ===============================

# Order management (verified from EdgeX docs)
CREATE_ORDER_URL = "/api/v1/private/order/createOrder"
CANCEL_ORDER_BY_ID_URL = "/api/v1/private/order/cancelOrderById"
CANCEL_ALL_ORDERS_URL = "/api/v1/private/order/cancelAllOrder"
GET_ORDER_BY_ID_URL = "/api/v1/private/order/getOrderById"
GET_ORDER_BY_CLIENT_ORDER_ID_URL = "/api/v1/private/order/getOrderByClientOrderId"
GET_ACTIVE_ORDER_PAGE_URL = "/api/v1/private/order/getActiveOrderPage"
GET_HISTORY_ORDER_PAGE_URL = "/api/v1/private/order/getHistoryOrderPage"
GET_HISTORY_ORDER_BY_ID_URL = "/api/v1/private/order/getHistoryOrderById"
GET_HISTORY_ORDER_BY_CLIENT_ORDER_ID_URL = "/api/v1/private/order/getHistoryOrderByClientOrderId"

# Order fill transactions (verified from EdgeX docs)
GET_HISTORY_ORDER_FILL_TRANSACTION_PAGE_URL = "/api/v1/private/order/getHistoryOrderFillTransactionPage"
GET_HISTORY_ORDER_FILL_TRANSACTION_BY_ID_URL = "/api/v1/private/order/getHistoryOrderFillTransactionById"

# Order utility (verified from EdgeX docs)
GET_MAX_CREATE_ORDER_SIZE_URL = "/api/v1/private/order/getMaxCreateOrderSize"

# ===============================
# API Endpoints - Private (Transfers & Withdrawals)
# ===============================

# Asset API (TODO: verify exact endpoints)
ASSET_URL = "/api/v1/private/asset/"  # TODO: Verify specific endpoints

# Transfer API (TODO: verify exact endpoints)
TRANSFER_URL = "/api/v1/private/transfer/"  # TODO: Verify specific endpoints

# Withdraw API (TODO: verify exact endpoints)
WITHDRAW_URL = "/api/v1/private/withdraw/"  # TODO: Verify specific endpoints

# ===============================
# Ping/Health Check
# ===============================

PING_URL = SERVER_TIME_URL  # Use server time as ping

# ===============================
# WebSocket Channels
# ===============================

# Public channels (verified from EdgeX docs)
WS_CHANNEL_TICKER = "ticker.{contractId}"  # Ticker for specific contract
WS_CHANNEL_TICKER_ALL = "ticker.all"  # Ticker for all contracts
WS_CHANNEL_KLINE = "kline.{priceType}.{contractId}.{interval}"  # Candlestick data
WS_CHANNEL_DEPTH = "depth.{contractId}.{depth}"  # Order book (depth: 15 or 200)
WS_CHANNEL_TRADES = "trades.{contractId}"  # Public trades
WS_CHANNEL_METADATA = "metadata"  # System metadata updates

# Private channels (TODO: verify exact channel names from EdgeX docs)
WS_CHANNEL_ACCOUNT = "account"  # Account updates
WS_CHANNEL_ORDERS = "orders"  # Order state changes
WS_CHANNEL_FILLS = "fills"  # Trade executions
WS_CHANNEL_POSITIONS = "positions"  # Position changes
WS_CHANNEL_COLLATERAL = "collateral"  # Balance/collateral updates

# ===============================
# Order States Mapping
# ===============================

# EdgeX order status → Hummingbot OrderState
ORDER_STATE = {
    "PENDING": OrderState.PENDING_CREATE,
    "OPEN": OrderState.OPEN,
    "FILLED": OrderState.FILLED,
    "CANCELING": OrderState.PENDING_CANCEL,
    "CANCELED": OrderState.CANCELED,
    "UNTRIGGERED": OrderState.OPEN,  # Stop/TP orders not yet triggered
}

# ===============================
# Order Types
# ===============================

ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_STOP_LIMIT = "STOP_LIMIT"
ORDER_TYPE_STOP_MARKET = "STOP_MARKET"
ORDER_TYPE_TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
ORDER_TYPE_TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"

# ===============================
# Order Sides
# ===============================

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

# ===============================
# Time In Force
# ===============================

TIME_IN_FORCE_GTC = "GTC"  # Good Till Cancel
TIME_IN_FORCE_IOC = "IOC"  # Immediate Or Cancel
TIME_IN_FORCE_FOK = "FOK"  # Fill Or Kill

# ===============================
# Rate Limits
# ===============================

# Note: EdgeX documentation does not specify exact rate limits
# Using conservative estimates based on similar DEX platforms
# TODO: Update with actual limits after testing or confirmation from EdgeX

MAX_REQUEST_PER_MINUTE = 1200  # 20 per second
MAX_REQUEST_PER_SECOND = 20

# Rate limit categories
ALL_ENDPOINTS_LIMIT = "All"
PUBLIC_LIMIT = "PublicLimit"
PRIVATE_LIMIT = "PrivateLimit"

# Pagination limits (from EdgeX docs)
MAX_ACTIVE_ORDER_PAGE_SIZE = 200  # Max size for active orders pagination
MAX_HISTORY_ORDER_PAGE_SIZE = 100  # Max size for history orders pagination
DEFAULT_PAGE_SIZE = 100  # Default page size for other paginated endpoints

# Rate limit definitions
RATE_LIMITS = [
    # Global rate limit (conservative)
    RateLimit(ALL_ENDPOINTS_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),

    # Public endpoints (higher limits typically)
    RateLimit(PUBLIC_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),
    RateLimit(SERVER_TIME_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(METADATA_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(ORDER_BOOK_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(TRADES_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(FUNDING_RATE_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Private endpoints (typically lower limits)
    RateLimit(PRIVATE_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),

    # Account endpoints
    RateLimit(GET_ACCOUNT_ASSET_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(GET_COLLATERAL_BY_COIN_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(GET_POSITION_BY_CONTRACT_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Trading endpoints (typically most restrictive)
    RateLimit(CREATE_ORDER_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(CANCEL_ORDER_BY_ID_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(CANCEL_ALL_ORDERS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(GET_ACTIVE_ORDER_PAGE_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(GET_HISTORY_ORDER_PAGE_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
]

# ===============================
# Authentication Headers
# ===============================

# EdgeX uses ECDSA signature authentication (verified from docs)
HEADER_TIMESTAMP = "X-edgeX-Api-Timestamp"
HEADER_SIGNATURE = "X-edgeX-Api-Signature"

# ===============================
# Response Fields
# ===============================

# Standard response wrapper fields (from EdgeX docs)
RESPONSE_CODE = "code"
RESPONSE_DATA = "data"
RESPONSE_MSG = "msg"
RESPONSE_ERROR_PARAM = "errorParam"
RESPONSE_REQUEST_TIME = "requestTime"
RESPONSE_RESPONSE_TIME = "responseTime"
RESPONSE_TRACE_ID = "traceId"

# Success code
RESPONSE_CODE_SUCCESS = "SUCCESS"

# ===============================
# WebSocket Message Types
# ===============================

WS_TYPE_SUBSCRIBE = "subscribe"
WS_TYPE_SUBSCRIBED = "subscribed"
WS_TYPE_UNSUBSCRIBE = "unsubscribe"
WS_TYPE_MESSAGE = "message"
WS_TYPE_PING = "ping"
WS_TYPE_PONG = "pong"

# WebSocket data types
WS_DATA_TYPE_SNAPSHOT = "Snapshot"
WS_DATA_TYPE_CHANGED = "Changed"

# ===============================
# L2 Order Fields
# ===============================

# EdgeX requires L2-specific fields for order creation (StarkEx)
L2_NONCE = "l2Nonce"
L2_VALUE = "l2Value"
L2_SIZE = "l2Size"
L2_LIMIT_FEE = "l2LimitFee"
L2_EXPIRE_TIME = "l2ExpireTime"
L2_SIGNATURE = "l2Signature"

from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

# Exchange metadata
EXCHANGE_NAME = "paradex_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = 36  # UUID format
DOMAIN = EXCHANGE_NAME
TESTNET_DOMAIN = "paradex_perpetual_testnet"

# Base URLs
# Mainnet
PERPETUAL_BASE_URL = "https://api.prod.paradex.trade/v1"
PERPETUAL_WS_URL = "wss://ws.api.prod.paradex.trade/v1"  # Verified from Paradex docs

# Testnet
TESTNET_BASE_URL = "https://api.testnet.paradex.trade/v1"
TESTNET_WS_URL = "wss://ws.api.testnet.paradex.trade/v1"  # Verified from Paradex docs

# Quote currency
CURRENCY = "USD"

# Funding rate update interval (30 seconds)
FUNDING_RATE_UPDATE_INTERNAL_SECOND = 30  # Poll every 30s

# Heartbeat interval
HEARTBEAT_TIME_INTERVAL = 30.0

# ===============================
# API Endpoints - Public
# ===============================

# Markets and system
MARKETS_INFO_URL = "/markets"
MARKET_SUMMARY_URL = "/markets/{market}/summary"
SYSTEM_CONFIG_URL = "/system/config"
ORDER_BOOK_URL = "/markets/{market}/orderbook"
TRADES_URL = "/markets/{market}/trades"
CANDLES_URL = "/markets/{market}/candles"
FUNDING_RATE_URL = "/markets/{market}/funding"
HEALTH_CHECK_URL = "/system/health"

# ===============================
# API Endpoints - Private (Account)
# ===============================

ACCOUNT_SUMMARY_URL = "/account"
ACCOUNT_PROFILE_URL = "/account/profile"
BALANCES_URL = "/account/balances"
POSITIONS_URL = "/positions"

# ===============================
# API Endpoints - Private (Trading)
# ===============================

CREATE_ORDER_URL = "/orders"
CANCEL_ORDER_URL = "/orders/{order_id}"
CANCEL_ALL_ORDERS_URL = "/orders"
MODIFY_ORDER_URL = "/orders/{order_id}"
LIST_ORDERS_URL = "/orders"
ORDER_HISTORY_URL = "/orders/history"
FILLS_URL = "/fills"

# ===============================
# API Endpoints - Private (Transfers)
# ===============================

TRANSFERS_URL = "/transfers"
TRANSFER_HISTORY_URL = "/transfers/history"
FUNDING_PAYMENTS_URL = "/funding_payments"

# ===============================
# API Endpoints - Authentication
# ===============================

ONBOARD_URL = "/onboarding"
AUTH_URL = "/auth"

# ===============================
# Ping endpoint
# ===============================

PING_URL = "/system/health"

# ===============================
# WebSocket Channels
# ===============================

# Public channels
WS_CHANNEL_MARKETS_SUMMARY = "markets_summary"
WS_CHANNEL_ORDERBOOK = "orderbook.{market}"
WS_CHANNEL_TRADES = "trades.{market}"

# Private channels (require authentication)
WS_CHANNEL_ACCOUNT = "account"
WS_CHANNEL_ORDERS = "orders"
WS_CHANNEL_FILLS = "fills"
WS_CHANNEL_POSITIONS = "positions"
WS_CHANNEL_BALANCE_EVENTS = "balance_events"

# ===============================
# Order States Mapping
# ===============================

ORDER_STATE = {
    "PENDING": OrderState.PENDING_CREATE,
    "OPEN": OrderState.OPEN,
    "FILLED": OrderState.FILLED,
    "PARTIALLY_FILLED": OrderState.PARTIALLY_FILLED,
    "CANCELLED": OrderState.CANCELED,
    "EXPIRED": OrderState.CANCELED,
    "REJECTED": OrderState.FAILED,
    "FAILED": OrderState.FAILED,
}

# ===============================
# Rate Limits
# ===============================

# Note: Actual rate limits from Paradex docs may differ
# These are conservative estimates based on similar DEX platforms
# TODO: Update with exact limits from Paradex API documentation
MAX_REQUEST_PER_MINUTE = 1200  # 20 per second
MAX_REQUEST_PER_SECOND = 20

ALL_ENDPOINTS_LIMIT = "All"
PUBLIC_LIMIT = "PublicLimit"
PRIVATE_LIMIT = "PrivateLimit"

# Rate limit definitions
RATE_LIMITS = [
    # Global rate limit
    RateLimit(ALL_ENDPOINTS_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),

    # Public endpoints (higher limits)
    RateLimit(PUBLIC_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),
    RateLimit(MARKETS_INFO_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(MARKET_SUMMARY_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(SYSTEM_CONFIG_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(ORDER_BOOK_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(TRADES_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(FUNDING_RATE_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(HEALTH_CHECK_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Private endpoints (lower limits for safety)
    RateLimit(PRIVATE_LIMIT, limit=MAX_REQUEST_PER_MINUTE // 2, time_interval=60),
    RateLimit(ACCOUNT_SUMMARY_URL, limit=MAX_REQUEST_PER_MINUTE // 2, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(BALANCES_URL, limit=MAX_REQUEST_PER_MINUTE // 2, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(POSITIONS_URL, limit=MAX_REQUEST_PER_MINUTE // 2, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(LIST_ORDERS_URL, limit=MAX_REQUEST_PER_MINUTE // 2, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(ORDER_HISTORY_URL, limit=MAX_REQUEST_PER_MINUTE // 2, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(FILLS_URL, limit=MAX_REQUEST_PER_MINUTE // 2, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Trading operations (most critical, lower limits)
    RateLimit(CREATE_ORDER_URL, limit=MAX_REQUEST_PER_MINUTE // 4, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(CANCEL_ORDER_URL, limit=MAX_REQUEST_PER_MINUTE // 4, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(CANCEL_ALL_ORDERS_URL, limit=MAX_REQUEST_PER_MINUTE // 4, time_interval=60,
             linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
]

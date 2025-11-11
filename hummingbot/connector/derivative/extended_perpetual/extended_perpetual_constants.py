from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

EXCHANGE_NAME = "extended_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = 32

DOMAIN = EXCHANGE_NAME
TESTNET_DOMAIN = "extended_perpetual_testnet"

# Base URLs
PERPETUAL_BASE_URL = "https://api.starknet.extended.exchange"
TESTNET_BASE_URL = "https://starknet.sepolia.extended.exchange"

# HTTP Streaming URLs (Extended uses HTTP GET streaming, not WebSocket)
PERPETUAL_STREAM_URL = "http://api.starknet.extended.exchange"
TESTNET_STREAM_URL = "http://starknet.sepolia.extended.exchange"

# WebSocket URLs (DEPRECATED - Extended uses HTTP streaming instead)
PERPETUAL_WS_URL = "wss://api.starknet.extended.exchange/stream.extended.exchange/v1"
TESTNET_WS_URL = "wss://starknet.sepolia.extended.exchange/stream.extended.exchange/v1"

# Funding rate update interval (1 hour for Extended)
# Note: Extended funding payments occur hourly
FUNDING_RATE_UPDATE_INTERNAL_SECOND = 60 * 60 * 1  # 1 hour

# Quote currency
CURRENCY = "USD"

# API Endpoints - Public
MARKETS_INFO_URL = "/api/v1/info/markets"
MARKET_STATS_URL = "/api/v1/info/markets/{market}/stats"
ORDER_BOOK_URL = "/api/v1/info/markets/{market}/orderbook"
TRADES_URL = "/api/v1/info/markets/{market}/trades"
CANDLES_URL = "/api/v1/info/candles/{market}/{candleType}"
FUNDING_RATE_URL = "/api/v1/info/{market}/funding"
OPEN_INTEREST_URL = "/api/v1/info/{market}/open-interests"
TICKER_PRICE_CHANGE_URL = "/api/v1/info/markets/{market}/stats"

# HTTP Streaming Endpoints (Server-Sent Events)
STREAM_ORDERBOOK_URL = "/stream.extended.exchange/v1/orderbooks/{market}"
STREAM_ACCOUNT_URL = "/stream.extended.exchange/v1/account"

# API Endpoints - Private (Account)
ACCOUNT_INFO_URL = "/api/v1/user/account/info"
BALANCE_URL = "/api/v1/user/balance"
ASSET_OPERATIONS_URL = "/api/v1/user/assetOperations"
LEVERAGE_URL = "/api/v1/user/leverage"
FEE_INFO_URL = "/api/v1/user/fees"

# API Endpoints - Private (Trading)
POSITIONS_URL = "/api/v1/user/positions"
POSITIONS_HISTORY_URL = "/api/v1/user/positions/history"
ORDERS_URL = "/api/v1/user/orders"
ORDERS_HISTORY_URL = "/api/v1/user/orders/history"
CREATE_ORDER_URL = "/api/v1/user/order"
CANCEL_ORDER_URL = "/api/v1/user/order/{id}"
MASS_CANCEL_URL = "/api/v1/user/order/massCancel"
DEADMAN_SWITCH_URL = "/api/v1/user/deadmanswitch"
TRADES_HISTORY_URL = "/api/v1/user/trades"
FUNDING_HISTORY_URL = "/api/v1/user/funding/history"

# Ping endpoint (for health check)
PING_URL = "/api/v1/info/markets"

# Order States mapping
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

# Heartbeat interval
HEARTBEAT_TIME_INTERVAL = 30.0

# Rate Limits
# Extended API: Standard = 1,000 requests/minute, Market Makers = 60,000 requests/5 minutes
# Conservative approach: 1,000 per minute = ~16.67 per second
MAX_REQUEST_PER_MINUTE = 1000
MAX_REQUEST_PER_SECOND = 16

ALL_ENDPOINTS_LIMIT = "All"

RATE_LIMITS = [
    # Global limit
    RateLimit(ALL_ENDPOINTS_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),

    # Public endpoints
    RateLimit(limit_id=MARKETS_INFO_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=MARKET_STATS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=ORDER_BOOK_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=TRADES_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=CANDLES_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=FUNDING_RATE_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=OPEN_INTEREST_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=PING_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Private endpoints
    RateLimit(limit_id=ACCOUNT_INFO_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=BALANCE_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=LEVERAGE_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=POSITIONS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=ORDERS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=CREATE_ORDER_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=CANCEL_ORDER_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=MASS_CANCEL_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=TRADES_HISTORY_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=FUNDING_HISTORY_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Streaming endpoints
    RateLimit(limit_id=STREAM_ORDERBOOK_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=STREAM_ACCOUNT_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
]

# Error messages
ORDER_NOT_EXIST_MESSAGE = "Order does not exist"
UNKNOWN_ORDER_MESSAGE = "Order was never placed, already canceled, or filled"

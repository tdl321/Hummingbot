from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

EXCHANGE_NAME = "lighter_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = 32

DOMAIN = EXCHANGE_NAME
TESTNET_DOMAIN = "lighter_perpetual_testnet"

# Base URLs
PERPETUAL_BASE_URL = "https://mainnet.zklighter.elliot.ai"
TESTNET_BASE_URL = "https://testnet.zklighter.elliot.ai"  # If testnet exists

# WebSocket URLs
PERPETUAL_WS_URL = "wss://mainnet.zklighter.elliot.ai/stream"
TESTNET_WS_URL = "wss://testnet.zklighter.elliot.ai/stream"

# Funding rate update interval (30 seconds for Lighter)
FUNDING_RATE_UPDATE_INTERNAL_SECOND = 30  # 30 seconds

# Quote currency
CURRENCY = "USD"

# API Endpoints - Public
STATUS_URL = "/status"
INFO_URL = "/info"
ORDER_BOOKS_URL = "/api/v1/orderBooks"  # Get market mappings
CANDLESTICKS_URL = "/api/v1/candlesticks"
FUNDING_RATES_URL = "/api/v1/fundings"  # Critical for funding rate strategy

# API Endpoints - Account
ACCOUNT_DETAILS_URL = "/api/v1/account"
ACCOUNT_LIMITS_URL = "/api/v1/limits"
ACCOUNT_METADATA_URL = "/api/v1/metadata"
ACCOUNT_PNL_URL = "/api/v1/pnl"
ACCOUNT_LIQUIDATION_URL = "/api/v1/liquidation"
ACCOUNT_FUNDING_URL = "/api/v1/funding"  # User's funding payments
POOL_METADATA_URL = "/api/v1/pool/metadata"

# API Endpoints - Orders
ACTIVE_ORDERS_URL = "/api/v1/orders/active"
INACTIVE_ORDERS_URL = "/api/v1/orders/inactive"
ORDER_BOOK_URL = "/api/v1/orderbook"
ORDER_BOOK_ORDERS_URL = "/api/v1/orderbook/orders"
RECENT_TRADES_URL = "/api/v1/trades"
TRADE_HISTORY_URL = "/api/v1/trades/history"
EXCHANGE_STATS_URL = "/api/v1/stats"
EXPORT_URL = "/api/v1/export"

# API Endpoints - Transactions
ACCOUNT_TRANSACTIONS_URL = "/api/v1/transactions/account"
BLOCK_TRANSACTIONS_URL = "/api/v1/transactions/block"
DEPOSIT_HISTORY_URL = "/api/v1/transactions/deposit"
WITHDRAWAL_HISTORY_URL = "/api/v1/transactions/withdrawal"
TRANSFER_HISTORY_URL = "/api/v1/transactions/transfer"
NONCE_URL = "/api/v1/transactions/nonce"
SEND_TX_URL = "/api/v1/sendTx"  # Send transaction
SEND_TX_BATCH_URL = "/api/v1/sendTxBatch"  # Batch transactions
L1_TX_URL = "/api/v1/l1Tx"

# API Endpoints - Blocks
BLOCKS_URL = "/api/v1/blocks"
BLOCK_HEIGHT_URL = "/api/v1/blocks/height"

# API Endpoints - Bridge
FAST_BRIDGE_URL = "/api/v1/fastbridge"

# API Endpoints - Notifications & Referrals
NOTIFICATIONS_ACK_URL = "/api/v1/notifications/ack"
REFERRAL_POINTS_URL = "/api/v1/referral/points"

# API Endpoints - Fees
TRANSFER_FEE_URL = "/api/v1/fees/transfer"
WITHDRAWAL_DELAY_URL = "/api/v1/fees/withdrawalDelay"

# Ping endpoint (for health check)
PING_URL = "/status"

# Order States mapping (to be updated based on Lighter's actual states)
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
# Lighter API: Conservative approach, actual limits TBD
MAX_REQUEST_PER_MINUTE = 600
MAX_REQUEST_PER_SECOND = 10

ALL_ENDPOINTS_LIMIT = "All"

RATE_LIMITS = [
    # Global limit
    RateLimit(ALL_ENDPOINTS_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),

    # Public endpoints
    RateLimit(limit_id=STATUS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=INFO_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=ORDER_BOOKS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=CANDLESTICKS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=FUNDING_RATES_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=PING_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Account endpoints
    RateLimit(limit_id=ACCOUNT_DETAILS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=ACCOUNT_FUNDING_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Order endpoints
    RateLimit(limit_id=ACTIVE_ORDERS_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=ORDER_BOOK_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=RECENT_TRADES_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),

    # Transaction endpoints
    RateLimit(limit_id=SEND_TX_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
    RateLimit(limit_id=SEND_TX_BATCH_URL, limit=MAX_REQUEST_PER_MINUTE, time_interval=60,
              linked_limits=[LinkedLimitWeightPair(ALL_ENDPOINTS_LIMIT)]),
]

# Error messages
ORDER_NOT_EXIST_MESSAGE = "Order does not exist"
UNKNOWN_ORDER_MESSAGE = "Order was never placed, already canceled, or filled"

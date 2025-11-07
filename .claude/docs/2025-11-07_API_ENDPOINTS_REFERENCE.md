# Extended & Lighter DEX - API Endpoints Reference

**Date**: 2025-11-07
**Source**: Official API Documentation Analysis

---

## 🔷 Extended DEX (formerly x10.exchange)

### Base URLs

**Mainnet REST API**: `https://api.starknet.extended.exchange`
**Mainnet WebSocket**: `wss://api.starknet.extended.exchange/stream.extended.exchange/v1`
**Testnet REST API**: `https://api.testnet.extended.exchange`

### Authentication

**Headers Required**:
- `X-Api-Key: <YOUR_API_KEY>` (all authenticated endpoints)
- `User-Agent: <YOUR_USER_AGENT>` (mandatory for all requests)
- `Content-Type: application/json` (POST requests)

**Stark Signatures**: All order management endpoints require SNIP12 standard Stark signatures

### Rate Limits

- **Standard**: 1,000 requests/minute per IP
- **Market Makers**: 60,000 requests per 5 minutes

---

## Extended REST API Endpoints

### Public Market Data

| Method | Endpoint | Description | Response Key Fields |
|--------|----------|-------------|---------------------|
| GET | `/api/v1/info/markets` | List all markets | `status`, `data` (array of market configs) |
| GET | `/api/v1/info/markets/{market}/stats` | Market statistics | `markPrice`, `indexPrice`, `24hVolume`, `fundingRate` |
| GET | `/api/v1/info/markets/{market}/orderbook` | Order book snapshot | `bids` (array), `asks` (array), `timestamp` |
| GET | `/api/v1/info/markets/{market}/trades` | Recent trades | `data` (array of trades) |
| GET | `/api/v1/info/{market}/funding` | Funding rate history | `data` (array): `m` (market), `T` (timestamp), `f` (funding rate) |
| GET | `/api/v1/info/candles/{market}/{candleType}` | OHLCV candles | Supports `trades`, `mark-prices`, `index-prices` |
| GET | `/api/v1/info/{market}/open-interests` | Open interest | Current open interest for market |

**Funding Rate Endpoint Parameters**:
```
GET /api/v1/info/{market}/funding
Query Params:
  - startTime: Unix timestamp in milliseconds
  - endTime: Unix timestamp in milliseconds
  - limit: Number of records to return (default: 100)

Response Schema:
{
  "status": "OK",
  "data": [
    {
      "m": "KAITO-USD",      // market
      "T": 1699876800000,    // timestamp (ms)
      "f": "0.0001"          // funding rate (decimal string)
    }
  ]
}
```

### Private Account Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/user/account/info` | Account info including vault ID | API Key |
| GET | `/api/v1/user/balance` | Account balance and margin | API Key |
| GET | `/api/v1/user/positions` | Open positions | API Key |
| GET | `/api/v1/user/positions/history` | Historical positions | API Key |
| GET | `/api/v1/user/funding/history` | Funding payment records | API Key |
| GET | `/api/v1/user/leverage` | Current leverage by market | API Key |
| PATCH | `/api/v1/user/leverage` | Update leverage | API Key + Stark Sig |

**Account Info Response**:
```json
{
  "status": "OK",
  "data": {
    "vault": "12345",           // Vault ID (required for signing)
    "vaultId": "12345",         // Alternative field name
    "accountId": "...",
    "starkPublicKey": "0x...",
    "balance": "1000.00"
  }
}
```

**Funding History Response**:
```json
{
  "status": "OK",
  "data": [
    {
      "market": "KAITO-USD",
      "fundingRate": "0.0001",
      "payment": "0.05",          // Payment amount in USD
      "timestamp": 1699876800000,
      "position": "100.0"
    }
  ]
}
```

### Order Management Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/user/order` | Create or edit order | API Key + Stark Sig |
| DELETE | `/api/v1/user/order/{id}` | Cancel by order ID | API Key + Stark Sig |
| DELETE | `/api/v1/user/order?externalId={id}` | Cancel by external ID | API Key + Stark Sig |
| POST | `/api/v1/user/order/massCancel` | Bulk cancel | API Key + Stark Sig |
| GET | `/api/v1/user/orders` | Open orders | API Key |
| GET | `/api/v1/user/orders/history` | Order history | API Key |
| GET | `/api/v1/user/trades` | Trade history | API Key |

**Order Creation Request Schema**:
```json
{
  "externalId": "string",        // Client order ID (optional)
  "market": "KAITO-USD",         // Market symbol
  "type": "LIMIT",               // LIMIT, MARKET, CONDITIONAL, TPSL
  "side": "BUY",                 // BUY or SELL
  "price": "0.15",               // Required even for market orders
  "qty": "100.0",                // Order quantity
  "fee": "0.0002",               // Max fee willing to pay (decimal: 0.1 = 10%)
  "expireTime": 1699976400000,   // Unix timestamp in ms (max 90 days mainnet)
  "reduceOnly": false,           // Optional
  "postOnly": false,             // Optional
  "timeInForce": "GTT",          // GTT (default) or IOC
  "starkSignature": {            // Generated via x10 SDK
    "r": "0x...",
    "s": "0x..."
  }
}
```

**Order Response Schema**:
```json
{
  "status": "OK",
  "data": {
    "orderId": "123456",         // Extended order ID
    "externalId": "client_001",  // Your client ID
    "market": "KAITO-USD",
    "type": "LIMIT",
    "side": "BUY",
    "price": "0.15",
    "qty": "100.0",
    "filled": "0.0",
    "status": "PENDING",         // PENDING, OPEN, FILLED, CANCELLED
    "createdAt": 1699876800000
  }
}
```

---

## Extended WebSocket API

### Connection

**URL**: `wss://api.starknet.extended.exchange/stream.extended.exchange/v1`

**Heartbeat**: Server sends ping every 15s, expects pong within 10s

### Subscription Format

```json
{
  "type": "subscribe",
  "channel": "orderbook",
  "market": "KAITO-USD"
}
```

### Available Channels

**Public Channels**:
- `orderbook:{market}` - Order book updates
- `trades:{market}` - Trade stream
- `funding:{market}` - Funding rate updates
- `candles:{market}:{interval}` - Candlestick data
- `markPrice:{market}` - Mark price updates
- `indexPrice:{market}` - Index price updates

**Private Channels** (require auth):
- `user:orders` - Order updates
- `user:positions` - Position updates
- `user:balances` - Balance updates
- `user:funding` - Funding payment notifications

### WebSocket Message Schemas

**Order Book Message**:
```json
{
  "channel": "orderbook",
  "market": "KAITO-USD",
  "data": {
    "bids": [["0.15", "100.0"], ["0.14", "200.0"]],
    "asks": [["0.16", "150.0"], ["0.17", "250.0"]],
    "timestamp": 1699876800000
  }
}
```

**Trade Message**:
```json
{
  "channel": "trades",
  "market": "KAITO-USD",
  "data": [{
    "id": "trade_123",
    "price": "0.15",
    "amount": "100.0",
    "side": "buy",
    "timestamp": 1699876800000
  }]
}
```

---

## 🔷 Lighter DEX

### Base URLs

**Mainnet REST API**: `https://mainnet.zklighter.elliot.ai`
**Mainnet WebSocket**: `wss://mainnet.zklighter.elliot.ai/stream`

### Authentication

**Transaction Signing**: All order operations require signatures via lighter SDK SignerClient
**API Key**: Used for read operations (not required for SDK signing)

### Rate Limits

- **Premium Account**: 24,000 weighted requests per minute
- **Standard Account**: 60 weighted requests per minute

---

## Lighter REST API Endpoints

### Public Market Data

| Method | Endpoint | Description | Key Response Fields |
|--------|----------|-------------|---------------------|
| GET | `/api/v1/orderBooks` | List all order books | `order_books` (array): `symbol`, `market_id` |
| GET | `/api/v1/orderbook` | Order book snapshot | `bids`, `asks`, `market_id` |
| GET | `/api/v1/recentTrades` | Recent trades | `trades` (array) |
| GET | `/api/v1/trades` | Historical trades | `trades` (array) |
| GET | `/api/v1/candlesticks` | OHLCV data | `candlesticks` (array) |
| GET | `/api/v1/funding-rates` | Current funding rates | See schema below |
| GET | `/api/v1/fundings` | Funding rate history | See schema below |
| GET | `/` | Service status | `status` |

**Order Books Endpoint** (For Market ID Mapping):
```
GET /api/v1/orderBooks

Response:
{
  "code": 200,
  "order_books": [
    {
      "symbol": "KAITO",         // Token symbol (add "-USD" for trading pair)
      "market_id": 33,           // Integer market ID (CRITICAL for orders!)
      "status": "active",
      "base_decimals": 18,
      "quote_decimals": 6
    }
  ]
}
```

**Fundings Endpoint** (Funding Rate History):
```
GET /api/v1/fundings
Query Params:
  - market_id: INTEGER (required)
  - resolution: STRING ("1h", "8h", "1d")
  - start_timestamp: UNIX timestamp in seconds
  - end_timestamp: UNIX timestamp in seconds
  - count_back: INTEGER (number of records, alternative to timestamps)

Response:
{
  "code": 200,
  "resolution": "1h",
  "fundings": [
    {
      "timestamp": 1699876800,     // Unix timestamp (seconds)
      "market_id": 33,
      "value": "0.0001",           // Funding rate value (string)
      "direction": "long"          // "long" (longs pay) or "short" (shorts pay)
    }
  ]
}
```

**Funding Rate Direction**:
- `"long"`: Longs pay shorts (positive rate for shorts, negative for strategy)
- `"short"`: Shorts pay longs (positive rate for longs, positive for strategy)

### Private Account Endpoints

| Method | Endpoint | Description | SDK Required |
|--------|----------|-------------|--------------|
| GET | `/api/v1/account` | Account details | No |
| GET | `/api/v1/accountLimits` | Trading limits | No |
| GET | `/api/v1/pnl` | Profit/loss data | No |
| GET | `/api/v1/accountActiveOrders` | Active orders | No |
| GET | `/api/v1/accountInactiveOrders` | Inactive orders | No |
| POST | `/api/v1/sendTx` | Submit signed transaction | Yes (SignerClient) |
| POST | `/api/v1/sendTxBatch` | Batch transactions | Yes (SignerClient) |

**Account Response**:
```json
{
  "code": 200,
  "account": {
    "account_id": 123,
    "l1_address": "0x...",
    "balance": "1000.00",
    "available_balance": "950.00",
    "positions": [...]
  }
}
```

### Order Placement via SDK

**Lighter uses SignerClient from lighter-sdk - NOT direct REST API!**

```python
from lighter import SignerClient

# Initialize
client = SignerClient(
    url="https://mainnet.zklighter.elliot.ai",
    private_key="0x...",  # Ethereum private key
    api_key_index=0,
    account_index=0
)

# LIMIT Order
order_tx, tx_hash, signature = client.create_order(
    market_index=33,              # From /api/v1/orderBooks
    client_order_index=123,       # Unique order identifier
    base_amount="100.0",          # Order size
    price="0.15",                 # Limit price
    is_ask=False,                 # False = BUY, True = SELL
    order_type=0,                 # 0 = LIMIT, 1 = FOK, 2 = IOC
    time_in_force=0,              # 0 = GTC
    reduce_only=False
)

# MARKET Order
order_tx, tx_hash, signature = client.create_market_order(
    market_index=33,
    client_order_index=124,
    base_amount="100.0",
    avg_execution_price="0.15",   # Reference price
    is_ask=False,
    reduce_only=False
)

# tx_hash.hash contains the transaction hash (exchange order ID)
```

---

## Lighter WebSocket API

### Connection

**URL**: `wss://mainnet.zklighter.elliot.ai/stream`

**Test Connection**: `wscat -c 'wss://mainnet.zklighter.elliot.ai/stream'`

### Subscription Format

```json
{
  "type": "subscribe",
  "channel": "CHANNEL_NAME",
  "auth": "TOKEN"              // Required for account channels
}
```

### Public Channels

**Order Book**:
```json
{
  "type": "subscribe",
  "channel": "order_book:33"   // market_id
}

// Response:
{
  "channel": "order_book:33",
  "offset": 12345,
  "order_book": {
    "asks": [{"price": "0.16", "size": "100.0"}],
    "bids": [{"price": "0.15", "size": "150.0"}],
    "offset": 12345
  }
}
```

**Trades**:
```json
{
  "type": "subscribe",
  "channel": "trade:33"
}

// Response:
{
  "channel": "trade:33",
  "trades": [{
    "trade_id": 456789,
    "tx_hash": "0x...",
    "market_id": 33,
    "size": "100.0",
    "price": "0.15",
    "ask_id": 123,
    "bid_id": 124,
    "is_maker_ask": true,
    "block_height": 5000000,
    "timestamp": 1699876800
  }]
}
```

**Market Stats** (includes funding):
```json
{
  "channel": "market_stats:33",
  "market_id": 33,
  "index_price": "0.15",
  "mark_price": "0.1505",
  "open_interest": "1000000.0",
  "current_funding_rate": "0.0001",
  "funding_rate": "0.0001",
  "funding_timestamp": 1699876800
}
```

### Account Channels (Require Auth)

Available channels:
- `account_all` - All account updates
- `account_market:{market_id}` - Market-specific updates
- `account_orders` - Order updates
- `account_all_positions` - Position updates
- `account_tx` - Transaction updates

---

## 🔑 Key Differences Summary

| Feature | Extended DEX | Lighter DEX |
|---------|--------------|-------------|
| **Market Identifier** | String: "KAITO-USD" | Integer: 33 |
| **Order Signing** | Stark signatures via x10 SDK | Ethereum signatures via lighter SDK |
| **Order API** | REST POST with signed payload | SDK method (SignerClient) |
| **Funding Interval** | Hourly (1h) | Hourly (1h) |
| **Funding Timestamp** | Milliseconds | Seconds |
| **WebSocket URL** | wss://api.starknet.extended.exchange/... | wss://mainnet.zklighter.elliot.ai/stream |
| **Order ID** | String | Integer |
| **Fees** | 0.02% maker, 0.05% taker | 0% fees |

---

## ✅ Implementation Checklist

### Extended Connector Verification:
- [ ] Base URL matches: `https://api.starknet.extended.exchange`
- [ ] Funding endpoint: `GET /api/v1/info/{market}/funding`
- [ ] Funding response parsing: `data[].f` (funding rate)
- [ ] Timestamp format: milliseconds
- [ ] Order placement via x10 SDK `PerpetualTradingClient`
- [ ] Vault ID fetched from `/api/v1/user/account/info`

### Lighter Connector Verification:
- [ ] Base URL matches: `https://mainnet.zklighter.elliot.ai`
- [ ] Market ID mapping from `/api/v1/orderBooks`
- [ ] Funding endpoint: `GET /api/v1/fundings`
- [ ] Funding response parsing: `fundings[].value` + `direction`
- [ ] Timestamp format: seconds
- [ ] Order placement via lighter SDK `SignerClient`

---

**Document Version**: 1.0
**Last Verified**: 2025-11-07

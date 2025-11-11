# EdgeX API Verification Report

**Date**: 2025-01-15
**Purpose**: Document verified EdgeX API endpoints before connector implementation
**Source**: EdgeX GitBook Documentation (https://edgex-1.gitbook.io/edgeX-documentation)

---

## Authentication Mechanism

### Method: ECDSA Signature Authentication

EdgeX uses signature-based authentication (NOT JWT tokens like Paradex). Key differences:
- No JWT token generation
- Each request requires fresh signature
- Signature includes timestamp, method, path, and sorted parameters

### Required Headers for Private APIs

1. **`X-edgeX-Api-Timestamp`** (string)
   - Timestamp when request was made (milliseconds)
   - Prevents replay attacks

2. **`X-edgeX-Api-Signature`** (string)
   - ECDSA signature using private key
   - Signature content format: `{timestamp}{METHOD}{path}{sortedParams}`
   - Hashed with SHA3 before signing

### Signature Generation Example
```
Message: 1735542383256GET/api/v1/private/account/getAccountAssetaccountId=543429922991899150
Hash: SHA3(message)
Signature: ECDSA_sign(hash, private_key)
```

### Private Key
- Obtained from account settings in EdgeX UI
- Used directly for request signing (no intermediate token)

### SDKs Available
- Python SDK
- Golang SDK

---

## Base URLs

### Production
- **REST API Base**: `https://api.edgex.exchange` (assumed, verify from SDK)
- **Public WebSocket**: `wss://api.edgex.exchange/api/v1/public/ws`
- **Private WebSocket**: `wss://api.edgex.exchange/api/v1/private/ws`

### Testnet
- **REST API Base**: TBD (check EdgeX docs for testnet URL)
- **WebSocket URLs**: TBD

---

## REST API Endpoints

### Public APIs (No Authentication)

#### Meta Data API

| Purpose | Method | Path | Parameters | Response Fields |
|---------|--------|------|------------|-----------------|
| Server Time | GET | `/api/v1/public/meta/getServerTime` | None | `timeMillis` |
| System Metadata | GET | `/api/v1/public/meta/getMetaData` | None | `global`, `coinList`, `contractList`, `multiChain` |

**Meta Data Response Structure:**
- `global`: App environment, account IDs, contract addresses, fee rates
- `coinList`: Supported coins with precision, asset details
- `contractList`: Trading pairs with leverage tiers, fees, funding rates
- `multiChain`: Cross-chain deposit/withdrawal configuration

#### Quote API
- Path prefix: `/api/v1/public/quote/...` (TBD - check docs)
- Purpose: Market data, prices, ticker information

#### Funding API
- Path prefix: `/api/v1/public/funding/...` (TBD - check docs)
- Purpose: Funding rate data

### Private APIs (Require Authentication)

#### Account API

| Purpose | Method | Path | Parameters | Response Fields |
|---------|--------|------|------------|-----------------|
| **Get Account Asset** | GET | `/api/v1/private/account/getAccountAsset` | `accountId` | `account`, `collateralList`, `positionList`, `version` |
| Get Account Page | GET | `/api/v1/private/account/getAccountPage` | `size`, `offsetData` | `dataList`, `nextPageOffsetData` |
| Get Account by ID | GET | `/api/v1/private/account/getAccountById` | `accountId` | `id`, `userId`, `ethAddress`, `l2Key` |
| Register Account | POST | `/api/v1/private/account/registerAccount` | `l2Key`, `l2KeyYCoordinate`, `clientAccountId` | `accountId` |

**Collateral (Balance) Endpoints:**

| Purpose | Method | Path | Parameters | Response Fields |
|---------|--------|------|------------|-----------------|
| **Get Collateral by Coin** | GET | `/api/v1/private/account/getCollateralByCoinId` | `accountId`, `coinIdList` | `amount`, `legacyAmount`, `cumDepositAmount` |
| Get Collateral Transactions | GET | `/api/v1/private/account/getCollateralTransactionPage` | `accountId`, `size`, `filterCoinIdList` | `id`, `type`, `deltaAmount`, `censorStatus` |
| Get Collateral by ID | GET | `/api/v1/private/account/getCollateralTransactionById` | `accountId`, `collateralTransactionIdList` | Transaction records |
| Get Asset Snapshot | GET | `/api/v1/private/account/getAccountAssetSnapshotPage` | `accountId`, `coinId`, `size` | `totalEquity`, `unrealizePnl`, `snapshotTime` |

**Position Endpoints:**

| Purpose | Method | Path | Parameters | Response Fields |
|---------|--------|------|------------|-----------------|
| **Get Position by Contract** | GET | `/api/v1/private/account/getPositionByContractId` | `accountId`, `contractIdList` | `openSize`, `openValue`, `fundingFee` |
| Get Position Term Page | GET | `/api/v1/private/account/getPositionTermPage` | `accountId`, `size`, `offsetData` | `termCount`, `cumOpenSize`, `cumCloseFee` |
| Get Position Transactions | GET | `/api/v1/private/account/getPositionTransactionPage` | `accountId`, `filterCoinIdList`, `filterContractIdList` | `id`, `type`, `fillPrice`, `realizePnl` |
| Get Position Transaction by ID | GET | `/api/v1/private/account/getPositionTransactionById` | `accountId`, `positionTransactionIdList` | Position details |

#### Order API

**Create Order:**

| Method | Path | Required Parameters |
|--------|------|---------------------|
| POST | `/api/v1/private/order/createOrder` | `accountId`, `contractId`, `side`, `size`, `price`, `clientOrderId`, `type`, `timeInForce`, `reduceOnly`, `l2Nonce`, `l2Value`, `l2Size`, `l2LimitFee`, `l2ExpireTime`, `l2Signature` |

**Cancel Orders:**

| Purpose | Method | Path | Parameters |
|---------|--------|------|------------|
| Cancel by ID | POST | `/api/v1/private/order/cancelOrderById` | `accountId`, `orderIdList` |
| Cancel All | POST | `/api/v1/private/order/cancelAllOrder` | `accountId`, optional filters |

**Query Orders:**

| Purpose | Method | Path | Parameters | Notes |
|---------|--------|------|------------|-------|
| Get by Order ID | GET | `/api/v1/private/order/getOrderById` | `accountId`, `orderIdList` | Active orders |
| Get by Client Order ID | GET | `/api/v1/private/order/getOrderByClientOrderId` | `accountId`, `clientOrderIdList` | Active orders |
| Active Orders Page | GET | `/api/v1/private/order/getActiveOrderPage` | `accountId`, `size` (max 200), `offsetData` | Paginated |
| History Orders Page | GET | `/api/v1/private/order/getHistoryOrderPage` | `accountId`, `size` (max 100), `offsetData` | Paginated |
| History by ID | GET | `/api/v1/private/order/getHistoryOrderById` | `accountId`, `orderIdList` | Historical |
| History by Client ID | GET | `/api/v1/private/order/getHistoryOrderByClientOrderId` | `accountId`, `clientOrderIdList` | Historical |

**Order Fills:**

| Purpose | Method | Path | Parameters |
|---------|--------|------|------------|
| Fill Transactions Page | GET | `/api/v1/private/order/getHistoryOrderFillTransactionPage` | `accountId`, `size`, `offsetData` |
| Fill by ID | GET | `/api/v1/private/order/getHistoryOrderFillTransactionById` | `accountId`, `fillTransactionIdList` |

**Utility:**

| Purpose | Method | Path | Parameters |
|---------|--------|------|------------|
| Max Order Size | POST | `/api/v1/private/order/getMaxCreateOrderSize` | `accountId`, `contractId`, `side`, `price` |

#### Order Status Values
- `PENDING` - Order submitted, awaiting confirmation
- `OPEN` - Order active in order book
- `FILLED` - Order completely filled
- `CANCELING` - Cancel request submitted
- `CANCELED` - Order cancelled
- `UNTRIGGERED` - Stop/take-profit order not yet triggered

#### Order Types
- `LIMIT` - Standard limit order
- `MARKET` - Market order
- `STOP_LIMIT` - Stop limit order
- `STOP_MARKET` - Stop market order
- `TAKE_PROFIT_LIMIT` - Take profit limit
- `TAKE_PROFIT_MARKET` - Take profit market

#### Asset API
- Path prefix: `/api/v1/private/asset/...` (TBD - check docs)
- Purpose: Asset management, deposits, withdrawals

#### Transfer API
- Path prefix: `/api/v1/private/transfer/...` (TBD - check docs)
- Purpose: Internal transfers

#### Withdraw API
- Path prefix: `/api/v1/private/withdraw/...` (TBD - check docs)
- Purpose: Withdrawal management

---

## WebSocket API

### Connection URLs

**Public WebSocket (Market Data):**
- URL: `/api/v1/public/ws` (full: `wss://api.edgex.exchange/api/v1/public/ws`)
- No authentication required

**Private WebSocket (User Data):**
- URL: `/api/v1/private/ws` (full: `wss://api.edgex.exchange/api/v1/private/ws`)
- Requires authentication

### Subscription Format

```json
{
  "type": "subscribe",
  "channel": "channel_name"
}
```

### Subscription Response

```json
{
  "type": "subscribed",
  "channel": "channel_name"
}
```

### Public Channels

| Channel | Format | Purpose | Parameters |
|---------|--------|---------|------------|
| Ticker | `ticker.{contractId}` or `ticker.all` | Ticker data for specific contract or all | contractId (optional) |
| K-Line/Candlestick | `kline.{priceType}.{contractId}.{interval}` | OHLCV data | priceType, contractId, interval |
| Order Book (Depth) | `depth.{contractId}.{depth}` | Order book snapshots/updates | contractId, depth (15 or 200) |
| Trades | `trades.{contractId}` | Public trade feed | contractId |
| Metadata | `metadata` | System metadata updates | None |

### Private Channels (TBD - verify from docs)
- Orders (order state changes)
- Fills (trade executions)
- Positions (position updates)
- Collateral (balance changes)

### Message Format

Data messages contain:
- `type`: "message" or specific type
- `dataType`: "Snapshot" (initial) or "Changed" (update)
- `data`: Array of data items
- `channel`: Channel name

### Heartbeat Mechanism

**Ping Message:**
```json
{
  "type": "ping",
  "time": "timestamp"
}
```

**Required Response:**
```json
{
  "type": "pong"
}
```

**Timeout**: Connection terminates after 5 consecutive missed pong responses

---

## Rate Limits

### Observed Limits (TBD - verify actual limits)
- Not explicitly documented
- Conservative estimate: 20 requests/second, 1200 requests/minute
- Need to test and verify actual limits

### Pagination Limits
- Active orders: max 200 per page
- History orders: max 100 per page
- Other endpoints: typically 100 per page

---

## Order State Mapping

### EdgeX → Hummingbot OrderState

| EdgeX Status | Hummingbot OrderState | Notes |
|--------------|----------------------|-------|
| PENDING | PENDING_CREATE | Order submitted |
| OPEN | OPEN | Order in book |
| FILLED | FILLED | Completely filled |
| CANCELING | PENDING_CANCEL | Cancel in progress |
| CANCELED | CANCELED | Cancelled |
| UNTRIGGERED | OPEN | Stop/TP not triggered yet |

---

## Key Differences from Paradex

### 1. Authentication
- **Paradex**: JWT token-based (generate once, refresh periodically)
- **EdgeX**: Signature per request (no JWT, fresh signature each time)

### 2. API Design
- **Paradex**: RESTful paths (`/orders`, `/positions`, `/account/balances`)
- **EdgeX**: RPC-style paths (`/getAccountAsset`, `/createOrder`, `/cancelOrderById`)

### 3. Parameter Passing
- **Paradex**: Path parameters and JSON body
- **EdgeX**: Query parameters for GET, JSON body for POST

### 4. WebSocket Channels
- **Paradex**: Simple channel names (`orders`, `fills`, `positions`)
- **EdgeX**: Parameterized channels (`ticker.{contractId}`, `depth.{contractId}.{depth}`)

### 5. Order Creation
- **EdgeX**: Requires L2-specific fields (`l2Nonce`, `l2Value`, `l2Size`, `l2LimitFee`, `l2ExpireTime`, `l2Signature`)
- **Paradex**: Simpler order creation, SDK handles L2 fields

---

## Implementation Considerations

### Critical Points

1. **No JWT Tokens**: Authentication is per-request signatures, not token-based
2. **L2 Order Fields**: Order creation requires StarkEx L2-specific parameters
3. **Python SDK**: EdgeX provides SDK that likely handles signature generation and L2 fields
4. **RPC-Style API**: Endpoints are named like functions, not RESTful resources
5. **Parameter Names**: Use exact parameter names (`accountId`, `contractId`, `coinIdList`)

### Recommended Approach

1. **Use EdgeX Python SDK** (if available) for:
   - Signature generation
   - L2 order field calculation
   - Request signing

2. **Direct REST API** for:
   - Balance fetching (`getCollateralByCoinId`)
   - Position fetching (`getPositionByContractId`)
   - Order querying

3. **WebSocket** for:
   - Real-time order book (`depth.{contractId}.200`)
   - Trade feed (`trades.{contractId}`)
   - Private updates (if channels exist)

### Next Steps

1. **Find EdgeX Python SDK**:
   - Check PyPI for `edgex-py` or similar
   - Review SDK documentation
   - Test SDK authentication

2. **Test API Endpoints**:
   - Use SDK or curl to test authentication
   - Verify exact parameter names
   - Save response examples

3. **Verify WebSocket Channels**:
   - Connect to public WebSocket
   - Test channel subscriptions
   - Verify message formats

4. **Test Private WebSocket**:
   - Determine authentication method for private WS
   - Test user data channels
   - Verify order/fill update formats

---

## Open Questions

1. **EdgeX Python SDK**:
   - [ ] Does it exist on PyPI?
   - [ ] What's the package name?
   - [ ] Does it handle signature generation?
   - [ ] Does it handle L2 order fields?

2. **Base URLs**:
   - [ ] Confirm production REST API base URL
   - [ ] Find testnet REST API URL
   - [ ] Verify WebSocket URLs

3. **Private WebSocket Channels**:
   - [ ] What are the exact channel names?
   - [ ] How to authenticate private WebSocket?
   - [ ] Message formats for orders, fills, positions?

4. **Rate Limits**:
   - [ ] What are the actual rate limits?
   - [ ] Are there endpoint-specific limits?
   - [ ] Is there IP-based rate limiting?

5. **Funding Rates**:
   - [ ] Where to fetch funding rates? (Funding API or metadata?)
   - [ ] Update frequency?
   - [ ] Historical funding rate endpoint?

6. **Position Mode & Leverage**:
   - [ ] Does EdgeX support hedge mode vs one-way mode?
   - [ ] How to set leverage per contract?
   - [ ] Cross margin vs isolated margin?

---

## Phase 0 Exit Criteria

- [x] Authentication mechanism documented (ECDSA signature)
- [x] REST API endpoints documented
- [x] WebSocket channels documented
- [x] Order states mapped to Hummingbot
- [ ] EdgeX Python SDK identified and tested
- [ ] Test API calls with authentication
- [ ] Verify WebSocket connectivity
- [ ] Save example API responses

**Status**: Partial - Need SDK testing and API verification with actual calls

**Next Action**: Find and test EdgeX Python SDK for authentication and order creation

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Author**: Claude Code

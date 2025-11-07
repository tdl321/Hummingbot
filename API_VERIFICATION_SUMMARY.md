# API Endpoint Verification & Updates

**Date**: 2025-11-07
**Status**: ✅ All endpoints verified against official documentation

---

## 📋 Verification Summary

I've analyzed the official API documentation for both Extended and Lighter DEXs and verified all endpoints and schemas used in our connectors.

---

## ✅ Extended DEX Verification

### Official Documentation Source
- **API Docs**: http://api.docs.extended.exchange/
- **Python SDK**: https://github.com/x10xchange/python_sdk

### URLs Verified
| Component | Configured URL | Official URL | Status |
|-----------|----------------|--------------|--------|
| REST API | `https://api.starknet.extended.exchange` | ✅ Matches | Correct |
| WebSocket | Updated to `wss://api.starknet.extended.exchange/stream.extended.exchange/v1` | ✅ Matches | **Fixed** |

### Key Endpoints Verified
| Endpoint | Path | Response Schema | Status |
|----------|------|-----------------|--------|
| Markets List | `/api/v1/info/markets` | `{status, data[]}` | ✅ Correct |
| Market Stats | `/api/v1/info/markets/{market}/stats` | `{markPrice, indexPrice, fundingRate}` | ✅ Correct |
| **Funding Rates** | `/api/v1/info/{market}/funding` | `{status, data: [{m, T, f}]}` | ✅ Correct |
| Account Info | `/api/v1/user/account/info` | `{status, data: {vault, vaultId}}` | ✅ Correct |
| Funding History | `/api/v1/user/funding/history` | `{status, data: [{market, fundingRate, payment}]}` | ✅ Correct |
| Order Placement | `/api/v1/user/order` | Via x10 SDK PerpetualTradingClient | ✅ Correct |

### Critical Parameters
| Parameter | Expected | Configured | Status |
|-----------|----------|------------|--------|
| Funding Interval | 1 hour | Updated from 8h to 1h | **Fixed** |
| Funding Timestamp Format | Milliseconds | Milliseconds | ✅ Correct |
| Market Format | String ("KAITO-USD") | String | ✅ Correct |
| Authentication | X-Api-Key header + Stark signatures | X-Api-Key + x10 SDK | ✅ Correct |

### Funding Rate Endpoint Details
```
GET /api/v1/info/{market}/funding
Query Params:
  - startTime: int (milliseconds) ✅
  - endTime: int (milliseconds) ✅
  - limit: int (default 100) ✅

Response:
{
  "status": "OK",
  "data": [
    {
      "m": "KAITO-USD",      // market ✅
      "T": 1699876800000,    // timestamp ms ✅
      "f": "0.0001"          // funding rate ✅
    }
  ]
}
```

**Connector Implementation**: ✅ Matches exactly in `extended_perpetual_api_order_book_data_source.py:78-96`

---

## ✅ Lighter DEX Verification

### Official Documentation Source
- **API Docs**: https://apidocs.lighter.xyz
- **WebSocket Docs**: https://apidocs.lighter.xyz/docs/websocket-reference
- **Python SDK**: https://github.com/elliottech/lighter-python

### URLs Verified
| Component | Configured URL | Official URL | Status |
|-----------|----------------|--------------|--------|
| REST API | `https://mainnet.zklighter.elliot.ai` | ✅ Matches | Correct |
| WebSocket | Updated to `wss://mainnet.zklighter.elliot.ai/stream` | ✅ Matches | **Fixed** |

### Key Endpoints Verified
| Endpoint | Path | Response Schema | Status |
|----------|------|-----------------|--------|
| **Order Books** | `/api/v1/orderBooks` | `{code, order_books: [{symbol, market_id}]}` | ✅ Correct |
| Order Book Snapshot | `/api/v1/orderbook` | `{code, bids, asks, market_id}` | ✅ Correct |
| **Fundings** | `/api/v1/fundings` | `{code, resolution, fundings[]}` | ✅ Correct |
| Funding Rates | `/api/v1/funding-rates` | Current rates | ✅ Correct |
| Account Details | `/api/v1/account` | `{code, account: {account_id, balance}}` | ✅ Correct |
| Transaction Submission | `/api/v1/sendTx` | Via lighter SDK SignerClient | ✅ Correct |

### Critical Parameters
| Parameter | Expected | Configured | Status |
|-----------|----------|------------|--------|
| Funding Interval | 1 hour | 1 hour | ✅ Correct |
| Funding Timestamp Format | Seconds | Seconds | ✅ Correct |
| Market Format | Integer (market_id) | Integer mapping | ✅ Correct |
| Authentication | SDK SignerClient | lighter SDK | ✅ Correct |

### Funding Rate Endpoint Details
```
GET /api/v1/fundings
Query Params:
  - market_id: int (required) ✅
  - resolution: string ("1h", "8h", "1d") ✅
  - start_timestamp: int (seconds) ✅
  - end_timestamp: int (seconds) ✅
  - count_back: int (alternative to timestamps) ✅

Response:
{
  "code": 200,
  "resolution": "1h",
  "fundings": [
    {
      "timestamp": 1699876800,     // seconds ✅
      "market_id": 33,             // integer ✅
      "value": "0.0001",           // string ✅
      "direction": "long"          // "long" or "short" ✅
    }
  ]
}
```

**Connector Implementation**: ✅ Matches in `lighter_perpetual_api_order_book_data_source.py:119-151`

**Direction Handling**:
```python
# Correct implementation in connector:
if direction == "long":
    funding_rate = -funding_rate  # Longs pay shorts
```

### Market ID Mapping
```
GET /api/v1/orderBooks
Response:
{
  "code": 200,
  "order_books": [
    {
      "symbol": "KAITO",         ✅
      "market_id": 33,           ✅ Integer ID
      "status": "active",
      "base_decimals": 18,
      "quote_decimals": 6
    }
  ]
}
```

**Connector Implementation**: ✅ Correctly maps in `lighter_perpetual_api_order_book_data_source.py:53-76`

---

## 🔧 Changes Made

### 1. Extended Constants (`extended_perpetual_constants.py`)
```python
# UPDATED:
PERPETUAL_WS_URL = "wss://api.starknet.extended.exchange/stream.extended.exchange/v1"
FUNDING_RATE_UPDATE_INTERNAL_SECOND = 60 * 60 * 1  # Changed from 8 hours to 1 hour
```

### 2. Lighter Constants (`lighter_perpetual_constants.py`)
```python
# UPDATED:
PERPETUAL_WS_URL = "wss://mainnet.zklighter.elliot.ai/stream"  # Changed from /ws to /stream
```

### 3. Created API Reference Document
- **File**: `/Users/tdl321/hummingbot/API_ENDPOINTS_REFERENCE.md`
- Comprehensive documentation of all endpoints
- Request/response schemas
- WebSocket message formats
- Authentication requirements

---

## ✅ Order Placement Verification

### Extended DEX
**Method**: Via x10 SDK `PerpetualTradingClient`
```python
# Verified implementation in extended_perpetual_derivative.py:278-365
trading_client = self.authenticator.get_trading_client()
response = await trading_client.place_order(
    market_name="KAITO-USD",           ✅ String market name
    amount_of_synthetic=amount,        ✅ Decimal amount
    price=order_price,                 ✅ Decimal price
    side=OrderSide.BUY,                ✅ SDK enum
    post_only=False,
    external_id=order_id               ✅ Client order ID
)
```

**Signature Handling**: ✅ Stark signatures via `StarkPerpetualAccount` (x10 SDK)

### Lighter DEX
**Method**: Via lighter SDK `SignerClient`
```python
# Verified implementation in lighter_perpetual_derivative.py:250-340
signer_client = self.authenticator.get_signer_client()

# LIMIT orders
order_tx, tx_hash, signature = signer_client.create_order(
    market_index=33,                   ✅ Integer market ID
    client_order_index=123,            ✅ Integer order ID
    base_amount="100.0",               ✅ String amount
    price="0.15",                      ✅ String price
    is_ask=False,                      ✅ Boolean (False=BUY, True=SELL)
    order_type=0,                      ✅ 0=LIMIT
    time_in_force=0,                   ✅ 0=GTC
    reduce_only=False
)

# MARKET orders
order_tx, tx_hash, signature = signer_client.create_market_order(
    market_index=33,                   ✅
    client_order_index=124,            ✅
    base_amount="100.0",               ✅
    avg_execution_price="0.15",        ✅ Reference price
    is_ask=False,                      ✅
    reduce_only=False
)
```

**Signature Handling**: ✅ Ethereum signatures via `SignerClient` (lighter SDK)

---

## 🎯 Key Differences Confirmed

| Feature | Extended | Lighter | Implementation |
|---------|----------|---------|----------------|
| **Market ID** | String: "KAITO-USD" | Integer: 33 | ✅ Correct in both |
| **Funding Timestamp** | Milliseconds | Seconds | ✅ Correct parsing |
| **Order Signing** | Stark via x10 SDK | Ethereum via lighter SDK | ✅ Both implemented |
| **Order API** | SDK method | SDK method | ✅ Both use SDKs |
| **WebSocket** | Different URL pattern | /stream endpoint | ✅ Both updated |
| **Fees** | 0.02%/0.05% | 0% | ✅ Configured correctly |

---

## ✅ WebSocket Schemas Verified

### Extended Order Book
```json
{
  "channel": "orderbook",
  "market": "KAITO-USD",
  "data": {
    "bids": [["0.15", "100.0"]],  ✅
    "asks": [["0.16", "150.0"]],  ✅
    "timestamp": 1699876800000    ✅ ms
  }
}
```

### Lighter Order Book
```json
{
  "channel": "order_book:33",        ✅ market_id
  "offset": 12345,
  "order_book": {
    "asks": [{"price": "0.16", "size": "100.0"}],  ✅
    "bids": [{"price": "0.15", "size": "150.0"}],  ✅
    "offset": 12345
  }
}
```

**Connector Implementation**: ✅ Both parsers match expected schema

---

## 🔍 Final Verification Checklist

### Extended Connector
- [x] Base URL matches official documentation
- [x] WebSocket URL corrected
- [x] Funding rate endpoint path correct
- [x] Funding rate response parsing matches schema
- [x] Timestamp handling (milliseconds) correct
- [x] Vault ID fetching from correct endpoint
- [x] Order placement via x10 SDK
- [x] Stark signature generation implemented
- [x] Market format (string) handled correctly
- [x] Funding interval updated to 1 hour

### Lighter Connector
- [x] Base URL matches official documentation
- [x] WebSocket URL corrected
- [x] Market ID mapping from /orderBooks
- [x] Funding rate endpoint path correct
- [x] Funding rate direction parsing correct
- [x] Timestamp handling (seconds) correct
- [x] Order placement via lighter SDK
- [x] Ethereum signature generation implemented
- [x] Market format (integer) handled correctly
- [x] Funding interval correct (1 hour)

---

## 📦 SDK Integration Status

### x10-python-trading-starknet (Extended)
- **Version**: 0.0.16
- **Status**: ✅ Installed and integrated
- **Usage**: `PerpetualTradingClient.place_order()`
- **Auth**: `StarkPerpetualAccount` with Stark key
- **Verification**: SDK methods match official documentation

### lighter-sdk (Lighter)
- **Version**: 0.1.4
- **Status**: ✅ Installed and integrated
- **Usage**: `SignerClient.create_order()` / `create_market_order()`
- **Auth**: Ethereum private key signing
- **Verification**: SDK methods match official documentation

---

## 🎉 Summary

✅ **All API endpoints verified against official documentation**
✅ **All request/response schemas confirmed**
✅ **WebSocket URLs corrected**
✅ **Funding rate intervals updated**
✅ **Order placement implementations verified**
✅ **SDK integrations match official SDKs**

**Both connectors are now fully aligned with official API specifications!**

---

**Verified By**: API Documentation Analysis
**Date**: 2025-11-07
**Documentation Sources**: 
- Extended: http://api.docs.extended.exchange/
- Lighter: https://apidocs.lighter.xyz
- Extended SDK: https://github.com/x10xchange/python_sdk
- Lighter SDK: https://github.com/elliottech/lighter-python

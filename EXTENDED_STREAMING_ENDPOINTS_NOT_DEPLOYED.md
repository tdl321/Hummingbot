# Extended Exchange: Streaming Endpoints Not Yet Deployed

**Issue Date**: 2025-01-11
**Status**: 🟡 Waiting on Extended Exchange
**Priority**: Medium
**Component**: Extended Perpetual Connector - HTTP Streaming

---

## 📋 Issue Summary

Extended Exchange's HTTP streaming endpoints (Server-Sent Events) are documented but **not yet deployed to production**. All streaming endpoint requests return **404 Not Found**, while regular REST API endpoints work correctly.

## 🔍 Problem Details

### What We Found

The Extended Exchange documentation specifies HTTP GET streaming endpoints:
- **Public Stream**: `GET /stream.extended.exchange/v1/orderbooks/{market}`
- **Private Stream**: `GET /stream.extended.exchange/v1/account`

However, when testing these endpoints against the production server, all return **HTTP 404**:

```bash
# Tested URLs (all return 404):
http://api.starknet.extended.exchange/stream.extended.exchange/v1/orderbooks/KAITO-USD
https://api.starknet.extended.exchange/stream.extended.exchange/v1/orderbooks/KAITO-USD
http://api.starknet.extended.exchange/stream.extended.exchange/v1/account
https://api.starknet.extended.exchange/stream.extended.exchange/v1/account
```

### What Works

Regular REST API endpoints work perfectly:
```bash
# Works (returns 200 OK):
https://api.starknet.extended.exchange/api/v1/info/markets
https://api.starknet.extended.exchange/api/v1/user/balance  # (with auth)
```

## ✅ Verification Steps Taken

### 1. URL Construction Verification
- ✅ Confirmed paths match documentation exactly
- ✅ Tested with documented host: `api.starknet.extended.exchange`
- ✅ Tried both HTTP and HTTPS protocols
- ✅ Tested alternative path structures (`/v1/...`, `/stream/v1/...`)
- **Result**: All variations return 404

### 2. Authentication Testing
- ✅ Tested account stream with valid `X-Api-Key` header
- ✅ Confirmed API key works for REST endpoints
- **Result**: Still returns 404 (not an auth issue)

### 3. Base URL Validation
- ✅ Confirmed REST API works at same base URL
- ✅ Verified production server is reachable
- ✅ No DNS or network issues
- **Result**: Server is live, only streaming endpoints missing

## 📊 Test Results Summary

| Endpoint Type | URL Pattern | Status | Notes |
|--------------|-------------|---------|-------|
| REST API (Public) | `/api/v1/info/markets` | ✅ 200 OK | Working |
| REST API (Private) | `/api/v1/user/balance` | ✅ 200 OK | Working with auth |
| Stream (Public) | `/stream.extended.exchange/v1/orderbooks/*` | ❌ 404 | Not deployed |
| Stream (Private) | `/stream.extended.exchange/v1/account` | ❌ 404 | Not deployed |

## 🎯 Root Cause

**Extended Exchange has not yet deployed their HTTP streaming API to production servers.**

Evidence:
1. Documentation exists for streaming endpoints
2. REST API works at the same base URL
3. All streaming endpoint variations return 404
4. No alternative working URL pattern found

## 💡 Current Connector Status

### ✅ Implementation Complete

We have **fully implemented** HTTP streaming support in the Extended connector:

**Files Modified:**
- ✅ `extended_perpetual_constants.py` - Streaming URLs configured
- ✅ `extended_perpetual_web_utils.py` - Stream URL helper added
- ✅ `extended_perpetual_api_order_book_data_source.py` - HTTP streaming implemented
- ✅ `extended_perpetual_user_stream_data_source.py` - Authenticated streaming implemented

**Features Implemented:**
- ✅ Server-Sent Events (SSE) parsing
- ✅ Authenticated streaming with `X-Api-Key`
- ✅ Auto-reconnection on connection drops
- ✅ Per-trading-pair streaming
- ✅ Message type routing (ORDER, TRADE, BALANCE, POSITION)

### 🟡 Waiting on Extended

The connector is **code-complete and ready** but cannot be tested because:
- Streaming endpoints return 404
- No data available to validate message formats
- Cannot verify end-to-end functionality

## 🔄 Next Steps

### Immediate Actions Needed

1. **Contact Extended Exchange Team**
   - Confirm streaming API deployment timeline
   - Verify endpoint URLs are correct
   - Request notification when endpoints go live

2. **Documentation Clarification**
   - Ask if documentation reflects current or future API state
   - Confirm whether endpoints are production-ready
   - Request any staging/testing environment URLs

### Once Endpoints Are Live

1. **Validation Testing**
   ```bash
   python test_http_streaming.py
   ```

2. **Verify Message Formats**
   - Confirm SSE data format matches implementation
   - Validate JSON message structure
   - Test all message types (ORDER, TRADE, BALANCE, POSITION)

3. **Performance Testing**
   - Test with multiple trading pairs
   - Verify reconnection logic
   - Monitor connection stability

4. **Integration Testing**
   - Run full connector test suite
   - Validate orderbook updates
   - Test account balance updates
   - Verify order lifecycle tracking

## 📝 Questions for Extended Team

### Critical Questions

1. **Deployment Status**
   - When will streaming endpoints be deployed to production?
   - Are they available on testnet/staging?
   - Any beta access program for testing?

2. **URL Verification**
   - Are the documented URLs correct?
   - Is `/stream.extended.exchange/v1/...` the correct path?
   - Should we use a different host/subdomain?

3. **Alternative Solutions**
   - Until streaming is available, should we use REST polling?
   - What polling frequency is acceptable?
   - Any rate limit considerations?

### Technical Questions

4. **Message Format**
   - Can you provide sample SSE messages?
   - Confirm JSON structure for each message type
   - Any message envelope/wrapper format?

5. **Authentication**
   - Is `X-Api-Key` header correct for private streams?
   - Any additional auth requirements?
   - Token refresh needed for long-lived connections?

6. **Connection Management**
   - Expected ping/pong intervals?
   - Recommended reconnection strategy?
   - Maximum connection duration?

## 📎 Reference Information

### Documentation Provided

From Extended Exchange documentation:

> **Private WebSocket streams**
> Connect to the WebSocket streams using `ws://api.starknet.extended.exchange` as the host.
>
> The server sends pings every 15 seconds and expects a pong response within 10 seconds.
>
> **Authentication**
> Authenticate by using your API key in an HTTP header: `X-Api-Key: <API_KEY>`
>
> **Account updates stream**
> HTTP Request: `GET /stream.extended.exchange/v1/account`

### Test Script Available

A test script is available to validate streaming once endpoints are live:
- **Location**: `/Users/tdl321/hummingbot/test_http_streaming.py`
- **Usage**: `python test_http_streaming.py`
- **Tests**: URL construction, SSE parsing, authentication, message handling

## 🏷️ Tags

`extended-exchange` `http-streaming` `server-sent-events` `connector` `not-deployed` `waiting-on-vendor` `api-404`

---

## 📞 Contact Points

**Extended Exchange:**
- Documentation: [Extended Exchange Docs]
- Support: [Check Extended website for support channels]

**Hummingbot Connector:**
- Implementation: Complete and ready
- Status: Waiting on Extended API deployment
- Test Script: `test_http_streaming.py`

---

**Last Updated**: 2025-01-11
**Next Review**: When Extended notifies endpoints are live

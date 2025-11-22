# Extended Exchange Streaming Tests

This directory contains test scripts to verify Extended exchange streaming capabilities for account data, including balance updates.

## Problem Statement

The Extended connector currently uses HTTP streaming (Server-Sent Events) for account updates, but balance fetching is failing with 401 errors. These tests help verify:

1. **WebSocket streaming** - Testing if WebSocket provides better balance updates
2. **HTTP streaming** - Verifying current SSE implementation
3. **Authentication methods** - Query parameter vs header authentication

## Test Scripts

### 1. WebSocket Test (`test_extended_websocket.py`)

Tests WebSocket connection for real-time account updates.

**Features:**
- Tests multiple URL formats and authentication methods
- Captures and categorizes message types (BALANCE, ORDER, POSITION, FUNDING)
- Handles ping/pong for connection keep-alive
- Saves raw messages for analysis
- 60-second listening window

**URLs tested:**
- Primary: `wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account?X-API-KEY=...`
- Alternative: `wss://api.starknet.extended.exchange/stream.extended.exchange/v1/account` (with header auth)

**Run:**
```bash
python scripts/test_extended_websocket.py
```

**Expected Output:**
- Connection status
- Real-time message display
- Message categorization (balance, order, position updates)
- Summary statistics

### 2. HTTP Streaming Test (`test_extended_http_stream.py`)

Tests current HTTP Server-Sent Events implementation.

**Features:**
- Tests SSE streaming with X-Api-Key header
- Parses `data:` formatted messages
- Categorizes updates by type
- Saves messages for comparison with WebSocket

**URL:**
- `https://stream.extended.exchange/v1/account`

**Run:**
```bash
python scripts/test_extended_http_stream.py
```

## Prerequisites

### Install Dependencies

```bash
pip install websockets aiohttp python-dotenv
```

### Environment Setup

Ensure `.env` file contains:
```env
EXTENDED_API_KEY=your_api_key_here
```

## Test Methodology

### Step 1: Run Both Tests Simultaneously

Terminal 1 (WebSocket):
```bash
python scripts/test_extended_websocket.py
```

Terminal 2 (HTTP Streaming):
```bash
python scripts/test_extended_http_stream.py
```

### Step 2: Trigger Account Updates

While tests are running, perform actions on Extended exchange:

1. **Check balance** - Visit Extended dashboard
2. **Place an order** - Submit a small limit order
3. **Cancel an order** - Cancel the order you just placed
4. **Open/close position** - Execute a small trade

### Step 3: Compare Results

After 60 seconds, both tests will display summaries showing:
- Total messages received
- Balance update count
- Order update count
- Position update count

**Key Questions:**
1. ✅ Does WebSocket receive balance updates?
2. ✅ Does HTTP streaming receive balance updates?
3. ✅ Which method receives more updates?
4. ✅ What is the message format difference?

## Expected Message Formats

### Balance Update (Expected)

```json
{
  "type": "BALANCE",
  "balance": "1000.00",
  "equity": "1050.00",
  "availableForTrade": "950.00",
  "availableForWithdrawal": "900.00",
  "timestamp": 1234567890
}
```

### Order Update (Expected)

```json
{
  "type": "ORDER",
  "orderId": "123456",
  "market": "BTC-USD",
  "side": "BUY",
  "status": "FILLED",
  "size": "0.01",
  "price": "50000.00"
}
```

## Troubleshooting

### WebSocket Connection Fails (401/403)

**Issue:** Authentication error

**Solutions:**
1. Verify API key in `.env` is correct
2. Check if API key has WebSocket permissions
3. Try alternative URL format (header vs query param)

### No Messages Received

**Issue:** Connection successful but no data

**Possible Causes:**
1. **Idle connection** - Extended may only send updates when account state changes
2. **New account** - Zero balance accounts might not receive updates
3. **Subscription required** - May need to send subscription message

**Test by:**
- Placing a test order on Extended exchange
- Checking balance on web UI
- Making a small deposit/withdrawal

### HTTP Streaming Returns 404

**Issue:** Balance endpoint returns 404

**Explanation:** Extended returns 404 for zero-balance accounts. This is expected behavior.

**Solution:** Fund account with small amount to test

## Analysis Guide

### Comparing WebSocket vs HTTP Streaming

After running both tests, compare:

| Metric | WebSocket | HTTP Streaming |
|--------|-----------|----------------|
| Balance updates received | ? | ? |
| Connection stability | ? | ? |
| Authentication method | Query param / Header | Header only |
| Message format | JSON | SSE (data: JSON) |
| Latency | ? | ? |

### Next Steps Based on Results

**If WebSocket receives balance updates:**
✅ Migrate connector to use WebSocket instead of HTTP streaming

**If neither receives balance updates:**
⚠️ Check if balance endpoint requires REST API polling instead
⚠️ Contact Extended support for streaming capabilities

**If both receive updates:**
✅ Choose WebSocket for better performance and bidirectional communication

## Integration Plan

Once WebSocket is verified working:

1. **Update constants** (`extended_perpetual_constants.py`):
   - Add WebSocket URL constant
   - Update authentication approach

2. **Modify user stream** (`extended_perpetual_user_stream_data_source.py`):
   - Replace HTTP streaming with WebSocket
   - Implement proper authentication
   - Add message parsing for balance updates

3. **Update connector** (`extended_perpetual_derivative.py`):
   - Process balance update events
   - Remove HTTP streaming fallback

## References

- Extended API Docs: https://api.docs.extended.exchange/
- Extended Python SDK: https://github.com/x10xchange/python_sdk
- WebSocket RFC: https://tools.ietf.org/html/rfc6455
- Server-Sent Events: https://html.spec.whatwg.org/multipage/server-sent-events.html

## Debug Tips

### Enable Verbose Logging

Modify scripts to add debug output:

```python
# At top of script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Capture Network Traffic

Use Wireshark or browser DevTools to inspect WebSocket frames:

```bash
# Browser console for WebSocket testing
ws = new WebSocket('wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account?X-API-KEY=YOUR_KEY')
ws.onmessage = (e) => console.log('Message:', e.data)
ws.onerror = (e) => console.error('Error:', e)
```

### Test with Extended Web UI

1. Open Extended exchange in browser
2. Open DevTools → Network tab
3. Filter for WS (WebSocket)
4. Observe WebSocket connections and messages
5. Compare with your test script output

---

**Created:** 2025-01-22
**Purpose:** Verify Extended exchange streaming capabilities for balance updates
**Status:** Ready for testing

# Extended Exchange Streaming & Balance Tests

## Quick Start

### 1. Install Dependencies
```bash
pip install websockets aiohttp python-dotenv
```

### 2. Verify .env Configuration
Ensure `/Users/tdl321/hummingbot/.env` contains:
```env
EXTENDED_API_KEY=your_api_key_here
```

### 3. Run Tests

**Option A: All tests with interactive menu**
```bash
./scripts/run_extended_streaming_tests.sh
```

**Option B: Individual tests**
```bash
# Test REST API balance (recommended first)
python scripts/test_extended_rest_balance.py

# Test WebSocket streaming
python scripts/test_extended_websocket.py

# Test HTTP streaming (current implementation)
python scripts/test_extended_http_stream.py
```

## Test Scripts Overview

### 1. `test_extended_rest_balance.py` ⭐ START HERE
**Purpose:** Verify REST API balance endpoint works before testing streaming

**What it does:**
- Tests `/api/v1/user/balance` endpoint
- Tests `/api/v1/user/account/info` endpoint
- Checks for authentication issues
- Detects whitespace in API key (common 401 cause)

**Expected results:**
- ✅ 200 OK with balance data (funded account)
- ✅ 404 Not Found (zero balance - this is normal)
- ❌ 401 Unauthorized (API key issue)

**Run first** to ensure API key is valid before testing streaming.

---

### 2. `test_extended_websocket.py`
**Purpose:** Test WebSocket streaming for account updates

**What it does:**
- Connects to `wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account`
- Tests query parameter authentication: `?X-API-KEY=...`
- Tests header authentication: `X-Api-Key: ...`
- Listens for 60 seconds
- Categorizes messages: BALANCE, ORDER, POSITION, FUNDING
- Saves raw messages to JSON file

**Expected results:**
- ✅ Connection successful → WebSocket works
- ❌ 401/403 error → Authentication issue
- ⏳ No messages → Idle connection (trigger updates by trading)

---

### 3. `test_extended_http_stream.py`
**Purpose:** Test current HTTP streaming (SSE) implementation

**What it does:**
- Connects to `https://stream.extended.exchange/v1/account`
- Uses Server-Sent Events format
- Parses `data:` formatted messages
- Compares with WebSocket results

**Expected results:**
- Should mirror current connector behavior
- Helps identify if issue is with streaming in general or just WebSocket

---

### 4. `run_extended_streaming_tests.sh`
**Purpose:** Run multiple tests side-by-side or sequentially

**Features:**
- Interactive menu
- Side-by-side testing with tmux
- Sequential testing without tmux
- Single test execution

---

## Testing Workflow

### Step 1: Verify REST API Works
```bash
python scripts/test_extended_rest_balance.py
```

**If this fails with 401:**
- Check API key in .env
- Look for whitespace: `EXTENDED_API_KEY= abc` should be `EXTENDED_API_KEY=abc`
- Regenerate API key in Extended dashboard
- Verify key has read permissions

**If this succeeds:**
- Proceed to streaming tests

---

### Step 2: Test Streaming Methods
```bash
# Run both tests in separate terminals, or use:
./scripts/run_extended_streaming_tests.sh
```

While tests run (60 second window):
1. Open Extended exchange in browser
2. Place a small test order
3. Cancel the order
4. Check your balance
5. Open/close a small position

This triggers account updates that should appear in test output.

---

### Step 3: Compare Results

After tests complete, check:

| Method | Connected? | Balance Updates? | Order Updates? | Notes |
|--------|-----------|------------------|----------------|-------|
| REST API | ? | N/A (polling) | N/A | Baseline test |
| WebSocket | ? | ? | ? | New method |
| HTTP Stream | ? | ? | ? | Current method |

---

## Interpreting Results

### Scenario A: WebSocket receives balance updates ✅
**Action:** Migrate connector to WebSocket
- Better performance
- Bidirectional communication
- Standard protocol

### Scenario B: HTTP Stream receives balance updates ✅
**Action:** Debug existing connector
- Current implementation should work
- Check message parsing logic
- Verify stream connection stays alive

### Scenario C: Neither receives balance updates ❌
**Possible causes:**
1. **Idle connection** - Extended only sends updates on state changes
2. **Zero balance** - New accounts may not receive updates
3. **Endpoint limitation** - Balance may require REST polling

**Action:**
- Fund account with small amount
- Place test orders while streaming
- Contact Extended support for clarification

### Scenario D: 401 errors everywhere ❌
**Cause:** API key authentication issue

**Action:**
1. Check for whitespace: `cat .env | od -c | grep EXTENDED`
2. Regenerate API key
3. Verify key format (32 hex characters)
4. Check API key permissions in Extended dashboard

---

## Common Issues & Solutions

### Issue: "401 Unauthorized" on all endpoints

**Solution:**
```bash
# Check for whitespace in .env
cat .env | grep EXTENDED_API_KEY

# Should be: EXTENDED_API_KEY=abc123...
# NOT:       EXTENDED_API_KEY= abc123...
#                              ^^ extra space causes 401
```

Fix in `.env`:
```bash
# Remove any spaces around = sign
EXTENDED_API_KEY=f4aa1ba3e3038adf522981a90d2a1c57
```

### Issue: "Connection timeout" on WebSocket

**Possible causes:**
- Firewall blocking WebSocket
- VPN interfering
- Invalid URL

**Test in browser console:**
```javascript
ws = new WebSocket('wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account?X-API-KEY=YOUR_KEY')
ws.onopen = () => console.log('Connected!')
ws.onerror = (e) => console.error('Error:', e)
ws.onmessage = (e) => console.log('Message:', e.data)
```

### Issue: No messages received but connection successful

**This is normal** if account is idle. Trigger updates by:
1. Placing an order
2. Canceling an order
3. Making a trade
4. Depositing funds

---

## File Outputs

Tests can save messages to JSON files:

```
extended_ws_messages_20250122_143022.json
extended_http_messages_20250122_143125.json
```

These files contain:
- Timestamp of each message
- Raw message data
- Categorization flags

Use for:
- Debugging message formats
- Comparing WebSocket vs HTTP
- Analyzing update frequency

---

## Next Steps After Testing

### If WebSocket works:
1. Update `extended_perpetual_constants.py`:
   ```python
   STREAM_ACCOUNT_WEBSOCKET_URL = "wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account"
   ```

2. Modify `extended_perpetual_user_stream_data_source.py`:
   - Replace HTTP streaming with WebSocket
   - Add query parameter authentication
   - Parse WebSocket messages

3. Test with Hummingbot connector

### If only HTTP works:
1. Debug existing `_read_stream_messages()` method
2. Add more logging
3. Verify SSE parsing logic
4. Check connection keep-alive

### If neither works:
1. Contact Extended support
2. Ask about streaming endpoint capabilities
3. Consider REST polling as fallback
4. Check API documentation updates

---

## Support

- Extended API Docs: https://api.docs.extended.exchange/
- Extended Discord: (check website)
- GitHub Issues: File bug reports with test outputs

---

**Created:** 2025-01-22
**Author:** Hummingbot Development Team
**Purpose:** Diagnose Extended exchange balance update streaming issues

# Paradex Connector Test Suite

Comprehensive test scripts for validating the Paradex perpetual futures connector implementation.

## 📋 Test Overview

Based on lessons learned from Extended and Lighter connector implementations, these tests ensure:
- ✅ All API endpoints exist before implementation
- ✅ Critical methods are fully implemented (not placeholders)
- ✅ WebSocket connectivity verified
- ✅ REST polling fallback functional
- ✅ No hardcoded credentials or security issues

## 🎯 Tests Available

### ⭐ Can Run WITHOUT API Key

#### 1. `validate_paradex_implementation.py`
**Purpose**: Validate connector code against lessons learned checklist

**What it checks**:
- No empty placeholder implementations (`pass` statements)
- No hardcoded credentials
- UTF-8 file handling
- Error handling in critical methods
- SDK integration
- Documentation
- WebSocket fallback implementation

**Usage**:
```bash
python test/paradex_connector/validate_paradex_implementation.py
```

**When to run**: FIRST - before any other tests

---

#### 2. `test_paradex_api_endpoints.py`
**Purpose**: Verify all Paradex API endpoints exist and return expected data

**What it tests**:
- `/system/health` - Health check
- `/system/config` - System configuration
- `/markets` - Market list
- `/markets/{market}/summary` - Market summary
- `/markets/{market}/orderbook` - Order book
- `/markets/{market}/trades` - Recent trades
- `/markets/{market}/funding` - Funding rates

**Usage**:
```bash
python test/paradex_connector/test_paradex_api_endpoints.py
```

**Expected outcome**: All endpoints return 200 OK (not 404)

**Critical**: Extended connector failed because streaming API returned 404 - this test prevents that!

---

#### 3. `test_paradex_websocket.py`
**Purpose**: Test WebSocket connectivity and message reception

**What it tests**:
- WebSocket connection establishment
- Public channel subscriptions
- Message format verification
- Connection stability

**Usage**:
```bash
python test/paradex_connector/test_paradex_websocket.py
```

**Test duration**: 30 seconds (configurable in script)

**Expected outcome**:
- Connection successful
- Messages received from subscribed channels
- OR graceful failure with recommendation to use REST polling

**Critical**: Many exchanges document WebSocket but don't deploy it - this verifies it works!

---

#### 4. `test_paradex_polling.py`
**Purpose**: Test connector in read-only mode with public data only

**What it tests**:
- Connector initialization
- Trading rules fetching
- Order book snapshots
- Funding rate polling
- Market data quality

**Usage**:
```bash
python test/paradex_connector/test_paradex_polling.py
```

**Expected outcome**: Connector fetches market data successfully

**Critical**: Verifies `_update_balances()` and `_update_positions()` are not empty `pass` statements!

---

### 🔐 Requires API Key (Skippable for Now)

#### 5. `test_paradex_auth.py` (TODO)
**Purpose**: Test JWT authentication and subkey functionality

**What it tests**:
- JWT token generation
- Token refresh
- Header formatting
- Authenticated endpoint access
- Subkey authentication flow

**Usage**:
```bash
export PARADEX_API_SECRET="0x..."
export PARADEX_ACCOUNT_ADDRESS="0x..."
python test/paradex_connector/test_paradex_auth.py
```

**When to run**: After getting API credentials

---

#### 6. `test_paradex_integration.py` (TODO)
**Purpose**: Full connector lifecycle test with real trading (testnet only!)

**What it tests**:
- Balance fetching
- Position tracking
- Order placement
- Order cancellation
- WebSocket user stream
- Funding payment tracking

**Usage**:
```bash
# TESTNET ONLY!
export PARADEX_API_SECRET="0x..."
export PARADEX_ACCOUNT_ADDRESS="0x..."
python test/paradex_connector/test_paradex_integration.py
```

**When to run**: Final validation before production

---

## 🚀 Recommended Testing Sequence

### Phase 1: Pre-Deployment Validation (No API Key Needed)

```bash
# Step 1: Validate implementation
python test/paradex_connector/validate_paradex_implementation.py
# ✅ Must pass all critical checks

# Step 2: Verify API endpoints
python test/paradex_connector/test_paradex_api_endpoints.py
# ✅ All endpoints should return 200 (not 404)

# Step 3: Test WebSocket
python test/paradex_connector/test_paradex_websocket.py
# ✅ Should connect and receive messages
# ⚠️  If fails: Ensure REST polling fallback is enabled

# Step 4: Test polling mode
python test/paradex_connector/test_paradex_polling.py
# ✅ Should fetch market data successfully
```

### Phase 2: Authentication Testing (Requires API Key)

```bash
# Step 5: Test authentication (when you have API key)
python test/paradex_connector/test_paradex_auth.py

# Step 6: Integration test on TESTNET
python test/paradex_connector/test_paradex_integration.py
```

### Phase 3: Production Readiness

```bash
# Run all tests in sequence
./test/paradex_connector/run_all_tests.sh

# Monitor for 24 hours on testnet before mainnet
```

---

## ❌ Common Issues & Solutions

### Issue: API Endpoints Return 404
**Solution**:
1. Verify URLs from Paradex documentation
2. Check API version (currently using /v1)
3. Enable REST polling fallback in connector
4. Update `paradex_perpetual_constants.py` with correct URLs

### Issue: WebSocket Connection Fails
**Solution**:
1. Verify WebSocket URL from Paradex docs
2. Check if authentication is required for public channels
3. Ensure REST polling fallback is implemented (MANDATORY)
4. Update `paradex_perpetual_api_order_book_data_source.py`

### Issue: Balance Always Shows $0
**Solution**:
1. Check `_update_balances()` is not just `pass`
2. Verify field names match Paradex API response
3. Test with `test_paradex_auth.py` (requires API key)
4. Check API credentials are valid

### Issue: Validation Script Fails
**Solution**:
1. Read error messages carefully
2. Fix critical issues first (empty implementations)
3. Update code and re-run validation
4. All critical checks must pass before deployment

---

## 📚 Related Documentation

- **Implementation Plan**: `.claude/docs/PARADEX_CONNECTOR_INTEGRATION_PLAN.md`
- **Lessons Learned**: `.claude/docs/PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md`
- **Paradex API Docs**: https://docs.paradex.trade
- **paradex_py SDK**: https://tradeparadex.github.io/paradex-py/

---

## 🎓 Lessons Learned Applied

These tests specifically address mistakes from previous connectors:

1. **Extended Connector Mistakes**:
   - ❌ `_update_balances()` was just `pass` → ✅ validation script checks for this
   - ❌ WebSocket API documented but returned 404 → ✅ `test_paradex_websocket.py` verifies
   - ❌ No polling fallback → ✅ `test_paradex_polling.py` tests fallback

2. **Lighter Connector Mistakes**:
   - ❌ Wrong API parameter names (`address` vs `l1_address`) → ✅ `test_paradex_api_endpoints.py` shows actual fields
   - ❌ Invalid API keys in encrypted config → ✅ Tests encourage direct API key validation first

3. **General Mistakes**:
   - ❌ UTF-8 mode not enabled → ✅ validation script checks file operations
   - ❌ No integration testing before deployment → ✅ comprehensive test suite provided

---

## 🤝 Contributing

When adding new tests:
1. Follow existing test patterns
2. Make tests runnable without API keys when possible
3. Provide clear error messages and recommendations
4. Update this README with new test descriptions
5. Add to recommended testing sequence

---

## ⚡ Quick Start

**I don't have an API key yet, what can I test?**

```bash
# Run these 4 tests - they require NO API key:
python test/paradex_connector/validate_paradex_implementation.py
python test/paradex_connector/test_paradex_api_endpoints.py
python test/paradex_connector/test_paradex_websocket.py
python test/paradex_connector/test_paradex_polling.py
```

**All 4 tests passed - what's next?**

1. Get Paradex API credentials:
   - Create Paradex account
   - Generate subkey (recommended for bots)
   - Fund testnet account

2. Run auth tests:
   ```bash
   python test/paradex_connector/test_paradex_auth.py
   ```

3. Run integration tests on testnet:
   ```bash
   python test/paradex_connector/test_paradex_integration.py
   ```

4. Deploy and monitor for 24 hours before mainnet

---

**Questions?** Check the lessons learned document or implementation plan for detailed guidance.

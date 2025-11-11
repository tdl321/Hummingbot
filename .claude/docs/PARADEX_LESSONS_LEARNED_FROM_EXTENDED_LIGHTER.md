# Paradex Connector: Lessons Learned from Extended & Lighter Mistakes

**Date**: 2025-11-11
**Purpose**: Critical mistakes to AVOID when implementing Paradex connector
**Source**: Extended and Lighter connector post-mortem analysis

---

## 🚨 CRITICAL: Read This Before Implementing Paradex

This document catalogs **every mistake** made during Extended and Lighter connector implementations, organized by severity and category. Each item includes the **root cause**, **impact**, and **prevention strategy** for Paradex.

**Use this as a checklist** - verify each item is addressed before deployment.

---

## Table of Contents

1. [Critical Mistakes (Blocks Trading)](#1-critical-mistakes-blocks-trading)
2. [High-Impact Mistakes (Authentication/API)](#2-high-impact-mistakes-authenticationapi)
3. [Medium-Impact Mistakes (Infrastructure)](#3-medium-impact-mistakes-infrastructure)
4. [Configuration & Environment Issues](#4-configuration--environment-issues)
5. [Security & Best Practices](#5-security--best-practices)
6. [Pre-Deployment Checklist](#6-pre-deployment-checklist)

---

## 1. Critical Mistakes (Blocks Trading)

### ❌ MISTAKE 1.1: Empty Placeholder Implementations

**What Happened (Extended & Lighter)**:
```python
# hummingbot/connector/derivative/extended_perpetual/extended_perpetual_derivative.py:662
async def _update_balances(self):
    """Update account balances. Placeholder for future implementation."""
    pass  # ❌ NOT IMPLEMENTED!

# hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_derivative.py:669
async def _update_positions(self):
    """Update positions. Placeholder for future implementation."""
    pass  # ❌ NOT IMPLEMENTED!
```

**Impact**:
- ❌ `get_available_balance()` always returns $0
- ❌ Pre-trade balance validation fails
- ❌ Strategy cannot execute trades
- ❌ Position tracking completely broken
- ❌ PnL calculations wrong

**Root Cause**:
- Connectors deployed with incomplete implementations
- Assumed SDK would handle balance updates (it doesn't)
- No integration tests caught this

**Prevention for Paradex**:

#### ✅ Implementation Checklist:
- [ ] **BEFORE committing**: Implement `_update_balances()` fully
- [ ] **BEFORE committing**: Implement `_update_positions()` fully
- [ ] **Test with real API**: Verify balances fetch correctly
- [ ] **Integration test**: Confirm `get_available_balance('USD')` > 0
- [ ] **Never use `pass`**: If not implemented, raise NotImplementedError

#### ✅ Code Template for Paradex:
```python
async def _update_balances(self):
    """
    Update account balances from Paradex API.

    CRITICAL: This method MUST be implemented for trading to work.
    DO NOT deploy with just 'pass' - implement fully!
    """
    try:
        # Fetch balances from Paradex API
        response = await self._api_get(
            path_url=CONSTANTS.BALANCES_URL,  # /account/balances
            is_auth_required=True,
            limit_id=CONSTANTS.BALANCES_URL
        )

        # Parse and validate response
        if not isinstance(response, dict) or "balances" not in response:
            self.logger().error(f"Invalid balance response: {response}")
            raise ValueError("Invalid balance response format")

        # Update internal balance tracking
        for balance_entry in response["balances"]:
            asset = balance_entry["asset"]
            total = Decimal(str(balance_entry.get("total", "0")))
            available = Decimal(str(balance_entry.get("available", "0")))

            self._account_balances[asset] = total
            self._account_available_balances[asset] = available

            self.logger().debug(
                f"Updated {asset}: total={total}, available={available}"
            )

    except Exception as e:
        self.logger().error(f"Error updating balances: {e}", exc_info=True)
        # DO NOT suppress - let caller handle error
        raise

async def _update_positions(self):
    """
    Update positions from Paradex API.

    CRITICAL: This method MUST be implemented for position tracking.
    """
    try:
        response = await self._api_get(
            path_url=CONSTANTS.POSITIONS_URL,  # /positions
            is_auth_required=True,
            limit_id=CONSTANTS.POSITIONS_URL
        )

        # Parse positions...
        # (Full implementation required)

    except Exception as e:
        self.logger().error(f"Error updating positions: {e}", exc_info=True)
        raise
```

#### ✅ Testing Requirements:
```python
# Create test_paradex_balances.py
async def test_balance_update():
    connector = ParadexPerpetualDerivative(...)

    # Update balances
    await connector._update_balances()

    # Verify balances are set
    balance = connector.get_balance('USD')
    available = connector.get_available_balance('USD')

    assert balance > 0, "❌ CRITICAL: Balance not updated!"
    assert available >= 0, "❌ CRITICAL: Available balance invalid!"

    print(f"✅ Balance: {balance}, Available: {available}")
```

---

### ❌ MISTAKE 1.2: Incomplete Trading Methods

**What Happened**:
- `_all_trade_updates_for_order()` returned empty list
- `_request_order_status()` returned placeholder data
- Orders placed but status never updated

**Prevention for Paradex**:
- [ ] Implement ALL required methods from `PerpetualDerivativePyBase`
- [ ] Never return empty lists - implement full logic or raise NotImplementedError
- [ ] Test order lifecycle: place → fill → track → cancel

---

## 2. High-Impact Mistakes (Authentication/API)

### ❌ MISTAKE 2.1: Wrong API Parameter Names

**What Happened (Lighter)**:
```python
# ❌ WRONG - Caused 400 Bad Request
accounts_response = await account_api.account(by="address", value=wallet_address)

# Error from API:
# code=20001 message='invalid param: value "address" for field "by"
# is not defined in options "[index l1_address]"'
```

**Root Cause**:
- Assumed parameter name without checking API documentation
- Used generic name "address" instead of Lighter-specific "l1_address"
- No validation of API responses during development

**Impact**:
- ❌ All balance fetches failed with 400 error
- ❌ Connector unusable until fix deployed
- ❌ Required Docker rebuild and redeployment

**Prevention for Paradex**:

#### ✅ API Parameter Verification:
- [ ] **BEFORE coding**: Read Paradex API docs for EXACT parameter names
- [ ] **Document** all parameter requirements in constants file
- [ ] **Test** each endpoint with minimal example first
- [ ] **Verify** response format matches expectations

#### ✅ For Paradex Specifically:
```python
# BEFORE implementing any API call, document expected params:

# Example: Paradex account balances endpoint
# GET /account/balances
# Parameters:
#   - None (authenticated endpoint, uses JWT)
# Response format:
#   {
#     "balances": [
#       {
#         "asset": "USDC",
#         "total": "1000.50",
#         "available": "950.25",
#         "locked": "50.25"
#       }
#     ]
#   }

# Then implement with exact field names
async def _update_balances(self):
    response = await self._api_get(
        path_url="/account/balances",  # Exact path from docs
        is_auth_required=True
    )

    # Validate response structure
    if "balances" not in response:
        raise ValueError(f"Missing 'balances' field in response: {response}")
```

#### ✅ Testing Strategy:
```python
# Test each API endpoint BEFORE full integration
async def test_paradex_api_params():
    """Verify Paradex API parameter names are correct"""

    # Test 1: Balances endpoint
    response = await api_get("/account/balances")
    assert "balances" in response, "Wrong response format"

    # Test 2: Orders endpoint
    response = await api_get("/orders")
    assert "orders" in response, "Wrong response format"

    # Test 3: Positions endpoint
    response = await api_get("/positions")
    assert "positions" in response, "Wrong response format"

    print("✅ All API parameter names verified")
```

---

### ❌ MISTAKE 2.2: Invalid/Expired API Keys in Config

**What Happened (Extended)**:
```
Error: HTTP status is 401. Error executing request GET
https://api.starknet.extended.exchange/api/v1/user/balance
```

**Root Cause**:
- Encrypted config file contained old/expired API key
- Config was never updated after regenerating API key
- Testing used hardcoded valid key, production used encrypted invalid key

**Impact**:
- ❌ All authenticated endpoints failed
- ❌ Connector appeared broken when code was correct
- ❌ Wasted hours debugging correct code

**Prevention for Paradex**:

#### ✅ API Key Management:
- [ ] **Test encrypted config**: Run connector with actual encrypted credentials
- [ ] **Validate keys**: Test API key directly before encrypting
- [ ] **Update process**: Document how to rotate API keys
- [ ] **Error messages**: Log clear messages for 401 errors

#### ✅ Pre-Deployment Key Validation:
```python
# Create tools/test_paradex_api_key.py
import os
import aiohttp
from dotenv import load_dotenv

async def validate_paradex_api_key():
    """Test Paradex API key before encrypting in config"""
    load_dotenv()

    api_key = os.getenv("PARADEX_API_SECRET")  # Subkey private key
    account = os.getenv("PARADEX_ACCOUNT_ADDRESS")

    # Test 1: Generate JWT token
    from paradex import ParadexSubkey, Environment
    client = ParadexSubkey(
        env=Environment.PROD,
        l2_private_key=api_key,
        l2_account_address=account
    )

    jwt_token = await client.auth.get_jwt_token()
    print(f"✅ JWT token generated: {jwt_token[:20]}...")

    # Test 2: Fetch balances
    balances = await client.fetch_balances()
    print(f"✅ Balances fetched: {balances}")

    # Test 3: Fetch account
    account_info = await client.fetch_account_summary()
    print(f"✅ Account: {account_info['account']}")

    print("\n✅ API key is VALID and ready to use!")

# Run this BEFORE encrypting credentials in Hummingbot
```

#### ✅ Error Handling:
```python
async def _update_balances(self):
    try:
        response = await self._api_get(...)
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            self.logger().error(
                "❌ AUTHENTICATION FAILED: API key is invalid or expired.\n"
                "Action required:\n"
                "1. Verify API key is correct in Paradex UI\n"
                "2. Regenerate API key if needed\n"
                "3. Update Hummingbot config: connect paradex_perpetual\n"
                "4. Test key with: python tools/test_paradex_api_key.py"
            )
        raise
```

---

### ❌ MISTAKE 2.3: Authentication Header Format Errors

**What Happened (Extended)**:
- Initially used wrong header name
- Header added in wrong location (not in preprocessor)
- User-Agent header missing (required by Extended)

**Prevention for Paradex**:

#### ✅ Authentication Implementation:
```python
# In paradex_perpetual_auth.py
async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
    """
    Add authentication headers to REST requests.

    Paradex requires:
    - Authorization: Bearer {jwt_token}
    - PARADEX-STARKNET-ACCOUNT: {account_address} (for subkeys)
    """
    if request.headers is None:
        request.headers = {}

    # Get valid JWT token (auto-refresh if expired)
    jwt_token = await self.get_jwt_token()

    # Add authentication headers (EXACT format from Paradex docs)
    request.headers["Authorization"] = f"Bearer {jwt_token}"
    request.headers["PARADEX-STARKNET-ACCOUNT"] = self._account_address

    return request
```

#### ✅ Verification Test:
```python
async def test_paradex_headers():
    """Verify authentication headers are correct"""
    auth = ParadexPerpetualAuth(...)

    request = RESTRequest(
        method=RESTMethod.GET,
        url="/account/balances"
    )

    # Authenticate request
    authenticated_request = await auth.rest_authenticate(request)

    # Verify headers
    assert "Authorization" in authenticated_request.headers
    assert authenticated_request.headers["Authorization"].startswith("Bearer ")
    assert "PARADEX-STARKNET-ACCOUNT" in authenticated_request.headers

    print("✅ Headers:", authenticated_request.headers)
```

---

## 3. Medium-Impact Mistakes (Infrastructure)

### ❌ MISTAKE 3.1: Assuming Undocumented Endpoints Exist

**What Happened (Extended)**:
```python
# Streaming endpoints documented but NOT deployed
PERPETUAL_STREAM_URL = "https://stream.extended.exchange"

# All streaming requests returned 404:
GET /stream.extended.exchange/v1/orderbooks/KAITO-USD  → 404
GET /stream.extended.exchange/v1/account  → 404
```

**Root Cause**:
- Documentation showed streaming API
- Assumed docs reflected production (they didn't)
- No verification that endpoints existed
- Implemented full streaming support for non-existent API

**Impact**:
- ⚠️ Streaming code never worked
- ⚠️ Had to implement REST polling fallback
- ⚠️ Wasted time on SSE parsing that couldn't be tested

**Prevention for Paradex**:

#### ✅ Endpoint Verification BEFORE Implementation:
```bash
# Test EVERY endpoint before writing code

# 1. Public endpoints (no auth)
curl https://api.prod.paradex.trade/v1/markets
curl https://api.prod.paradex.trade/v1/system/config

# 2. Private endpoints (with JWT)
curl -H "Authorization: Bearer <token>" \
     https://api.prod.paradex.trade/v1/account/balances

# 3. WebSocket endpoints
wscat -c wss://ws.prod.paradex.trade/v1/ws

# Document results:
# ✅ Works: Markets endpoint returns 200
# ✅ Works: Balances endpoint returns 200 (with auth)
# ❌ DOES NOT WORK: WebSocket returns 404
#    → DO NOT implement WebSocket until verified!
```

#### ✅ Implementation Strategy:
```python
# In paradex_perpetual_api_order_book_data_source.py

async def listen_for_subscriptions(self):
    """
    Subscribe to order book updates.

    IMPORTANT: Verify WebSocket endpoint exists before implementing!
    Use REST polling fallback if WebSocket not deployed.
    """
    # Try WebSocket first (if verified to exist)
    try:
        if self._ws_endpoint_verified:  # Only if tested manually
            await self._listen_for_subscriptions_websocket()
        else:
            self.logger().warning(
                "WebSocket endpoint not verified, using REST polling"
            )
            await self._listen_for_subscriptions_polling()
    except Exception as e:
        self.logger().warning(f"WebSocket failed: {e}, falling back to REST")
        await self._listen_for_subscriptions_polling()
```

#### ✅ Checklist:
- [ ] Test each REST endpoint with curl/Postman BEFORE coding
- [ ] Test WebSocket connection with wscat BEFORE coding
- [ ] Document which endpoints work in production
- [ ] Implement REST polling fallback for critical features
- [ ] Add feature flags for experimental endpoints

---

### ❌ MISTAKE 3.2: No Polling Fallback for Streaming

**What Happened**: Extended streaming failed, no alternative path

**Prevention for Paradex**:
```python
# Always implement both streaming AND polling

async def _listen_for_subscriptions_websocket(self):
    """WebSocket streaming (preferred if available)"""
    pass

async def _listen_for_subscriptions_polling(self):
    """REST API polling (fallback, always works)"""
    polling_interval = 2.0  # 2 seconds
    while True:
        for trading_pair in self._trading_pairs:
            snapshot = await self._order_book_snapshot(trading_pair)
            self._message_queue[self._snapshot_messages_queue_key].put_nowait(snapshot)
        await asyncio.sleep(polling_interval)
```

---

## 4. Configuration & Environment Issues

### ❌ MISTAKE 4.1: UTF-8 Mode Not Enabled

**What Happened**:
- `PYTHONUTF8` environment variable not set
- Docker environment used locale encoding instead of UTF-8
- Potential for UnicodeDecodeError with non-ASCII data

**Prevention for Paradex**:

#### ✅ Dockerfile Configuration:
```dockerfile
# In Dockerfile (BOTH builder and release stages)
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1  # ✅ CRITICAL: Enable UTF-8 mode
```

#### ✅ Defensive File Operations:
```python
# Always specify encoding explicitly (defense in depth)
with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
    data = f.read()

# For API responses
response_text = response.text.encode('utf-8', errors='replace').decode('utf-8')
```

---

### ❌ MISTAKE 4.2: Insecure File Permissions

**What Happened**: `.env` file had 644 permissions (readable by all users)

**Prevention for Paradex**:
```bash
# Set secure permissions on credential files
chmod 600 .env
chmod 600 conf/connectors/paradex_perpetual.yml

# Verify in deployment script
if [ $(stat -f %A .env) != "600" ]; then
    echo "❌ ERROR: .env has insecure permissions"
    exit 1
fi
```

---

## 5. Security & Best Practices

### ❌ MISTAKE 5.1: No Pre-Deployment Security Audit

**What Happened**: Security audit only done AFTER deployment

**Prevention for Paradex**:

#### ✅ Security Checklist (BEFORE Deployment):
- [ ] No hardcoded credentials in code
- [ ] All private keys stored in .env (not code)
- [ ] .env protected by .gitignore
- [ ] .env has 600 permissions
- [ ] Exception messages don't leak secrets
- [ ] All file operations specify encoding
- [ ] Using official Paradex SDK (not custom crypto)
- [ ] Input validation on all user inputs
- [ ] Proper error handling (no bare except)

---

### ❌ MISTAKE 5.2: No Integration Testing Before Live Use

**What Happened**: Paper trading worked, live trading revealed missing implementations

**Prevention for Paradex**:

#### ✅ Integration Test Suite:
```python
# tests/integration/test_paradex_live.py

async def test_full_lifecycle():
    """Test complete trading lifecycle with real Paradex API"""

    # 1. Initialize connector
    connector = ParadexPerpetualDerivative(...)

    # 2. Test balance fetch
    await connector._update_balances()
    balance = connector.get_available_balance('USD')
    assert balance > 0, "❌ Balance not updated"

    # 3. Test trading rules
    await connector._update_trading_rules()
    assert len(connector._trading_rules) > 0, "❌ Trading rules not loaded"

    # 4. Test funding rates
    await connector._update_funding_rates()
    assert len(connector._funding_rates) > 0, "❌ Funding rates not updated"

    # 5. Test position fetch
    await connector._update_positions()
    # (Should not error even if no positions)

    # 6. Test order placement (small amount)
    order_id = await connector._place_order(
        order_id="test_order_1",
        trading_pair="BTC-USD-PERP",
        amount=Decimal("0.001"),  # $50 worth
        trade_type=TradeType.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("50000")
    )
    assert order_id, "❌ Order placement failed"

    # 7. Test order cancellation
    await connector._place_cancel(order_id, ...)

    print("✅ Full lifecycle test PASSED")
```

---

## 6. Pre-Deployment Checklist

### Phase 1: API Verification ✅

Before writing ANY code:

- [ ] **Test ALL REST endpoints** with curl/Postman
  - [ ] Public: `/markets`, `/system/config`
  - [ ] Private: `/account/balances`, `/positions`, `/orders`
- [ ] **Test WebSocket connection** (if documented)
  - [ ] Public channels (if any)
  - [ ] Private channels (if any)
- [ ] **Document actual API behavior**
  - [ ] Response formats (exact field names)
  - [ ] Required parameters
  - [ ] Authentication method
  - [ ] Rate limits
- [ ] **Test JWT authentication**
  - [ ] Generate token via SDK
  - [ ] Test token in API calls
  - [ ] Verify token expiry/refresh

### Phase 2: Core Implementation ✅

- [ ] **Implement `_update_balances()` FULLY**
  - [ ] Test returns real balance > 0
  - [ ] Handle zero balance case
  - [ ] Proper error handling
- [ ] **Implement `_update_positions()` FULLY**
  - [ ] Test with open positions
  - [ ] Test with no positions
  - [ ] Proper error handling
- [ ] **Implement `_update_trading_rules()` FULLY**
  - [ ] Parse all market data
  - [ ] Extract min/max order sizes
  - [ ] Handle delisted markets
- [ ] **Implement `_place_order()` via SDK**
  - [ ] Test LIMIT orders
  - [ ] Test MARKET orders
  - [ ] Verify order ID returned
- [ ] **Implement `_place_cancel()` via SDK**
  - [ ] Test cancel by order_id
  - [ ] Test cancel all
  - [ ] Handle already-filled orders

### Phase 3: Authentication & Security ✅

- [ ] **Verify auth header format**
  - [ ] Authorization: Bearer {jwt}
  - [ ] PARADEX-STARKNET-ACCOUNT header (if using subkeys)
- [ ] **Test JWT token generation**
  - [ ] Via SDK successfully
  - [ ] Auto-refresh before expiry
- [ ] **Test encrypted config**
  - [ ] Encrypt API key
  - [ ] Decrypt and verify
  - [ ] Test in Docker container
- [ ] **Security audit**
  - [ ] No hardcoded credentials
  - [ ] .env permissions 600
  - [ ] Exception messages safe
  - [ ] File operations specify encoding

### Phase 4: Integration Testing ✅

- [ ] **Unit tests**
  - [ ] Auth tests
  - [ ] Balance parsing tests
  - [ ] Order creation tests
- [ ] **Integration tests**
  - [ ] Full lifecycle test (see above)
  - [ ] Error handling tests
  - [ ] Reconnection tests
- [ ] **Manual testing**
  - [ ] Run connector in Hummingbot
  - [ ] Verify balances display
  - [ ] Place small test order
  - [ ] Cancel test order
  - [ ] Monitor for 1 hour

### Phase 5: Deployment ✅

- [ ] **Dockerfile verification**
  - [ ] PYTHONUTF8=1 set in BOTH stages
  - [ ] All dependencies installed
  - [ ] paradex_py SDK included
- [ ] **Build and test**
  - [ ] Docker build succeeds
  - [ ] Container starts without errors
  - [ ] Connector loads successfully
- [ ] **Production readiness**
  - [ ] Valid API key in config
  - [ ] Encrypted credentials tested
  - [ ] Logs show no errors
  - [ ] Balance fetching works
  - [ ] Position tracking works

---

## 7. Common Error Patterns & Solutions

### Pattern 1: "Balance Always Shows $0"
**Symptom**: `get_available_balance()` returns 0
**Cause**: `_update_balances()` not implemented or not called
**Fix**: Implement method fully, verify it's called by framework

### Pattern 2: "401 Unauthorized"
**Symptom**: All authenticated requests fail
**Cause**: Invalid API key in encrypted config
**Fix**: Test key directly, update config with valid key

### Pattern 3: "400 Bad Request: Invalid param"
**Symptom**: API returns parameter error
**Cause**: Wrong parameter name in API call
**Fix**: Read API docs for exact parameter names

### Pattern 4: "404 Not Found on Endpoint"
**Symptom**: Endpoint documented but returns 404
**Cause**: Endpoint not deployed to production
**Fix**: Test endpoint with curl first, implement REST fallback

### Pattern 5: "UnicodeDecodeError"
**Symptom**: Random encoding errors in Docker
**Cause**: UTF-8 mode not enabled
**Fix**: Add PYTHONUTF8=1 to Dockerfile

---

## 8. Reference: Working Code Examples

### ✅ Complete Balance Update (Based on Extended Fix)
```python
async def _update_balances(self):
    """
    Update account balances from Paradex API.

    Endpoint: GET /account/balances
    Response: {"balances": [{"asset": "USDC", "total": "1000", ...}]}
    """
    try:
        response = await self._api_get(
            path_url=CONSTANTS.BALANCES_URL,
            is_auth_required=True,
            limit_id=CONSTANTS.BALANCES_URL
        )

        if isinstance(response, dict) and "balances" in response:
            for balance_entry in response["balances"]:
                asset = balance_entry["asset"]
                total_balance = Decimal(str(balance_entry.get("total", "0")))
                available_balance = Decimal(str(balance_entry.get("available", "0")))

                # Update Hummingbot's internal balance tracking
                self._account_balances[asset] = total_balance
                self._account_available_balances[asset] = available_balance

                self.logger().debug(
                    f"Updated {asset} balance: total={total_balance}, "
                    f"available={available_balance}"
                )
        else:
            self.logger().warning(f"Unexpected balance response format: {response}")

    except Exception as e:
        self.logger().error(
            f"Error updating Paradex balances: {str(e)}",
            exc_info=True
        )
        # Re-raise to signal failure to framework
        raise
```

### ✅ Complete Position Update
```python
async def _update_positions(self):
    """
    Update positions from Paradex API.

    Endpoint: GET /positions
    Response: {"positions": [{"market": "BTC-USD-PERP", "size": "1.5", ...}]}
    """
    try:
        response = await self._api_get(
            path_url=CONSTANTS.POSITIONS_URL,
            is_auth_required=True,
            limit_id=CONSTANTS.POSITIONS_URL
        )

        if isinstance(response, dict) and "positions" in response:
            # Clear existing positions
            self._account_positions.clear()

            for position_data in response["positions"]:
                trading_pair = position_data["market"]
                position_side_str = position_data.get("side", "NONE")

                # Parse position
                position_side = (
                    PositionSide.LONG if position_side_str == "LONG"
                    else PositionSide.SHORT if position_side_str == "SHORT"
                    else None
                )

                if position_side:
                    amount = Decimal(str(position_data.get("size", "0")))
                    entry_price = Decimal(str(position_data.get("entry_price", "0")))

                    position = Position(
                        trading_pair=trading_pair,
                        position_side=position_side,
                        unrealized_pnl=Decimal(str(position_data.get("unrealized_pnl", "0"))),
                        entry_price=entry_price,
                        amount=amount,
                        leverage=Decimal(str(position_data.get("leverage", "1"))),
                    )

                    self._account_positions[trading_pair] = position

                    self.logger().debug(
                        f"Updated position for {trading_pair}: "
                        f"{position_side.name} {amount} @ {entry_price}"
                    )

    except Exception as e:
        self.logger().error(
            f"Error updating Paradex positions: {str(e)}",
            exc_info=True
        )
        raise
```

---

## 9. Final Checklist: Ready to Deploy?

Print this section and check off EVERY item before deploying:

### Code Completeness
- [ ] All methods from `PerpetualDerivativePyBase` implemented
- [ ] No `pass` placeholders in critical methods
- [ ] `_update_balances()` returns real data
- [ ] `_update_positions()` returns real data
- [ ] `_place_order()` works via SDK
- [ ] `_place_cancel()` works via SDK
- [ ] Error handling in all methods

### API Integration
- [ ] All endpoints tested with curl
- [ ] Parameter names verified from docs
- [ ] Response formats documented
- [ ] JWT authentication working
- [ ] Rate limits configured
- [ ] WebSocket verified (or polling fallback)

### Configuration
- [ ] Valid API key tested directly
- [ ] Encrypted config tested in Docker
- [ ] .env permissions set to 600
- [ ] .gitignore protects .env
- [ ] PYTHONUTF8=1 in Dockerfile

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Small order test successful
- [ ] Balance display correct
- [ ] Position display correct

### Security
- [ ] No hardcoded credentials
- [ ] Exception messages safe
- [ ] File operations specify encoding
- [ ] Using official SDK only
- [ ] Security audit passed

---

## 10. Emergency Rollback Plan

If Paradex connector fails in production:

1. **Immediate**: Comment out Paradex in connector list
2. **Revert**: To last known good Docker image
3. **Debug**: In isolated test environment
4. **Fix**: Address specific issue
5. **Test**: Full integration tests again
6. **Deploy**: With caution, monitor closely

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Next Review**: After Paradex connector implementation

**Use this document as your CHECKLIST. Do not deploy until every item is verified!**


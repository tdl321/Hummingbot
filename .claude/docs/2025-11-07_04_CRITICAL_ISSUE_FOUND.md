# 🚨 CRITICAL ISSUE FOUND: Balance Updates Not Implemented

**Date**: 2025-11-07
**Severity**: **HIGH** - Blocks live trading
**Status**: ⚠️ **MUST FIX BEFORE LIVE TRADING**

---

## Root Cause Identified

The balance checking features we implemented in the strategy **cannot work** because the underlying connectors have placeholder implementations:

### Extended Perpetual Connector
**File**: `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_derivative.py:662`

```python
async def _update_balances(self):
    """Update account balances. Placeholder for future implementation."""
    pass  # ❌ NOT IMPLEMENTED!
```

### Lighter Perpetual Connector
**File**: `hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_derivative.py:669`

```python
async def _update_balances(self):
    """Update account balances. Placeholder for future implementation."""
    pass  # ❌ NOT IMPLEMENTED!
```

---

## Impact

### What This Means:

1. **❌ `get_available_balance()` returns 0 or stale data**
   - Our balance checking code will always see $0 balance
   - Pre-trade validations will always fail
   - Strategy won't be able to trade

2. **❌ `get_balance()` returns 0 or stale data**
   - Status display shows incorrect balances
   - No way to know real account state

3. **❌ Position tracking doesn't work**
   - `_update_positions()` also just has `pass`
   - Can't track open positions
   - Can't calculate PnL correctly

4. **❌ The entire connector is incomplete**
   - These are newly added connectors (commit ca5db1c16)
   - They have basic order placement via SDK
   - But lack critical account state management

---

## Why Extended API Returned Error 1006

The API endpoint `/api/v1/user/balance` likely works fine, but:
1. We were testing it in isolation
2. The connector itself never calls it
3. The connector's `_update_balances()` method is empty
4. Hummingbot never updates the internal balance state

---

## Solution Options

### Option 1: ✅ **Implement Balance Updates** (Recommended)

Implement the missing methods in both connectors:

**For Extended**:
```python
async def _update_balances(self):
    """Update account balances from Extended API."""
    try:
        response = await self._api_get(
            path_url=CONSTANTS.ACCOUNT_INFO_URL,
            is_auth_required=True
        )

        if response.get('status') == 'OK':
            data = response['data']
            # Extract balance from account info
            # Extended returns balance in account info
            total_balance = Decimal(str(data.get('balance', '0')))
            available_balance = Decimal(str(data.get('availableBalance', '0')))

            quote = CONSTANTS.CURRENCY  # USD
            self._account_balances[quote] = total_balance
            self._account_available_balances[quote] = available_balance

    except Exception as e:
        self.logger().error(f"Error updating Extended balances: {e}", exc_info=True)
        raise
```

**For Lighter**:
```python
async def _update_balances(self):
    """Update account balances using Lighter SDK."""
    try:
        # Use the lighter SDK's SignerClient
        if self.authenticator and self.authenticator._signer_client:
            # Query blockchain state via SDK
            account_info = await self.authenticator._signer_client.get_account_info()

            total_balance = Decimal(str(account_info.get('balance', '0')))
            available = Decimal(str(account_info.get('available', '0')))

            quote = CONSTANTS.CURRENCY  # USD
            self._account_balances[quote] = total_balance
            self._account_available_balances[quote] = available

    except Exception as e:
        self.logger().error(f"Error updating Lighter balances: {e}", exc_info=True)
        raise
```

**Estimated Time**: 2-3 hours per connector
**Difficulty**: Medium (need to understand each exchange's API format)

### Option 2: ⚠️ **Use Paper Trading Mode Only**

Continue with paper trading simulation:
- No real funds at risk
- Can test strategy logic
- But won't work for live trading

**Time**: 0 hours
**Limitation**: Cannot go live

### Option 3: ⚠️ **Manual Balance Tracking**

Track balances outside Hummingbot:
- Monitor via exchange web interfaces
- Manually ensure sufficient funds
- Rely on exchange-side rejections if insufficient

**Risk**: HIGH - Could place orders without checking funds first

---

## Recommended Action Plan

### Immediate (Before Live Trading):

1. **✅ MUST Implement `_update_balances()` for both connectors**
   - Critical for any live trading
   - Required for balance checks to work
   - Needed for accurate accounting

2. **✅ MUST Implement `_update_positions()` for both connectors**
   - Critical for position tracking
   - Needed for PnL calculation
   - Required for exit condition checks

3. **✅ Test implementations thoroughly**
   - Verify balances update correctly
   - Test with real account data
   - Ensure no errors in polling loop

### Short Term (This Week):

4. **Implement other missing methods**:
   - `_all_trade_updates_for_order()` - Currently returns empty list
   - `_request_order_status()` - Returns placeholder data
   - Order book snapshot handling
   - Trade history fetching

5. **Add error handling**:
   - Retry logic for API failures
   - Graceful degradation
   - Clear error messages

### Long Term (Before Production):

6. **Complete connector testing**:
   - Test all order types
   - Test position management
   - Test funding payment tracking
   - Test websocket reconnection

7. **Documentation**:
   - Document API quirks
   - Add troubleshooting guide
   - Create testing checklist

---

## Why This Wasn't Caught Earlier

1. **Connectors are very new** (added Nov 2-7, 2025)
2. **Basic functionality works** (order placement via SDK)
3. **But account state management incomplete**
4. **No integration tests** for balance updates
5. **Paper trading might work** (uses simulated balances)

---

## Comparison with Working Connectors

### Hyperliquid (Working Example):

```python
async def _update_balances(self):
    account_info = await self._api_post(
        path_url=CONSTANTS.ACCOUNT_INFO_URL,
        data={"type": CONSTANTS.USER_STATE_TYPE,
              "user": self.hyperliquid_perpetual_api_key}
    )
    quote = CONSTANTS.CURRENCY
    self._account_balances[quote] = Decimal(account_info["crossMarginSummary"]["accountValue"])
    self._account_available_balances[quote] = Decimal(account_info["withdrawable"])
```

**This is what Extended and Lighter need!**

---

## Testing the Fix

Once implemented, test with this script:

```python
import asyncio
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative

async def test_balance():
    # Initialize connector
    connector = ExtendedPerpetualDerivative(...)

    # Update balances
    await connector._update_balances()

    # Check if balances are set
    print(f"Total: {connector.get_balance('USD')}")
    print(f"Available: {connector.get_available_balance('USD')}")

    assert connector.get_balance('USD') > 0, "Balance not updated!"
    print("✅ Balance update works!")

asyncio.run(test_balance())
```

---

## Current State Summary

| Component | Status | Impact |
|-----------|--------|--------|
| **Strategy balance checks** | ✅ Implemented | Ready to use |
| **Extended `_update_balances()`** | ❌ Not implemented | **Blocks live trading** |
| **Lighter `_update_balances()`** | ❌ Not implemented | **Blocks live trading** |
| **Extended `_update_positions()`** | ❌ Not implemented | **Blocks position tracking** |
| **Lighter `_update_positions()`** | ❌ Not implemented | **Blocks position tracking** |
| **Order placement** | ✅ Working | Can place orders |
| **Funding rate tracking** | ✅ Working | Can read funding rates |

---

## Workaround for Testing NOW

### Paper Trading Mode:

The paper trade connectors (`extended_perpetual_paper_trade`, `lighter_perpetual_paper_trade`) use **simulated balances**:

1. Edit your config:
```yaml
# Use paper trading connectors (KEEP these for now)
connectors:
  - extended_perpetual_paper_trade
  - lighter_perpetual_paper_trade
```

2. Configure paper trade balances in Hummingbot settings:
```
paper_trade_account_balance:
  USD: 10000
```

3. Test strategy logic with simulated balances
4. Strategy will work in paper mode
5. **Cannot go live until connectors are fixed**

---

## Next Steps

**I can help you**:

1. **✅ Implement `_update_balances()` for both connectors**
   - I'll write the code
   - Following Hyperliquid pattern
   - Using correct API endpoints
   - With proper error handling

2. **✅ Implement `_update_positions()` for both connectors**
   - Track open positions
   - Calculate PnL
   - Support strategy exit logic

3. **✅ Test implementations**
   - Create test script
   - Verify with your accounts
   - Ensure polling works

**Would you like me to implement these now?**

This is **required** before you can use live trading mode. The balance checking we added to the strategy is correct, but it depends on these connector methods working.

---

**Priority**: 🔴 **CRITICAL** - Must fix before live trading
**Estimated Effort**: 4-6 hours total
**Complexity**: Medium
**Risk if not fixed**: Cannot trade live, balances always show $0

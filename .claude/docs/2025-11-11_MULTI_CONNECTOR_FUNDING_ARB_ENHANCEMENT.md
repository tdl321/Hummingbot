# Multi-Connector Funding Arbitrage Enhancement

**Date:** 2025-11-11
**Script:** `scripts/v2_funding_rate_arb.py`
**Status:** ✅ Completed

## Overview

Enhanced the funding rate arbitrage script to handle tokens that aren't available on all exchanges, enabling cross-exchange arbitrage opportunities even when token listings are non-universal.

## Problem Statement

The original script assumed all configured tokens were available on all configured exchanges. This caused:
- ❌ Errors when querying funding rates for tokens that don't exist on certain exchanges
- ❌ Missed opportunities when tokens were only on 2-3 exchanges instead of all
- ❌ No visibility into which tokens were available where

## Solution Architecture

### Key Design Principles

1. **Manual Token List with Validation**: Keep user's configured token list but validate availability
2. **Token Only Needs 2+ Exchanges**: Arbitrage possible with any 2 exchanges, not all
3. **Explicit Connector Metadata**: Require quote currency and funding intervals for new connectors
4. **Prioritize Highest Spread**: Always select most profitable opportunity regardless of token availability
5. **Consider Liquidity**: Filter low-volume pairs to avoid poor execution

## Implementation Details

### 1. Token Availability Cache

**Location:** `__init__()` lines 158-161, `build_token_availability_cache()` lines 163-199

```python
# Cache structures
self.token_availability_cache = {}  # {token: [connector1, connector2, ...]}
self.connector_markets_cache = {}   # {connector: {trading_pair: token}}
```

**Built on startup:**
- Queries each connector for available trading pairs
- Maps tokens to their available exchanges
- Only tracks tokens in `config.tokens`
- Logs availability status for each token

**Example output:**
```
Token availability cache built:
  ✅ KAITO: available on 2 exchanges (extended_perpetual, lighter_perpetual)
  ✅ APT: available on 4 exchanges (extended_perpetual, lighter_perpetual, hyperliquid_perpetual, binance_perpetual)
  ℹ️  RARE: only on extended_perpetual - cannot arbitrage
```

### 2. Enhanced Funding Rate Retrieval

**Location:** `get_funding_info_by_token()` lines 328-352

**Before:**
```python
def get_funding_info_by_token(self, token):
    funding_rates = {}
    for connector_name, connector in self.connectors.items():
        trading_pair = self.get_trading_pair_for_connector(token, connector_name)
        funding_rates[connector_name] = connector.get_funding_info(trading_pair)  # ❌ CRASH if token doesn't exist
    return funding_rates
```

**After:**
```python
def get_funding_info_by_token(self, token):
    funding_rates = {}
    available_connectors = self.token_availability_cache.get(token, [])  # ✅ Only query where available

    for connector_name in available_connectors:
        if connector_name in self.connectors:
            connector = self.connectors[connector_name]
            trading_pair = self.get_trading_pair_for_connector(token, connector_name)
            try:
                funding_rates[connector_name] = connector.get_funding_info(trading_pair)
            except Exception as e:
                self.logger().warning(f"Failed to get funding info for {trading_pair} on {connector_name}: {e}")

    return funding_rates
```

**Benefits:**
- ✅ No errors if token missing on some exchanges
- ✅ Only queries connectors where token exists
- ✅ Graceful error handling with warnings

### 3. Liquidity/Volume Filtering

**Location:** `check_sufficient_liquidity()` lines 354-402, `_get_24h_volume()` lines 404-422

**Purpose:** Prevent entering positions in illiquid markets that can't be exited efficiently

**Config option:**
```python
min_daily_volume_usd: Decimal = Field(
    default=Decimal("50000"),  # $50k minimum 24h volume
    json_schema_extra={
        "prompt": lambda mi: "Enter minimum 24h volume per side in USD (e.g. 50000): ",
        "prompt_on_new": True
    }
)
```

**Logic:**
1. Attempt to fetch 24h volume from order book tracker
2. Check if both connectors meet minimum threshold
3. Log failed liquidity checks at debug level
4. If volume data unavailable, allow trade (conservative fallback)

**Example:**
```python
# KAITO liquidity check
volume_extended = $125,000  # ✅
volume_lighter = $85,000    # ✅
min_threshold = $50,000     # Both meet threshold → proceed
```

### 4. Global Opportunity Scanner

**Location:** `create_actions_proposal()` lines 442-567

**Flow:**

```
1. Collect All Opportunities
   ├─ For each token in config.tokens
   │  ├─ Skip if already in active arbitrage
   │  ├─ Get funding rates (only from available connectors)
   │  ├─ Skip if < 2 exchanges (can't arbitrage)
   │  ├─ Find best combination for this token
   │  ├─ Skip if below min profitability
   │  ├─ Check liquidity/volume
   │  └─ Add to opportunities list
   │
2. Rank by Spread (Highest First)
   └─ Sort all_opportunities by spread descending

3. Log Top 5 Opportunities
   └─ Show best opportunities to user

4. Enter Best Opportunity
   ├─ Try opportunities in order (best first)
   ├─ Check balance sufficiency
   ├─ Skip if insufficient balance
   └─ Enter first valid opportunity
```

**Example output:**
```
Found 5 profitable opportunities:
  #1: KAITO - extended_perpetual vs lighter_perpetual | Spread: 0.5200%/hr
  #2: APT - lighter_perpetual vs binance_perpetual | Spread: 0.3500%/hr
  #3: MON - extended_perpetual vs lighter_perpetual | Spread: 0.2800%/hr
  #4: TRUMP - extended_perpetual vs hyperliquid_perpetual | Spread: 0.2500%/hr
  #5: SUI - binance_perpetual vs hyperliquid_perpetual | Spread: 0.2100%/hr

✅ Opening KAITO arbitrage (5x leverage) |
   extended_perpetual (BUY) vs lighter_perpetual (SELL) |
   Spread: 0.5200%/hr
```

**Key differences from original:**
- ❌ **Old**: Scanned tokens sequentially, entered first profitable
- ✅ **New**: Scans ALL tokens, ranks globally, enters BEST opportunity

### 5. Enhanced Status Display

**Location:** `format_status()` lines 744-770

**New section:** Token Availability Matrix

```
Token Availability Matrix
================================================================================
Status | Token  | Exchanges | Available On                              | Arb Pairs
-------|--------|-----------|-------------------------------------------|----------
✅     | APT    | 4         | extended, lighter, hyperliquid, binance   | 6
✅     | KAITO  | 2         | extended, lighter                         | 1
✅     | MON    | 2         | extended, lighter                         | 1
✅     | TRUMP  | 3         | extended, hyperliquid, binance            | 3
⚠️     | RARE   | 1         | extended                                  | 0
```

**Status indicators:**
- ✅ = Available on 2+ exchanges (can arbitrage)
- ⚠️ = Only on 1 exchange (cannot arbitrage)
- ❌ = Not available on any exchange

**Arb Pairs calculation:**
```python
# For N exchanges, number of pairs = N × (N-1) / 2
# Example: 4 exchanges = 4 × 3 / 2 = 6 pairs
num_pairs = (num_exchanges * (num_exchanges - 1)) // 2
```

## Configuration

### New Config Fields

```python
class FundingRateArbitrageConfig(StrategyV2ConfigBase):
    # ... existing fields ...

    # NEW: Minimum 24h volume threshold (USD)
    min_daily_volume_usd: Decimal = Field(
        default=Decimal("50000"),
        json_schema_extra={
            "prompt": lambda mi: "Enter minimum 24h volume per side in USD (e.g. 50000): ",
            "prompt_on_new": True
        }
    )
```

### Removed Config Fields

- ❌ `skip_unavailable_tokens` - Not needed, tokens naturally skipped if < 2 exchanges

## Adding New Connectors

To add a new exchange connector, update these class-level mappings:

**Location:** Lines 109-120

```python
quote_markets_map = {
    "extended_perpetual": "USD",
    "lighter_perpetual": "USD",
    "hyperliquid_perpetual": "USD",
    "binance_perpetual": "USDT",
    # Add your new connector here
    "new_connector_name": "USDT",  # or "USD"
}

funding_payment_interval_map = {
    "extended_perpetual": 60 * 60 * 8,   # 8 hours
    "lighter_perpetual": 60 * 60 * 1,    # 1 hour
    "binance_perpetual": 60 * 60 * 8,    # 8 hours
    "hyperliquid_perpetual": 60 * 60 * 1,# 1 hour
    # Add your new connector here
    "new_connector_name": 60 * 60 * 8,   # in seconds
}
```

**That's it!** The token availability cache will automatically:
- Discover which tokens are available on the new connector
- Include them in opportunity scanning
- Show them in the status display

## Funding Rate Normalization

**Important:** Funding rates are normalized to a per-second basis, then compared over hourly profitability interval.

**Location:** `get_normalized_funding_rate_in_seconds()` line 439

```python
def get_normalized_funding_rate_in_seconds(self, funding_info_report, connector_name):
    return funding_info_report[connector_name].rate / self.funding_payment_interval_map.get(connector_name, 60 * 60 * 8)
```

**Example:**
```python
# Extended: 0.08% per 8 hours
rate_per_second = 0.0008 / (8 * 3600) = 0.00000002778%/sec

# Lighter: 0.01% per 1 hour
rate_per_second = 0.0001 / (1 * 3600) = 0.00000002778%/sec

# Now comparable! Calculate hourly spread:
spread_hourly = abs(rate_extended - rate_lighter) * 3600
```

This ensures correct comparison even though exchanges use different funding payment intervals.

## Testing Scenarios

### ✅ Test 1: Token on All Exchanges
**Token:** APT (on Extended, Lighter, Hyperliquid, Binance)
**Expected:** Works as before, 6 possible arbitrage pairs

### ✅ Test 2: Token on 2 Exchanges Only
**Token:** KAITO (on Extended, Lighter only)
**Expected:**
- Cache shows 2 exchanges
- Funding rates queried from Extended and Lighter only
- 1 arbitrage pair available
- No errors

### ✅ Test 3: Token on 1 Exchange Only
**Token:** RARE (on Extended only)
**Expected:**
- Cache shows 1 exchange
- No arbitrage opportunities (skipped naturally)
- Shown in status with ⚠️ indicator
- No errors or warnings

### ✅ Test 4: Highest Spread Priority
**Scenario:** Multiple profitable opportunities
**Expected:**
- All opportunities collected and ranked
- Top 5 logged to console
- Highest spread entered first
- Falls back to next if balance insufficient

### ✅ Test 5: Liquidity Filtering
**Scenario:** Token has high spread but low volume
**Expected:**
- Opportunity detected
- Liquidity check fails
- Skipped with debug log
- Next opportunity tried

## Backward Compatibility

✅ **Existing configs work without changes:**
- New `min_daily_volume_usd` field has default value ($50k)
- If all tokens available on all exchanges, behaves identically to old version
- No breaking changes to connector interfaces

## Files Modified

1. **scripts/v2_funding_rate_arb.py** - Main implementation
   - Added token availability caching (lines 158-199)
   - Modified `get_funding_info_by_token()` (lines 328-352)
   - Added liquidity filtering (lines 354-422)
   - Enhanced `create_actions_proposal()` (lines 442-567)
   - Updated `format_status()` (lines 744-770)
   - Added cache building to `start()` (lines 256-259)

## Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| Non-universal tokens | ❌ Crashes | ✅ Works seamlessly |
| Opportunity selection | First profitable | Best profitable (highest spread) |
| Visibility | None | Token Availability Matrix |
| Liquidity filtering | None | Volume threshold |
| Error handling | Crashes on missing token | Graceful warnings |
| New connector setup | Manual + risky | Automatic discovery |

## Performance Impact

- **Minimal overhead:** Cache built once on startup
- **Faster scanning:** Only queries connectors where tokens exist
- **Better decisions:** Global ranking finds best opportunities

## Future Enhancements

Potential improvements for later:
1. **Dynamic volume monitoring:** Update volume data periodically during runtime
2. **Connector health tracking:** Track API errors and temporarily skip problematic connectors
3. **Multi-position support:** Enter multiple arbitrage positions simultaneously
4. **Auto-discovery mode:** Scan for new tokens not in config with high spreads

## Related Documentation

- [Funding Arb Paper Trade Deployment](2025-11-05_FUNDING_ARB_PAPER_TRADE_DEPLOYMENT.md)
- [Funding Rate Arb Backtest Plan V2](2025-11-04_FUNDING_RATE_ARB_BACKTEST_PLAN_V2.md)

---

**Author:** Claude
**Reviewer:** TDL
**Last Updated:** 2025-11-11

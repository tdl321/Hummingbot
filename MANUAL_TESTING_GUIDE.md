# Manual Testing Guide: Balance & Position Updates

**Date**: 2025-11-07
**Purpose**: Verify the newly implemented balance and position update methods work correctly
**Implementation**: Extended and Lighter connector `_update_balances()` and `_update_positions()` methods

---

## Prerequisites

✅ Extended and Lighter connectors have been updated with balance/position tracking
✅ Strategy has been updated with balance checking features
✅ You have API credentials ready for both exchanges

---

## Test Plan

### Phase 1: Connector Configuration & Balance Verification
### Phase 2: Strategy Balance Checking
### Phase 3: Live Trading Validation

---

## Phase 1: Connector Configuration & Balance Verification

### Step 1: Start Hummingbot

```bash
cd /Users/tdl321/hummingbot
./bin/hummingbot
```

**Expected**: Hummingbot CLI starts successfully

---

### Step 2: Connect to Extended Perpetual

```
connect extended_perpetual
```

**What happens**: Hummingbot will prompt you for:
1. API Key (from Extended DEX account settings)
2. API Secret

**Enter your credentials** when prompted.

**Expected Result**:
```
✅ Successfully connected to extended_perpetual
```

**Test the connection**:
```
balance
```

**What to look for**:

✅ **SUCCESS - If you see real balance**:
```
Exchange    Asset    Total Balance    Available Balance
extended_perpetual    USD    2500.00    2400.00
```
This means `_update_balances()` is working! 🎉

⚠️ **NORMAL - If you see $0 but no errors**:
```
Exchange    Asset    Total Balance    Available Balance
extended_perpetual    USD    0.00    0.00
```
This means:
- Your Extended account has zero balance (404 response handled correctly)
- OR balance update hasn't run yet (wait 5-10 seconds and try `balance` again)

❌ **FAILURE - If you see errors**:
```
Error updating balances...
```
Check logs: `tail -f logs/logs_hummingbot.log | grep -i extended`

---

### Step 3: Connect to Lighter Perpetual

```
connect lighter_perpetual
```

**What happens**: Hummingbot will prompt you for:
1. Wallet Address (your zkSync wallet address)
2. API Secret (leave blank or press Enter - not used for Lighter)

**Expected Result**:
```
✅ Successfully connected to lighter_perpetual
```

**Test the connection**:
```
balance
```

**What to look for**:

✅ **SUCCESS - If you see real balance**:
```
Exchange    Asset    Total Balance    Available Balance
lighter_perpetual    USD    2600.00    2500.00
```
This means Lighter SDK integration is working! 🎉

⚠️ **NORMAL - If you see $0**:
- Account may not exist on Lighter yet
- Account may have zero balance
- Wait 5-10 seconds for first update cycle

❌ **FAILURE - If you see errors**:
```
Error: lighter-sdk not found
```
Fix: Install SDK with `pip install lighter-sdk`

---

### Step 4: Check Status

```
status
```

**What to look for**:

Should show both connectors as connected:
```
Connectors:
  ✅ extended_perpetual: CONNECTED
  ✅ lighter_perpetual: CONNECTED
```

---

### Step 5: Verify Position Tracking (If you have open positions)

```
positions
```

**Expected for accounts with open positions**:
```
Trading Pair    Position    Entry Price    Unrealized PnL    Leverage
BTC-USD    LONG 0.5    45000.00    120.50    5x
```

**Expected for accounts with no positions**:
```
No open positions
```

Both are valid - this confirms position tracking works.

---

## Phase 2: Strategy Balance Checking

### Step 6: Start the Strategy (Paper Trading First)

**IMPORTANT**: Test with paper trading first!

**Check current config**:
```bash
# Outside Hummingbot
cat conf/scripts/v2_funding_rate_arb.yml | grep connectors
```

Should show:
```yaml
connectors:
  - extended_perpetual_paper_trade
  - lighter_perpetual_paper_trade
```

**Start strategy**:
```
start --script v2_funding_rate_arb.py
```

---

### Step 7: Observe Startup Balance Check

**What to look for in logs**:

✅ **SUCCESS**:
```
[INFO] Checking initial balances...
[INFO] ✅ extended_perpetual_paper_trade: $10000.00 available (can open up to 90 positions)
[INFO] ✅ lighter_perpetual_paper_trade: $10000.00 available (can open up to 90 positions)
```

This confirms:
- ✅ `check_sufficient_balance()` method works
- ✅ `get_required_margin()` calculation works
- ✅ Startup balance validation works

⚠️ **WARNING (if real connector has low balance)**:
```
[WARNING] ⚠️ extended_perpetual has insufficient balance!
Available: $50.00, Required: $110.00
```

This is GOOD - it means the safety checks are working!

---

### Step 8: Monitor Status Display

While strategy is running:
```
status
```

**Look for the new "Balance Status for Arbitrage" section**:

```
================================================================================
Balance Status for Arbitrage
================================================================================
✅ extended_perpetual_paper_trade:
   Total: $10000.00 | Available: $10000.00
   Required per position: $110.00
   Max positions: 90

✅ lighter_perpetual_paper_trade:
   Total: $10000.00 | Available: $10000.00
   Required per position: $110.00
   Max positions: 90
```

✅ This confirms `format_status()` balance display works!

---

### Step 9: Watch for Pre-Trade Balance Validation

**In the logs, when strategy finds an arbitrage opportunity**:

✅ **SUCCESS - Sufficient balance**:
```
[INFO] extended_perpetual_paper_trade - Required: $110.00, Available: $10000.00
[INFO] lighter_perpetual_paper_trade - Required: $110.00, Available: $10000.00
[INFO] Best Combination: extended_perpetual_paper_trade | lighter_perpetual_paper_trade | BUY KAITO | SELL KAITO
[INFO] Starting executors...
```

✅ **SUCCESS - Insufficient balance (trade blocked)**:
```
[INFO] extended_perpetual - Required: $110.00, Available: $50.00
[WARNING] Insufficient balance for KAITO arbitrage.
extended_perpetual shortfall: $60.00, lighter_perpetual shortfall: $0.00. Skipping...
```

Both outcomes are good - they confirm the pre-trade validation works!

---

### Step 10: Stop Strategy

```
stop
```

---

## Phase 3: Live Trading Validation (CRITICAL SAFETY STEPS)

⚠️ **DO NOT SKIP THESE STEPS**

### Step 11: Verify Account Balances

Before switching to live trading, **manually verify** your real balances:

**Extended DEX**:
1. Go to https://app.extended.exchange/
2. Log in with your account
3. Check "Wallet" or "Portfolio" section
4. Note your **Available Balance**

**Lighter DEX**:
1. Go to https://lighter.xyz/
2. Connect your zkSync wallet
3. Check your collateral balance
4. Note your **Available Balance**

**Recommendation**:
- Start with small balances ($100-200 per exchange)
- Each trade will use ~$110 (for $500 position at 5x leverage)
- Ensure you have at least 2-3x the required margin

---

### Step 12: Fund Accounts (If Needed)

If balances are zero or insufficient:

**Extended DEX**:
1. Deposit USDC to Starknet
2. Bridge to Extended DEX
3. Wait for confirmation

**Lighter DEX**:
1. Deposit to zkSync Era
2. Send to Lighter contract
3. Wait for confirmation

---

### Step 13: Update Strategy Config for Live Trading

**CRITICAL**: This switches from paper trading to LIVE TRADING with REAL MONEY

```bash
# Outside Hummingbot - edit config file
nano conf/scripts/v2_funding_rate_arb.yml
```

Change:
```yaml
connectors:
  - extended_perpetual_paper_trade   # ❌ Remove _paper_trade
  - lighter_perpetual_paper_trade    # ❌ Remove _paper_trade
```

To:
```yaml
connectors:
  - extended_perpetual   # ✅ Live trading
  - lighter_perpetual    # ✅ Live trading
```

**Also reduce position size for initial testing**:
```yaml
position_size_quote: 100  # Changed from 500 to 100 for safety
```

Save and exit (Ctrl+X, Y, Enter)

---

### Step 14: Restart Hummingbot & Connect Live

```bash
./bin/hummingbot
```

**Connect to LIVE exchanges**:
```
connect extended_perpetual
connect lighter_perpetual
```

**Verify real balances**:
```
balance
```

**Should now show your REAL balances**:
```
Exchange              Asset    Total Balance    Available Balance
extended_perpetual    USD      200.00          180.00
lighter_perpetual     USD      200.00          190.00
```

✅ If balances match what you see on the exchange websites, `_update_balances()` is working correctly!

---

### Step 15: Start Live Strategy (With Caution)

```
start --script v2_funding_rate_arb.py
```

**Watch startup balance check**:
```
[INFO] Checking initial balances...
[INFO] ✅ extended_perpetual: $180.00 available (can open up to 1 positions)
[INFO] ✅ lighter_perpetual: $190.00 available (can open up to 1 positions)
```

---

### Step 16: Monitor First Trade Attempt

**Watch the logs carefully for**:

1. **Balance validation**:
```
[INFO] extended_perpetual - Required: $22.00, Available: $180.00
[INFO] lighter_perpetual - Required: $22.00, Available: $190.00
```

2. **Trade execution** (if opportunity found):
```
[INFO] Best Combination: extended_perpetual | lighter_perpetual | BUY KAITO | SELL KAITO
[INFO] Starting executors...
```

3. **Order submission**:
```
[INFO] Created BUY order for KAITO on extended_perpetual
[INFO] Created SELL order for KAITO on lighter_perpetual
```

4. **Balance update after trade**:
After 5-10 seconds, check:
```
balance
```

Available balance should decrease by ~$22 (margin locked in position).

---

### Step 17: Verify Position Tracking

After first position opens:
```
positions
```

**Expected**:
```
Trading Pair    Exchange           Position    Entry Price    Unrealized PnL    Leverage
KAITO-USD       extended_perpetual LONG 200    0.0050         0.00              5x
KAITO-USD       lighter_perpetual  SHORT 200   0.0052         0.00              5x
```

✅ This confirms `_update_positions()` works!

---

### Step 18: Monitor Balance Updates

As positions change and funding payments occur:

**Check balance periodically**:
```
balance
```

**Total balance should change** based on:
- Unrealized PnL from positions
- Funding rate payments
- Trading fees

**Available balance should change** based on:
- Margin locked in positions
- Margin released when positions close

---

## Success Criteria

### ✅ Phase 1 Complete
- [x] Both connectors connect successfully
- [x] `balance` command shows real balances (not $0)
- [x] Balances update every 5-10 seconds
- [x] `positions` command shows open positions (if any exist)
- [x] No errors in logs related to balance updates

### ✅ Phase 2 Complete
- [x] Strategy starts successfully
- [x] Startup balance check displays correct amounts
- [x] Status display shows balance section
- [x] Pre-trade validation logs balance checks
- [x] Trades are blocked when balance insufficient

### ✅ Phase 3 Complete
- [x] Live connectors show real exchange balances
- [x] Balance matches exchange website/app
- [x] Positions appear after trades execute
- [x] Balance updates after trades (margin locked)
- [x] Unrealized PnL reflected in total balance

---

## Troubleshooting

### Issue: Balance shows $0.00 even after waiting

**Check**:
1. Are you connected? `status` should show CONNECTED
2. Check logs: `tail -f logs/logs_hummingbot.log | grep balance`
3. Does account actually have funds? Check exchange website
4. Try disconnecting and reconnecting

**In Hummingbot**:
```
disconnect extended_perpetual
connect extended_perpetual
balance
```

---

### Issue: Extended returns error 1006

**Possible causes**:
- API key incorrect or expired
- Account not activated
- Network issues
- Extended API temporary issue

**Check**:
1. Verify API key in Extended DEX settings
2. Check you can log into https://app.extended.exchange/
3. Try again in a few minutes
4. Check Extended Discord for API status

---

### Issue: Lighter SDK error

**Error**: `ModuleNotFoundError: No module named 'lighter'`

**Fix**:
```bash
pip install lighter-sdk
```

**Error**: `No accounts found for address`

**Causes**:
- Wallet address incorrect in config
- Account not created on Lighter yet
- No deposits made to Lighter

**Fix**:
1. Verify wallet address is correct
2. Visit https://lighter.xyz/ and connect wallet
3. Make a test deposit

---

### Issue: Strategy not checking balances

**Symptoms**: No "Checking initial balances..." message

**Possible causes**:
- Using old version of strategy file
- Strategy config issue

**Fix**:
1. Verify you're using the updated strategy:
```bash
grep "check_sufficient_balance" scripts/v2_funding_rate_arb.py
```
Should return matches.

2. Restart Hummingbot and strategy

---

### Issue: Positions not showing

**Check**:
1. Do you actually have open positions? Check exchange website
2. Wait 5-10 seconds for update cycle
3. Check logs: `tail -f logs/logs_hummingbot.log | grep position`

---

## Expected Test Results

### With Zero Balance Accounts

Extended:
```
[INFO] Extended account has zero balance (404 response)
```

Lighter:
```
No accounts found for this address
```

Both are **normal and correct** - the error handling works!

---

### With Funded Accounts ($200 each)

Startup:
```
[INFO] ✅ extended_perpetual: $200.00 available (can open up to 1 positions)
[INFO] ✅ lighter_perpetual: $200.00 available (can open up to 1 positions)
```

Balance command:
```
Exchange              Asset    Total    Available
extended_perpetual    USD      200.00   200.00
lighter_perpetual     USD      200.00   200.00
```

Status display:
```
✅ extended_perpetual:
   Total: $200.00 | Available: $200.00
   Required per position: $22.00
   Max positions: 9
```

After opening 1 position:
```
Available balance: ~$178 (200 - 22 margin)
```

---

## Validation Checklist

Before considering testing complete, verify:

- [ ] Extended connector retrieves balance via API
- [ ] Extended connector retrieves positions via API
- [ ] Extended handles 404 errors gracefully (zero balance)
- [ ] Lighter connector retrieves balance via SDK
- [ ] Lighter connector retrieves positions via SDK
- [ ] Lighter handles account not found gracefully
- [ ] Strategy displays startup balance check
- [ ] Strategy shows balance in status display
- [ ] Strategy validates balance before trades
- [ ] Strategy blocks trades when insufficient balance
- [ ] Balance updates every 5-10 seconds
- [ ] Position tracking updates when trades execute
- [ ] Unrealized PnL reflected in total balance
- [ ] Margin locked/released affects available balance

---

## Next Steps After Testing

### If All Tests Pass ✅

1. **Start small**: Keep position size at $100-200
2. **Monitor closely**: Watch first few trades carefully
3. **Check hourly**: Verify balances match exchange
4. **Scale gradually**: Increase position size slowly
5. **Review daily**: Check PnL and funding payments

### If Tests Fail ❌

1. **Document the error**: Copy exact error message
2. **Check logs**: `tail -f logs/logs_hummingbot.log`
3. **Verify credentials**: API keys, wallet addresses
4. **Test connectivity**: Can you access exchange websites?
5. **Report issue**: Share logs and error details

---

## Safety Reminders

⚠️ **Before Live Trading**:

1. ✅ Test with paper trading first
2. ✅ Verify balances match exchange
3. ✅ Start with small position sizes ($100)
4. ✅ Ensure sufficient margin (2-3x required)
5. ✅ Monitor first trades closely
6. ✅ Have stop-loss configured (3% in config)
7. ✅ Understand funding rate mechanics
8. ✅ Know how to stop the bot quickly (`stop` command)

---

## Log File Locations

Balance update logs:
```bash
tail -f logs/logs_hummingbot.log | grep -i "balance\|position"
```

Extended connector logs:
```bash
tail -f logs/logs_hummingbot.log | grep -i extended
```

Lighter connector logs:
```bash
tail -f logs/logs_hummingbot.log | grep -i lighter
```

Strategy logs:
```bash
tail -f logs/logs_hummingbot.log | grep v2_funding_rate_arb
```

---

## Quick Reference: Hummingbot Commands

| Command | Purpose |
|---------|---------|
| `connect <exchange>` | Connect to an exchange |
| `balance` | Show account balances |
| `positions` | Show open positions |
| `status` | Show bot status and strategy info |
| `start --script <name>` | Start a strategy |
| `stop` | Stop the running strategy |
| `exit` | Exit Hummingbot |
| `history` | Show trade history |

---

**Testing Date**: _____________
**Tester**: _____________
**Results**: _____________

---

**Document Version**: 1.0
**Last Updated**: 2025-11-07
**Status**: Ready for Testing

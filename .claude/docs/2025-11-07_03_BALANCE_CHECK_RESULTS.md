# Live Balance Check Results

**Date**: 2025-11-07
**Wallet Addresses Verified**: ✅
**API Connectivity**: ⚠️ Partial

---

## Test Results

### Extended DEX (Starknet)

**Account Status**: ✅ **ACTIVE**
```
Wallet: 0x6255b6B72B34e257A68aFa9231128B4800b0b1CC
Account ID: 126169
Status: ACTIVE
L2 Public Key: 0x3c9be2751ada989c9b23e229ef4d3f79108c1f5ad4078652356781abbe25c91
```

**Balance Query Status**: ❌ API Error
```
Endpoint: GET /api/v1/user/balance
Response: {"status":"ERROR","error":{"code":1006,"message":"Internal Server Error"}}

Endpoint: GET /api/v1/user/positions
Response: {"status":"ERROR","error":{"code":1006,"message":"Internal Server Error"}}
```

**Possible Causes**:
1. Account needs to complete onboarding/deposit first
2. API key permissions need to be updated
3. Account has no trading history yet
4. Extended API temporary issue

**Recommendation**: ✅ Check balance manually via web interface
- URL: https://starknet.extended.exchange
- Login with wallet: `0x6255b6B72B34e257A68aFa9231128B4800b0b1CC`
- Verify USD balance in account dashboard

---

### Lighter DEX (zkSync)

**Wallet Address**: ✅ Verified
```
Wallet: 0x5D7EA455f1945E3Ea022478Bb7B33A1EBB2031DA
Contract: 0x3B4D794a66304F130a4Db8F2551B0070dfCf5ca7
Network: zkSync Era Mainnet
```

**Balance Query Status**: ⚠️ Requires SDK/Web3
```
Lighter DEX uses on-chain state for balances.

Options to check balance:
1. Web interface (recommended)
2. lighter-python SDK with SignerClient
3. Web3.py with zkSync provider
4. Direct blockchain query
```

**Recommendation**: ✅ Check balance manually via web interface
- URL: https://mainnet.zklighter.elliot.ai
- Connect wallet: `0x5D7EA455f1945E3Ea022478Bb7B33A1EBB2031DA`
- View account balance in dashboard

---

## Manual Balance Check Instructions

### For Extended DEX:

1. **Visit**: https://starknet.extended.exchange
2. **Connect Wallet**: Click "Connect Wallet"
3. **Select**: Argent X or Braavos (Starknet wallets)
4. **Verify**: Wallet address matches `0x6255b6B72B34e257A68aFa9231128B4800b0b1CC`
5. **Check Balance**: Look for USD balance in top-right corner
6. **Screenshot**: Take screenshot of balance for records

### For Lighter DEX:

1. **Visit**: https://mainnet.zklighter.elliot.ai
2. **Connect Wallet**: Click "Connect" in top-right
3. **Select**: MetaMask or other zkSync-compatible wallet
4. **Verify**: Wallet address matches `0x5D7EA455f1945E3Ea022478Bb7B33A1EBB2031DA`
5. **Check Balance**: Look for USD/USDC balance in account section
6. **Screenshot**: Take screenshot of balance for records

---

## Required Balances for Trading

### Strategy Configuration:
- **Position Size**: $500 per side
- **Leverage**: 5x
- **Required Margin**: **$110.00** per position (including 10% buffer)

### Recommended Funding:

| Level | Per Exchange | Total (Both) | Max Positions | Use Case |
|-------|-------------|--------------|---------------|----------|
| **Minimum** | $110 | $220 | 1 | Testing only |
| **Conservative** | $550 | $1,100 | 5 | Limited trading |
| **Comfortable** | $1,100 | $2,200 | 10 | Regular trading |
| **Optimal** | $2,500+ | $5,000+ | 20+ | Full strategy |

### Calculation Formula:
```
Required Margin = (Position Size / Leverage) × Safety Buffer
                = ($500 / 5) × 1.1
                = $100 × 1.1
                = $110 per position

Max Positions = Available Balance / Required Margin
```

---

## Next Steps

### 1. ✅ Verify Balances Manually

**Extended DEX**:
- [ ] Visit https://starknet.extended.exchange
- [ ] Connect wallet `0x6255b6B72B34e257A68aFa9231128B4800b0b1CC`
- [ ] Check USD balance: $_________
- [ ] Record max positions: _________ positions

**Lighter DEX**:
- [ ] Visit https://mainnet.zklighter.elliot.ai
- [ ] Connect wallet `0x5D7EA455f1945E3Ea022478Bb7B33A1EBB2031DA`
- [ ] Check USDC balance: $_________
- [ ] Record max positions: _________ positions

### 2. 🏦 Fund Accounts (If Needed)

**If balances are insufficient:**

**Extended DEX (Starknet)**:
1. Bridge USDC to Starknet:
   - Use: https://bridge.starknet.io
   - Or: https://layerswap.io
   - From: Ethereum/Arbitrum/Base
   - To: Starknet (wallet: `0x6255b6B72B34e257A68aFa9231128B4800b0b1CC`)

2. Deposit to Extended:
   - Visit Extended exchange
   - Click "Deposit"
   - Transfer USDC from wallet to trading account
   - Wait for confirmation

**Lighter DEX (zkSync)**:
1. Bridge USDC to zkSync Era:
   - Use: https://bridge.zksync.io
   - Or: https://app.orbiter.finance
   - From: Ethereum/Arbitrum/Optimism
   - To: zkSync Era (wallet: `0x5D7EA455f1945E3Ea022478Bb7B33A1EBB2031DA`)

2. Deposit to Lighter:
   - Visit Lighter exchange
   - Click "Deposit"
   - Transfer USDC from wallet to trading account
   - Wait for confirmation

### 3. 🧪 Test Strategy

**After funding:**

```bash
cd /Users/tdl321/hummingbot
./bin/hummingbot

# In Hummingbot:
start --script v2_funding_rate_arb.py

# Check status:
status

# Watch for balance checks in logs:
# - Startup balance check should show your balances
# - Pre-trade checks should validate before each trade
```

**Expected Startup Logs**:
```
[INFO] Checking initial balances...
[INFO] ✅ extended_perpetual: $2500.00 available (can open up to 22 positions)
[INFO] ✅ lighter_perpetual: $2500.00 available (can open up to 22 positions)
```

### 4. 📊 Monitor First Trades

**Watch for these logs**:
```
[INFO] extended_perpetual - Required: $110.00, Available: $2500.00
[INFO] lighter_perpetual - Required: $110.00, Available: $2500.00
[INFO] Best Combination: extended_perpetual | lighter_perpetual | BUY...
[INFO] Starting executors...
```

**If insufficient balance**:
```
[WARNING] Insufficient balance for KAITO arbitrage.
extended_perpetual shortfall: $60.00. Skipping...
```

---

## Troubleshooting

### Extended API Errors (Current Issue)

**Problem**: Balance endpoint returns error 1006
```json
{"status":"ERROR","error":{"code":1006,"message":"Internal Server Error"}}
```

**Possible Solutions**:
1. **Complete Account Setup**:
   - Deposit funds first (API may require activity)
   - Complete any KYC if required
   - Enable trading permissions

2. **Check API Key**:
   - Verify API key is active in Extended dashboard
   - Regenerate API key if needed
   - Update `.env` file with new key

3. **Wait and Retry**:
   - Extended API may have temporary issues
   - Try again in 30 minutes
   - Check Extended status page

4. **Use Hummingbot Connector**:
   - The connector may have better error handling
   - Will automatically retry
   - Logs will show detailed errors

### Lighter Balance Query

**Why can't we query directly?**
- Lighter uses on-chain state (not centralized DB)
- Requires blockchain query or SDK initialization
- Web interface queries blockchain directly

**Solutions**:
1. ✅ Use web interface (easiest)
2. Initialize lighter SDK in Python
3. Use Web3.py with zkSync provider
4. Let Hummingbot connector handle it (best for trading)

---

## Balance Checking Features Implemented

Your strategy now includes automatic balance checking:

### ✅ On Startup
```python
[INFO] Checking initial balances...
[INFO] ✅ extended_perpetual: $2500.00 available (can open up to 22 positions)
```

### ✅ Before Each Trade
```python
[INFO] extended_perpetual - Required: $110.00, Available: $2500.00
[INFO] lighter_perpetual - Required: $110.00, Available: $2500.00
```

### ✅ In Status Display
```
================================================================================
Balance Status for Arbitrage
================================================================================
✅ extended_perpetual:
   Total: $2500.00 | Available: $2400.00
   Required per position: $110.00
   Max positions: 21
```

### ✅ Automatic Protection
```python
if not sufficient_balance:
    self.logger().warning("Insufficient balance... Skipping...")
    continue  # Prevents unsafe trade
```

---

## Summary

| Item | Status | Action Required |
|------|--------|-----------------|
| Extended Account | ✅ Active | Check balance manually |
| Lighter Account | ✅ Verified | Check balance manually |
| Balance API | ⚠️ Error | Use web interface or wait |
| Strategy Code | ✅ Ready | Balance checks implemented |
| Trading Protection | ✅ Active | Auto-blocks insufficient trades |

**Overall Status**: ✅ **Ready for manual balance verification**

**Next Critical Step**:
1. Check balances manually on both exchanges
2. Fund accounts if needed (minimum $110 per exchange)
3. Test in paper trading mode first
4. Monitor first live trades closely

---

## Contact & Support

**Extended DEX**:
- Dashboard: https://starknet.extended.exchange
- Docs: https://docs.extended.exchange
- Support: Check their Discord/Telegram

**Lighter DEX**:
- Dashboard: https://mainnet.zklighter.elliot.ai
- Docs: https://docs.lighter.xyz
- Support: Check their Discord/Telegram

**Hummingbot**:
- Docs: https://docs.hummingbot.org
- Discord: https://discord.gg/hummingbot

---

**Report Generated**: 2025-11-07
**Automated Balance Check**: Partial (API issues)
**Recommendation**: Use web interfaces to verify balances before trading

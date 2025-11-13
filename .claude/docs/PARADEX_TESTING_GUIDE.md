# Paradex Connector Testing Guide

**Status:** Ready for API credential testing (95% → 100%)
**Date:** 2025-11-13

---

## Overview

You now have Paradex API credentials and can complete the final 5% of testing to validate the connector works end-to-end with real API calls.

## What You Need

### 1. Paradex Credentials

You should have:
- **Subkey Private Key** (Starknet L2, format: `0x...`)
- **Main Account Address** (Paradex account, format: `0x...`)

**Where to get them:**
- Testnet: https://testnet.paradex.trade
- Mainnet: https://paradex.trade

**How to create a subkey:** See `.claude/docs/PARADEX_USER_GUIDE.md` section 4.

### 2. Environment Setup

```bash
# Set credentials as environment variables (recommended for testing)
export PARADEX_API_SECRET="0x..."  # Your subkey private key
export PARADEX_ACCOUNT_ADDRESS="0x..."  # Your main account address
```

**Security Note:** Never commit credentials to Git!

---

## Testing Approach (3 Levels)

We've created 3 levels of tests, from simplest to most comprehensive:

### Level 1: Quick Auth Test (1 minute)
**Purpose:** Verify credentials work and can generate JWT tokens

```bash
python scripts/quick_test_paradex_auth.py
```

**What it tests:**
- ✅ JWT token generation
- ✅ Basic API call to `/account` endpoint
- ✅ Credentials are valid

**Expected output:**
```
✅ JWT token generated successfully!
✅ API call successful!
🎉 AUTHENTICATION TEST PASSED!
```

### Level 2: Integration Test (5 minutes)
**Purpose:** Test all core connector functionality

```bash
# Testnet (recommended first)
python scripts/test_paradex_integration.py

# Mainnet (after testnet passes)
python scripts/test_paradex_integration.py --mainnet
```

**What it tests:**
1. ✅ Authentication (JWT token)
2. ✅ Balance fetching
3. ✅ Trading rules
4. ✅ Order book data
5. ✅ Funding information
6. ✅ Order placement (real order!)
7. ✅ Order cancellation
8. ✅ WebSocket streaming

**Expected output:**
```
Results: 8/8 tests passed
🎉 ALL TESTS PASSED! Connector is working correctly.
```

**Safety Note:** Test 6 will place a REAL order on the exchange (far from market price) and immediately cancel it. You'll be prompted to confirm.

### Level 3: Hummingbot CLI Test (10 minutes)
**Purpose:** Test the connector through the actual Hummingbot interface

```bash
# Start Hummingbot
./start

# OR with Docker
docker compose up -d
docker attach hummingbot
```

**Commands to test:**

```
# 1. Connect to Paradex
> connect paradex_perpetual_testnet
# Enter your credentials when prompted

# 2. Check connection status
> status

# 3. Check balance
> balance

# 4. List available markets
> list markets paradex_perpetual_testnet

# 5. Check order book
> order_book paradex_perpetual_testnet BTC-USD-PERP

# 6. Check funding rate
> funding_rate paradex_perpetual_testnet ETH-USD-PERP

# 7. (Optional) Create and run a strategy
> create
# Choose strategy: pure_market_making
# Exchange: paradex_perpetual_testnet
# Trading pair: ETH-USD-PERP
# Follow prompts...

> start
# Monitor for a few minutes
> status
> stop
```

---

## Test Sequence (Recommended Order)

### Step 1: Quick Auth Test ⚡
```bash
export PARADEX_API_SECRET="0x..."
export PARADEX_ACCOUNT_ADDRESS="0x..."
python scripts/quick_test_paradex_auth.py
```

**If this fails:** Check your credentials are correct.

### Step 2: Integration Test (Testnet) 🧪
```bash
python scripts/test_paradex_integration.py
```

**If this fails:** Check the specific test that failed and review logs.

### Step 3: Integration Test (Mainnet) 🚀
```bash
python scripts/test_paradex_integration.py --mainnet
```

**Only run this after testnet passes!**

### Step 4: Hummingbot CLI Test 💻
```bash
./start
> connect paradex_perpetual_testnet
# Test commands listed above
```

---

## Troubleshooting

### Problem: "401 Unauthorized"

**Causes:**
- Subkey not registered with main account
- Wrong account address
- Wrong API secret

**Solutions:**
1. Verify subkey is registered on Paradex website
2. Check account address matches exactly
3. Regenerate subkey if needed

### Problem: "ModuleNotFoundError: No module named 'paradex'"

**Solution:**
```bash
pip install paradex-py>=0.4.6
```

### Problem: "Balance shows $0"

**Solutions:**
1. Fund your testnet account from Paradex Discord faucet
2. Wait 1-2 minutes for balance to sync
3. Check balance on Paradex website to confirm

### Problem: "Order placement test fails"

**Causes:**
- Insufficient balance
- Market not available
- Position limit reached

**Solutions:**
1. Check balance: `balance` command
2. Verify market is active on Paradex
3. Check logs for specific error

---

## Expected Test Results

### ✅ Success Indicators

**Quick Auth Test:**
```
✅ JWT token generated successfully!
✅ API call successful!
```

**Integration Test:**
```
✅ PASS - auth
✅ PASS - balance
✅ PASS - trading_rules
✅ PASS - order_book
✅ PASS - funding_info
✅ PASS - order_placement
✅ PASS - order_cancellation
✅ PASS - websocket
Results: 8/8 tests passed
```

**Hummingbot CLI:**
```
> status
✅ paradex_perpetual_testnet: Connected

> balance
USDC  |  100.00  |  100.00
```

### ❌ Failure Indicators

**Authentication errors:**
```
❌ Authentication failed: 401 Unauthorized
```
→ Check credentials

**Connection errors:**
```
❌ WebSocket connection failed
```
→ Check internet connection, try again

**Order errors:**
```
❌ Order placement failed: Insufficient margin
```
→ Fund your account

---

## What to Do After Testing

### If All Tests Pass ✅

**Congratulations!** The connector is working. Next steps:

1. **Document results:**
   - Take screenshots
   - Save test output
   - Note any warnings

2. **Create GitHub issue (optional):**
   - Report successful testing
   - Share test results
   - Provide feedback

3. **Start using the connector:**
   - Create your strategies
   - Monitor performance
   - Report any issues

### If Tests Fail ❌

1. **Gather information:**
   - Which test failed?
   - What was the error message?
   - Check logs: `logs` command in Hummingbot

2. **Try fixes:**
   - Review troubleshooting section above
   - Check Paradex API status: https://status.paradex.trade
   - Verify credentials are correct

3. **Report issues:**
   - Create GitHub issue with full error details
   - Include test output
   - Describe steps to reproduce

---

## Test Scripts Reference

### Created Test Scripts

1. **`scripts/quick_test_paradex_auth.py`**
   - Quick authentication test
   - ~1 minute
   - No order placement

2. **`scripts/test_paradex_integration.py`**
   - Comprehensive integration test
   - ~5 minutes
   - Includes order placement (with confirmation)
   - Full WebSocket testing

### Existing Test Scripts (No Credentials Needed)

3. **`test/paradex_connector/test_paradex_websocket.py`**
   - WebSocket connectivity test
   - No authentication required

4. **`test/paradex_connector/test_paradex_api_endpoints.py`**
   - Public API endpoint tests
   - No authentication required

---

## Next Steps After Testing

### Short Term (Today)

1. ✅ Run quick auth test
2. ✅ Run integration test (testnet)
3. ✅ Test in Hummingbot CLI
4. ✅ Document results

### Medium Term (This Week)

1. Run integration test on mainnet
2. Deploy a simple strategy (e.g., pure market making)
3. Monitor for 24 hours
4. Validate funding payments work correctly

### Long Term (This Month)

1. Test advanced strategies
2. Monitor connector stability
3. Report any bugs/issues
4. Share feedback with Hummingbot community

---

## Additional Resources

### Documentation
- **User Guide:** `.claude/docs/PARADEX_USER_GUIDE.md`
- **Connector README:** `hummingbot/connector/derivative/paradex_perpetual/README.md`
- **Implementation Status:** `.claude/PARADEX_INFRASTRUCTURE_COMPLETE.md`

### Unit Tests (Mocked - No Credentials)
```bash
# Run all unit tests
pytest test/hummingbot/connector/derivative/paradex_perpetual/

# Run specific test file
pytest test/hummingbot/connector/derivative/paradex_perpetual/test_paradex_perpetual_auth.py -v
```

### Support
- **Paradex Discord:** https://discord.gg/paradex
- **Hummingbot Discord:** https://discord.gg/hummingbot
- **Paradex Docs:** https://docs.paradex.trade
- **Hummingbot Docs:** https://docs.hummingbot.org

---

## Safety Reminders

### Testing Best Practices

✅ **DO:**
- Start with testnet
- Use small amounts
- Monitor closely
- Document everything
- Ask questions if unsure

❌ **DON'T:**
- Skip testnet testing
- Use large amounts initially
- Share your private keys
- Ignore errors/warnings
- Rush to mainnet

### Security Notes

- **Subkeys are safer:** Cannot withdraw funds
- **Never commit credentials:** Use environment variables
- **Start small:** Test with minimal amounts
- **Monitor regularly:** Check positions and balances
- **Rotate keys:** Change subkeys periodically

---

## Questions?

If you encounter issues or have questions:

1. Check this guide's troubleshooting section
2. Review the User Guide (`.claude/docs/PARADEX_USER_GUIDE.md`)
3. Check Paradex status page: https://status.paradex.trade
4. Ask in Hummingbot Discord: https://discord.gg/hummingbot

---

**Ready to test? Start with the Quick Auth Test!**

```bash
export PARADEX_API_SECRET="0x..."
export PARADEX_ACCOUNT_ADDRESS="0x..."
python scripts/quick_test_paradex_auth.py
```

**Good luck! 🚀**

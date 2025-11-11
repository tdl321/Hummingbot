# Paradex Connector - Complete User Setup Guide

**Last Updated:** 2025-11-11
**Connector Version:** 1.0.0
**For:** Hummingbot Users

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Prerequisites](#2-prerequisites)
3. [Getting Started with Paradex](#3-getting-started-with-paradex)
4. [Subkey Setup (Recommended)](#4-subkey-setup-recommended)
5. [Connecting to Hummingbot](#5-connecting-to-hummingbot)
6. [Testing Your Connection](#6-testing-your-connection)
7. [Your First Trade](#7-your-first-trade)
8. [Advanced Configuration](#8-advanced-configuration)
9. [Troubleshooting](#9-troubleshooting)
10. [FAQ](#10-faq)

---

## 1. Introduction

### What is Paradex?

Paradex is a Layer 2 decentralized exchange built on Starknet, offering:

- **Zero Trading Fees:** 0% maker, 0% taker on 100+ perpetual markets
- **High Liquidity:** Better-than-CEX depth on major pairs
- **250+ Markets:** Perpetuals, options, pre-markets, spot
- **Privacy-Focused:** zk-encrypted accounts
- **Early Access:** Trade new tokens before CEX listings

### Why Use Paradex with Hummingbot?

1. **Zero Fees = More Profit:** No fees means market making strategies are highly profitable
2. **High-Frequency Friendly:** No cost to place/cancel orders
3. **Funding Arbitrage:** Exploit funding rate differences across exchanges
4. **Early Token Access:** Bot trade new listings before competition

---

## 2. Prerequisites

### System Requirements

- **Hummingbot:** v2.0.0+ (with Paradex connector)
- **Python:** 3.10+
- **Internet:** Stable connection (for WebSocket)
- **RAM:** 2GB+ available

### Paradex Requirements

- Paradex account (mainnet or testnet)
- USDC balance for trading
- Starknet wallet (MetaMask with Starknet plugin, or Argent X, or Braavos)

### Knowledge Requirements

- Basic understanding of perpetual futures
- Familiarity with Hummingbot commands
- Understanding of API keys and security

---

## 3. Getting Started with Paradex

### Step 1: Create Paradex Account

#### Option A: Mainnet (Real Money)

1. Go to https://paradex.trade
2. Click "Connect Wallet"
3. Choose wallet type:
   - MetaMask (with Starknet plugin)
   - Argent X
   - Braavos
4. Follow wallet connection prompts
5. Complete KYC if required
6. Your account address will be displayed in top-right

**Save your account address:** `0x...` (you'll need this for Hummingbot)

#### Option B: Testnet (Practice)

1. Go to https://testnet.paradex.trade
2. Connect wallet (same process as mainnet)
3. Get testnet USDC from Paradex Discord faucet
4. Practice risk-free!

### Step 2: Fund Your Account

1. Bridge USDC to Starknet L2:
   - Use https://starkgate.starknet.io
   - Or deposit directly from Ethereum L1
   - Or transfer from another Starknet wallet

2. Deposit to Paradex:
   - Click "Deposit" on Paradex
   - Enter amount
   - Confirm transaction in wallet
   - Wait ~15 minutes for L1 → L2 confirmation

**Recommended Starting Amount:**
- Testnet: 100-1000 testnet USDC (free from faucet)
- Mainnet: 100-500 USDC (start small!)

---

## 4. Subkey Setup (Recommended)

### What is a Subkey?

A **subkey** is a secondary private key with **limited permissions**:

✅ **Can:**
- Place orders
- Cancel orders
- View account data
- Trade on your behalf

❌ **Cannot:**
- Withdraw funds
- Transfer assets
- Change account settings

**Why use subkeys for bots?**
- **Security:** If your bot is compromised, attacker cannot drain funds
- **Peace of mind:** Trade 24/7 without full account risk
- **Best practice:** Recommended by Paradex for algorithmic trading

### Step-by-Step Subkey Creation

#### Method 1: Using Python (Recommended)

1. Install Starknet Python library:
```bash
pip install starknet-py
```

2. Generate random subkey:
```python
from starknet_py.net.signer.stark_curve_signer import KeyPair

# Generate random keypair
keypair = KeyPair.generate()

print(f"Subkey Private Key (keep secret!): {hex(keypair.private_key)}")
print(f"Subkey Public Key: {hex(keypair.public_key)}")
```

3. **IMPORTANT:** Save both values securely:
   - **Private Key** (0x...): You'll enter this in Hummingbot
   - **Public Key** (0x...): Register this with Paradex

Example output:
```
Subkey Private Key (keep secret!): 0x1234abcd...
Subkey Public Key: 0x5678ef01...
```

#### Method 2: Using Paradex Website

1. Log in to Paradex: https://paradex.trade
2. Go to: **Account Settings → API Management**
3. Click "Generate New Subkey"
4. Follow on-screen instructions
5. **Download and save** the private key (shown only once!)
6. Subkey is automatically registered

### Step 3: Register Subkey with Paradex

If you generated the subkey manually (Method 1):

1. Log in to Paradex with your main account
2. Navigate to: **Account Settings → API Management**
3. Click "Register Existing Subkey"
4. Paste your **subkey public key** (0x...)
5. Set permissions:
   - ✅ Trading (required)
   - ❌ Withdrawals (keep disabled!)
6. Confirm with wallet signature
7. Subkey is now active!

### Security Best Practices

- **Never share your private key** with anyone
- **Store in password manager** (1Password, LastPass, etc.)
- **Use different subkey per bot** if running multiple strategies
- **Rotate subkeys monthly** for maximum security
- **Backup offline** in secure location

---

## 5. Connecting to Hummingbot

### Step 1: Start Hummingbot

```bash
# Navigate to Hummingbot directory
cd hummingbot

# Start Hummingbot
./start
```

Or if using Docker:
```bash
docker compose up -d
docker attach hummingbot
```

### Step 2: Connect to Paradex

#### For Mainnet:

```
> connect paradex_perpetual
```

You'll be prompted for:

**Prompt 1: Subkey Private Key**
```
Enter your Paradex subkey private key (Starknet L2 private key, 0x...):
>>>
```

**Enter your subkey private key:**
```
0x1234abcd... [paste your private key here]
```

**Prompt 2: Main Account Address**
```
Enter your Paradex main account address (0x...):
>>>
```

**Enter your main Paradex account address:**
```
0x5678ef01... [paste your account address]
```

#### For Testnet:

```
> connect paradex_perpetual_testnet
```

Follow same prompts, but use testnet credentials.

### Step 3: Verify Connection

Check connection status:
```
> status
```

Should show:
```
✅ paradex_perpetual: Connected
```

View your balance:
```
> balance
```

Expected output:
```
Asset    | Total Balance | Available Balance
---------|---------------|------------------
USDC     |     500.00    |      500.00
```

---

## 6. Testing Your Connection

### Test 1: Check Markets

```
> list markets paradex_perpetual
```

Should display available trading pairs:
```
BTC-USD-PERP
ETH-USD-PERP
SOL-USD-PERP
...
```

### Test 2: Check Order Book

```
> order_book paradex_perpetual BTC-USD-PERP
```

Should show bids and asks:
```
Bids:
Price     | Size
----------|------
50000.00  | 1.50
49999.50  | 2.30
...

Asks:
Price     | Size
----------|------
50001.00  | 1.20
50001.50  | 0.80
...
```

### Test 3: Check Funding Rate

```
> funding_rate paradex_perpetual ETH-USD-PERP
```

Should show current funding rate:
```
Market: ETH-USD-PERP
Funding Rate: 0.0001 (0.01%)
Next Funding: 2025-11-11 16:00:00 UTC
```

---

## 7. Your First Trade

### Test Trade (Small Amount)

Let's place a small test order to verify everything works:

#### Step 1: Create Simple Strategy

```
> create
```

Choose strategy:
```
What is your market making strategy?
>>> pure_market_making
```

Configure parameters:
```
Enter your maker exchange name:
>>> paradex_perpetual

Enter the token trading pair you would like to trade on paradex_perpetual:
>>> ETH-USD-PERP

How far away from the mid price do you want to place the first bid order? (Enter 1 to indicate 1%)
>>> 0.5

How far away from the mid price do you want to place the first ask order? (Enter 1 to indicate 1%)
>>> 0.5

How much do you want to trade per order (denominated in the base asset)?
>>> 0.01
```

#### Step 2: Start Strategy

```
> start
```

Monitor status:
```
> status
```

Should show:
```
Strategy: pure_market_making
Market: paradex_perpetual - ETH-USD-PERP

Active Orders:
Order ID | Side | Price    | Amount | Status
---------|------|----------|--------|-------
abc123   | BUY  | 2450.00  | 0.01   | OPEN
def456   | SELL | 2460.00  | 0.01   | OPEN
```

#### Step 3: Cancel and Stop

After testing:
```
> stop
```

Verify orders are cancelled:
```
> balance
```

Balance should be back to original amount (minus any small fees/funding).

---

## 8. Advanced Configuration

### Multiple Trading Pairs

Edit strategy config to trade multiple pairs:

```yaml
markets:
  - BTC-USD-PERP
  - ETH-USD-PERP
  - SOL-USD-PERP
```

### Custom Rate Limits

If you encounter rate limits, adjust in connector:

```python
# In paradex_perpetual_constants.py
MAX_REQUEST_PER_MINUTE = 600  # Reduce if needed
```

### WebSocket vs REST Polling

By default, WebSocket is used for real-time updates.

If WebSocket is unstable:
```python
# Connector automatically falls back to REST polling
# No configuration needed!
```

### Testnet/Mainnet Switching

Use domain parameter in strategy config:

```yaml
# For testnet
exchange: paradex_perpetual_testnet

# For mainnet
exchange: paradex_perpetual
```

---

## 9. Troubleshooting

### Problem: "Invalid credentials" or 401 Unauthorized

**Causes:**
1. Subkey not registered with main account
2. Wrong account address
3. Subkey expired/revoked

**Solutions:**
1. Verify subkey is registered on Paradex website
2. Double-check account address (0x...)
3. Regenerate subkey if necessary
4. Restart Hummingbot to refresh JWT token

### Problem: Balance shows $0

**Causes:**
1. Funds not deposited to Paradex
2. L1 → L2 bridge still pending
3. Initial sync delay

**Solutions:**
1. Check balance on Paradex website
2. Wait 15 minutes for bridge completion
3. Run `balance` command to force refresh
4. Check logs for errors: `logs`

### Problem: WebSocket keeps disconnecting

**Causes:**
1. Network instability
2. Paradex server issues
3. Firewall blocking WebSocket

**Solutions:**
1. Check internet connection
2. Verify https://status.paradex.trade
3. REST polling fallback automatically activates
4. No action needed if orders still work

### Problem: Orders not filling

**Causes:**
1. Price not competitive
2. Insufficient margin
3. Market illiquid
4. Order size too large

**Solutions:**
1. Check order book depth
2. Verify available balance
3. Reduce order size
4. Adjust spreads closer to mid

### Problem: High funding payments

**Explanation:**
- Funding payments occur every 8 hours
- Long positions pay when rate is positive
- Short positions pay when rate is negative

**Solutions:**
1. Monitor funding rates: `funding_rate`
2. Close positions before funding time
3. Use funding arbitrage strategies
4. Switch to markets with lower rates

---

## 10. FAQ

### Q: Is Paradex safe?

**A:** Paradex is a non-custodial DEX on Starknet L2. You retain custody of funds. Smart contracts are audited. Always DYOR.

### Q: What are the trading fees?

**A:** Zero fees (0% maker, 0% taker) on 100+ perpetual markets for retail traders.

### Q: Can I withdraw funds anytime?

**A:** Yes! Withdrawals typically take ~15 minutes for L2 → L1 bridging. No withdrawal fees on L2.

### Q: What's the minimum deposit?

**A:** No official minimum, but recommend 100+ USDC for effective trading.

### Q: Can I use leverage?

**A:** Yes, Paradex offers up to 20x leverage on most pairs. Use responsibly!

### Q: What if I lose my subkey?

**A:** Generate a new subkey and register it. The old key becomes inactive.

### Q: Can I have multiple subkeys?

**A:** Yes! Create different subkeys for different bots/strategies.

### Q: Does Hummingbot support Paradex options?

**A:** Not yet. Currently supports perpetual futures only.

### Q: How do I get testnet USDC?

**A:** Join Paradex Discord and request from the faucet channel.

### Q: Can I run multiple bots on same account?

**A:** Yes, but be careful of position conflicts. Use different subkeys for isolation.

---

## Additional Resources

### Paradex Resources
- **Documentation:** https://docs.paradex.trade
- **Discord:** https://discord.gg/paradex
- **Twitter:** @tradeparadex
- **Status Page:** https://status.paradex.trade

### Hummingbot Resources
- **Documentation:** https://docs.hummingbot.org
- **Discord:** https://discord.gg/hummingbot
- **GitHub:** https://github.com/hummingbot/hummingbot
- **Academy:** https://hummingbot.org/academy

### Connector Documentation
- **README:** `hummingbot/connector/derivative/paradex_perpetual/README.md`
- **Test Suite:** `test/paradex_connector/README.md`
- **Implementation Plan:** `.claude/docs/PARADEX_CONNECTOR_INTEGRATION_PLAN.md`
- **Lessons Learned:** `.claude/docs/PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md`

---

## Support

Need help? Reach out:

1. **Hummingbot Discord:** Best for strategy/bot questions
2. **Paradex Discord:** Best for exchange/account questions
3. **GitHub Issues:** For connector bugs

---

**Happy Bot Trading! 🤖📈**

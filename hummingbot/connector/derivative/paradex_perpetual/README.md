# Paradex Perpetual Connector

## Overview

Paradex is a Layer 2 decentralized exchange (DEX) built on Starknet, offering perpetual futures trading with **zero trading fees** for retail traders across 100+ markets.

**Key Features:**
- 🆓 **Zero trading fees** (0% maker, 0% taker) on 100+ perpetual markets
- 🔒 **Privacy-focused** with zk-encrypted accounts
- 💧 **Better-than-CEX liquidity**
- 📊 **250+ markets** including perpetuals, options, pre-markets, and spot
- 🏦 **Unified margin account** for capital efficiency
- 🚀 **Early token listings** and pre-market access

**Official Resources:**
- Website: https://paradex.trade
- Documentation: https://docs.paradex.trade
- Python SDK: https://tradeparadex.github.io/paradex-py/

---

## Prerequisites

### 1. Install paradex-py SDK

```bash
pip install paradex-py>=0.4.6
```

The connector uses the official Paradex Python SDK for authentication and order signing.

### 2. Paradex Account

You need a Paradex account with one of two authentication methods:

#### Option A: Subkey Authentication (Recommended ⭐)

**Why subkeys?**
- **Limited access**: Can only trade, cannot withdraw funds
- **Safer for bots**: If compromised, attacker cannot drain your account
- **L2-only**: No Ethereum mainnet private key needed

**How to create a subkey:**

1. Generate a random Starknet keypair:
```python
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.signer import BaseSigner
from starknet_py.net.models import StarknetChainId

# Generate random keypair
private_key = BaseSigner.generate_private_key()
print(f"Subkey Private Key: {hex(private_key)}")
```

2. Register the subkey with your main account:
   - Log in to Paradex with your main account
   - Go to Account Settings → API Keys
   - Add the subkey public address
   - Authorize for trading

3. Use in Hummingbot:
   - **API Secret**: The subkey private key (0x...)
   - **Account Address**: Your main Paradex account address (0x...)

#### Option B: Main Private Key (Full Access)

Uses your Starknet L2 private key directly. **Not recommended for bots** as it has full withdrawal access.

---

## Configuration

### Mainnet Configuration

1. Start Hummingbot:
```bash
hummingbot
```

2. Connect to Paradex:
```
> connect paradex_perpetual
```

3. Enter credentials:
```
Enter your Paradex subkey private key (Starknet L2 private key, 0x...):
>>> 0x... [your subkey private key]

Enter your Paradex main account address (0x...):
>>> 0x... [your main account address]
```

4. Verify connection:
```
> balance
```

### Testnet Configuration

For testing, use the testnet domain:

```
> connect paradex_perpetual_testnet
```

Testnet requires:
- Testnet subkey (generate same way as mainnet)
- Testnet account with test USDC
- Get testnet funds from Paradex Discord faucet

---

## Supported Features

### ✅ Fully Supported

- **Market Data:**
  - Real-time order books (WebSocket + REST fallback)
  - Trade history
  - Funding rates
  - 24h statistics

- **Trading:**
  - Limit orders
  - Market orders
  - Order cancellation
  - Position tracking

- **Account Management:**
  - Balance tracking
  - Position monitoring
  - Funding payment tracking
  - Real-time updates via WebSocket

### ⏳ Roadmap (Not Yet Implemented)

- Advanced order types (Stop Loss, Take Profit)
- Perpetual options trading
- Pre-market access
- Batch order operations

---

## Trading Pairs

Paradex uses the format: `{BASE}-USD-PERP`

**Popular pairs:**
- `BTC-USD-PERP` - Bitcoin perpetual
- `ETH-USD-PERP` - Ethereum perpetual
- `SOL-USD-PERP` - Solana perpetual
- `DOGE-USD-PERP` - Dogecoin perpetual

**Full list:** Available via `/markets` endpoint or Paradex website

---

## Example Usage

### Pure Market Making Strategy

```yaml
strategy: pure_market_making
exchange: paradex_perpetual
market: BTC-USD-PERP
bid_spread: 0.1
ask_spread: 0.1
order_amount: 0.001
order_refresh_time: 30
```

### Perpetual Market Making Strategy

```yaml
strategy: perpetual_market_making
derivative: paradex_perpetual
market: ETH-USD-PERP
leverage: 5
bid_spread: 0.08
ask_spread: 0.08
order_amount: 0.01
```

### Funding Rate Arbitrage

```yaml
strategy: spot_perpetual_arbitrage
spot_connector: binance
spot_market: ETH-USDT
derivative_connector: paradex_perpetual
derivative_market: ETH-USD-PERP
min_funding_rate: 0.01
```

---

## Fee Structure

### Retail Traders (Default)
- **Maker Fee:** 0% 🎉
- **Taker Fee:** 0% 🎉
- **Applicable to:** 100+ perpetual markets

### Institutional Traders
Fee tiers may apply - check Paradex documentation for details.

### Important Notes
- **No withdrawal fees** on Starknet L2
- **Gas fees** apply for L1 ↔ L2 bridging (one-time setup)
- **Funding payments** apply every 8 hours (standard for perpetuals)

---

## Troubleshooting

### Connection Issues

**Problem:** `401 Unauthorized` errors

**Solutions:**
1. Verify your subkey is registered with your main account
2. Check that the account address is correct
3. Ensure subkey has trading permissions
4. Try regenerating JWT token (restart Hummingbot)

**Problem:** `WebSocket connection failed`

**Solutions:**
1. Check internet connection
2. Verify Paradex services are online (check status page)
3. REST polling fallback should automatically activate
4. No action needed if balances/orders still work

### Balance Shows $0

**Solutions:**
1. Verify you have deposited USDC to your Paradex account
2. Check balance on Paradex website
3. Wait a few seconds for initial sync
4. Run `balance` command to force refresh

### Orders Not Filling

**Check:**
1. Order price is competitive (check order book)
2. Sufficient margin available
3. Market is liquid (check recent trades)
4. No API errors in logs (`logs` command)

### API Rate Limits

Paradex has generous rate limits, but if you encounter them:
1. Reduce order refresh frequency
2. Use WebSocket updates instead of polling
3. Batch operations where possible

---

## Security Best Practices

### ✅ DO

- **Use subkeys for trading bots** - Cannot withdraw, safer
- **Keep private keys secure** - Never share or commit to Git
- **Start with small amounts** - Test on testnet first
- **Monitor regularly** - Check positions and balances
- **Use separate trading account** - Don't use your main holding account

### ❌ DON'T

- **Share private keys** - Compromised keys = lost funds
- **Use main key in bots** - Use subkeys instead
- **Skip testnet testing** - Always test before mainnet
- **Ignore funding rates** - Can accumulate significant costs
- **Over-leverage** - Start conservative (2-3x leverage)

---

## Known Limitations

1. **Starknet Network Dependency**
   - Paradex is on Starknet L2
   - L1 ↔ L2 bridging has delays (~15 minutes)
   - Plan deposits/withdrawals accordingly

2. **USD-Denominated Only**
   - All perpetuals are USD-quoted
   - Settlement in USDC

3. **No Hedging Mode**
   - One-way position mode only
   - Cannot have simultaneous long/short on same market

4. **WebSocket May Disconnect**
   - Auto-reconnect implemented
   - REST polling fallback available
   - No data loss during disconnections

---

## Performance Tips

### Optimize for Low Latency

1. **Enable WebSocket** (default)
   - Real-time order updates
   - Faster than REST polling

2. **Co-locate if possible**
   - Paradex servers are globally distributed
   - Lower latency = better execution

3. **Use Limit Orders**
   - Zero fees as maker
   - Better price control

### Optimize for Cost

1. **Take advantage of zero fees**
   - Make markets instead of taking
   - No urgency penalty

2. **Monitor funding rates**
   - Long positions pay if rate is positive
   - Short positions pay if rate is negative
   - Rates update every 8 hours

3. **Use unified margin**
   - Cross-margin by default
   - Efficient capital usage

---

## Support

### Hummingbot Support

- **Discord:** https://discord.gg/hummingbot
- **GitHub:** https://github.com/hummingbot/hummingbot
- **Docs:** https://docs.hummingbot.org

### Paradex Support

- **Discord:** https://discord.gg/paradex
- **Twitter:** @tradeparadex
- **Docs:** https://docs.paradex.trade

### Connector Issues

If you encounter connector-specific issues:

1. Check the logs: `logs` command in Hummingbot
2. Verify API is working: https://api.prod.paradex.trade/v1/system/health
3. Report bugs: https://github.com/hummingbot/hummingbot/issues

---

## Additional Resources

- **Paradex Lessons Learned:** `.claude/docs/PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md`
- **Implementation Plan:** `.claude/docs/PARADEX_CONNECTOR_INTEGRATION_PLAN.md`
- **Test Suite:** `test/paradex_connector/README.md`
- **Status Document:** `.claude/PARADEX_STATUS.md`

---

## Version History

- **v1.0.0** (2025-11-11) - Initial release
  - Zero-fee perpetual trading
  - Subkey authentication
  - WebSocket streaming with REST fallback
  - Comprehensive error handling

---

**Happy Trading on Paradex! 🚀**

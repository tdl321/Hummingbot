# Paradex Credentials Setup Guide

**Quick Reference:** How to get and configure your Paradex credentials

---

## What You Need

For Paradex authentication, you need **TWO** pieces of information:

| Credential | What It Is | Where to Get It | Format |
|------------|------------|-----------------|--------|
| **L1 Address** | Your Ethereum L1 address | MetaMask | `0x...` (40 hex chars) |
| **L2 Subkey** | Your Starknet L2 private key | Generate + Register | `0x...` (64 hex chars) |

---

## Step-by-Step Setup

### Step 1: Get Your L1 Ethereum Address

This is the **EASIEST** part:

1. Open MetaMask (or your Ethereum wallet)
2. Click to copy the address shown at the top
3. Save it - you'll need this for configuration

**Example:** `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`

**This is:**
- ✅ Your Ethereum L1 address
- ✅ The address you use to connect to Paradex website
- ✅ The address shown in MetaMask
- ❌ NOT your Starknet L2 address

---

### Step 2: Generate L2 Subkey

**Option A: Using Python (Recommended)**

```python
# Install starknet-py if you haven't
# pip install starknet-py

from starknet_py.net.signer.stark_curve_signer import KeyPair

# Generate random keypair
keypair = KeyPair.generate()

print(f"L2 Private Key (SAVE THIS!): {hex(keypair.private_key)}")
print(f"L2 Public Key (for registration): {hex(keypair.public_key)}")
```

**Save both values:**
- **L2 Private Key:** Use this in Hummingbot (keep secret!)
- **L2 Public Key:** Register this on Paradex website

**Option B: Using Paradex Website**

1. Go to https://paradex.trade (or https://testnet.paradex.trade)
2. Connect your wallet
3. Go to: **Account Settings → API Management**
4. Click "Generate New Subkey"
5. **Download and save the private key** (shown only once!)

---

### Step 3: Register Subkey on Paradex

If you used Option A (Python generation):

1. Go to https://paradex.trade (or testnet)
2. Connect your wallet (using your L1 Ethereum address)
3. Go to: **Account Settings → API Management**
4. Click "Register Existing Subkey"
5. Paste your **L2 Public Key** (not private!)
6. Set permissions:
   - ✅ Trading (required)
   - ❌ Withdrawals (keep disabled for security!)
7. Confirm with wallet signature
8. Subkey is now active!

---

## Configuration Methods

### Method 1: Environment Variables (Quick Testing)

```bash
# For testnet:
export PARADEX_API_SECRET="0x..."  # Your L2 subkey private key
export PARADEX_ACCOUNT_ADDRESS="0x..."  # Your L1 Ethereum address

# Run test:
python scripts/quick_test_paradex_auth.py
```

### Method 2: .env File (Recommended)

Edit `/Users/tdl321/hummingbot/.env`:

```bash
# Paradex Testnet Credentials
PARADEX_TESTNET_L1_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb  # Your L1 address
PARADEX_TESTNET_L2_SUBKEY_PRIVATE_KEY=0x...  # Your L2 subkey

# Paradex Mainnet Credentials (for later)
PARADEX_MAINNET_L1_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb  # Same L1 address
PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY=0x...  # Different L2 subkey for mainnet
```

**⚠️ IMPORTANT:** Never commit `.env` file to git!

### Method 3: Hummingbot CLI (Interactive)

```bash
./start
> connect paradex_perpetual_testnet

# You'll be prompted:
# Enter your Paradex subkey L2 private key (Starknet L2 private key, 0x...):
# >>> 0x...  [paste L2 subkey]

# Enter your Paradex L1 account address (Ethereum L1 address, 0x...):
# >>> 0x...  [paste L1 address]
```

---

## Verification Checklist

Before testing, verify:

- [ ] L1 address is 42 characters (including `0x`)
- [ ] L1 address matches your MetaMask address
- [ ] L2 subkey is 66 characters (including `0x`)
- [ ] L2 subkey is registered on Paradex website
- [ ] Using testnet credentials for initial testing

---

## Testing Your Credentials

### Quick Test (1 minute)

```bash
# Set credentials
export PARADEX_API_SECRET="0x..."
export PARADEX_ACCOUNT_ADDRESS="0x..."

# Run test
python scripts/quick_test_paradex_auth.py
```

**Expected output:**
```
============================================================
PARADEX AUTHENTICATION TEST
============================================================

Account: 0x742d35Cc...f0bEb
Testing authentication...

Step 1: Getting JWT token...
✅ JWT token generated successfully!

Step 2: Testing API call...
✅ API call successful!

============================================================
🎉 AUTHENTICATION TEST PASSED!
============================================================
```

---

## Common Mistakes

### ❌ Using L2 Address Instead of L1

**Wrong:**
```bash
PARADEX_ACCOUNT_ADDRESS=0x3c9be2751ada989c9b23e229ef4d3f79108c1f5ad4078652356781abbe25c91
# This is an L2 Starknet address (longer)
```

**Correct:**
```bash
PARADEX_ACCOUNT_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
# This is your L1 Ethereum address (from MetaMask)
```

### ❌ Using Main Private Key Instead of Subkey

**Wrong:**
```bash
PARADEX_API_SECRET=<your-main-wallet-private-key>
# NEVER use your main wallet private key!
```

**Correct:**
```bash
PARADEX_API_SECRET=0x...  # Generated L2 subkey (safe for bots)
```

### ❌ Not Registering Subkey

**Error:** `401 Unauthorized`

**Solution:** Make sure you registered your L2 public key on Paradex website before testing.

---

## Security Best Practices

### ✅ DO

- **Use subkeys for bots** - Cannot withdraw funds
- **Generate new subkey for each bot** - Better security isolation
- **Store credentials in password manager** - 1Password, LastPass, etc.
- **Use different subkeys for testnet/mainnet** - Separate concerns
- **Rotate subkeys monthly** - Good security hygiene
- **Test on testnet first** - Always!

### ❌ DON'T

- **Never use main wallet private key** - Use subkeys!
- **Never commit credentials to git** - Add `.env` to `.gitignore`
- **Never share private keys** - Not even screenshots
- **Don't skip testnet testing** - Could lose real money
- **Don't use mainnet keys on testnet** - Keep them separate

---

## Testnet vs Mainnet

| | Testnet | Mainnet |
|---|---------|---------|
| **URL** | https://testnet.paradex.trade | https://paradex.trade |
| **Funds** | Free testnet USDC (faucet) | Real USDC (your money) |
| **Risk** | Zero | High |
| **Purpose** | Testing, development | Real trading |
| **Credentials** | Separate testnet subkey | Separate mainnet subkey |

**Recommendation:** Always test thoroughly on testnet before using mainnet!

---

## Getting Testnet Funds

1. Go to Paradex Discord: https://discord.gg/paradex
2. Find the #faucet channel
3. Request testnet USDC
4. Wait for approval (usually quick)
5. Check balance on https://testnet.paradex.trade

---

## Troubleshooting

### "401 Unauthorized"

**Possible causes:**
1. Subkey not registered on Paradex website
2. Wrong L1 address
3. Wrong L2 subkey

**Solutions:**
1. Log into Paradex → Account Settings → API Management
2. Verify your L2 public key is listed
3. Check L1 address matches your MetaMask address

### "Failed to initialize Paradex client"

**Cause:** Incorrect credential format

**Check:**
- L1 address is exactly 42 characters (including `0x`)
- L2 subkey is exactly 66 characters (including `0x`)
- Both start with `0x`

### "ModuleNotFoundError: No module named 'paradex_py'"

**Solution:**
```bash
pip install paradex-py>=0.4.6
```

---

## Quick Reference Card

```bash
# Your Credentials Template
# -------------------------

# L1 Ethereum Address (from MetaMask):
L1_ADDRESS=0x...  # 42 chars total

# L2 Subkey Private Key (generated):
L2_SUBKEY=0x...  # 66 chars total

# Configuration:
export PARADEX_API_SECRET="${L2_SUBKEY}"
export PARADEX_ACCOUNT_ADDRESS="${L1_ADDRESS}"

# Test:
python scripts/quick_test_paradex_auth.py
```

---

## Next Steps

Once credentials are configured:

1. ✅ Run quick auth test
2. ✅ Run full integration test
3. ✅ Connect via Hummingbot CLI
4. ✅ Start with small test trades
5. ✅ Monitor for 24 hours
6. ✅ Scale up gradually

---

## Support

**Questions about:**
- **Credentials:** This guide
- **Paradex platform:** https://discord.gg/paradex
- **Hummingbot:** https://discord.gg/hummingbot
- **Connector issues:** `PARADEX_TESTING_GUIDE.md`

---

**Last Updated:** 2025-11-13
**Connector Version:** 1.0.0

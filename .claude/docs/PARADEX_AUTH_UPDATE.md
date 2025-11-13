# Paradex Authentication Update - Critical Information

**Date:** 2025-11-13
**Status:** IMPORTANT - Authentication Parameters Clarified

---

## Critical Update: L1 vs L2 Addresses

### What Changed

After reviewing the official `paradex-py` SDK (v0.4.9) and Paradex API documentation, we've clarified the correct authentication parameters:

### Authentication Requirements

**For Subkey Authentication, you need:**

1. **L2 Subkey Private Key** (api_secret)
   - This is your Starknet L2 subkey private key
   - Format: `0x...` (64 hex characters)
   - Generated via Starknet key generation tools
   - **Cannot withdraw funds** (security feature)

2. **L1 Ethereum Address** (account_address)
   - This is your main account's **Ethereum L1 address**
   - **NOT the L2 Starknet address!**
   - Format: `0x...` (40 hex characters)
   - This is the Ethereum address you use to connect to Paradex website

---

## Why This Matters

The `paradex-py` SDK requires:
- `init_account(l1_address=..., l2_private_key=...)`
- The `l1_address` parameter expects an **Ethereum L1 address**, not a Starknet L2 address

### Common Confusion

❌ **WRONG:** Using your L2 Starknet address as account_address
✅ **CORRECT:** Using your L1 Ethereum address as account_address

---

## How to Find Your Addresses

### Finding Your L1 Ethereum Address

1. **From MetaMask:**
   - Open MetaMask
   - Your Ethereum address is shown at the top
   - Format: `0x...` (40 hex characters after 0x)
   - Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`

2. **From Paradex Website:**
   - Connect your wallet to https://paradex.trade or https://testnet.paradex.trade
   - The address shown when connecting is your L1 Ethereum address

### Finding Your L2 Subkey Private Key

1. **Generate a new L2 subkey:**
   ```python
   from starknet_py.net.signer.stark_curve_signer import KeyPair

   keypair = KeyPair.generate()
   print(f"L2 Private Key: {hex(keypair.private_key)}")
   print(f"L2 Public Key: {hex(keypair.public_key)}")
   ```

2. **Register the subkey:**
   - Go to Paradex website → Account Settings → API Management
   - Register the L2 public key
   - Use the L2 private key for Hummingbot

---

## Updated Configuration Prompts

When connecting to Paradex, you'll see:

```
> connect paradex_perpetual

Enter your Paradex subkey L2 private key (Starknet L2 private key, 0x...):
>>> 0x...  # Your L2 subkey private key

Enter your Paradex L1 account address (Ethereum L1 address, 0x...):
>>> 0x...  # Your Ethereum L1 address (from MetaMask)
```

---

## Technical Details

### SDK Implementation

```python
from paradex_py import Paradex

# Initialize Paradex client
client = Paradex(
    env="testnet",
    l2_private_key="0x...",  # L2 subkey private key
)

# Initialize account with L1 address
client.init_account(
    l1_address="0x...",      # L1 Ethereum address (REQUIRED!)
    l2_private_key="0x...",  # L2 subkey private key
)

# Get JWT token for authentication
auth_headers = client.account.auth_headers()
# Returns: {"Authorization": "Bearer <jwt_token>"}
```

### JWT Token Management

- **Expiry:** JWT tokens expire every **5 minutes** (not 1 hour!)
- **Refresh:** We automatically refresh tokens **1 minute before expiry**
- **Format:** `Bearer <jwt_token>` in Authorization header

---

## What We Fixed

### 1. Dockerfile
Added `paradex-py` to explicit pip install:
```dockerfile
RUN python3 -m pip install ... cairo-lang paradex-py
```

### 2. Auth Implementation
Fixed `paradex_perpetual_auth.py`:
- ✅ Correct SDK initialization with `Paradex` class
- ✅ Proper `init_account()` call with L1 address
- ✅ JWT token expiry set to 5 minutes (per Paradex docs)
- ✅ Token refresh 1 minute before expiry
- ✅ Synchronous `auth_headers()` call

### 3. Configuration Prompts
Updated `paradex_perpetual_utils.py`:
- ✅ Clarified "L2 private key" for api_secret
- ✅ Clarified "L1 Ethereum address" for account_address

---

## Testing Instructions

### Updated Quick Test

```bash
# Set your credentials (IMPORTANT: Use L1 Ethereum address!)
export PARADEX_API_SECRET="0x..."        # L2 subkey private key
export PARADEX_ACCOUNT_ADDRESS="0x..."   # L1 Ethereum address (from MetaMask)

# Run quick auth test
python scripts/quick_test_paradex_auth.py
```

### Expected Success Output

```
============================================================
PARADEX AUTHENTICATION TEST
============================================================

Account: 0x742d35Cc...f0bEb  # Your L1 Ethereum address
Testing authentication...

Step 1: Getting JWT token...
✅ JWT token generated successfully!
   Token preview: Bearer eyJ...

Step 2: Testing API call...
✅ API call successful!
   Account data received

============================================================
🎉 AUTHENTICATION TEST PASSED!
============================================================
```

### If You Get Errors

**Error:** "Failed to initialize Paradex client"
- Check that account_address is your **L1 Ethereum address** (not L2!)
- Check that api_secret is your **L2 subkey private key**

**Error:** "401 Unauthorized"
- Verify your L2 subkey is registered on Paradex website
- Make sure you registered the correct L2 public key

---

## Summary of Changes

| File | Change | Reason |
|------|--------|--------|
| `Dockerfile` | Added `paradex-py` to pip install | Ensure Docker has SDK |
| `paradex_perpetual_auth.py` | Fixed SDK initialization | Use correct `Paradex` class and `init_account()` |
| `paradex_perpetual_auth.py` | Updated JWT expiry to 5 min | Match Paradex docs |
| `paradex_perpetual_auth.py` | Added domain parameter | Support testnet/mainnet detection |
| `paradex_perpetual_utils.py` | Clarified L1/L2 in prompts | Prevent user confusion |
| `PARADEX_AUTH_UPDATE.md` | Created this document | Document changes |

---

## Next Steps

1. **Review your credentials:**
   - Confirm you have your L1 Ethereum address (from MetaMask)
   - Confirm you have your L2 subkey private key
   - Verify L2 subkey is registered on Paradex website

2. **Test authentication:**
   ```bash
   export PARADEX_API_SECRET="0x..."  # L2 private key
   export PARADEX_ACCOUNT_ADDRESS="0x..."  # L1 Ethereum address
   python scripts/quick_test_paradex_auth.py
   ```

3. **If test passes:**
   - Run full integration test
   - Connect via Hummingbot CLI
   - Start trading!

4. **If test fails:**
   - Double-check you're using L1 address (not L2)
   - Verify subkey is registered
   - Check error message for specific issue

---

## Questions?

- **What if I only have my L2 address?**
  - You need your L1 Ethereum address (the one you use to connect to Paradex website with MetaMask)

- **Can I use my L2 Starknet address instead?**
  - No, the SDK requires L1 Ethereum address for `init_account()`

- **Where do I find my L1 address?**
  - Open MetaMask → It's the address shown at the top
  - Or connect to Paradex website → It's the address shown when connecting

- **Do I need to generate a new subkey?**
  - Only if you don't already have one
  - If you have one registered on Paradex, use that

---

**Updated:** 2025-11-13 by Claude Code
**Verified against:** paradex-py v0.4.9, Paradex API Documentation

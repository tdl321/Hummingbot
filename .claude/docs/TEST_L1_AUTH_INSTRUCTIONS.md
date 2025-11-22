# Test L1 Authentication - Quick Guide

## 🎯 Goal
Test if your Ethereum wallet is now registered with Extended and can create subaccounts.

## ✅ Prerequisites

Before testing, make sure you've done ONE of these:

### Option A: Connected Wallet to Extended Web UI
```
1. ✅ Went to https://app.extended.exchange
2. ✅ Connected your wallet (MetaMask, etc.)
3. ✅ Can see your dashboard/balance
```

### Option B: Already Have Extended Account
```
1. ✅ Previously signed up for Extended
2. ✅ Know which wallet you used
3. ✅ Have that wallet's private key
```

## 🧪 Run the Test

### Method 1: Interactive Test
```bash
cd /Users/tdl321/hummingbot
python scripts/debug_l1_auth.py
```

When prompted:
1. Enter your Ethereum private key
2. Press Enter

### Method 2: Using Shell Script
```bash
cd /Users/tdl321/hummingbot
./scripts/quick_test_l1_auth.sh
```

## 📊 Understanding the Results

### ✅ SUCCESS (Wallet is registered):
```
✅ SUCCESS! L1 authentication worked!

   Your wallet IS registered with Extended.
   The SDK subaccount creation should work.

   Wallet address: 0xYOUR_ADDRESS
```

**Next step**: Run subaccount creation:
```bash
python scripts/run_extended_subaccount.py
```

### ❌ FAILED (Wallet not registered):
```
❌ FAILED: 401 Unauthorized

   Your Ethereum wallet (0xYOUR_ADDRESS)
   is NOT registered with Extended DEX!
```

**Next step**: Use Web UI method instead (see below)

### ⚠️  PARTIAL SUCCESS (Wrong wallet):
```
✅ Private key format is VALID
   → Derived address: 0xABC123...

❌ But this wallet is not registered
```

**Problem**: You're using a different wallet than the one registered with Extended.

**Solution**:
1. Find the correct wallet (check Extended web UI)
2. Or register this new wallet by connecting it to Extended

## 🔧 If Test Fails - Use Web UI Method

Don't waste time troubleshooting L1 auth. Just get API keys from the web:

### Step 1: Go to API Management
```
https://app.extended.exchange/api-management
```

### Step 2: Generate New API Key
1. Click "+ New API Key" or "Generate"
2. Give it a name: "Hummingbot Trading"
3. **IMMEDIATELY COPY** these values:
   - API Key (starts with `x10-`)
   - Stark Private Key (starts with `0x`)
   - Vault ID (number)

### Step 3: Update Hummingbot
```bash
cd /Users/tdl321/hummingbot
nano conf/connectors/extended_perpetual.yml
```

Replace:
```yaml
extended_perpetual_api_key: YOUR_NEW_X10_KEY_HERE
extended_perpetual_api_secret: YOUR_NEW_STARK_KEY_HERE
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 4: Test New Credentials
```bash
python scripts/test_extended_balance.py
```

Enter your new API key when prompted.

Expected:
```
✅ SUCCESS! Your credentials are working!
```

## 🎯 Decision Flow

```
Did L1 auth test succeed?
├─ YES → Run: python scripts/run_extended_subaccount.py
│         Create subaccount via SDK ✅
│
└─ NO  → Use Web UI method
          Get API keys from: https://app.extended.exchange/api-management
          Update Hummingbot config
          Skip SDK entirely ✅
```

## 💡 Why Web UI Method is Better

| Feature | SDK Method | Web UI Method |
|---------|------------|---------------|
| **Complexity** | High (L1 auth, wallet registration) | Low (just copy keys) |
| **Prerequisites** | Registered wallet, correct private key | Any Extended access |
| **Success rate** | 50% (wallet issues common) | 100% (always works) |
| **Time to complete** | 10-30 min (with troubleshooting) | 2 minutes |
| **What you get** | New subaccount + API keys | API keys for existing account |

## 🐛 Troubleshooting

### "Non-hexadecimal digit found"
**Problem**: Your private key format is wrong.

**Solutions**:
- Remove any spaces or extra characters
- Ensure it's 64 hex characters (or 66 with `0x`)
- Should only contain: 0-9, a-f, A-F
- Try adding `0x` prefix if missing

### "Account not found"
**Problem**: Wallet not registered with Extended.

**Solution**: Use web UI method (skip SDK)

### "Invalid signature"
**Problem**: Private key might be corrupted.

**Solution**: Re-export from wallet:
- MetaMask: Settings → Security → Reveal Private Key
- Copy fresh, try again

### Still Can't Get It Working?
**Just use the web UI method!** It's faster and always works:

```
1. https://app.extended.exchange/api-management
2. Generate API Key
3. Copy to Hummingbot
4. Done ✅
```

## 📝 Summary

### If You Have 5 Minutes
→ Use Web UI method (guaranteed to work)

### If You Want to Learn/Debug
→ Run L1 auth test (educational but optional)

### If Test Succeeds
→ Great! SDK will work, run subaccount script

### If Test Fails
→ No problem! Use web UI method instead

---

## 🚀 Quick Commands

```bash
# Test L1 auth
cd /Users/tdl321/hummingbot
python scripts/debug_l1_auth.py

# If succeeds, create subaccount
python scripts/run_extended_subaccount.py

# If fails, test API keys from web UI
python scripts/test_extended_balance.py

# Check current config
cat conf/connectors/extended_perpetual.yml | grep api
```

## ✅ Final Recommendation

**For fastest resolution of your 401 error:**

1. ✅ Go to https://app.extended.exchange/api-management
2. ✅ Generate fresh API key
3. ✅ Update Hummingbot config
4. ✅ Test with `test_extended_balance.py`
5. ✅ Start trading!

**Total time: 2-3 minutes**

No need to debug L1 auth, wallet registration, or SDK issues. Just get fresh keys and move on! 🎉

## ❓ Troubleshooting 401 Unauthorized Errors

If you are still getting `401 Unauthorized` errors even with fresh API keys, it might be due to copy-paste issues or format problems.

### 1. Check for Whitespace
Ensure there are no leading or trailing spaces in your API key or secret in the config file.

**Correct:**
```yaml
extended_perpetual_api_key: x10-abc...
extended_perpetual_api_secret: 0x123...
```

**Incorrect (spaces):**
```yaml
extended_perpetual_api_key: " x10-abc... "
```

### 2. Verify Private Key Format
The API secret (Stark private key) must be a hex string. It can optionally start with `0x`.
- Length: Typically 64 hex characters (or 66 with `0x`).
- Characters: 0-9, a-f, A-F.

### 3. Double Check Vault ID
Ensure the Vault ID matches the one associated with your API key in the Extended dashboard.
```

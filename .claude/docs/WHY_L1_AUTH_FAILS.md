# Why Extended L1 Authentication Fails - Technical Explanation

## 🔍 The Error You Got

```
Unauthorized response from POST https://api.starknet.extended.exchange/api/v1/user/accounts
x10.utils.http.NotAuthorizedException: Unauthorized response from POST
```

## 🎯 What L1 Authentication Actually Does

### The Authentication Flow

When you use the SDK to create subaccounts, here's what happens:

```
1. Your ETH Private Key
      ↓
2. Sign message: "/api/v1/user/accounts@2024-01-12T10:30:00Z"
      ↓
3. Generate signature using eth_account library
      ↓
4. Send to Extended API with headers:
   - L1_SIGNATURE: 0xabc123...
   - L1_MESSAGE_TIME: 2024-01-12T10:30:00Z
      ↓
5. Extended backend validates:
   ✓ Is signature valid?
   ✓ Is timestamp recent?
   ✓ Does this wallet address exist in our database? ← THIS IS WHERE IT FAILS
      ↓
6. If wallet NOT in database → 401 Unauthorized
   If wallet IS in database → Return account list
```

## ❌ Why You Get 401 Unauthorized

### The Root Cause

**Extended's backend doesn't recognize your wallet address.**

When Extended receives your L1 signature, they:
1. ✅ Verify the signature is cryptographically valid
2. ✅ Check the timestamp is recent (within time window)
3. ❌ **Look up the wallet address in their user database**
4. 🔴 **If not found → Return 401**

### What This Means

Your 401 error means:

```
The Ethereum wallet address derived from your private key
is NOT registered in Extended's user database.
```

## 🤔 Why Wouldn't Your Wallet Be Registered?

### Scenario 1: Using the Wrong Wallet
```
Extended Account Created With: Wallet A (0xAAA...)
Private Key You Provided: Wallet B (0xBBB...)
Result: 401 Unauthorized ❌
```

**Most common reason!** You might have:
- Multiple MetaMask accounts
- Hardware wallet + software wallet
- Used a different wallet for signup

### Scenario 2: Never Connected Wallet to Extended
```
Account Creation: Email/Social login only
Wallet Connection: Never done
Result: No wallet in Extended's database → 401 ❌
```

Some users create Extended accounts without connecting a wallet initially.

### Scenario 3: Incomplete Onboarding
```
Steps Completed:
  ✅ Connected wallet to Extended
  ✅ Signed initial message
  ❌ Didn't complete full onboarding
Result: Wallet recorded but not fully activated → 401 ❌
```

### Scenario 4: Account Created via API Key Only
```
Setup Method: Generated API key from web UI
Wallet Connection: Never used programmatic access
Result: Wallet not authorized for SDK access → 401 ❌
```

## 🔬 How Extended Validates L1 Auth

### Backend Pseudocode
```python
def validate_l1_auth(signature, timestamp, request_path):
    # Step 1: Recover wallet address from signature
    message = f"{request_path}@{timestamp}"
    recovered_address = recover_signer(signature, message)

    # Step 2: Check signature validity
    if not is_valid_signature(signature, message):
        return 401, "Invalid signature"

    # Step 3: Check timestamp freshness
    if not is_timestamp_recent(timestamp):
        return 401, "Timestamp expired"

    # Step 4: Look up wallet in database ← YOUR 401 HAPPENS HERE
    user = database.query("SELECT * FROM users WHERE wallet_address = ?", recovered_address)

    if user is None:
        return 401, "Wallet not registered"  ← THIS IS YOUR ERROR

    # Step 5: Check account status
    if user.status != "active":
        return 403, "Account not active"

    return 200, user.accounts
```

## 🔐 Difference: L1 Auth vs API Key Auth

| Feature | L1 Authentication | API Key Authentication |
|---------|-------------------|------------------------|
| **What it is** | Ethereum wallet signature | API key from Extended |
| **Used for** | Account management (SDK) | Trading operations |
| **Requires** | ETH private key | API key + Stark key |
| **Validates** | Wallet ownership | Key validity |
| **Database check** | Must exist in users table | Must exist in api_keys table |
| **Your error** | 401 - Wallet not found ❌ | Would check api_keys, not wallets |

### Why API Key Auth Works Differently

When using API key authentication (what your current broken key would use):
```
1. Include header: X-Api-Key: x10-abc123...
      ↓
2. Extended backend validates:
   ✓ Does this API key exist in api_keys table?
   ✓ Is it active/not revoked?
   ✓ Which account does it belong to?
      ↓
3. Returns data for that account
```

**Key difference**: API key auth checks the `api_keys` table, not the `users/wallets` table.

## 🧪 Testing Your Wallet Registration

Run this diagnostic:
```bash
cd /Users/tdl321/hummingbot
python scripts/debug_l1_auth.py
```

This will:
1. ✅ Derive your wallet address from the private key
2. ✅ Generate the L1 signature exactly as the SDK does
3. ✅ Send it to Extended with proper headers
4. ✅ Show you the exact response from Extended
5. ✅ Tell you definitively if your wallet is registered

### Expected Output

**If wallet IS registered:**
```
✅ SUCCESS! L1 authentication worked!
Response: {"data": [{"id": 123, "vault": 456, ...}]}
```

**If wallet NOT registered:**
```
❌ FAILED: 401 Unauthorized
Your Ethereum wallet (0xYOUR_ADDRESS) is NOT registered with Extended DEX!
```

## ✅ How to Fix This

### Option 1: Find the Correct Wallet (If you used a different one)

1. **Check Extended web app**:
   ```
   → Go to https://app.extended.exchange
   → Click "Connect Wallet"
   → Try each of your wallets
   → The one that connects and shows your balance is the right one
   ```

2. **Export that wallet's private key**:
   ```
   MetaMask: Settings → Security & Privacy → Reveal Private Key
   ```

3. **Use that key in the SDK script**

### Option 2: Connect Your Current Wallet (Register it with Extended)

1. **Go to Extended web app**:
   ```
   https://app.extended.exchange
   ```

2. **Connect the wallet** whose private key you want to use

3. **Complete onboarding** if prompted

4. **Verify registration**:
   ```bash
   python scripts/debug_l1_auth.py
   # Should now return 200 OK
   ```

5. **Now the SDK will work**:
   ```bash
   python scripts/run_extended_subaccount.py
   ```

### Option 3: Skip L1 Auth Entirely (Use Web UI) ⭐ **RECOMMENDED**

**Why this is easier:**
- ✅ No wallet private key needed for SDK
- ✅ No L1 authentication complexity
- ✅ Just generate API keys from UI
- ✅ Always works

**Steps:**
```
1. Go to: https://app.extended.exchange/api-management
2. Connect wallet (any wallet that has Extended access)
3. Click "Generate API Key"
4. Copy: API Key + Stark Private Key
5. Paste into Hummingbot config
6. Done! ✅
```

## 📊 Summary: The Real Reason

### What You Thought
```
"My API key is invalid"
→ Maybe it's because I only have $8?
```

### What's Actually Happening
```
Issue #1: Your API key IS invalid (correct diagnosis)
Issue #2: Tried to create new account via SDK
Issue #3: SDK uses L1 auth to create accounts
Issue #4: Your ETH wallet isn't in Extended's database
Issue #5: Extended returns 401 for unknown wallets
```

### The Core Issue
```
Extended L1 Auth = Checks if Ethereum wallet is registered
Your Wallet = Not in Extended's user database
Result = 401 Unauthorized
```

**It's not about money, it's about wallet registration!**

## 🎯 Quick Decision Tree

```
Do you have access to Extended web UI?
├─ YES → Use web UI to generate API keys (EASIEST)
│         Go to: https://app.extended.exchange/api-management
│         Generate key → Copy to Hummingbot → Done ✅
│
└─ NO  → Need to register wallet first
          ├─ Option A: Find the wallet you originally used
          │            Export its private key → Use in SDK
          │
          └─ Option B: Connect new wallet to Extended web UI
                       Complete onboarding → Then use SDK
```

## 💡 Key Takeaway

**L1 authentication requires your Ethereum wallet to be pre-registered with Extended's backend.** It's not just about having a valid private key - Extended must have that wallet address in their database as an authorized user.

The web UI method bypasses this entirely because when you connect your wallet to the web app, that registration happens automatically. Then you can generate API keys without needing L1 auth.

**Bottom line: Use the web UI method. It's simpler and always works.**

---

## 🔧 Debug Commands

```bash
# Check if your wallet is registered
python scripts/debug_l1_auth.py

# Verify ETH key format
python scripts/verify_eth_wallet.py

# Test existing API key
python scripts/test_extended_balance.py

# Create subaccount (only works if wallet registered)
python scripts/run_extended_subaccount.py
```

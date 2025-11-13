# L1 Wallet vs L2 Stark Key - The Relationship Explained

## 🎯 Your Question

> "What if my wallet that is connected is different from my Stark private key?"

**SHORT ANSWER:** They're SUPPOSED to be different keys, but they MUST be derived from the SAME L1 wallet!

---

## 🔑 Understanding the Two Key Types

### **L1 Ethereum Wallet**
- **What:** Your Ethereum private key (e.g., from MetaMask)
- **Used For:** Account management, authentication, signing into Extended
- **Example:** `0x1234abcd...` (your ETH private key)

### **L2 Stark Private Key**
- **What:** A Starknet cryptographic key derived FROM your L1 wallet
- **Used For:** Signing trading orders on Starknet L2
- **Example:** `0x5678efgh...` (different from L1 key)

**They are DIFFERENT keys by design!**

---

## 🔗 The Critical Relationship

```
L1 Ethereum Wallet (0xAAAA...)
        ↓
    [Derivation Process]
        ↓
L2 Stark Private Key (0xBBBB...)
        ↓
L2 Stark Public Key (0xCCCC...)
        ↓
    Vault ID (12345)
```

**IMPORTANT:** The L2 Stark key is **mathematically derived** from your L1 wallet!

### Derivation Formula (Simplified):
```python
# When you connect wallet to Extended UI:
l1_wallet = "0xYourEthereumPrivateKey"
account_index = 0  # Your first account

# Extended derives L2 key:
l2_stark_key = derive_stark_key(l1_wallet, account_index)

# This L2 key is unique to YOUR L1 wallet!
```

---

## ⚠️ The Problem Scenario

### **If You Have Different Wallets:**

```
UI Connected:
  L1 Wallet A (0xAAAA...)
      ↓
  L2 Stark Key A (0x1111...)  ← UI uses this
      ↓
  Vault A (12345)

SDK/Hummingbot:
  L1 Wallet B (0xBBBB...)  ← Different wallet!
      ↓
  L2 Stark Key B (0x2222...)  ← Different key!
      ↓
  Vault B (99999)  ← Different vault!
```

**Result:**
- ❌ L2 Stark Key B doesn't match your UI account
- ❌ Vault B doesn't exist or is empty
- ❌ You're trying to trade with wrong keys
- ❌ Extended rejects authentication

---

## 🔍 How to Check If They Match

### **Step 1: Find Your UI Wallet**
```
1. Go to https://app.extended.exchange
2. Look at connected wallet address (top right)
3. Copy it: 0xYOUR_UI_WALLET_ADDRESS
```

### **Step 2: Find Your SDK Wallet**
```bash
python scripts/compare_wallet_addresses.py
# Enter your private key
# It will show the derived address
```

### **Step 3: Compare**
```
UI Wallet:  0xAAAA...
SDK Wallet: 0xBBBB...

Same? ✅ Good - keys should work
Different? ❌ Problem - keys won't work
```

---

## 🎯 What Your Stark Private Key Should Be

### **For Your UI Account:**

Your correct Stark private key is the one that was generated when you FIRST connected your wallet to Extended UI.

**Where is it?**
- Go to: https://app.extended.exchange/api-management
- Your UI wallet is already connected
- The Stark Private Key shown there is the CORRECT one for YOUR account

**That's the key you should use in Hummingbot!**

---

## 💡 Why Different L1 Wallet = Wrong Stark Key

### **The Math:**
```
L1 Wallet A → generates → L2 Stark Key A (for Account A)
L1 Wallet B → generates → L2 Stark Key B (for Account B)

If you use Wallet B's Stark key with Account A → FAIL ❌
```

### **What Extended Checks:**
```python
# When you try to trade:
1. API Key → Which account? (Account A)
2. Stark signature on order
3. Does this Stark public key belong to Account A?
   → Checks: Is stark_public_key == Account A's registered key?
4. If NO → Reject order (wrong key!)
```

---

## ✅ The Correct Configuration

### **Scenario: You Can Trade in UI**

This means you have:
```
UI Account:
  ✅ L1 Wallet: 0xAAAA... (connected to UI)
  ✅ L2 Stark Key: 0x1111... (derived from wallet A)
  ✅ Vault ID: 12345
  ✅ Can trade ✅
```

**For Hummingbot to work, you need:**
```
Hummingbot Config:
  extended_perpetual_api_key: x10-your-key
  extended_perpetual_api_secret: 0x1111...  ← MUST be the L2 key from UI!
```

**If you use a different Stark key (from different L1 wallet):**
```
  extended_perpetual_api_secret: 0x2222...  ← From different wallet
  Result: Orders rejected, authentication fails ❌
```

---

## 🔧 How to Get the CORRECT Keys

### **Method 1: From UI API Management** ⭐ **RECOMMENDED**

```
1. Go to: https://app.extended.exchange/api-management
2. Your wallet is already connected (the correct one!)
3. Click "Generate API Key" or view existing keys
4. Copy EXACTLY:
   - API Key: x10-abc123...
   - Stark Private Key: 0x123abc...  ← This is the CORRECT L2 key!
   - Vault ID: 12345
5. Use these in Hummingbot
```

**Why this works:**
- UI already knows which L1 wallet you're using
- Shows you the L2 Stark key derived from YOUR wallet
- Guaranteed to match your account

### **Method 2: Derive from L1 Wallet (Advanced)**

If you want to use SDK:
```python
# You need the SAME L1 wallet that's connected to UI
l1_wallet = "0xAAAA..."  # Must match UI wallet!
account_index = 0

# SDK derives L2 key:
from x10.perpetual.user_client.onboarding import get_l2_keys_from_l1_account

l2_keys = get_l2_keys_from_l1_account(
    l1_account=Account.from_key(l1_wallet),
    account_index=account_index,
    signing_domain="extended.exchange"
)

print(f"L2 Private Key: {l2_keys.private_hex}")
# This WILL match the Stark key in UI (if same L1 wallet)
```

---

## 📊 Compatibility Matrix

| L1 Wallet Used | L2 Stark Key Derived | Works with UI Account? |
|----------------|----------------------|------------------------|
| Same as UI (0xAAAA...) | Key A (0x1111...) | ✅ YES |
| Different from UI (0xBBBB...) | Key B (0x2222...) | ❌ NO |

---

## 🎯 Your Specific Situation

### **If Wallets Are Different:**

```
UI Wallet:     0xAAAA... (your trading account)
    ↓
UI Stark Key:  0x1111... (correct key for this account)

SDK Wallet:    0xBBBB... (different wallet!)
    ↓
SDK Stark Key: 0x2222... (wrong key for UI account!)
```

**What happens:**
1. ❌ L1 authentication fails (wallet not recognized)
2. ❌ Even if you manually use Stark Key from UI, might have issues
3. ❌ API key + wrong Stark key = authentication mismatch

**Solution:**
Use the API key + Stark key from UI API Management (they're paired correctly).

---

## ✅ Summary

### **Key Relationships:**
```
1 L1 Wallet → 1 L2 Stark Key Pair → 1 Account → 1 Vault

If L1 wallet is different → Everything else is different → Won't work
```

### **What You Should Do:**

**Since you can trade in UI:**
```
1. ✅ Your UI has the correct L1 wallet connected
2. ✅ Go to API Management in that UI
3. ✅ Copy the Stark Private Key shown there
4. ✅ That's the CORRECT key for your account
5. ✅ Use it in Hummingbot
```

**Don't try to derive keys from a different L1 wallet** - they won't match your UI account!

---

## 🔍 Quick Test

Want to verify your keys match?

```bash
# Get the Stark public key from your private key
python -c "
import fast_stark_crypto
stark_private = 0x1234...  # Your Stark private key
stark_public = fast_stark_crypto.get_public_key(stark_private)
print(f'Stark Public Key: {hex(stark_public)}')
"

# Then compare with what's in Extended UI API Management
# They should match!
```

---

## 💡 Final Answer to Your Question

**Q:** "What if my wallet that is connected is different from my Stark private key?"

**A:** Then you're using the **wrong Stark private key!**

The Stark private key is derived from the L1 wallet. If they're from different wallets:
- ✅ Technically both are valid keys
- ❌ But only the Stark key from the UI wallet will work with your UI account
- ❌ Using a different Stark key = trying to use someone else's trading key

**Solution:** Get the Stark private key from Extended UI API Management - that's the correct one for your account.

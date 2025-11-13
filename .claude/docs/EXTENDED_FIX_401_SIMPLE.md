# Fix Extended 401 Error - Simple Method (Web UI)

## 🎯 The Problem
You're getting 401 Unauthorized errors because your API credentials are invalid.

## ✅ Simplest Solution: Use Extended Web UI

**Instead of creating subaccounts via SDK (which requires L1 auth), just use the web interface!**

## 🚀 Step-by-Step Instructions

### Step 1: Go to Extended API Management
```
https://app.extended.exchange/api-management
```

### Step 2: Connect Your Wallet
- Click "Connect Wallet"
- Use MetaMask or your preferred wallet
- Sign the connection request

### Step 3: Select or Create Subaccount
- You'll see your existing subaccounts (if any)
- Click "Create Subaccount" if you want a new one
- Or use an existing subaccount

### Step 4: Generate API Key
- Click "Generate API Key" or "+ New API Key"
- Give it a name (e.g., "Hummingbot Trading")
- **IMPORTANT**: Copy and save these values immediately:
  - **API Key** (starts with `x10-`)
  - **Stark Private Key** (starts with `0x`)
  - **Vault ID** (a number)

### Step 5: Update Hummingbot Config

#### Option A: Edit Config File
```bash
cd /Users/tdl321/hummingbot
nano conf/connectors/extended_perpetual.yml
```

Update these fields:
```yaml
extended_perpetual_api_key: x10-YOUR-NEW-KEY-HERE
extended_perpetual_api_secret: 0xYOUR-STARK-PRIVATE-KEY-HERE
```

#### Option B: Use Hummingbot CLI
```
1. Start Hummingbot
2. Run: config extended_perpetual_api_key
3. Enter new API key
4. Run: config extended_perpetual_api_secret
5. Enter new Stark private key
```

### Step 6: Test Your Credentials
```bash
cd /Users/tdl321/hummingbot
python scripts/test_extended_balance.py
```

Enter your new API key when prompted.

Expected output:
```
✅ SUCCESS! Your credentials are working!
```

## 🔍 Why The SDK Method Failed

The error you got:
```
Unauthorized response from POST https://api.starknet.extended.exchange/api/v1/user/accounts
```

This means:
1. ❌ The Ethereum wallet you used isn't registered with Extended
2. ❌ Or the wallet needs to be connected through the web UI first
3. ❌ Or there's a mismatch between the wallet and the account

**The web UI method bypasses all of this!** You just connect your wallet and generate keys directly.

## 📊 Comparison: SDK vs Web UI

| Method | Pros | Cons |
|--------|------|------|
| **SDK** | Scriptable, automated | Requires L1 wallet auth, can fail |
| **Web UI** ✅ | Always works, visual interface | Manual process |

## ⚠️ Important Security Notes

When you generate API keys from the web UI:
- **API Key** = Public identifier (like username)
- **Stark Private Key** = Secret for signing orders (like password)
- **NEVER share your Stark Private Key!**
- Save these in a secure password manager

## 🐛 Still Getting 401 After This?

If you still get 401 errors after using web UI keys:

### 1. Verify you copied the keys correctly
```bash
# Check what's in your config
cat conf/connectors/extended_perpetual.yml | grep api
```

### 2. Make sure keys aren't encrypted wrong
The config should show encrypted values (long hex strings), not plaintext.

### 3. Test with the raw API
```bash
cd /Users/tdl321/hummingbot
python scripts/test_extended_balance.py
```

If test script works but Hummingbot doesn't:
- ✅ Keys are valid
- ❌ Problem is in Hummingbot's key storage/decryption

### 4. Clear and reconfigure
```bash
# Backup current config
cp conf/connectors/extended_perpetual.yml conf/connectors/extended_perpetual.yml.backup

# Remove the config
rm conf/connectors/extended_perpetual.yml

# Start Hummingbot and reconfigure from scratch
```

## 💡 Pro Tips

1. **Create multiple API keys**: One for testing, one for production
2. **Use descriptive names**: "Hummingbot - Mainnet - Trading"
3. **Rotate keys regularly**: Generate new keys every few months
4. **Test before deleting old keys**: Make sure new keys work first

## ✅ Success Checklist

- [ ] Connected wallet to https://app.extended.exchange/api-management
- [ ] Generated new API key from web UI
- [ ] Copied API Key (x10-...)
- [ ] Copied Stark Private Key (0x...)
- [ ] Noted Vault ID
- [ ] Updated Hummingbot config
- [ ] Tested with `test_extended_balance.py`
- [ ] No more 401 errors! 🎉

## 🎯 Quick Reference

**Extended Links:**
- Web App: https://app.extended.exchange
- API Management: https://app.extended.exchange/api-management
- Docs: https://api.docs.extended.exchange
- Discord: https://discord.gg/extended

**Your Issue:**
- Error: 401 Unauthorized
- Root Cause: Invalid/corrupted API credentials
- Solution: Generate fresh keys from web UI
- Time to Fix: ~5 minutes

---

**Need more help?** Run the diagnostic:
```bash
python scripts/verify_eth_wallet.py
```

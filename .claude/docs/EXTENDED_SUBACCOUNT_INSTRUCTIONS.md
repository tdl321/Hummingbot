# Extended DEX Subaccount Creation Instructions

## 🎯 Goal
Create a new Extended DEX subaccount with fresh API credentials to fix your 401 authentication error.

## 📋 What You'll Get
- ✅ New subaccount on Extended DEX
- ✅ Fresh API key
- ✅ Stark L2 keys for order signing
- ✅ Vault ID
- ✅ All credentials ready for Hummingbot

## 🚀 How to Run

### Option 1: Interactive Script (Recommended)
```bash
cd /Users/tdl321/hummingbot
python scripts/run_extended_subaccount.py
```

When prompted:
1. **Enter your Ethereum private key** - This is the L1 wallet that owns your Extended account
2. **Enter account index** - Press Enter to use auto-suggested index, or type a number (1, 2, 3, etc.)

### Option 2: Command Line with Environment Variable
```bash
cd /Users/tdl321/hummingbot
export ETH_PRIVATE_KEY='0x1234...your ethereum private key here...'
python scripts/create_extended_subaccount_simple.py
```

### Option 3: Edit and Run Simple Script
1. Open `scripts/create_extended_subaccount_simple.py`
2. Find line 108: `ETH_PRIVATE_KEY = os.environ.get('ETH_PRIVATE_KEY', '')`
3. Change to: `ETH_PRIVATE_KEY = '0x1234...your key...'`
4. Save and run: `python scripts/create_extended_subaccount_simple.py`

## 🔑 Finding Your Ethereum Private Key

Your Ethereum private key is from the wallet you used to:
- Sign up for Extended DEX
- Connect to Extended's web app
- Make deposits to Extended

**Where to find it:**
- **MetaMask**: Settings → Security & Privacy → Reveal Private Key
- **Other wallets**: Check your wallet's export/backup feature

**Security Note**: Your ETH private key is only used locally to sign authentication messages. It's never transmitted anywhere except to Extended's authentication endpoints.

## 📊 Expected Output

The script will display:
```
================================================================
✅ SUCCESS! Your Extended DEX Credentials
================================================================

📝 Copy these to your Hummingbot configuration:

   extended_perpetual_api_key: x10-abc123def456...
   extended_perpetual_api_secret: 0x789abc...

📊 Account Details:
   - Account Index: 1
   - Account ID: 12345
   - Vault ID: 67890
   - L2 Public Key: 0xabc...

================================================================
```

Credentials are also saved to: `extended_credentials_account_1.txt`

## 🔧 Using the New Credentials in Hummingbot

### Method 1: Update Config File Directly
```bash
# Edit the Extended config
nano conf/connectors/extended_perpetual.yml

# Or use vi
vi conf/connectors/extended_perpetual.yml
```

Replace the old values with your new:
- `extended_perpetual_api_key: <your new api key>`
- `extended_perpetual_api_secret: <your new stark private key>`

### Method 2: Reconfigure in Hummingbot CLI
```
1. Start Hummingbot
2. Run: config extended_perpetual_api_key
3. Enter new API key
4. Run: config extended_perpetual_api_secret
5. Enter new Stark private key (api_secret)
```

## ✅ Verify It Works

After updating credentials:
```bash
cd /Users/tdl321/hummingbot
python scripts/test_extended_balance.py
```

You should see your balance without 401 errors!

## 🐛 Troubleshooting

### Error: "No accounts found"
**Solution**: You need to onboard first. Use the interactive script (Option 1) and it will handle onboarding.

### Error: "Subaccount already exists"
**Solution**: The script will automatically use the existing subaccount and just create a new API key.

### Error: "Invalid private key"
**Solution**: Make sure your ETH private key:
- Is from the wallet connected to Extended
- Starts with `0x` (or the script adds it automatically)
- Is 64 characters long (66 with `0x` prefix)

### Still Getting 401 Errors After Update
**Solution**:
1. Verify you copied the NEW credentials (not old ones)
2. Restart Hummingbot completely
3. Check the credentials are decrypted properly
4. Try the balance test script

## 💡 Why This Fixes Your 401 Error

Your current API key is invalid/corrupted, causing 401 Unauthorized errors. Creating a fresh subaccount with a new API key gives you:
- ✅ Valid API credentials
- ✅ Clean authentication state
- ✅ No legacy/corrupted keys

The $8 balance has nothing to do with 401 errors - those are purely authentication issues.

## 📞 Need Help?

If you run into issues:
1. Check that your ETH wallet has access to Extended DEX
2. Verify you're using mainnet (not testnet)
3. Make sure you have internet connection
4. Check Extended DEX status: https://status.extended.exchange

## 🎉 Success Checklist

- [ ] Run subaccount creation script
- [ ] Copy new `extended_perpetual_api_key`
- [ ] Copy new `extended_perpetual_api_secret`
- [ ] Update Hummingbot config
- [ ] Restart Hummingbot
- [ ] Test balance fetch (should see no 401 errors)
- [ ] Ready to trade! 🚀

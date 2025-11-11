# How to Run Debug Tests

The debug scripts have been created and are ready to run. They require your Hummingbot password interactively.

---

## Prerequisites

✅ Password verification file exists: `/Users/tdl321/hummingbot/conf/.password_verification`
✅ Extended config exists: `/Users/tdl321/hummingbot/conf/connectors/extended_perpetual.yml`
✅ All dependencies installed (including `aioprocessing`)

---

## Test Sequence

### Test 1: Config Decryption (START HERE)

**Purpose**: See what API credentials are actually stored in your encrypted config

**Command**:
```bash
cd /Users/tdl321/hummingbot
python debug_config_decryption.py
```

**What it will do**:
1. Read your encrypted config file
2. Ask for your Hummingbot password
3. Decrypt the API key and secret
4. Compare with known valid credentials
5. Tell you if the config has the wrong keys

**Expected outcomes**:
- ✅ **Credentials match** → Config is correct, issue is elsewhere
- ❌ **Credentials don't match** → Config has wrong API key (proceed to fix script)

**Important**: Have your Hummingbot password ready!

---

### Test 2: Encryption Round-Trip (Optional)

**Purpose**: Verify Hummingbot's encryption system works correctly

**Command**:
```bash
python test_encryption_roundtrip.py
```

**What it will do**:
1. Ask for your Hummingbot password
2. Test encrypting and decrypting various values
3. Verify round-trip preserves exact values
4. Test with Extended API credentials

**Expected outcome**:
- ✅ All tests pass → Encryption system is working
- ❌ Tests fail → Potential encryption issue

---

### Test 3: Connector Initialization (If needed)

**Purpose**: Trace how credentials flow from config to connector to API

**Command**:
```bash
python debug_connector_init.py
```

**What it will do**:
1. Login to Security system with your password
2. Decrypt Extended config
3. Initialize connector
4. Test header generation
5. Make actual API call
6. Show where authentication fails

**Run this if**:
- Config has correct credentials but still getting 401
- Need to trace exact flow of credential usage

---

## Quick Start Guide

### Scenario A: Don't know if config is correct

```bash
# Step 1: Check what's in the config
python debug_config_decryption.py
# Enter your password when prompted

# If output shows "❌ MISMATCH":
python fix_extended_config.py
# Enter password, confirm to proceed

# Step 2: Validate in Docker
python validate_extended_docker.py
# Enter container name when prompted
```

---

### Scenario B: Want comprehensive diagnostics

```bash
# Run all three tests in sequence:

# 1. Check encryption system
python test_encryption_roundtrip.py

# 2. Check config contents
python debug_config_decryption.py

# 3. Trace connector flow
python debug_connector_init.py
```

---

## Common Issues

### "ModuleNotFoundError: No module named 'aioprocessing'"

**Fix**:
```bash
pip install aioprocessing
```

### "Invalid password"

**Causes**:
1. Wrong password entered
2. Password file corrupted
3. Using different password than when config was created

**Try**:
- Double-check password (it's case-sensitive)
- Try password variants
- If all fail, may need to recreate configs

### "Config file does not exist"

**Fix**:
You need to create the config first:
```bash
# In Docker:
docker exec -it <container> bash
bin/hummingbot.py
# Then: connect extended_perpetual
```

---

## Understanding the Output

### debug_config_decryption.py Output

**Good output (credentials match)**:
```
✅ CONCLUSION: Encrypted config contains CORRECT credentials!

   The 401 errors are NOT due to wrong credentials in config.

   Next step: Run debug_connector_init.py to trace credential flow
```

**Bad output (credentials don't match)**:
```
❌ CONCLUSION: Encrypted config has WRONG API KEY!

   Stored in config: abc123...xyz789
   Valid key:        f4aa1ba3...2a1c57

   This explains the 401 Unauthorized errors!

   SOLUTION: Update the config with correct credentials
   Run: python fix_extended_config.py
```

---

### test_encryption_roundtrip.py Output

**Good output**:
```
Test Summary
Tests passed: 7/7

Results:
  ✅ PASS - Simple ASCII
  ✅ PASS - Extended API Key
  ✅ PASS - Extended API Secret
  ✅ PASS - Long hex string
  ✅ PASS - Special chars
  ✅ PASS - Empty string
  ✅ PASS - Unicode

✅ ALL TESTS PASSED!
   Hummingbot's encryption/decryption system is working correctly.
```

---

### debug_connector_init.py Output

**Good flow**:
```
STEP 1: Security System Login
✅ Password validated
✅ Security system logged in

STEP 2: Retrieving Decrypted Config
✅ Extended perpetual config found
  extended_perpetual_api_key: f4aa1ba3...2a1c57
  extended_perpetual_api_secret: 0x17d34f...89c0c2e1

STEP 3: Validating Against Known Credentials
  API Key Match: ✅ YES
  API Secret Match: ✅ YES

STEP 4: Initializing Connector
✅ Connector created successfully
✅ Authenticator exists

STEP 5: Testing Auth Header Generation
✅ X-Api-Key header present: f4aa1ba3...2a1c57
✅ Header matches stored API key
✅ Header matches known valid API key

STEP 6: Testing Actual API Call
✅ API call successful!
Balance data:
  Balance: 7.989998
  Equity: 7.989998
  Available: 7.989998
```

**Bad flow (shows where it breaks)**:
```
STEP 6: Testing Actual API Call

❌ API call failed: Error executing request GET
   https://api.starknet.extended.exchange/api/v1/user/balance.
   HTTP status is 401. Error:

🔍 401 UNAUTHORIZED ERROR DETECTED!

This means:
  1. Headers were sent correctly
  2. But the API key is rejected by Extended API

Possible causes:
  a) API key in config is wrong/expired
  b) API key is for wrong environment (testnet vs mainnet)
  c) API key belongs to different sub-account
```

---

## Next Steps Based on Results

### If config has wrong credentials:
```bash
# 1. Fix the config
python fix_extended_config.py

# 2. Copy to Docker
docker cp conf/connectors/extended_perpetual.yml <container>:/conf/connectors/

# 3. Restart Docker
docker restart <container>

# 4. Validate
python validate_extended_docker.py
```

### If config has correct credentials but still 401:
- API key may be revoked/expired on Extended's side
- Environment mismatch (testnet key on mainnet)
- Sub-account mismatch
- Regenerate API key from Extended UI

### If encryption tests fail:
- Password file may be corrupted
- May need to backup configs and recreate from scratch
- Check if `.password_verification` file is intact

---

## Tips for Success

1. **Have password ready** before running scripts
2. **Run tests in order** (config check → fix → validate)
3. **Save output** to files for reference:
   ```bash
   python debug_config_decryption.py > debug_output.txt 2>&1
   ```
4. **Take your time** - read the output carefully
5. **Backup configs** before making changes

---

## Support Commands

### Check if config exists:
```bash
ls -la conf/connectors/extended_perpetual.yml
```

### Check password file:
```bash
ls -la conf/.password_verification
```

### View raw encrypted config:
```bash
head -20 conf/connectors/extended_perpetual.yml
```

### Check Docker container:
```bash
docker ps
```

### View Docker logs:
```bash
docker exec <container> tail -100 /logs/logs_hummingbot.log | grep -i "extended\|401"
```

---

**Ready to start?** Run the first test:

```bash
cd /Users/tdl321/hummingbot
python debug_config_decryption.py
```

Good luck! 🚀

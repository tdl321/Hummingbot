# Extended Connector Debug Tools

This directory contains comprehensive debugging tools for diagnosing and fixing Extended connector authentication issues in Hummingbot.

---

## Problem Overview

**Symptom**: Extended connector gets 401 Unauthorized errors in Docker

**Root Cause**: Encrypted configuration contains wrong/expired API credentials

**Solution**: Use these tools to diagnose and fix the issue

---

## Debugging Tools

### 1. `debug_config_decryption.py` - Config Decryption Inspector

**Purpose**: Decrypt and display what API credentials are actually stored in the encrypted config

**What it does**:
- Reads `/conf/connectors/extended_perpetual.yml`
- Decrypts API key and secret using your password
- Compares with known valid credentials
- Shows exactly what's causing 401 errors

**Usage**:
```bash
python debug_config_decryption.py
# Enter your Hummingbot password when prompted
```

**Expected Output**:
- ✅ If credentials match → Config is correct, issue is elsewhere
- ❌ If credentials don't match → Config needs updating

---

### 2. `debug_connector_init.py` - Connector Initialization Tracer

**Purpose**: Trace how the connector receives and uses credentials from the Security system

**What it does**:
- Logs into Hummingbot Security system
- Retrieves decrypted config
- Initializes Extended connector
- Tests header generation
- Makes actual API call
- Shows exact flow from config → connector → API

**Usage**:
```bash
python debug_connector_init.py
# Enter your Hummingbot password when prompted
```

**Expected Output**:
- Shows decrypted credentials at each step
- Verifies authentication headers
- Tests actual API call
- Identifies where in the flow things break

---

### 3. `test_encryption_roundtrip.py` - Encryption System Validator

**Purpose**: Verify Hummingbot's encryption/decryption system works correctly

**What it does**:
- Tests encrypt → decrypt round-trip on various values
- Includes Extended API key and secret
- Validates encryption preserves exact values
- Ensures no corruption or encoding issues

**Usage**:
```bash
python test_encryption_roundtrip.py
# Enter your Hummingbot password when prompted
```

**Expected Output**:
- ✅ All tests pass → Encryption system is working
- ❌ Tests fail → Potential encryption/password issue

---

### 4. `fix_extended_config.py` - Config Update Tool

**Purpose**: Update encrypted config with correct API credentials

**What it does**:
- Creates backup of current config
- Encrypts correct credentials with your password
- Updates config file safely
- Verifies the update worked

**Safety Features**:
- Creates timestamped backup before changes
- Verifies decryption after update
- Rolls back if anything fails

**Usage**:
```bash
python fix_extended_config.py
# Enter your Hummingbot password when prompted
# Confirm when prompted to proceed
```

**Expected Output**:
- ✅ Config updated and verified
- Backup saved to `extended_perpetual_backup_YYYYMMDD_HHMMSS.yml`

**After running**:
If running Docker, copy updated config:
```bash
docker cp conf/connectors/extended_perpetual.yml <container>:/conf/connectors/
```

---

### 5. `validate_extended_docker.py` - Docker Validation Tool

**Purpose**: End-to-end validation of Extended connector in Docker

**What it does**:
- Checks if Docker container is running
- Verifies config file exists in container
- Analyzes recent logs for 401 errors
- Tests API key encryption format
- Provides actionable recommendations

**Usage**:
```bash
python validate_extended_docker.py
# Enter your Docker container name when prompted
```

**Expected Output**:
- Checklist of validation steps
- 401 error count from recent logs
- Recommendations for fixing issues

---

## Diagnostic Workflow

### Step 1: Identify the Problem

Run the decryption inspector:
```bash
python debug_config_decryption.py
```

**If credentials DON'T match**: Proceed to Step 2
**If credentials DO match**: Proceed to Step 3

### Step 2: Fix Config (If Needed)

Update config with correct credentials:
```bash
python fix_extended_config.py
```

If running in Docker:
```bash
# Copy updated config to Docker
docker cp conf/connectors/extended_perpetual.yml <container>:/conf/connectors/

# Restart Hummingbot
docker restart <container>
```

### Step 3: Trace Connector Flow

If config is correct but still getting 401:
```bash
python debug_connector_init.py
```

This shows where in the credential flow things break.

### Step 4: Validate in Docker

After fixes, verify in Docker:
```bash
python validate_extended_docker.py
```

Check logs for no more 401 errors.

### Step 5: Test Encryption System (If Needed)

If seeing weird decryption issues:
```bash
python test_encryption_roundtrip.py
```

---

## Common Scenarios

### Scenario 1: Wrong API Key in Config

**Symptoms**:
- 401 errors in Docker logs
- Password validates successfully

**Diagnosis**:
```bash
python debug_config_decryption.py
```
Shows: "❌ MISMATCH - API key in config is WRONG!"

**Fix**:
```bash
python fix_extended_config.py
```

---

### Scenario 2: Testnet vs Mainnet Mismatch

**Symptoms**:
- API key works in direct tests
- But fails in connector

**Diagnosis**:
- Config has testnet credentials
- Connector configured for mainnet (or vice versa)

**Fix**:
- Update config with correct environment credentials
- Or change connector domain setting

---

### Scenario 3: Sub-Account Mismatch

**Symptoms**:
- API key and secret both correct
- Still getting 401 errors

**Diagnosis**:
- API key from one sub-account
- Stark key from different sub-account

**Fix**:
- Regenerate both from same Extended sub-account
- Update config with matching pair

---

### Scenario 4: Encryption System Issue

**Symptoms**:
- MAC mismatch errors
- Password validation fails
- Decryption produces garbage

**Diagnosis**:
```bash
python test_encryption_roundtrip.py
```
Shows failures in round-trip tests

**Fix**:
- Password file may be corrupted
- May need to recreate configs from scratch

---

## Known Valid Credentials

For reference during debugging:

```
API Key (mainnet): f4aa1ba3e3038adf522981a90d2a1c57
API Secret (Stark): 0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1
```

These have been verified to work:
- ✅ Direct API test (200 OK)
- ✅ Connector test (200 OK)
- ✅ Balance fetch (7.989998 USD)

---

## Hummingbot Encryption System

### How It Works

1. **Encryption** (`config_crypt.py`):
   - AES-128-CTR cipher
   - PBKDF2 key derivation (1M iterations)
   - Values stored as hex-encoded JSON

2. **Password Verification** (`.password_verification`):
   - Encrypts word "HummingBot" with password
   - Validates password by decrypting and comparing

3. **Config Loading**:
   - `Security.login()` decrypts all configs
   - Fields marked `is_secure: true` are auto-decrypted
   - Decrypted values passed to connector constructor

### Config Structure

```yaml
connector: extended_perpetual

extended_perpetual_api_key: 7b2263727970746f223a207b22636970686572...
# This is hex-encoded encrypted JSON:
# {
#   "crypto": {
#     "cipher": "aes-128-ctr",
#     "ciphertext": "...",
#     "kdf": "pbkdf2",
#     "kdfparams": {...},
#     "mac": "..."
#   },
#   "version": 3,
#   "alias": ""
# }

extended_perpetual_api_secret: 7b2263727970746f223a207b22636970686572...
# Same structure for secret
```

---

## Troubleshooting Tips

### "Invalid password" Error

**Cause**: Password doesn't match the one used to encrypt configs

**Solutions**:
1. Try different password variants (caps, spaces, etc.)
2. Check if `.password_verification` file is correct
3. May need to recreate configs with `connect` command

### "MAC mismatch" Error

**Cause**: Encrypted data corrupted or wrong password

**Solutions**:
1. Verify password is correct
2. Restore from backup if available
3. Recreate config from scratch

### Config Exists But Empty Values

**Cause**: Decryption failing silently

**Solutions**:
1. Check password is correct
2. Verify config file isn't manually edited
3. Look for corruption in hex values

### 401 After Fixing Config

**Cause**: Docker still using old config or not restarted

**Solutions**:
1. Ensure config copied to Docker container
2. Restart Docker container
3. Verify restart picked up new config

---

## Files Reference

### Created Diagnostic Tools
- `debug_config_decryption.py` - Config decryption inspector
- `debug_connector_init.py` - Connector initialization tracer
- `test_encryption_roundtrip.py` - Encryption system validator
- `fix_extended_config.py` - Config update tool
- `validate_extended_docker.py` - Docker validation tool

### Existing Test Tools (Previous Work)
- `test_extended_api_key.py` - Direct API key validation
- `test_extended_auth.py` - Connector authentication test
- `test_extended_headers.py` - Header generation test

### Documentation
- `CONNECTOR_AUTH_FIXES.md` - Authentication fixes summary
- `EXTENDED_AUTH_DEBUG_RESULTS.md` - Debug results and findings
- `DEBUG_TOOLS_README.md` - This file

---

## Support

If you're still experiencing issues after using these tools:

1. **Collect diagnostic output**:
   ```bash
   python debug_config_decryption.py > decryption_output.txt 2>&1
   python debug_connector_init.py > connector_output.txt 2>&1
   python validate_extended_docker.py > docker_output.txt 2>&1
   ```

2. **Check Extended API status**:
   - Visit: https://api.starknet.extended.exchange/api/v1/info/health
   - Verify API is operational

3. **Regenerate credentials**:
   - Extended mainnet: https://app.extended.exchange/perp
   - Generate new API key + Stark key
   - Update config with new credentials

4. **Review Hummingbot logs**:
   ```bash
   tail -f logs/logs_hummingbot.log
   # or in Docker:
   docker exec <container> tail -f /logs/logs_hummingbot.log
   ```

---

## Additional Notes

### Why Direct Tests Work But Docker Fails

The diagnostic tests confirmed:
- API key is valid (works in direct HTTP test)
- Connector code is correct (works in local test)
- Headers are generated correctly (verified)

**But Docker gets 401 errors because**:
- Docker uses encrypted config file
- Encrypted config contains different (wrong) credentials
- When decrypted with password, wrong values passed to connector

### Solution is Simple

Update the encrypted config with correct credentials:
1. Run `fix_extended_config.py`
2. Copy to Docker
3. Restart

---

**Last Updated**: 2025-11-11
**Status**: All tools created and ready for use

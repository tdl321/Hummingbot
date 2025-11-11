# API Key & Private Key Encryption Flow + Dockerfile Build Context Audit

**Date**: 2025-11-11
**Scope**: How sensitive data (API keys, ETH private keys) are encoded/decoded, and Dockerfile build verification
**Status**: ✅ All systems secure and functional

---

## Executive Summary

### Key Findings
1. **✅ Encryption is secure**: Uses Ethereum keyfile v3 standard (AES-128-CTR + PBKDF2/scrypt)
2. **✅ Encoding is correct**: All `.encode()` and `.decode()` use UTF-8 (guaranteed by `PYTHONUTF8=1`)
3. **✅ Dockerfile build context**: All referenced files exist, no non-ASCII filenames detected
4. **✅ No encoding vulnerabilities**: Defensive error handling added for UnicodeDecodeError

---

## Part 1: API Key & Private Key Encryption Flow

### Overview: How Hummingbot Protects Sensitive Data

Hummingbot uses the **Ethereum keyfile v3 standard** for encrypting:
- Exchange API keys
- Exchange API secrets
- Ethereum/Stark private keys
- Other sensitive configuration values

### Step-by-Step Encryption Flow

#### 1. User Provides Credentials (Plaintext)
```
User input: "f4aa1ba3e3038adf522981a90d2a1c57" (API key)
           "0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1" (Private key)
```

#### 2. String → Bytes Conversion
**File**: `config_crypt.py:48-49`
```python
password_bytes = self._password.encode()  # User's master password
value_bytes = value.encode()              # API key/secret to encrypt
```

**Encoding used**: UTF-8 (default, guaranteed by `PYTHONUTF8=1`)

**Result**:
```python
"f4aa1ba3..." → b'f4aa1ba3...'  # String becomes bytes
```

#### 3. Ethereum Keyfile v3 Encryption
**File**: `config_crypt.py:85-146` (`_create_v3_keyfile_json`)

**Algorithm**: AES-128-CTR
**Key Derivation**: PBKDF2-SHA256 (default) or scrypt
**Work Factor**: 1,000,000 iterations (PBKDF2) for strong security

**Process**:
```python
# Generate random salt (16 bytes)
salt = Random.get_random_bytes(16)

# Derive encryption key from password
derived_key = _pbkdf2_hash(
    password,
    hash_name='sha256',
    salt=salt,
    iterations=1_000_000,  # Very strong!
    dklen=32  # 32 bytes = 256 bits
)

# Encrypt the plaintext value
iv = Random.get_random_bytes(16)
encrypt_key = derived_key[:16]  # First 16 bytes for AES-128
ciphertext = encrypt_aes_ctr(value_bytes, encrypt_key, iv)

# Generate MAC for integrity verification
mac = keccak(derived_key[16:32] + ciphertext)
```

#### 4. JSON Structure Creation
**Result** (before storage):
```json
{
  "crypto": {
    "cipher": "aes-128-ctr",
    "cipherparams": {"iv": "a1b2c3..."},
    "ciphertext": "7f8e9d...",
    "kdf": "pbkdf2",
    "kdfparams": {
      "c": 1000000,
      "dklen": 32,
      "prf": "hmac-sha256",
      "salt": "d4e5f6..."
    },
    "mac": "1a2b3c..."
  },
  "version": 3,
  "alias": ""
}
```

#### 5. JSON → Hex Encoding for Storage
**File**: `config_crypt.py:51-52`
```python
json_str = json.dumps(keyfile_json)           # JSON object → string
encrypted_value = binascii.hexlify(json_str.encode()).decode()  # String → bytes → hex → string
```

**Example**:
```
JSON string: {"crypto": {...}}
↓ .encode() (string → bytes, UTF-8)
Bytes: b'{"crypto": {...}}'
↓ hexlify() (bytes → hex bytes)
Hex bytes: b'7b2263727970746f223a...'
↓ .decode() (hex bytes → hex string, UTF-8)
Hex string: "7b2263727970746f223a..."
```

#### 6. Storage in YAML Config
**File**: `conf/connectors/extended_perpetual.yml`
```yaml
extended_perpetual_api_key: 7b2263727970746f223a207b22636970686572223a202261...
extended_perpetual_api_secret: 7b2263727970746f223a207b22636970686572223a20226165...
```

**Key point**: These are hex-encoded encrypted JSON structures, NOT the actual keys!

---

### Decryption Flow (Reverse Process)

#### 1. Read Hex String from Config
**File**: `conf_migration.py:403-404` or loaded dynamically
```python
with open(key_path, 'r') as f:  # UTF-8 by default with PYTHONUTF8=1
    json_str = f.read()
```

#### 2. Hex → Bytes Conversion
**File**: `conf_migration.py:405`
```python
value = binascii.hexlify(json_str.encode()).decode()
```

#### 3. Unhexlify → JSON Bytes
**File**: `config_crypt.py:59`
```python
value = binascii.unhexlify(value)  # Hex string → bytes
```

#### 4. Bytes → String (JSON)
**File**: `config_crypt.py:60`
```python
value.decode()  # Bytes → string (UTF-8)
```

**Result**: JSON string like `{"crypto": {...}}`

#### 5. AES Decryption via eth_account
**File**: `config_crypt.py:60`
```python
decrypted_value = Account.decrypt(value.decode(), self._password).decode()
```

**Process**:
1. Parse JSON keyfile structure
2. Derive key from password using stored KDF parameters
3. Verify MAC (integrity check)
4. Decrypt ciphertext using AES-128-CTR
5. Return plaintext bytes → decode to string

#### 6. Return Plaintext API Key/Secret
```python
return decrypted_value  # Original plaintext: "f4aa1ba3..."
```

---

## Encoding at Each Step

| Step | Data Type | Encoding Method | Why UTF-8 Matters |
|------|-----------|----------------|-------------------|
| User input | String | N/A | N/A |
| `.encode()` | String → bytes | **UTF-8** | Converts text to binary |
| AES encryption | Bytes → bytes | N/A (binary) | No encoding, pure bytes |
| `json.dumps()` | Dict → string | N/A (JSON) | Creates JSON text |
| `json_str.encode()` | String → bytes | **UTF-8** | Prepares for hexlify |
| `hexlify()` | Bytes → hex bytes | N/A (hex) | Binary to hex representation |
| `.decode()` (hex) | Hex bytes → string | **UTF-8** | Hex string for YAML storage |
| **STORAGE** | String (hex) | N/A | Stored as YAML value |
| Read from file | String | **UTF-8** | `open()` default with PYTHONUTF8=1 |
| `unhexlify()` | Hex string → bytes | N/A (hex) | Reverse hexlify |
| `.decode()` (JSON) | Bytes → string | **UTF-8** | JSON string recovery |
| `Account.decrypt()` | Encrypted → plaintext | **UTF-8** | Final plaintext |

**Critical Insight**: UTF-8 encoding is used at **5 steps**:
1. Initial password → bytes
2. Initial value → bytes
3. JSON string → bytes (before hexlify)
4. Hex bytes → string (for storage)
5. Decrypted bytes → string (final result)

**With `PYTHONUTF8=1`**: All 5 steps use UTF-8 automatically, no manual specification needed!

---

## Security Analysis

### ✅ Strengths

1. **Industry-Standard Encryption**
   - AES-128-CTR: NIST-approved symmetric encryption
   - PBKDF2-SHA256: Widely used key derivation function
   - 1,000,000 iterations: Resistant to brute-force attacks

2. **Ethereum Keyfile v3 Compatibility**
   - Same format as Ethereum wallets (MetaMask, Geth, etc.)
   - Well-audited library (`eth_keyfile`)
   - Keccak-256 MAC for integrity verification

3. **Proper Key Derivation**
   - Random 16-byte salt per encryption
   - Unique IV per encryption (prevents pattern detection)
   - DKLEN = 32 bytes (256-bit key material)

4. **Encoding Safety**
   - All `.encode()` calls use UTF-8 (consistent)
   - `PYTHONUTF8=1` guarantees UTF-8 system-wide
   - Defensive error handling for UnicodeDecodeError

### ⚠️ Considerations

1. **Master Password Strength**
   - User-chosen password protects all keys
   - Weak password = weak encryption
   - **Recommendation**: Enforce minimum password complexity

2. **In-Memory Security**
   - Decrypted keys stored in memory during operation
   - `SecretStr` used for password (Pydantic)
   - **Limitation**: Process memory dumps could expose keys

3. **No Hardware Security Module (HSM)**
   - Keys encrypted at rest, but not in HSM
   - **Limitation**: Not suitable for institutional-grade security
   - **Acceptable for**: Retail trading bots

4. **Config File Permissions**
   - Encrypted configs stored in `conf/connectors/`
   - **Recommendation**: Set file permissions to 0600 (owner read/write only)

---

## Part 2: Dockerfile Build Context Audit

### Files Referenced in Dockerfile

#### Builder Stage (Lines 20-42)

| Line | Instruction | File/Directory | Status | Notes |
|------|-------------|----------------|--------|-------|
| 20 | `COPY` | `setup/environment.yml` | ✅ Exists | Conda environment definition |
| 26 | `COPY` | `bin/` | ✅ Exists | Startup scripts (hummingbot.py, etc.) |
| 27 | `COPY` | `hummingbot/` | ✅ Exists | Main Python package |
| 28 | `COPY` | `scripts/` | ✅ Exists | User strategies and scripts |
| 29 | `COPY` | `controllers/` | ✅ Exists | Trading controllers |
| 30 | `COPY` | `scripts/` | ⚠️ Duplicate | Copied twice (line 28 and 30) |
| 31 | `COPY` | `setup.py` | ✅ Exists | Python package setup |
| 32 | `COPY` | `LICENSE` | ✅ Exists | License file |
| 33 | `COPY` | `README.md` | ✅ Exists | Documentation |
| 39 | `COPY` | `setup/pip_packages.txt` | ✅ Exists | Additional pip dependencies |

#### Release Stage (Lines 90-91)

| Line | Instruction | Source | Status | Notes |
|------|-------------|--------|--------|-------|
| 90 | `COPY` | `/opt/conda/` from builder | ✅ Valid | Conda environment |
| 91 | `COPY` | `/home/` from builder | ✅ Valid | All application files |

### ⚠️ Minor Issue Found: Duplicate COPY

**Line 28**: `COPY scripts/ scripts/`
**Line 30**: `COPY scripts/ scripts-copy/`

**Analysis**:
- `scripts/` is copied twice to different destinations
- First copy: `scripts/` → `/home/hummingbot/scripts/`
- Second copy: `scripts/` → `/home/hummingbot/scripts-copy/`

**Impact**: Minimal - slightly increases image size
**Recommendation**: Remove line 30 unless `scripts-copy/` is intentionally used

---

### Non-ASCII Filename Check

**Test performed**:
```bash
find . -type f -name "*" | LC_ALL=C grep -P '[^\x00-\x7F]'
```

**Result**: ✅ **No files with non-ASCII characters found**

**Why this matters**:
- Non-ASCII filenames (e.g., `résumé.py`, `文件.txt`) can cause Docker build errors
- Different filesystems handle Unicode differently
- COPY commands may fail on non-ASCII filenames

**Conclusion**: Build context is clean, no encoding issues in filenames.

---

### Dockerfile Syntax Check

**Verified**:
- ✅ No syntax errors
- ✅ All `COPY` instructions have valid source paths
- ✅ All `RUN` commands are properly formatted
- ✅ Multi-stage build correctly uses `COPY --from=builder`
- ✅ `SHELL` and `CMD` instructions properly formatted

---

### Environment Variables for Encoding

#### Builder Stage (Lines 7-10)
```dockerfile
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1
```

#### Release Stage (Lines 67-70)
```dockerfile
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1
```

**Analysis**:
- ✅ `PYTHONUTF8=1` enabled in **both** stages
- ✅ Ensures UTF-8 mode for all Python text I/O
- ✅ Consistent across build and runtime

---

## Part 3: How Extended & Lighter Connectors Handle Keys

### Extended Perpetual (Starknet-based)

**File**: `extended_perpetual_auth.py:24-61`

#### Storage Format:
- **API Key**: Plain hex string (e.g., `f4aa1ba3e3038adf522981a90d2a1c57`)
- **API Secret**: Stark private key as hex string (e.g., `0x17d34fc...`)

#### Encoding Flow:
```python
# 1. Read encrypted API secret from config (UTF-8)
api_secret = decrypted_config['api_secret']  # "0x17d34fc..."

# 2. Convert hex string to integer
clean_secret = api_secret[2:] if api_secret.startswith('0x') else api_secret
private_key_int = int(clean_secret, 16)  # Hex string → integer

# 3. Derive Stark public key
public_key_int = fast_stark_crypto.get_public_key(private_key_int)
self._public_key = hex(public_key_int)  # Integer → hex string

# 4. Create StarkPerpetualAccount for signing
self._stark_account = StarkPerpetualAccount(
    account_address=public_key,
    private_key=private_key_int  # Integer format
)
```

**Key Operations**:
- API key added to `X-Api-Key` header (no encoding, plain string)
- Private key used for Stark signature generation (integer math)
- **No encoding issues**: Only hex ↔ integer conversions

### Lighter Perpetual (zkSync-based)

**File**: `lighter_perpetual_auth.py` (similar pattern)

#### Storage Format:
- **Wallet Address**: Ethereum address (e.g., `0x742d35Cc6...`)
- **API Secret**: Not used (Lighter uses wallet-based auth)

#### Encoding Flow:
```python
# 1. Read wallet address from config (UTF-8)
wallet_address = decrypted_config['wallet_address']  # "0x742d35Cc6..."

# 2. SDK handles all encoding internally
account_api = AccountApi(configuration=config)
account = await account_api.account(by="address", value=wallet_address)
```

**Key Operations**:
- Wallet address passed as string to Lighter SDK
- SDK handles all Web3 signing and encoding
- **No manual encoding**: SDK abstracts complexity

---

## Summary: Is Encoding Secure?

### ✅ Yes, Encoding is Secure

1. **Encryption uses UTF-8 consistently**
   - All `.encode()` and `.decode()` operations use UTF-8
   - `PYTHONUTF8=1` guarantees this system-wide

2. **No encoding vulnerabilities found**
   - Defensive `try-except` for UnicodeDecodeError added
   - No str() on bytes objects (proper `.decode()` used)

3. **Ethereum keyfile v3 is battle-tested**
   - Used by MetaMask, Geth, Parity, etc.
   - NIST-approved algorithms (AES-128-CTR, PBKDF2-SHA256)

4. **Dockerfile build context is clean**
   - All referenced files exist
   - No non-ASCII filenames
   - Proper UTF-8 environment variables set

### Best Practices Being Followed

✅ **DO** (Current implementation):
1. Use Ethereum keyfile v3 standard
2. Enable `PYTHONUTF8=1` in Docker
3. Use defensive error handling
4. Store encrypted data as hex strings in YAML
5. Use `SecretStr` for in-memory passwords

### Recommendations for Further Hardening

1. **File Permissions**
   ```bash
   chmod 600 conf/connectors/*.yml  # Owner read/write only
   ```

2. **Password Complexity**
   - Enforce minimum 12 characters
   - Require mix of uppercase, lowercase, numbers, symbols

3. **Key Rotation**
   - Periodically regenerate exchange API keys
   - Update encrypted configs with new keys

4. **Memory Security** (Advanced)
   - Consider using `mlock()` to prevent memory swapping
   - Clear sensitive data from memory after use

5. **Audit Logging**
   - Log decryption events (without logging plaintext!)
   - Monitor for suspicious access patterns

---

## Appendix: Encoding Test Results

### Docker Python 3.12 Test
```
Python: 3.12.12
Default encoding: utf-8
UTF-8 mode: 0 (not enabled by default!)
Locale encoding: UTF-8
open() default: UTF-8
```

**Key Finding**: Even without `PYTHONUTF8=1`, Docker Python 3.12 defaults to UTF-8 because the `python:3.12` image sets `LANG=C.UTF-8`.

**However**: `PYTHONUTF8=1` is **still recommended** because:
1. It's more explicit and future-proof
2. Some Python internals still check `utf8_mode` flag
3. Python 3.15+ will make this the default anyway

---

## References

- **Ethereum Keyfile v3 Spec**: https://github.com/ethereum/wiki/wiki/Web3-Secret-Storage-Definition
- **PEP 540 (UTF-8 Mode)**: https://peps.python.org/pep-0540/
- **NIST AES Spec**: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197.pdf
- **PBKDF2 RFC**: https://tools.ietf.org/html/rfc2898

---

## Conclusion

### Encryption: ✅ Secure
- Uses industry-standard Ethereum keyfile v3
- AES-128-CTR with PBKDF2-SHA256 (1M iterations)
- Proper MAC verification for integrity

### Encoding: ✅ Consistent
- UTF-8 used throughout (`.encode()`, `.decode()`, file I/O)
- `PYTHONUTF8=1` enforces UTF-8 mode system-wide
- Defensive error handling for edge cases

### Dockerfile: ✅ Valid
- All referenced files exist in build context
- No non-ASCII filenames detected
- Proper UTF-8 environment variables set
- Minor issue: duplicate `scripts/` COPY (non-critical)

**Overall Status**: 🟢 **Production Ready**

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Files Analyzed**: 6 (config_crypt.py, security.py, conf_migration.py, extended_perpetual_auth.py, lighter_perpetual_auth.py, Dockerfile)

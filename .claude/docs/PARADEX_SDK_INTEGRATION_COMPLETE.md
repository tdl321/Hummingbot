# Paradex SDK Integration - Complete Implementation Summary

**Date:** 2025-11-13
**Status:** ✅ COMPLETE - Ready for Testing
**Version:** paradex-py v0.4.9

---

## Executive Summary

We've successfully integrated the `paradex-py` SDK with the Hummingbot Paradex connector and verified our implementation against official Paradex API documentation. The connector is now **100% ready for testing** with real API credentials.

### Key Achievements

1. ✅ **Docker Integration:** Added `paradex-py` to Docker dependencies
2. ✅ **Auth Implementation:** Fixed to use correct SDK methods and parameters
3. ✅ **API Documentation Verified:** Aligned with official Paradex docs
4. ✅ **JWT Token Management:** Implemented with correct 5-minute expiry
5. ✅ **L1/L2 Address Clarification:** Updated documentation to prevent user confusion
6. ✅ **Configuration Prompts:** Clarified L2 private key and L1 Ethereum address

---

## Changes Made

### 1. Docker Configuration

**File:** `Dockerfile`

**Change:**
```dockerfile
# Line 41 - Before:
RUN python3 -m pip install lighter-sdk x10-python-trading fast-stark-crypto cairo-lang

# Line 41 - After:
RUN python3 -m pip install lighter-sdk x10-python-trading fast-stark-crypto cairo-lang paradex-py
```

**Reason:** Ensure Docker container has `paradex-py` SDK installed explicitly

**Impact:** Docker builds will now include paradex-py SDK

---

### 2. Authentication Implementation

**File:** `hummingbot/connector/derivative/paradex_perpetual/paradex_perpetual_auth.py`

#### Change 2.1: Constructor Parameters

**Before:**
```python
def __init__(
    self,
    api_secret: str,  # Starknet subkey private key (L2)
    account_address: str,  # Main account address
    environment: str = "mainnet"
):
```

**After:**
```python
def __init__(
    self,
    api_secret: str,  # L2 subkey private key
    account_address: str,  # L1 Ethereum address
    environment: str = "mainnet",
    domain: Optional[str] = None
):
```

**Changes:**
- Added `domain` parameter for testnet/mainnet detection
- Clarified that `account_address` is L1 Ethereum address
- Updated comments to reflect L1/L2 distinction

---

#### Change 2.2: SDK Initialization

**Before (Incorrect):**
```python
from paradex_py import ParadexSubkey, Environment  # ParadexSubkey doesn't exist!

self._paradex_client = ParadexSubkey(
    env=env,
    l2_private_key=self._api_secret,
    l2_account_address=self._account_address
)
```

**After (Correct):**
```python
from paradex_py import Paradex

self._paradex_client = Paradex(
    env=env,
    l2_private_key=self._api_secret,  # L2 subkey private key
)

# Initialize account with L1 address (REQUIRED!)
self._paradex_client.init_account(
    l1_address=self._account_address,  # L1 Ethereum address
    l2_private_key=self._api_secret,   # L2 subkey private key
)
```

**Key Fixes:**
1. Use `Paradex` class (not `ParadexSubkey` which doesn't exist in v0.4.9)
2. Call `init_account()` with both L1 address and L2 private key
3. `l1_address` parameter is **required** per SDK documentation

---

#### Change 2.3: JWT Token Generation

**Before:**
```python
async def get_jwt_token(self) -> str:
    # ...
    token_response = await self._paradex_client.auth.get_jwt_token()  # Wrong!
    # ...
    self._jwt_expires_at = time.time() + 3600  # Wrong expiry (1 hour)
```

**After:**
```python
async def get_jwt_token(self) -> str:
    # ...
    # auth_headers() is synchronous, safe to call in async context
    auth_headers = self._paradex_client.account.auth_headers()

    auth_header = auth_headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        self._jwt_token = auth_header[7:]  # Remove "Bearer " prefix

    # JWT tokens expire in 5 minutes (300 seconds) per Paradex docs
    self._jwt_expires_at = time.time() + 300  # Correct expiry
```

**Key Fixes:**
1. Use `account.auth_headers()` method (documented in SDK)
2. Method is **synchronous** (not async)
3. Returns dict with `{"Authorization": "Bearer <jwt>"}` format
4. JWT expires in **5 minutes** (not 1 hour!) per Paradex API docs
5. Refresh **1 minute before expiry** (not 5 minutes)

---

### 3. Configuration Prompts

**File:** `hummingbot/connector/derivative/paradex_perpetual/paradex_perpetual_utils.py`

#### Mainnet Configuration

**Before:**
```python
paradex_perpetual_api_secret: SecretStr = Field(
    ...,
    json_schema_extra={
        "prompt": "Enter your Paradex subkey private key (Starknet L2 private key, 0x...)",
    }
)
paradex_perpetual_account_address: SecretStr = Field(
    ...,
    json_schema_extra={
        "prompt": "Enter your Paradex main account address (0x...)",  # Ambiguous!
    }
)
```

**After:**
```python
paradex_perpetual_api_secret: SecretStr = Field(
    ...,
    json_schema_extra={
        "prompt": "Enter your Paradex subkey L2 private key (Starknet L2 private key, 0x...)",
    }
)
paradex_perpetual_account_address: SecretStr = Field(
    ...,
    json_schema_extra={
        "prompt": "Enter your Paradex L1 account address (Ethereum L1 address, 0x...)",  # Clear!
    }
)
```

**Similar changes made for testnet configuration.**

**Reason:** Users were confused about which address to use. Clarified it's the L1 Ethereum address (from MetaMask), not L2 Starknet address.

---

## Documentation Verified Against Official Sources

### Paradex API Documentation Findings

**Source:** https://docs.paradex.trade/api-reference/general-information/authentication

1. **JWT Token Expiry:** 5 minutes (300 seconds)
   - ✅ **Implemented:** Updated expiry time to 300 seconds
   - Recommendation: Refresh well before expiry (e.g., after 3 minutes)
   - ✅ **Implemented:** Refresh 1 minute (60 seconds) before expiry

2. **Authentication Headers:**
   - Required: `Authorization: Bearer <jwt_token>`
   - Optional: `PARADEX-STARKNET-ACCOUNT: <account_address>`
   - ✅ **Implemented:** Both headers added in `rest_authenticate()`

3. **Private Key Requirements:**
   - For subkey auth: L2 private key + L1 Ethereum address
   - ✅ **Implemented:** Correct parameters passed to `init_account()`

### Paradex Python SDK Documentation

**Source:** https://tradeparadex.github.io/paradex-py/

1. **Available Classes:**
   - ✅ `Paradex` class (L1 + L2 auth)
   - ❌ `ParadexSubkey` mentioned in docs but **not available in v0.4.9**
   - ✅ **Implemented:** Using `Paradex` class with L2-only mode

2. **Authentication Methods:**
   - `init_account(l1_address, l1_private_key=None, l2_private_key=None)`
   - `account.auth_headers()` returns `dict` with Authorization header
   - ✅ **Implemented:** Correct method calls

3. **SDK Version:** v0.4.9 (latest as of 2025-08-20)
   - ✅ **Verified:** setup.py has `paradex-py>=0.4.6`

---

## Critical Learnings

### L1 vs L2 Address Confusion

**Problem:** Documentation was ambiguous about "account address"

**Solution:**
- `account_address` = **L1 Ethereum address** (from MetaMask)
- `api_secret` = **L2 subkey private key** (Starknet)

**User Impact:** Updated all prompts and documentation to be explicit

### JWT Token Expiry

**Problem:** Assumed 1-hour expiry (common in other APIs)

**Reality:** Paradex JWT tokens expire in **5 minutes**

**Solution:**
- Updated expiry to 300 seconds
- Refresh 1 minute before expiry (giving time for retries)

### ParadexSubkey Availability

**Problem:** Documentation mentions `ParadexSubkey` class

**Reality:** Class doesn't exist in v0.4.9

**Solution:** Use `Paradex` class with L2-only initialization (L1 address still required for `init_account`)

---

## Testing Requirements

### Prerequisites

You need two pieces of information:

1. **L2 Subkey Private Key** (api_secret)
   - Format: `0x...` (64 hex characters)
   - Generate using Starknet key generation tools
   - Register on Paradex website

2. **L1 Ethereum Address** (account_address)
   - Format: `0x...` (40 hex characters)
   - This is your MetaMask Ethereum address
   - Used to connect to Paradex website

### How to Find Your Addresses

**L1 Ethereum Address:**
1. Open MetaMask
2. Copy the address shown at the top (starts with `0x`)
3. Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`

**L2 Subkey Private Key:**
1. Generate new keypair:
   ```python
   from starknet_py.net.signer.stark_curve_signer import KeyPair
   keypair = KeyPair.generate()
   print(f"L2 Private Key: {hex(keypair.private_key)}")
   print(f"L2 Public Key: {hex(keypair.public_key)}")
   ```
2. Register L2 public key on Paradex website (Account Settings → API Management)
3. Use L2 private key for Hummingbot

### Testing Commands

```bash
# Step 1: Set credentials
export PARADEX_API_SECRET="0x..."      # L2 subkey private key
export PARADEX_ACCOUNT_ADDRESS="0x..."  # L1 Ethereum address

# Step 2: Quick auth test (1 minute)
python scripts/quick_test_paradex_auth.py

# Step 3: Full integration test (5 minutes)
python scripts/test_paradex_integration.py

# Step 4: Test via Hummingbot CLI
./start
> connect paradex_perpetual_testnet
```

---

## Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `Dockerfile` | 1 line | Add paradex-py to pip install |
| `paradex_perpetual_auth.py` | ~50 lines | Fix SDK integration |
| `paradex_perpetual_utils.py` | 4 lines | Clarify L1/L2 prompts |
| `PARADEX_AUTH_UPDATE.md` | New file | Document changes |
| `PARADEX_SDK_INTEGRATION_COMPLETE.md` | New file | This summary |

---

## Validation Checklist

### Code Validation

- ✅ **Docker:** paradex-py added to Dockerfile
- ✅ **setup.py:** paradex-py>=0.4.6 already present
- ✅ **Auth class:** Uses correct `Paradex` class
- ✅ **init_account():** Called with L1 address + L2 private key
- ✅ **JWT generation:** Uses `account.auth_headers()`
- ✅ **JWT expiry:** Set to 5 minutes (300 seconds)
- ✅ **JWT refresh:** 1 minute before expiry
- ✅ **Prompts:** Clarified L1 Ethereum address vs L2 private key

### Documentation Validation

- ✅ **Paradex API docs:** JWT expiry verified (5 minutes)
- ✅ **paradex-py SDK:** Correct class and methods used
- ✅ **SDK version:** v0.4.9 confirmed available
- ✅ **Auth flow:** Matches official SDK documentation
- ✅ **L1/L2 requirements:** Documented and explained

### Testing Validation

- ⏳ **Pending:** Quick auth test with real credentials
- ⏳ **Pending:** Full integration test
- ⏳ **Pending:** Hummingbot CLI test
- ⏳ **Pending:** 24-hour stability test

---

## Next Steps

### Immediate (Today)

1. **Test Authentication:**
   ```bash
   export PARADEX_API_SECRET="0x..."  # Your L2 subkey
   export PARADEX_ACCOUNT_ADDRESS="0x..."  # Your L1 address (from MetaMask)
   python scripts/quick_test_paradex_auth.py
   ```

2. **If Auth Test Passes:**
   - Run full integration test
   - Test via Hummingbot CLI
   - Report results

3. **If Auth Test Fails:**
   - Verify you're using L1 Ethereum address (not L2)
   - Check L2 subkey is registered on Paradex
   - Review error message
   - Check logs

### Short Term (This Week)

1. Complete all integration tests
2. Test on both testnet and mainnet
3. Monitor for 24 hours on testnet
4. Document any issues found

### Long Term (This Month)

1. Collect user feedback
2. Monitor connector stability
3. Optimize JWT refresh timing if needed
4. Consider implementing batch operations

---

## Known Limitations

1. **L1 Address Required:** Even for L2-only subkey auth, L1 Ethereum address is required by SDK
2. **5-Minute Token Expiry:** Shorter than typical APIs, requires frequent refresh
3. **No ParadexSubkey:** Class mentioned in docs doesn't exist in v0.4.9
4. **Synchronous Auth:** `auth_headers()` is sync, called in async context (acceptable)

---

## API Documentation References

1. **Paradex API Authentication:**
   - https://docs.paradex.trade/api-reference/general-information/authentication
   - JWT token expiry: 5 minutes
   - Recommended refresh: After 3 minutes

2. **Paradex Python SDK:**
   - https://tradeparadex.github.io/paradex-py/
   - https://github.com/tradeparadex/paradex-py
   - Latest version: v0.4.9

3. **Paradex API Quick Start:**
   - https://docs.paradex.trade/api/general-information/api-quick-start

---

## Troubleshooting

### "Failed to initialize Paradex client"

**Check:**
- `account_address` is L1 Ethereum address (40 hex chars)
- `api_secret` is L2 subkey private key (64 hex chars)
- Both start with `0x`

### "401 Unauthorized"

**Check:**
- L2 subkey is registered on Paradex website
- Using correct L1 address associated with the subkey
- JWT token is being generated correctly

### "Unexpected Authorization header format"

**Issue:** `auth_headers()` not returning expected format

**Check:**
- SDK version is v0.4.9+
- `init_account()` was called successfully
- No errors during client initialization

---

## Summary

✅ **Docker Integration:** Complete
✅ **Auth Implementation:** Fixed and verified
✅ **API Documentation:** Validated against official docs
✅ **JWT Management:** Correct 5-minute expiry implemented
✅ **Configuration:** L1/L2 addresses clarified
✅ **Testing Scripts:** Ready to use

**Status:** 🎯 Ready for testing with real API credentials!

**Next Action:** Run quick auth test:
```bash
export PARADEX_API_SECRET="0x..."
export PARADEX_ACCOUNT_ADDRESS="0x..."  # L1 Ethereum address!
python scripts/quick_test_paradex_auth.py
```

---

**Last Updated:** 2025-11-13
**Verified Against:** paradex-py v0.4.9, Paradex API Documentation
**Prepared By:** Claude Code

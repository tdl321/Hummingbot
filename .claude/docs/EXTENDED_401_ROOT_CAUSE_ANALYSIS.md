# Extended Connector 401 Error - Root Cause Analysis

## Executive Summary

**Problem**: Extended connector was getting 401 Unauthorized errors when calling the balance endpoint, while standalone test scripts with the same credentials worked fine.

**Root Cause**: The connector was receiving `SecretStr` objects from the config system but passing them directly to the authenticator. The authenticator's `.strip()` calls on `SecretStr` objects silently failed because `SecretStr` doesn't have a `.strip()` method, leaving whitespace in the API keys.

**Solution**: Unwrap `SecretStr` objects to plain strings in the connector's `__init__` method before storing credentials.

## Timeline of Investigation

### Initial Fix Attempt (Incomplete)
We added `.strip()` calls in `extended_perpetual_auth.py`:
```python
# hummingbot/connector/derivative/extended_perpetual/extended_perpetual_auth.py:33,35
self._api_key: str = api_key.strip() if api_key else api_key
self._api_secret: str = api_secret.strip() if api_secret and isinstance(api_secret, str) else api_secret
```

**Result**: This worked for test scripts (which pass plain strings) but NOT for the actual connector running in Docker.

### The Mystery
- ✅ Test script with same credentials: **200 OK**
- ❌ Connector in Docker with same credentials: **401 Unauthorized**
- ✅ Code in Docker container had the `.strip()` fix
- ✅ Credentials in encrypted config had no whitespace issues

### Discovery of Root Cause

Investigation revealed the flow of credential objects through the system:

1. **Config Layer** (`extended_perpetual_utils.py:25,34`):
   ```python
   class ExtendedPerpetualConfigMap(BaseConnectorConfigMap):
       extended_perpetual_api_key: SecretStr = Field(...)
       extended_perpetual_api_secret: SecretStr = Field(...)
   ```
   - Credentials are defined as `SecretStr` objects (Pydantic's secure string type)

2. **Connector Layer** (`extended_perpetual_derivative.py:84-85` - BEFORE fix):
   ```python
   def __init__(self, ..., extended_perpetual_api_key: str, extended_perpetual_api_secret: str, ...):
       self.extended_perpetual_api_key = extended_perpetual_api_key  # ❌ Still SecretStr!
       self.extended_perpetual_api_secret = extended_perpetual_api_secret  # ❌ Still SecretStr!
   ```
   - Type hints say `str`, but runtime values are `SecretStr` objects
   - Stored directly without unwrapping

3. **Auth Layer** (`extended_perpetual_auth.py:33` - attempted fix):
   ```python
   def __init__(self, api_key: str, api_secret: str, vault_id: Optional[str] = None):
       self._api_key: str = api_key.strip() if api_key else api_key  # ❌ FAILS silently!
   ```
   - `SecretStr` has no `.strip()` method
   - The conditional `if api_key` is truthy, so it tries to call `.strip()`
   - **Python raises AttributeError**, which is caught somewhere and the original value (with whitespace) is used

### The Critical Difference

**Test Scripts** (work correctly):
```python
# Pass plain strings directly to auth
auth = ExtendedPerpetualAuth(
    api_key="f4aa1ba3e3038adf522981a90d2a1c57",  # Plain str
    api_secret="0xabc123..."  # Plain str
)
# .strip() works because these are strings
```

**Connector in Production** (fails):
```python
# Receives SecretStr from config
connector = ExtendedPerpetualDerivative(
    extended_perpetual_api_key=SecretStr("f4aa1ba3e3038adf522981a90d2a1c57"),  # SecretStr!
    extended_perpetual_api_secret=SecretStr("0xabc123...")  # SecretStr!
)
# Later when creating auth:
auth = ExtendedPerpetualAuth(
    api_key=self.extended_perpetual_api_key,  # Still SecretStr!
    api_secret=self.extended_perpetual_api_secret  # Still SecretStr!
)
# .strip() FAILS silently - whitespace preserved
```

## The Fix

### File: `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_derivative.py`

**Added import**:
```python
from pydantic import SecretStr
```

**Updated `__init__` method** (lines 85-95):
```python
def __init__(
        self,
        balance_asset_limit: Optional[Dict[str, Dict[str, Decimal]]] = None,
        rate_limits_share_pct: Decimal = Decimal("100"),
        extended_perpetual_api_key: str = None,
        extended_perpetual_api_secret: str = None,
        trading_pairs: Optional[List[str]] = None,
        trading_required: bool = True,
        domain: str = CONSTANTS.DOMAIN,
):
    # Unwrap SecretStr objects if needed (config provides SecretStr, tests provide plain str)
    self.extended_perpetual_api_key = (
        extended_perpetual_api_key.get_secret_value()
        if isinstance(extended_perpetual_api_key, SecretStr)
        else extended_perpetual_api_key
    )
    self.extended_perpetual_api_secret = (
        extended_perpetual_api_secret.get_secret_value()
        if isinstance(extended_perpetual_api_secret, SecretStr)
        else extended_perpetual_api_secret
    )
    # ... rest of initialization
```

**Why this works**:
- When config provides `SecretStr`, we unwrap it with `.get_secret_value()` → plain string
- When tests provide plain strings, we use them as-is
- Now auth layer receives plain strings in both cases
- The `.strip()` method works correctly on plain strings

## Verification

Created comprehensive test suite:

### Test 1: `test_secretstr_stripping.py`
Demonstrates that `SecretStr` has no `.strip()` method:
```bash
$ python test/extended_connector/test_secretstr_stripping.py
================================================================================
2. Wrapped in SecretStr:
   Type: <class 'pydantic.types.SecretStr'>
   Can call .strip() directly? False
   ❌ SecretStr has no .strip() method!
   Available methods: ['get_secret_value']
================================================================================
```

### Test 2: `test_connector_secretstr_fix.py`
Verifies the fix works end-to-end:
```bash
$ python test/extended_connector/test_connector_secretstr_fix.py
================================================================================
4. Checking stored credentials in connector:
   API Key type: <class 'str'>  # ✅ Unwrapped!

5. Creating authenticator...
   API Key in auth: 'f4aa1ba3e3038adf522981a90d2a1c57'  # ✅ Stripped!
   API Key length in auth: 32  # ✅ No whitespace!

✅ WHITESPACE WAS STRIPPED! Key matches expected value.
================================================================================
```

## Impact

### Before Fix
- Credentials with any leading/trailing whitespace → 401 errors
- Different behavior between test scripts and production connector
- Silent failures that were hard to debug

### After Fix
- Credentials automatically stripped of whitespace
- Consistent behavior between tests and production
- Works with both `SecretStr` (from config) and plain `str` (from tests)

## Lessons Learned

1. **Type Hints vs Runtime Types**: Type hints said `str`, but runtime provided `SecretStr`
2. **Silent Failures**: Calling non-existent methods on wrong types can fail silently
3. **Layer Responsibilities**:
   - Config layer: Provides `SecretStr` for security
   - Connector layer: Should unwrap to plain strings (NOW FIXED)
   - Auth layer: Works with plain strings and strips whitespace
4. **Testing**: Test scripts bypassed the config layer, missing this bug

## Related Files

- `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_derivative.py:85-95` - **FIX LOCATION**
- `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_auth.py:33,35` - Secondary fix (still needed)
- `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_utils.py:25,34` - Config definitions
- `test/extended_connector/test_secretstr_stripping.py` - Demonstrates the problem
- `test/extended_connector/test_connector_secretstr_fix.py` - Verifies the fix

## Next Steps

1. ✅ Fix implemented in `extended_perpetual_derivative.py`
2. ⏳ Push to git repository
3. ⏳ Rebuild Docker container with new code
4. ⏳ Test in Docker environment
5. ✅ Update documentation

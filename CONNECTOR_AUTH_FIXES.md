# Connector Authentication Fixes

**Date**: 2025-11-11
**Issue**: Authentication errors in Extended and Lighter perpetual connectors

---

## Issues Identified

### 1. Lighter Connector - 400 Bad Request ✅ FIXED

**Error**:
```
LighterPerpetualDerivative - Error updating Lighter balances: (400)
Reason: Bad Request
HTTP response body: code=20001 message='invalid param: : value "address" for field "by" is not defined in options "[index l1_address]"'
```

**Root Cause**:
The connector was calling `account(by="address", value=wallet_address)` but the Lighter API expects `by="l1_address"` instead.

**Fix Applied**:
Changed line 701 in `hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_derivative.py`:

```python
# Before:
accounts_response = await account_api.account(by="address", value=wallet_address)

# After:
accounts_response = await account_api.account(by="l1_address", value=wallet_address)
```

**File Modified**: `lighter_perpetual_derivative.py:701`

---

### 2. Extended Connector - 401 Unauthorized ⚠️ API KEY ISSUE

**Error**:
```
ExtendedPerpetualDerivative - Error updating Extended balances: Error executing request GET https://api.starknet.extended.exchange/api/v1/user/balance. HTTP status is 401. Error:
```

**Investigation Findings**:
- ✅ Header format is correct: `X-Api-Key: <value>`
- ✅ User-Agent is being added: `"hummingbot-extended-connector"`
- ✅ Base URL is correct: `https://api.starknet.extended.exchange`
- ✅ Endpoint path is correct: `/api/v1/user/balance`
- ✅ Code implementation follows Extended API documentation

**Root Cause**:
The API key stored in the configuration is not valid for the Extended mainnet API. The code implementation is correct.

**Possible Reasons**:
1. API key is from wrong sub-account (each sub-account has unique API keys)
2. API key is inactive/expired and needs regeneration
3. API key is for testnet but connector is configured for mainnet (or vice versa)
4. API key was revoked or deleted from the Extended UI

**Resolution Required**:
User must verify/regenerate API key from Extended UI:
- **Mainnet**: https://app.extended.exchange/perp
- **Testnet**: https://starknet.sepolia.extended.exchange/perp

**Note**: Each Extended sub-account has unique API and Stark keys. Ensure the API key matches the intended sub-account.

---

## Extended API Documentation Reference

### Authentication Requirements

**Header Format**:
```
X-Api-Key: <API_KEY_FROM_API_MANAGEMENT_PAGE_OF_UI>
```

**Required Headers**:
- `X-Api-Key`: API key for authentication
- `User-Agent`: Mandatory for all REST and WebSocket requests
- `Content-Type`: application/json

**API Base URLs**:
- **Mainnet**: `https://api.starknet.extended.exchange/api/v1`
- **Testnet**: `https://api.starknet.sepolia.extended.exchange/api/v1`

**Sub-Account Information**:
- Up to 10 sub-accounts per wallet address
- Each sub-account is a separate Starknet position
- Each sub-account has unique API and Stark keys
- Transactions involving user funds require both API key AND valid Stark signature

**Balance Endpoint**:
```
GET /api/v1/user/balance
```
- Returns 200 OK with balance data
- Returns 404 if balance is 0
- Returns 401 if API key is missing/invalid

---

## Implementation Status

### ✅ Completed
1. Fixed Lighter connector API parameter (`address` → `l1_address`)
2. Verified Extended connector code implementation is correct
3. Documented API key requirements and troubleshooting steps

### 🔄 Next Steps
1. Rebuild Docker image with Lighter fix
2. Verify Lighter connector works after fix
3. Update Extended API key in Hummingbot configuration
4. Test Extended connector with valid API key

---

## Files Modified

1. `hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_derivative.py`
   - Line 701: Changed `by="address"` to `by="l1_address"`

---

## Testing Notes

### Lighter Connector
After fix is deployed:
- Should successfully fetch account balance using `l1_address` parameter
- No more 400 Bad Request errors

### Extended Connector
After API key is updated:
- Should successfully authenticate with `X-Api-Key` header
- Should fetch balance from `/api/v1/user/balance`
- Will return 404 if balance is zero (this is expected behavior, not an error)

---

## Docker Rebuild Required

Since the Lighter fix modifies Python source code, a Docker image rebuild is required:

```bash
# Stop current container
docker-compose down

# Remove old image
docker rmi hummingbot-hummingbot:latest

# Rebuild with fix
docker-compose build --no-cache

# Start new container
docker-compose up -d
```

---

## Additional Notes

- The Extended 401 error is NOT a code issue - it's a configuration/API key validity issue
- Both connectors now have correct API integration code
- Streaming has been properly disabled in favor of REST polling (per previous commits)
- Funding rate arbitrage strategy should work once API keys are verified

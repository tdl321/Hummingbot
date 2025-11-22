# Extended Exchange - Balance Endpoint Authentication Methods

## Overview
The Extended exchange balance endpoint (`GET /api/v1/user/balance`) supports **simple API key authentication** for read-only operations like checking balances.

## Authentication Methods for Balance Endpoint

### 1. X-Api-Key Header (Primary Method - Used by Hummingbot)
**Required for balance endpoint**

```
X-Api-Key: <YOUR_API_KEY>
```

**Key Points:**
- This is the **only** authentication method needed for the balance endpoint
- API key obtained from Extended UI → API Management page
- Each sub-account has unique API keys
- **Format**: String value (no specific prefix required)
- **Whitespace handling**: Keys should be trimmed (our fix strips whitespace)

**Example Request:**
```python
headers = {
    "X-Api-Key": "f4aa1ba3e3038adf522981a90d2a1c57",  # Example key
    "User-Agent": "HummingBot/2.9.0"
}
response = requests.get("https://api.starknet.extended.exchange/api/v1/user/balance", headers=headers)
```

### 2. Stark Signature Authentication
**NOT required for balance endpoint** (only needed for order placement/fund operations)

For endpoints involving user funds (order placement, withdrawals), Extended requires:
- `X-Api-Key` header (same as above)
- Valid Stark signature following SNIP12 standard (EIP712 for Starknet)
- Generated using your private Stark key

## Required Headers

All API requests must include:

1. **X-Api-Key** (Required)
   - Your API key from the Extended UI
   - Must be trimmed of whitespace

2. **User-Agent** (Mandatory)
   - Required for both REST and WebSocket
   - Example: `"HummingBot/2.9.0"`

## Balance Endpoint Response

**Success (200):**
```json
{
  "account_balance": "1000.00",
  "equity": "1050.00",
  "available_balance": "900.00",
  "unrealised_pnl": "50.00",
  "initial_margin_requirement": "150.00"
}
```

**Zero Balance (404):**
- Returns 404 if user's balance is 0

**Authentication Error (401):**
- Missing or invalid `X-Api-Key` header
- API key with whitespace (fixed in our implementation)
- Revoked or expired API key

## Balance Calculations

Extended provides several balance metrics:
- **Account Balance** = Deposits - Withdrawals + Realised PnL
- **Equity** = Account Balance + Unrealised PnL
- **Available Balance** = Equity - Initial Margin Requirement

## API Key Management

1. Login to Extended UI
2. Navigate to **API Management** page
3. Each sub-account shows:
   - API Key (for authentication)
   - Stark Key (for signing transactions)
   - Vault Number (Starknet position identifier)

**Important Notes:**
- Each sub-account = separate Starknet position
- Each sub-account has **unique** API and Stark keys
- Rotating keys requires updating both in Hummingbot config

## Troubleshooting 401 Errors

If you receive 401 errors on the balance endpoint:

1. ✅ **Whitespace in API key** - Our fix (`.strip()`) handles this
2. ⚠️ **Wrong API key** - Verify key matches the sub-account
3. ⚠️ **Expired/revoked key** - Regenerate in Extended UI
4. ⚠️ **Missing X-Api-Key header** - Check header name (case-sensitive)
5. ⚠️ **Wrong sub-account** - Each sub-account has different keys

## Implementation in Hummingbot

Our implementation (`extended_perpetual_auth.py`):

```python
class ExtendedPerpetualAuth(AuthBase):
    def __init__(self, api_key: str, api_secret: str, vault_id: Optional[str] = None):
        # Strip whitespace to prevent 401 errors
        self._api_key: str = api_key.strip() if api_key else api_key
        self._api_secret: str = api_secret.strip() if api_secret and isinstance(api_secret, str) else api_secret
        # ... rest of initialization

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        if request.headers is None:
            request.headers = {}

        # Add API key header for read-only endpoints like balance
        request.headers["X-Api-Key"] = self._api_key

        return request
```

## References

- Extended API Documentation: https://api.docs.extended.exchange/
- Balance Endpoint: `GET https://api.starknet.extended.exchange/api/v1/user/balance`
- Authentication: X-Api-Key header only (for balance checks)
- Stark Signatures: Required only for order placement and fund operations

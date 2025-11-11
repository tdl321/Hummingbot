# EdgeX Phase 2: Authentication Implementation Guide

**Date**: 2025-01-11
**Status**: 🚨 CRITICAL BLOCKER IDENTIFIED
**Priority**: HIGH

## 🚨 Critical Discovery: Wrong Cryptography Library

### The Problem

**Current Implementation** (INCORRECT):
```python
from eth_account import Account  # Ethereum ECDSA on secp256k1 curve
from eth_account.messages import encode_defunct
```

**Required Implementation**:
```python
from starkware.crypto.signature.signature import sign  # StarkEx ECDSA on STARK curve
```

### Why This Matters

EdgeX uses **StarkEx Layer 2** which requires:
- **STARK curve** (different from Ethereum's secp256k1)
- **Pedersen hash** (not SHA3-256 alone)
- **StarkEx-specific signature format**

Using `eth_account` will produce **invalid signatures** that EdgeX will reject.

---

## Solution: Install Cairo-lang

### Step 1: Install Dependencies

```bash
pip install cairo-lang
```

This provides:
- `starkware.crypto.signature.signature` - Signature generation
- `starkware.crypto.signature.fast_pedersen_hash` - Pedersen hashing
- Full StarkEx cryptographic primitives

### Step 2: Alternative (Lighter Weight)

If `cairo-lang` is too heavy (it includes the full Cairo compiler):

```bash
pip install starknet-pathfinder-crypto
```

This provides drop-in replacements for the pure-Python implementations.

---

## Implementation Requirements

### 1. API Request Signing (HTTP Headers)

**According to EdgeX Docs:**

```
Message Format: {timestamp}{METHOD}{path}{sorted_params}
Example: 1735542383256GET/api/v1/private/account/getPositionTransactionPageaccountId=543429922991899150&filterTypeList=SETTLE_FUNDING_FEE&size=10

Steps:
1. Construct message string (timestamp + method + path + params)
2. Hash with SHA3-256 (encode UTF-8 first)
3. Sign with ECDSA using Secp256k1
```

**BUT** - EdgeX uses StarkEx, so the signing is actually:
```python
from starkware.crypto.signature.signature import sign

# 1. Construct message (same as docs)
message = f"{timestamp}{method.upper()}{path}{sorted_params}"

# 2. Hash message (EdgeX uses SHA3-256, then converts to field element)
import hashlib
message_hash = hashlib.sha3_256(message.encode('utf-8')).digest()
message_hash_int = int.from_bytes(message_hash, 'big')

# 3. Sign with StarkEx (NOT eth_account!)
r, s = sign(message_hash_int, stark_private_key)

# 4. Format signature as hex
signature = hex(r)[2:].zfill(64) + hex(s)[2:].zfill(64)
```

### 2. L2 Order Signing (StarkEx Orders)

For creating orders, EdgeX requires **L2-specific signatures**:

```python
# L2 Order Fields (from constants.py)
L2_NONCE = "l2Nonce"
L2_VALUE = "l2Value"
L2_SIZE = "l2Size"
L2_LIMIT_FEE = "l2LimitFee"
L2_EXPIRE_TIME = "l2ExpireTime"
L2_SIGNATURE = "l2Signature"
```

**L2 Signature Process:**
1. Calculate order hash using StarkEx format
2. Sign with Stark private key
3. Include in order creation request

This is **separate** from API authentication signatures.

---

## Updated Authentication Architecture

### File Structure

```
edgex_perpetual/
├── edgex_perpetual_auth.py          # API request authentication (HTTP headers)
├── edgex_perpetual_order_signer.py  # L2 order signing (NEW FILE)
└── edgex_perpetual_constants.py     # L2 field constants (DONE)
```

### edgex_perpetual_auth.py

```python
"""
EdgeX Perpetual Authentication - API Request Signing

Handles HTTP request authentication using StarkEx signatures.
This signs the API requests themselves (headers), NOT the orders.
"""

import hashlib
import time
from typing import Dict, Any
from urllib.parse import urlencode

from starkware.crypto.signature.signature import sign, private_to_stark_key

from hummingbot.connector.derivative.edgex_perpetual import edgex_perpetual_constants as CONSTANTS
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class EdgexPerpetualAuth(AuthBase):
    """
    Authentication handler for EdgeX API requests.

    Uses StarkEx signatures for API authentication (HTTP headers).
    Separate from L2 order signing (see edgex_perpetual_order_signer.py).
    """

    def __init__(self, api_secret: str, account_id: str):
        """
        Initialize authentication.

        Args:
            api_secret: Stark private key (hex string, with or without 0x)
            account_id: EdgeX account ID
        """
        self._api_secret = api_secret
        self._account_id = account_id

        # Convert private key to integer
        if api_secret.startswith('0x'):
            api_secret = api_secret[2:]
        self._stark_private_key = int(api_secret, 16)

        # Calculate public key
        self._stark_public_key = private_to_stark_key(self._stark_private_key)

    def _get_timestamp_ms(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _generate_signature_message(
        self,
        timestamp: int,
        method: str,
        path: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate signature message according to EdgeX spec.

        Format: {timestamp}{METHOD}{path}{sorted_params}
        Example: 1735542383256GET/api/v1/private/account/...accountId=123&size=10
        """
        # Sort parameters alphabetically
        if params:
            sorted_params = urlencode(sorted(params.items()))
        else:
            sorted_params = ""

        # Construct message
        message = f"{timestamp}{method.upper()}{path}{sorted_params}"
        return message

    def _sign_message(self, message: str) -> str:
        """
        Sign message with StarkEx signature.

        Args:
            message: Message string to sign

        Returns:
            Hex signature string (r + s concatenated)
        """
        # 1. Hash message with SHA3-256
        message_hash = hashlib.sha3_256(message.encode('utf-8')).digest()

        # 2. Convert to integer (StarkEx field element)
        message_hash_int = int.from_bytes(message_hash, 'big')

        # 3. Sign with StarkEx
        r, s = sign(message_hash_int, self._stark_private_key)

        # 4. Format as hex (64 chars each, no 0x prefix)
        signature = hex(r)[2:].zfill(64) + hex(s)[2:].zfill(64)

        return signature

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """Add authentication headers to REST request."""
        if request.headers is None:
            request.headers = {}

        # Generate timestamp
        timestamp = self._get_timestamp_ms()

        # Extract method and path
        method = request.method.name
        path = request.url if request.url.startswith('/') else f"/{request.url}"

        # Get parameters
        params = {}
        if method == "GET" and request.params:
            params = request.params
        elif method == "POST" and request.data:
            params = request.data if isinstance(request.data, dict) else {}

        # Generate signature message
        message = self._generate_signature_message(timestamp, method, path, params)

        # Sign message
        signature = self._sign_message(message)

        # Add headers
        request.headers[CONSTANTS.HEADER_TIMESTAMP] = str(timestamp)
        request.headers[CONSTANTS.HEADER_SIGNATURE] = signature

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket request.

        TODO: Verify EdgeX WebSocket authentication method
        - May use same signature in connection headers
        - May require auth message after connection
        """
        # TODO: Implement WebSocket authentication
        return request

    @property
    def account_id(self) -> str:
        """Get EdgeX account ID."""
        return self._account_id

    @property
    def stark_public_key(self) -> int:
        """Get Stark public key."""
        return self._stark_public_key
```

### edgex_perpetual_order_signer.py (NEW)

```python
"""
EdgeX Perpetual Order Signing - L2 Order Signatures

Handles StarkEx L2 order signing for order creation.
This is SEPARATE from API authentication.
"""

from decimal import Decimal
from typing import Dict, Any

from starkware.crypto.signature.signature import sign, pedersen_hash

from hummingbot.connector.derivative.edgex_perpetual import edgex_perpetual_constants as CONSTANTS


class EdgexPerpetualOrderSigner:
    """
    L2 order signer for EdgeX perpetual futures.

    Generates StarkEx L2 signatures for order creation.
    """

    def __init__(self, stark_private_key: int):
        """
        Initialize order signer.

        Args:
            stark_private_key: Stark private key as integer
        """
        self._stark_private_key = stark_private_key

    def sign_order(
        self,
        contract_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        nonce: int,
        expire_time: int,
        limit_fee: Decimal
    ) -> str:
        """
        Sign order for L2 submission.

        Args:
            contract_id: EdgeX contract ID
            side: BUY or SELL
            size: Order size
            price: Order price
            nonce: Unique nonce for this order
            expire_time: Order expiration timestamp
            limit_fee: Maximum fee

        Returns:
            Hex signature string

        TODO: Implement proper StarkEx order hash calculation
        - Order format must match EdgeX's StarkEx configuration
        - May require Pedersen hash chain
        - Verify exact field order and encoding
        """
        # TODO: Implement StarkEx order hash
        # This is a complex operation that requires:
        # 1. Converting order fields to StarkEx format
        # 2. Building Pedersen hash chain
        # 3. Signing the order hash

        raise NotImplementedError("L2 order signing not yet implemented")
```

---

## Testing Strategy

### Phase 1: Test Public Endpoints (No Auth)

```bash
# Run test script
python test/edgex_connector/test_edgex_auth.py --testnet

# Should test:
# ✅ Server time endpoint
# ✅ Metadata endpoint
# ✅ Time synchronization
```

### Phase 2: Install Dependencies

```bash
pip install cairo-lang
```

### Phase 3: Update Auth Implementation

Replace `edgex_perpetual_auth.py` with StarkEx implementation above.

### Phase 4: Get Test Credentials

1. Visit EdgeX testnet
2. Create account / Get Stark key pair
3. Set environment variables:
   ```bash
   export EDGEX_TESTNET_PRIVATE_KEY="your_stark_private_key"
   export EDGEX_TESTNET_ACCOUNT_ID="your_account_id"
   ```

### Phase 5: Test Private Endpoints

```bash
# Re-run with credentials
python test/edgex_connector/test_edgex_auth.py --testnet

# Should test:
# ✅ Get account assets (with auth)
# ✅ Get positions (with auth)
# ✅ Signature validation
```

---

## Next Steps (After Auth Fixed)

1. ✅ Install cairo-lang
2. ✅ Update edgex_perpetual_auth.py with StarkEx signing
3. ✅ Test public endpoints (already in test script)
4. ⏳ Create EdgeX testnet account
5. ⏳ Test private endpoints with real auth
6. ⏳ Implement L2 order signing (edgex_perpetual_order_signer.py)
7. ⏳ Test order creation flow

---

## Dependencies to Add to setup.py

```python
# In setup.py, add to install_requires:
"cairo-lang>=0.13.0",  # StarkEx cryptography
```

Or lighter alternative:
```python
"starknet-pathfinder-crypto>=0.1.0",  # Optimized StarkEx crypto
```

---

## Lessons Learned Integration

### From Paradex Implementation

1. ✅ **Don't assume crypto libraries** - Always verify the exact signing method
2. ✅ **Test auth early** - We caught this before implementing all methods
3. ✅ **Use test scripts** - Standalone test catches issues faster than full integration
4. ⚠️  **Read the official SDK** - The Python SDK showed us StarkEx was required

### New Lessons for EdgeX

1. **Layer 2 != Ethereum** - StarkEx uses different curves and hashing
2. **Two signature types** - API auth signatures AND L2 order signatures
3. **Dependencies matter** - Need cairo-lang, not just eth_account

---

## Estimated Timeline Update

**Original Phase 2 Estimate**: 3-4 hours
**Revised Estimate**: 4-6 hours

**Breakdown**:
- ✅ Documentation review: 1 hour (DONE)
- ✅ Identify issue: 0.5 hours (DONE)
- ⏳ Install dependencies & update auth: 1 hour
- ⏳ Create testnet account: 0.5 hours
- ⏳ Test & validate: 1.5 hours
- ⏳ Implement L2 order signer skeleton: 1 hour
- ⏳ Documentation: 0.5 hours

**Total Progress**: ~30% of Phase 2 complete

---

## Current Status

✅ **Completed**:
- API documentation review
- Base URLs verified
- Test script created
- Critical issue identified

🚧 **In Progress**:
- Installing StarkEx dependencies
- Updating authentication implementation

⏳ **Pending**:
- Testnet account creation
- Authentication testing
- L2 order signing implementation

---

## References

- [EdgeX Authentication Docs](https://edgex-1.gitbook.io/edgeX-documentation/api/authentication)
- [EdgeX Python SDK](https://github.com/edgex-Tech/edgex-python-sdk)
- [StarkEx Signature Docs](https://docs.starkware.co/starkex/crypto/signature.html)
- [Cairo Lang Package](https://pypi.org/project/cairo-lang/)
- [StarkEx Resources](https://github.com/starkware-libs/starkex-resources)

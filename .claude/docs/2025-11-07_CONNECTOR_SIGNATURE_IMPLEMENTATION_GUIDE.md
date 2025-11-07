# Connector Signature Implementation Guide

**Status**: Extended and Lighter connectors built, read-only mode active
**Goal**: Add order signing for live trading capability
**Date**: 2025-11-07

---

## 📋 Overview

Both connectors are **fully functional for funding rate monitoring** but need signature implementations for order placement.

### Current Status:
- ✅ Extended connector: Market data, funding rates (READ-ONLY)
- ✅ Lighter connector: Market data, funding rates (READ-ONLY)
- ❌ Extended connector: Order placement (NEEDS SIGNATURES)
- ❌ Lighter connector: Order placement (NEEDS SIGNATURES)

---

## 🔑 Extended DEX - Stark Signature Implementation

### Required Dependencies:

```bash
pip install git+https://github.com/x10xchange/python_sdk.git
```

**SDK**: x10 Python SDK (Extended Exchange Python SDK)
**Repository**: https://github.com/x10xchange/python_sdk
**Signature Type**: StarkWare Stark signatures

### Implementation Steps:

#### 1. Install SDK:
```bash
cd /Users/tdl321/hummingbot
pip install git+https://github.com/x10xchange/python_sdk.git
```

#### 2. Update `extended_perpetual_auth.py`:

**File**: `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_auth.py`

Add imports:
```python
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.orders import OrderSide, OrderType as X10OrderType
```

Update `__init__` method:
```python
def __init__(self, api_key: str, api_secret: str):
    self._api_key = api_key
    self._api_secret = api_secret

    # Initialize Stark account from SDK
    self._stark_account = StarkPerpetualAccount(
        api_key=api_key,
        private_key=api_secret,  # Stark private key
        public_key=self._derive_public_key(api_secret),
        config=MAINNET_CONFIG
    )
```

Implement `_sign_order` method:
```python
def _sign_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sign order using Stark signature.

    Args:
        order_params: {
            'market': 'KAITO-USD',
            'side': 'BUY' or 'SELL',
            'price': Decimal,
            'size': Decimal,
            'order_type': 'LIMIT' or 'MARKET',
            'client_order_id': str
        }

    Returns:
        Signed order ready for API submission
    """
    # Convert to X10 SDK format
    side = OrderSide.BUY if order_params['side'] == 'BUY' else OrderSide.SELL
    order_type = X10OrderType.LIMIT if order_params['order_type'] == 'LIMIT' else X10OrderType.MARKET

    # Use SDK to sign
    signed_order = self._stark_account.sign_order(
        market=order_params['market'],
        side=side,
        price=str(order_params['price']),
        size=str(order_params['size']),
        order_type=order_type,
        client_order_id=order_params['client_order_id']
    )

    return signed_order
```

#### 3. Update `extended_perpetual_derivative.py`:

**File**: `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_derivative.py`

Update `_place_order` method (around line 274):
```python
async def _place_order(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        trade_type: TradeType,
        order_type: OrderType,
        price: Decimal,
        position_action: PositionAction = PositionAction.NIL,
        **kwargs,
) -> Tuple[str, float]:
    """Place an order on Extended."""
    try:
        ex_trading_pair = await self.exchange_symbol_associated_to_pair(trading_pair)

        # Prepare order parameters
        order_params = {
            'market': ex_trading_pair,
            'side': 'BUY' if trade_type == TradeType.BUY else 'SELL',
            'price': price,
            'size': amount,
            'order_type': 'LIMIT' if order_type == OrderType.LIMIT else 'MARKET',
            'client_order_id': order_id
        }

        # Sign order using authenticator
        if self.authenticator:
            signed_order = self.authenticator._sign_order(order_params)
        else:
            raise ValueError("No authenticator available for order signing")

        # Submit to Extended API
        response = await self._api_post(
            path_url=CONSTANTS.CREATE_ORDER_URL,
            data=signed_order,
            is_auth_required=True
        )

        # Parse response
        exchange_order_id = response.get('orderId', '')
        timestamp = self.current_timestamp

        return exchange_order_id, timestamp

    except Exception as e:
        self.logger().error(f"Error placing order: {e}", exc_info=True)
        raise
```

---

## 🔑 Lighter DEX - Transaction Signing Implementation

### Required Dependencies:

```bash
pip install lighter-sdk
# OR
pip install git+https://github.com/elliottech/lighter-python.git
```

**SDK**: lighter-python
**Repository**: https://github.com/elliottech/lighter-python
**Signature Type**: Lighter zkRollup transaction signing

### Implementation Steps:

#### 1. Install SDK:
```bash
cd /Users/tdl321/hummingbot
pip install lighter-sdk
```

#### 2. Update `lighter_perpetual_auth.py`:

**File**: `hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_auth.py`

Add imports:
```python
import lighter
from lighter import ApiClient, TransactionApi
```

Update `__init__` method:
```python
def __init__(self, api_key: str, api_secret: str):
    self._api_key = api_key
    self._api_secret = api_secret

    # Initialize Lighter client
    self._lighter_client = lighter.ApiClient(
        api_key=api_key,
        api_secret=api_secret
    )
```

Implement `_sign_order` method:
```python
async def _sign_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sign order using Lighter SDK.

    Args:
        order_params: {
            'market_id': int,
            'side': 'BUY' or 'SELL',
            'price': str,
            'amount': str,
            'order_type': 'LIMIT' or 'MARKET'
        }

    Returns:
        Signed transaction ready for API submission
    """
    # Use Lighter SDK to create and sign transaction
    tx_api = lighter.TransactionApi(self._lighter_client)

    # Create order transaction
    order_tx = await tx_api.create_order_transaction(
        market_id=order_params['market_id'],
        side=order_params['side'].lower(),  # 'buy' or 'sell'
        price=order_params['price'],
        amount=order_params['amount'],
        order_type=order_params['order_type'].lower()  # 'limit' or 'market'
    )

    return order_tx
```

#### 3. Update `lighter_perpetual_derivative.py`:

**File**: `hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_derivative.py`

Update `_place_order` method (around line 235):
```python
async def _place_order(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        trade_type: TradeType,
        order_type: OrderType,
        price: Decimal,
        position_action: PositionAction = PositionAction.NIL,
        **kwargs,
) -> Tuple[str, float]:
    """Place an order on Lighter."""
    try:
        # Get market ID for this trading pair
        if not self._market_id_map:
            await self._initialize_market_mappings()

        market_id = self._market_id_map.get(trading_pair)
        if market_id is None:
            raise ValueError(f"Market ID not found for {trading_pair}")

        # Prepare order parameters
        order_params = {
            'market_id': market_id,
            'side': 'BUY' if trade_type == TradeType.BUY else 'SELL',
            'price': str(price),
            'amount': str(amount),
            'order_type': 'LIMIT' if order_type == OrderType.LIMIT else 'MARKET'
        }

        # Sign order using authenticator
        if self.authenticator:
            signed_tx = await self.authenticator._sign_order(order_params)
        else:
            raise ValueError("No authenticator available for transaction signing")

        # Submit to Lighter API
        response = await self._api_post(
            path_url=CONSTANTS.SEND_TX_URL,
            data=signed_tx,
            is_auth_required=True
        )

        # Parse response
        exchange_order_id = response.get('tx_hash', '')
        timestamp = self.current_timestamp

        return exchange_order_id, timestamp

    except Exception as e:
        self.logger().error(f"Error placing order: {e}", exc_info=True)
        raise
```

---

## 🧪 Testing Order Placement

### Step 1: Test with Small Amounts

Create test script `test_order_placement.py`:

```python
import asyncio
from decimal import Decimal
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative
from hummingbot.core.data_type.common import OrderType, TradeType, PositionAction

async def test_extended_order():
    """Test order placement on Extended with $1."""

    connector = ExtendedPerpetualDerivative(
        extended_perpetual_api_key="YOUR_API_KEY",
        extended_perpetual_api_secret="YOUR_STARK_PRIVATE_KEY",
        trading_pairs=["KAITO-USD"],
        trading_required=True
    )

    await connector.start_network()

    try:
        # Place small test order
        exchange_order_id, timestamp = await connector._place_order(
            order_id="test_001",
            trading_pair="KAITO-USD",
            amount=Decimal("1"),  # $1 worth
            trade_type=TradeType.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("0.10"),  # Set limit price
            position_action=PositionAction.OPEN
        )

        print(f"✅ Order placed successfully!")
        print(f"   Exchange Order ID: {exchange_order_id}")
        print(f"   Timestamp: {timestamp}")

    except Exception as e:
        print(f"❌ Order failed: {e}")

    finally:
        await connector.stop_network()

# Run test
asyncio.run(test_extended_order())
```

### Step 2: Verify Order Status

Check Extended/Lighter UI or API to confirm:
- Order appears in order book
- Order fills correctly
- Position opens as expected

### Step 3: Test Cancellation

```python
# Cancel order
await connector._place_cancel("test_001", tracked_order)
```

---

## 📦 Complete Installation Commands

```bash
cd /Users/tdl321/hummingbot

# Install Extended (x10) SDK
pip install git+https://github.com/x10xchange/python_sdk.git

# Install Lighter SDK
pip install lighter-sdk

# Verify installations
python -c "import x10; print('x10 SDK:', x10.__version__)"
python -c "import lighter; print('Lighter SDK installed')"
```

---

## 🔐 API Key Setup

### Extended DEX:
1. Go to https://extended.exchange
2. Connect wallet
3. Create sub-account
4. Generate API key + Stark key
5. Save both securely

### Lighter DEX:
1. Go to https://lighter.xyz
2. Connect Ethereum wallet
3. Create account (sign registration message)
4. Create sub-account
5. Generate API key (up to 256 keys per sub-account)
6. Save API key + secret securely

---

## ⚠️ Important Security Notes

1. **Never commit API keys to git**
2. **Test with small amounts first** ($1-$10)
3. **Use paper trading mode initially**
4. **Verify order fills before scaling up**
5. **Monitor positions closely after enabling live trading**

---

## 🎯 Next Steps After Implementation

1. ✅ Install both SDKs
2. ✅ Update auth classes with signature methods
3. ✅ Update _place_order methods
4. ✅ Test with $1 orders
5. ✅ Verify order fills
6. ✅ Test cancellation
7. ✅ Enable in production strategy
8. ✅ Scale up position sizes

---

## 📝 Files Modified

### Extended:
- `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_auth.py`
- `hummingbot/connector/derivative/extended_perpetual/extended_perpetual_derivative.py`

### Lighter:
- `hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_auth.py`
- `hummingbot/connector/derivative/lighter_perpetual/lighter_perpetual_derivative.py`

---

## 💡 Troubleshooting

### "Invalid Signature" Error:
- Check API key is correct
- Verify Stark private key (Extended)
- Ensure nonce is incrementing (Lighter)

### "Insufficient Balance" Error:
- Check account has sufficient collateral
- Verify leverage settings
- Check margin requirements

### "Market Not Found" Error:
- Verify trading pair format
- Check market is active
- Ensure market ID is correct (Lighter)

---

## 📚 References

- Extended (x10) SDK: https://github.com/x10xchange/python_sdk
- Extended API Docs: http://api.docs.extended.exchange/
- Lighter SDK: https://github.com/elliottech/lighter-python
- Lighter API Docs: https://apidocs.lighter.xyz/
- StarkNet Signing: https://starknetpy.readthedocs.io/en/latest/guide/signing.html

---

**Status**: Guide complete, implementation ready to begin
**Estimated Time**: 4-6 hours per connector
**Difficulty**: Intermediate to Advanced

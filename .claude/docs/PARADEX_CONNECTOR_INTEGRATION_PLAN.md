# Paradex Perpetual Connector Integration Plan

**Date**: 2025-11-11
**Status**: Planning Phase
**Target**: Integrate Paradex DEX perpetual futures connector into Hummingbot

---

## 🚨 CRITICAL: Read This First

**BEFORE implementing this connector**, you MUST read:
📄 **[PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md](PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md)**

This document catalogs **every mistake** made in Extended and Lighter connectors and provides prevention strategies. Use it as a checklist throughout implementation.

---

## Table of Contents
1. [Overview](#1-overview)
2. [Paradex Platform Details](#2-paradex-platform-details)
3. [Authentication Architecture](#3-authentication-architecture)
4. [API Endpoints Mapping](#4-api-endpoints-mapping)
5. [Connector Architecture](#5-connector-architecture)
6. [File-by-File Implementation Guide](#6-file-by-file-implementation-guide)
7. [SDK Integration (paradex_py)](#7-sdk-integration-paradex_py)
8. [WebSocket Channel Mapping](#8-websocket-channel-mapping)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Checklist](#10-deployment-checklist)
11. [Appendix: Code Templates](#11-appendix-code-templates)

---

## 1. Overview

### 1.1 Objective
Create a Hummingbot connector for Paradex DEX perpetual futures trading, following the same architectural pattern as the Extended and Lighter perpetual connectors.

### 1.2 Paradex DEX Summary
- **Platform**: Starknet Layer 2 DEX
- **Markets**: 250+ including perpetual futures, dated options, perpetual options, pre-markets, spot
- **Key Features**:
  - Zero trading fees for retail traders (100+ perpetual markets)
  - Privacy-focused (zk-encrypted accounts)
  - Better-than-CEX liquidity
  - Unified margin account
  - Early token listings
- **Website**: https://paradex.trade
- **Documentation**: https://docs.paradex.trade

### 1.3 Connector Pattern
Following the proven pattern from Extended and Lighter connectors:
- Inherit from `PerpetualDerivativePyBase`
- 8 core files per connector
- SDK integration for authentication and signing
- WebSocket for real-time data
- REST API for account/order operations

---

## 2. Paradex Platform Details

### 2.1 Technical Specifications

| Aspect | Details |
|--------|---------|
| **Network** | Starknet (Layer 2) |
| **Base URL (Testnet)** | `https://api.testnet.paradex.trade/v1` |
| **Base URL (Mainnet)** | `https://api.prod.paradex.trade/v1` |
| **WebSocket URL** | TBD from docs |
| **API Version** | v1 |
| **Authentication** | JWT tokens |
| **Order Signing** | Starknet signatures |
| **SDK** | `paradex_py` (PyPI) |

### 2.2 Trading Features

#### Fee Structure
- **Perpetual Futures (Retail)**: 0% maker, 0% taker (100+ markets)
- **Other Products**: TBD (likely maker/taker fees for options, dated contracts)

#### Leverage
- TBD - Need to verify max leverage per market from API

#### Funding Rates
- TBD - Need to confirm funding interval (8hr standard or different?)

#### Position Modes
- **One-Way Mode**: Standard (likely default)
- **Hedge Mode**: TBD - Need to verify support

### 2.3 Market Types
1. **Perpetual Futures**: BTC-USD-PERP, ETH-USD-PERP, etc.
2. **Dated Options**: Traditional options with expiry
3. **Perpetual Options**: Novel product with no expiry
4. **Pre-Markets**: Early token trading
5. **Spot**: Traditional spot markets

**Focus for v1 connector**: Perpetual Futures only

---

## 3. Authentication Architecture

### 3.1 Authentication Methods

Paradex provides three credential tiers:

#### 3.1.1 Main Private Key (Full Access)
- **Access Level**: Complete account control
- **Capabilities**: Trading, withdrawals, transfers
- **Risk**: High - can drain account
- **Use Case**: Account setup, fund management
- **SDK Class**: `Paradex` (requires L1 + L2 credentials)

```python
from paradex import Paradex, Environment

paradex = Paradex(
    env=Environment.MAINNET,
    l1_address="0x...",  # Ethereum address
    l1_private_key="0x...",  # Ethereum private key
    l2_private_key="0x..."  # Starknet private key
)
```

#### 3.1.2 Subkeys (Trading-Only Access) ⭐ **RECOMMENDED**
- **Access Level**: Restricted
- **Capabilities**: Place/cancel orders, read account data
- **Restrictions**: NO withdrawals, NO transfers, NO sensitive account changes
- **Risk**: Low - cannot drain funds
- **Use Case**: Algorithmic trading, bot operations
- **SDK Class**: `ParadexSubkey` (L2-only, no L1 needed)

```python
from paradex import ParadexSubkey, Environment

paradex = ParadexSubkey(
    env=Environment.MAINNET,
    l2_private_key="0x...",  # Randomly generated Starknet keypair
    l2_account_address="0x..."  # Main account address
)
```

**Subkey Authentication Flow**:
1. Generate random Starknet keypair (subkey)
2. Register subkey with main account via main key
3. Use subkey for all trading operations
4. Subkey signs orders, includes main account address in headers

**Required Headers with Subkeys**:
- `Authorization: Bearer {jwt_token}` - JWT from subkey
- `PARADEX-STARKNET-ACCOUNT`: Main account address
- `PARADEX-STARKNET-SIGNATURE`: Signature from subkey

#### 3.1.3 Readonly Tokens
- **Access Level**: Read-only
- **Capabilities**: GET requests only (balances, positions, orders)
- **Use Case**: Monitoring, analytics, dashboards
- **Implementation**: Extended-expiry JWT

### 3.2 JWT Token Management

#### Token Generation
```python
# Via paradex_py SDK
jwt_token = await paradex.auth.get_jwt_token()
```

#### Token Properties
- **Format**: Standard JWT (JSON Web Token)
- **Expiration**: TBD (need to check SDK default, typically 1-24 hours)
- **Refresh**: Required before expiry
- **Storage**: In-memory only (regenerate on restart)

#### Token Usage
```python
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
```

### 3.3 Order Signing

Orders require Starknet signature:
- **Method**: ECDSA on Stark curve
- **SDK Handling**: `paradex_py` handles signing internally
- **Connector Role**: Call SDK methods, don't implement signing

```python
# SDK handles signing automatically
order = await paradex_client.submit_order(
    market="BTC-USD-PERP",
    side="BUY",
    size="0.1",
    order_type="LIMIT",
    price="50000"
)
```

---

## 4. API Endpoints Mapping

### 4.1 Public Endpoints (No Authentication)

| Purpose | Method | Endpoint | Hummingbot Usage |
|---------|--------|----------|------------------|
| List Markets | GET | `/v1/markets` | Trading rules, market info |
| Market Summary | GET | `/v1/markets/{market}/summary` | Ticker, 24h stats |
| System Config | GET | `/v1/system/config` | Exchange metadata |
| Order Book | GET | `/v1/markets/{market}/orderbook` | Snapshot (fallback) |
| Recent Trades | GET | `/v1/markets/{market}/trades` | Trade history |
| Candles | GET | `/v1/markets/{market}/candles` | Historical OHLCV |
| Funding Rates | GET | `/v1/markets/{market}/funding` | Funding rate data |
| Health Check | GET | `/v1/system/health` | Ping endpoint |

### 4.2 Private Endpoints (Require JWT)

#### Account Management
| Purpose | Method | Endpoint | Hummingbot Usage |
|---------|--------|----------|------------------|
| Account Summary | GET | `/v1/account` | Account details |
| Account Profile | GET | `/v1/account/profile` | User metadata |
| Balances | GET | `/v1/account/balances` | Asset balances |
| Positions | GET | `/v1/positions` | Open positions |

#### Trading Operations
| Purpose | Method | Endpoint | Hummingbot Usage |
|---------|--------|----------|------------------|
| Create Order | POST | `/v1/orders` | Place order (via SDK) |
| Cancel Order | DELETE | `/v1/orders/{order_id}` | Cancel order (via SDK) |
| Cancel All | DELETE | `/v1/orders` | Mass cancel (via SDK) |
| Modify Order | PUT | `/v1/orders/{order_id}` | Edit order (via SDK) |
| List Orders | GET | `/v1/orders` | Active orders |
| Order History | GET | `/v1/orders/history` | Filled/cancelled |
| Fills | GET | `/v1/fills` | Trade fills |

#### Transfers & Funding
| Purpose | Method | Endpoint | Hummingbot Usage |
|---------|--------|----------|------------------|
| Transfers | POST | `/v1/transfers` | Deposits/withdrawals |
| Transfer History | GET | `/v1/transfers/history` | Transaction log |
| Funding Payments | GET | `/v1/funding_payments` | Funding history |

#### Authentication
| Purpose | Method | Endpoint | Hummingbot Usage |
|---------|--------|----------|------------------|
| Onboard Account | POST | `/v1/onboarding` | Initial setup |
| Get JWT | POST | `/v1/auth` | Token generation |

### 4.3 WebSocket Channels

#### Public Channels
| Channel | Subscription | Data | Hummingbot Usage |
|---------|--------------|------|------------------|
| Markets Summary | `markets_summary` | Ticker, stats, funding | Market data |
| Order Book | `orderbook.{market}` | Bids/asks updates | Order book |
| Trades | `trades.{market}` | Public trades | Recent trades |

#### Private Channels (Require Auth)
| Channel | Subscription | Data | Hummingbot Usage |
|---------|--------------|------|------------------|
| Account | `account` | Account updates | General account |
| Orders | `orders` | Order state changes | Order tracking |
| Fills | `fills` | Trade executions | Fill events |
| Positions | `positions` | Position changes | Position tracking |
| Balance Events | `balance_events` | Balance changes | Real-time balance |

---

## 5. Connector Architecture

### 5.1 File Structure

```
hummingbot/connector/derivative/paradex_perpetual/
├── __init__.py                                    # Module initialization
├── paradex_perpetual_constants.py                # Constants, endpoints, rate limits
├── paradex_perpetual_utils.py                    # Config map, fees, domain settings
├── paradex_perpetual_auth.py                     # JWT authentication, SDK wrapper
├── paradex_perpetual_web_utils.py                # HTTP client factory
├── paradex_perpetual_derivative.py               # Main connector logic
├── paradex_perpetual_api_order_book_data_source.py  # Market data streaming
└── paradex_perpetual_user_stream_data_source.py  # Private user data streaming
```

### 5.2 Class Hierarchy

```
PerpetualDerivativePyBase (abstract)
    └── ParadexPerpetualDerivative
            ├── ParadexPerpetualAuth
            ├── ParadexPerpetualAPIOrderBookDataSource
            └── ParadexPerpetualUserStreamDataSource
```

### 5.3 Component Responsibilities

#### 5.3.1 Constants File
- API endpoint paths
- Base URLs (mainnet/testnet)
- WebSocket URLs
- Rate limit definitions
- Order state mappings
- Error messages
- Funding rate intervals
- Default values

#### 5.3.2 Utils File
- Connector configuration schema
- Fee structure definition
- Domain settings (mainnet/testnet)
- Example trading pairs
- Helper functions

#### 5.3.3 Auth File
- JWT token management
- SDK initialization
- Request signing (delegated to SDK)
- Header injection
- Token refresh logic

#### 5.3.4 Web Utils File
- Async HTTP client creation
- Request/response handling
- Error parsing
- API throttler integration
- Retry logic

#### 5.3.5 Main Derivative File
- Core trading logic
- Order lifecycle management
- Balance/position updates
- Trading rule enforcement
- Funding rate tracking
- SDK method calls for orders

#### 5.3.6 Order Book Data Source
- WebSocket subscription management
- Order book snapshot/update parsing
- Trade stream handling
- Funding rate extraction
- Market data caching

#### 5.3.7 User Stream Data Source
- Private WebSocket channels
- Order update events
- Trade fill events
- Position change events
- Balance update events
- Event parsing to Hummingbot format

---

## 6. File-by-File Implementation Guide

### 6.1 `__init__.py`

**Purpose**: Module initialization and exports

**Implementation**:
```python
"""Paradex Perpetual Derivative Connector."""

from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative import (
    ParadexPerpetualDerivative,
)

__all__ = ["ParadexPerpetualDerivative"]
```

---

### 6.2 `paradex_perpetual_constants.py`

**Purpose**: Centralized constants for API interaction

**Key Components**:

#### Exchange Metadata
```python
EXCHANGE_NAME = "paradex_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = 36  # UUID format
DOMAIN = EXCHANGE_NAME
TESTNET_DOMAIN = "paradex_perpetual_testnet"
```

#### Base URLs
```python
# Mainnet
PERPETUAL_BASE_URL = "https://api.prod.paradex.trade/v1"
PERPETUAL_WS_URL = "wss://ws.prod.paradex.trade/v1/ws"  # TBD - verify

# Testnet
TESTNET_BASE_URL = "https://api.testnet.paradex.trade/v1"
TESTNET_WS_URL = "wss://ws.testnet.paradex.trade/v1/ws"  # TBD - verify
```

#### API Endpoints
```python
# Public
MARKETS_INFO_URL = "/markets"
MARKET_SUMMARY_URL = "/markets/{market}/summary"
SYSTEM_CONFIG_URL = "/system/config"
ORDER_BOOK_URL = "/markets/{market}/orderbook"
TRADES_URL = "/markets/{market}/trades"
CANDLES_URL = "/markets/{market}/candles"
FUNDING_RATE_URL = "/markets/{market}/funding"
HEALTH_CHECK_URL = "/system/health"

# Private - Account
ACCOUNT_SUMMARY_URL = "/account"
ACCOUNT_PROFILE_URL = "/account/profile"
BALANCES_URL = "/account/balances"
POSITIONS_URL = "/positions"

# Private - Trading
CREATE_ORDER_URL = "/orders"
CANCEL_ORDER_URL = "/orders/{order_id}"
CANCEL_ALL_ORDERS_URL = "/orders"
MODIFY_ORDER_URL = "/orders/{order_id}"
LIST_ORDERS_URL = "/orders"
ORDER_HISTORY_URL = "/orders/history"
FILLS_URL = "/fills"

# Private - Transfers
TRANSFERS_URL = "/transfers"
TRANSFER_HISTORY_URL = "/transfers/history"
FUNDING_PAYMENTS_URL = "/funding_payments"

# Authentication
ONBOARD_URL = "/onboarding"
AUTH_URL = "/auth"

# Ping
PING_URL = "/system/health"
```

#### WebSocket Channels
```python
# Public channels
WS_CHANNEL_MARKETS_SUMMARY = "markets_summary"
WS_CHANNEL_ORDERBOOK = "orderbook.{market}"
WS_CHANNEL_TRADES = "trades.{market}"

# Private channels
WS_CHANNEL_ACCOUNT = "account"
WS_CHANNEL_ORDERS = "orders"
WS_CHANNEL_FILLS = "fills"
WS_CHANNEL_POSITIONS = "positions"
WS_CHANNEL_BALANCE_EVENTS = "balance_events"
```

#### Order States
```python
ORDER_STATE = {
    "PENDING": OrderState.PENDING_CREATE,
    "OPEN": OrderState.OPEN,
    "FILLED": OrderState.FILLED,
    "PARTIALLY_FILLED": OrderState.PARTIALLY_FILLED,
    "CANCELLED": OrderState.CANCELED,
    "EXPIRED": OrderState.CANCELED,
    "REJECTED": OrderState.FAILED,
    "FAILED": OrderState.FAILED,
}
```

#### Rate Limits
```python
# TBD - Need actual limits from Paradex docs
# Conservative estimates based on similar DEXs
MAX_REQUEST_PER_MINUTE = 1200  # 20 per second
MAX_REQUEST_PER_SECOND = 20

ALL_ENDPOINTS_LIMIT = "All"

RATE_LIMITS = [
    RateLimit(ALL_ENDPOINTS_LIMIT, limit=MAX_REQUEST_PER_MINUTE, time_interval=60),
    # ... individual endpoint limits
]
```

#### Other Constants
```python
CURRENCY = "USD"  # Quote currency
FUNDING_RATE_UPDATE_INTERNAL_SECOND = 30  # Poll every 30s
HEARTBEAT_TIME_INTERVAL = 30.0
```

---

### 6.3 `paradex_perpetual_utils.py`

**Purpose**: Configuration schema and utility functions

**Key Components**:

#### Fee Schema
```python
from decimal import Decimal
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

# Zero fees for retail traders
DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0"),
    taker_percent_fee_decimal=Decimal("0"),
    buy_percent_fee_deducted_from_returns=True
)

CENTRALIZED = False  # Paradex is a DEX
EXAMPLE_PAIR = "BTC-USD-PERP"
BROKER_ID = "HBOT"
```

#### Configuration Map
```python
from pydantic import Field, SecretStr
from hummingbot.client.config.config_data_types import BaseConnectorConfigMap

class ParadexPerpetualConfigMap(BaseConnectorConfigMap):
    connector: str = "paradex_perpetual"

    # Subkey private key (recommended)
    paradex_perpetual_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Paradex subkey private key (Starknet hex)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )

    # Main account address (for subkey authentication)
    paradex_perpetual_account_address: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Paradex main account address (0x...)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )

KEYS = ParadexPerpetualConfigMap.model_construct()
```

#### Testnet Configuration
```python
class ParadexPerpetualTestnetConfigMap(BaseConnectorConfigMap):
    connector: str = "paradex_perpetual_testnet"
    # Similar fields as mainnet

OTHER_DOMAINS = ["paradex_perpetual_testnet"]
OTHER_DOMAINS_PARAMETER = {"paradex_perpetual_testnet": "paradex_perpetual_testnet"}
OTHER_DOMAINS_EXAMPLE_PAIR = {"paradex_perpetual_testnet": "BTC-USD-PERP"}
OTHER_DOMAINS_DEFAULT_FEES = {"paradex_perpetual_testnet": [0, 0]}
OTHER_DOMAINS_KEYS = {"paradex_perpetual_testnet": ParadexPerpetualTestnetConfigMap.model_construct()}
```

---

### 6.4 `paradex_perpetual_auth.py`

**Purpose**: Authentication management with paradex_py SDK

**Key Components**:

#### Imports
```python
import time
from typing import Any, Dict, Optional
from paradex import ParadexSubkey, Environment
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest
```

#### Auth Class Structure
```python
class ParadexPerpetualAuth(AuthBase):
    """
    Authentication handler for Paradex Perpetual API.

    Uses paradex_py SDK for:
    - JWT token generation
    - Order signing (via SDK methods)
    - Subkey authentication (L2-only, trading restrictions)
    """

    def __init__(
        self,
        api_secret: str,  # Starknet subkey private key
        account_address: str,  # Main account address
        environment: str = "mainnet"
    ):
        self._api_secret = api_secret
        self._account_address = account_address
        self._environment = Environment.PROD if environment == "mainnet" else Environment.TESTNET

        # JWT token management
        self._jwt_token: Optional[str] = None
        self._jwt_expires_at: Optional[float] = None

        # Lazy-initialize SDK client
        self._paradex_client: Optional[ParadexSubkey] = None

    def _initialize_client(self):
        """Initialize ParadexSubkey client."""
        if self._paradex_client is None:
            self._paradex_client = ParadexSubkey(
                env=self._environment,
                l2_private_key=self._api_secret,
                l2_account_address=self._account_address
            )

    async def get_jwt_token(self) -> str:
        """
        Get valid JWT token, refreshing if needed.

        Returns:
            Valid JWT token string
        """
        # Check if token exists and is not expired
        if self._jwt_token and self._jwt_expires_at:
            # Refresh 5 minutes before expiry
            if time.time() < (self._jwt_expires_at - 300):
                return self._jwt_token

        # Generate new token via SDK
        self._initialize_client()
        token_response = await self._paradex_client.auth.get_jwt_token()

        self._jwt_token = token_response["jwt_token"]
        self._jwt_expires_at = token_response["expires_at"]  # Unix timestamp

        return self._jwt_token

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Add authentication headers to REST requests.

        Paradex requires:
        - Authorization: Bearer {jwt_token}
        - PARADEX-STARKNET-ACCOUNT: {main_account_address} (for subkeys)
        """
        if request.headers is None:
            request.headers = {}

        # Get valid JWT token
        jwt_token = await self.get_jwt_token()

        # Add authentication headers
        request.headers["Authorization"] = f"Bearer {jwt_token}"
        request.headers["PARADEX-STARKNET-ACCOUNT"] = self._account_address

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Add authentication to WebSocket requests.

        Paradex WebSocket auth sends JWT in initial subscription message.
        """
        # Get valid JWT token
        jwt_token = await self.get_jwt_token()

        # Add to request payload (exact format TBD from docs)
        if request.payload is None:
            request.payload = {}

        request.payload["jwt_token"] = jwt_token
        request.payload["account"] = self._account_address

        return request

    def get_paradex_client(self) -> ParadexSubkey:
        """
        Get ParadexSubkey client for order operations.

        Returns:
            ParadexSubkey instance for SDK method calls
        """
        self._initialize_client()
        return self._paradex_client
```

---

### 6.5 `paradex_perpetual_web_utils.py`

**Purpose**: Web client factory and utilities

**Key Components**:

```python
from typing import Any, Dict, Optional
from hummingbot.connector.derivative.paradex_perpetual import paradex_perpetual_constants as CONSTANTS
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.auth import AuthBase

def build_api_factory(
    throttler: Optional[AsyncThrottler] = None,
    auth: Optional[AuthBase] = None,
) -> WebAssistantsFactory:
    """
    Build WebAssistantsFactory for Paradex API.

    Args:
        throttler: Rate limiter
        auth: Authentication handler

    Returns:
        Configured WebAssistantsFactory
    """
    throttler = throttler or create_throttler()
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        auth=auth,
    )
    return api_factory

def create_throttler() -> AsyncThrottler:
    """Create rate limiter with Paradex limits."""
    return AsyncThrottler(CONSTANTS.RATE_LIMITS)

def get_rest_url_for_endpoint(
    endpoint: str,
    domain: str = CONSTANTS.DOMAIN
) -> str:
    """
    Get full REST URL for endpoint.

    Args:
        endpoint: API endpoint path
        domain: Domain (mainnet or testnet)

    Returns:
        Full URL
    """
    base_url = (
        CONSTANTS.TESTNET_BASE_URL
        if domain == CONSTANTS.TESTNET_DOMAIN
        else CONSTANTS.PERPETUAL_BASE_URL
    )
    return f"{base_url}{endpoint}"

def get_ws_url_for_endpoint(
    domain: str = CONSTANTS.DOMAIN
) -> str:
    """
    Get WebSocket URL.

    Args:
        domain: Domain (mainnet or testnet)

    Returns:
        WebSocket URL
    """
    return (
        CONSTANTS.TESTNET_WS_URL
        if domain == CONSTANTS.TESTNET_DOMAIN
        else CONSTANTS.PERPETUAL_WS_URL
    )
```

---

### 6.6 `paradex_perpetual_derivative.py`

**Purpose**: Main connector implementation

**Key Structure** (400+ lines, showing outline):

```python
class ParadexPerpetualDerivative(PerpetualDerivativePyBase):
    """
    Paradex Perpetual Derivative connector.

    Implements perpetual futures trading on Paradex DEX via paradex_py SDK.
    """

    web_utils = web_utils
    SHORT_POLL_INTERVAL = 5.0
    LONG_POLL_INTERVAL = 12.0

    def __init__(
        self,
        balance_asset_limit: Optional[Dict[str, Dict[str, Decimal]]] = None,
        rate_limits_share_pct: Decimal = Decimal("100"),
        paradex_perpetual_api_secret: str = None,
        paradex_perpetual_account_address: str = None,
        trading_pairs: Optional[List[str]] = None,
        trading_required: bool = True,
        domain: str = CONSTANTS.DOMAIN,
    ):
        """Initialize Paradex connector."""
        self.paradex_perpetual_api_secret = api_secret
        self.paradex_perpetual_account_address = account_address
        self._trading_required = trading_required
        self._trading_pairs = trading_pairs
        self._domain = domain
        self._position_mode = None
        self._last_funding_fee_payment_ts: Dict[str, float] = {}
        super().__init__(balance_asset_limit, rate_limits_share_pct)

    # Properties
    @property
    def name(self) -> str:
        return self._domain

    @property
    def authenticator(self) -> Optional[ParadexPerpetualAuth]:
        return self._auth

    # Core methods (implement from PerpetualDerivativePyBase)
    async def _update_balances(self):
        """Fetch balances from /account/balances endpoint."""
        # GET /v1/account/balances
        pass

    async def _update_positions(self):
        """Fetch positions from /positions endpoint."""
        # GET /v1/positions
        pass

    async def _update_trading_rules(self):
        """Fetch trading rules from /markets endpoint."""
        # GET /v1/markets
        pass

    async def _update_funding_rates(self):
        """Fetch funding rates from market data."""
        # GET /v1/markets/{market}/funding
        pass

    async def _place_order(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        trade_type: TradeType,
        order_type: OrderType,
        price: Decimal,
        **kwargs
    ) -> Tuple[str, float]:
        """
        Place order via paradex_py SDK.

        Uses SDK's submit_order() method which handles signing.
        """
        # Get ParadexSubkey client
        client = self._auth.get_paradex_client()

        # Build order via SDK
        order = await client.submit_order(
            market=trading_pair,
            side="BUY" if trade_type == TradeType.BUY else "SELL",
            size=str(amount),
            order_type="LIMIT" if order_type == OrderType.LIMIT else "MARKET",
            price=str(price) if order_type == OrderType.LIMIT else None,
            # ... other params
        )

        return order["id"], order["created_at"]

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        """
        Cancel order via paradex_py SDK.

        Uses SDK's cancel_order() method which handles signing.
        """
        client = self._auth.get_paradex_client()
        await client.cancel_order(order_id=order_id)

    # Other required methods...
```

---

### 6.7 `paradex_perpetual_api_order_book_data_source.py`

**Purpose**: Market data streaming via WebSocket

**Key Structure**:

```python
class ParadexPerpetualAPIOrderBookDataSource(OrderBookTrackerDataSource):
    """
    Order book data source for Paradex.

    Manages WebSocket subscriptions for:
    - Order book snapshots and updates
    - Trade stream
    - Market summaries (for funding rates)
    """

    async def listen_for_subscriptions(self):
        """Main WebSocket listener loop."""
        # Connect to Paradex WebSocket
        # Subscribe to:
        # - orderbook.{market} for each trading pair
        # - trades.{market} for each trading pair
        # - markets_summary for funding rates
        pass

    async def listen_for_order_book_diffs(self):
        """Parse order book updates from WebSocket."""
        pass

    async def listen_for_order_book_snapshots(self):
        """Parse order book snapshots."""
        pass

    async def listen_for_trades(self):
        """Parse trade events."""
        pass

    async def get_funding_info(self, trading_pair: str):
        """Extract funding rate from market summary or REST API."""
        pass
```

---

### 6.8 `paradex_perpetual_user_stream_data_source.py`

**Purpose**: Private user data streaming via WebSocket

**Key Structure**:

```python
class ParadexPerpetualUserStreamDataSource(UserStreamTrackerDataSource):
    """
    User stream data source for Paradex.

    Manages authenticated WebSocket for:
    - Order updates (orders channel)
    - Trade fills (fills channel)
    - Position changes (positions channel)
    - Balance updates (balance_events channel)
    """

    async def listen_for_user_stream(self):
        """Main authenticated WebSocket listener loop."""
        # Connect with JWT authentication
        # Subscribe to private channels:
        # - orders
        # - fills
        # - positions
        # - balance_events
        pass

    def _parse_order_update(self, event: Dict) -> OrderUpdate:
        """Parse order update event into Hummingbot format."""
        pass

    def _parse_trade_update(self, event: Dict) -> TradeUpdate:
        """Parse fill event into Hummingbot format."""
        pass

    def _parse_position_update(self, event: Dict):
        """Parse position change event."""
        pass

    def _parse_balance_update(self, event: Dict):
        """Parse balance update event."""
        pass
```

---

## 7. SDK Integration (paradex_py)

### 7.1 Installation

```bash
pip install paradex_py
```

**Current Version**: 0.4.6 (as of Nov 2025)

### 7.2 SDK Structure

#### Main Classes

| Class | Purpose | Credentials Required | Use Case |
|-------|---------|---------------------|----------|
| `Paradex` | Full access (L1+L2) | Ethereum + Starknet keys | Initial setup, withdrawals |
| `ParadexSubkey` | Trading-only (L2) | Subkey + main address | Bot trading ⭐ |
| `ParadexApiClient` | REST API wrapper | JWT token | HTTP requests |
| `ParadexWebsocketClient` | WebSocket wrapper | JWT token | Real-time data |

#### Environment Enum
```python
from paradex import Environment

Environment.PROD     # Mainnet
Environment.TESTNET  # Testnet
```

### 7.3 Key SDK Methods

#### Authentication
```python
# Initialize subkey client (recommended for connector)
from paradex import ParadexSubkey, Environment

client = ParadexSubkey(
    env=Environment.PROD,
    l2_private_key="0x...",  # Subkey private key
    l2_account_address="0x..."  # Main account address
)

# Get JWT token
jwt = await client.auth.get_jwt_token()
```

#### Account Operations
```python
# Fetch account summary
account = await client.fetch_account_summary()

# Fetch balances
balances = await client.fetch_balances()
# Returns: {"balances": [{"asset": "USDC", "available": "1000", ...}, ...]}

# Fetch positions
positions = await client.fetch_positions()
```

#### Order Operations
```python
# Place limit order
order = await client.submit_order(
    market="BTC-USD-PERP",
    side="BUY",  # or "SELL"
    size="0.1",
    order_type="LIMIT",
    price="50000",
    time_in_force="GTC",  # GTC, IOC, FOK
    client_id="my_order_123"  # Optional custom ID
)

# Place market order
order = await client.submit_order(
    market="BTC-USD-PERP",
    side="SELL",
    size="0.1",
    order_type="MARKET"
)

# Cancel order
await client.cancel_order(order_id="ORDER_ID")

# Cancel multiple orders
await client.cancel_orders_batch(order_ids=["ID1", "ID2", "ID3"])

# Modify order
await client.modify_order(
    order_id="ORDER_ID",
    size="0.2",  # New size
    price="51000"  # New price
)
```

#### Market Data
```python
# Fetch markets
markets = await client.fetch_markets()

# Fetch order book
orderbook = await client.fetch_orderbook(market="BTC-USD-PERP")
```

#### WebSocket Streaming
```python
from paradex import ParadexWebsocketClient

# Initialize WebSocket client
ws_client = ParadexWebsocketClient(env=Environment.PROD)

# Define callback
async def on_order_update(data):
    print(f"Order update: {data}")

# Subscribe to channel
await ws_client.subscribe(
    channel="orders",
    callback=on_order_update
)

# Keep connection alive
await ws_client.pump_until()  # Run forever
```

### 7.4 SDK Integration Strategy

#### In Auth File (`paradex_perpetual_auth.py`)
- Initialize `ParadexSubkey` instance
- Use for JWT token generation
- Expose via `get_paradex_client()` method

#### In Main Derivative File (`paradex_perpetual_derivative.py`)
- Call SDK methods for order operations:
  - `submit_order()` instead of raw POST /orders
  - `cancel_order()` instead of raw DELETE /orders/{id}
- Use REST API directly for read operations:
  - GET /account/balances
  - GET /positions
  - GET /markets

#### In Data Sources
- Use SDK's `ParadexWebsocketClient` for WebSocket connections
- Subscribe to channels via SDK methods
- Parse events from SDK callbacks

#### Error Handling
```python
from paradex.exceptions import ParadexAPIException

try:
    order = await client.submit_order(...)
except ParadexAPIException as e:
    # Handle API errors
    print(f"API error: {e.status_code} - {e.message}")
except Exception as e:
    # Handle other errors
    print(f"Unexpected error: {e}")
```

---

## 8. WebSocket Channel Mapping

### 8.1 Public Channels

#### 8.1.1 Markets Summary
**Channel**: `markets_summary`

**Purpose**: Real-time ticker data, 24h stats, funding rates

**Subscription**:
```python
await ws_client.subscribe(
    channel="markets_summary",
    callback=on_markets_summary
)
```

**Event Format** (example):
```json
{
  "channel": "markets_summary",
  "data": {
    "market": "BTC-USD-PERP",
    "last_price": "50000.5",
    "mark_price": "50001.2",
    "index_price": "50000.0",
    "funding_rate": "0.0001",
    "next_funding_time": 1699564800,
    "open_interest": "1250000",
    "volume_24h": "5000000",
    "high_24h": "51000",
    "low_24h": "49000",
    "price_change_24h": "500"
  }
}
```

**Hummingbot Usage**:
- Ticker updates
- Funding rate tracking (critical for funding arbitrage)
- 24h statistics

#### 8.1.2 Order Book
**Channel**: `orderbook.{market}`

**Purpose**: Order book snapshots and incremental updates

**Subscription**:
```python
await ws_client.subscribe(
    channel=f"orderbook.BTC-USD-PERP",
    callback=on_orderbook_update
)
```

**Event Types**:
1. **Snapshot** (initial full order book)
```json
{
  "channel": "orderbook.BTC-USD-PERP",
  "type": "snapshot",
  "data": {
    "bids": [
      ["50000", "1.5"],  // [price, size]
      ["49999", "2.3"]
    ],
    "asks": [
      ["50001", "1.2"],
      ["50002", "0.8"]
    ],
    "sequence": 12345
  }
}
```

2. **Update** (incremental changes)
```json
{
  "channel": "orderbook.BTC-USD-PERP",
  "type": "update",
  "data": {
    "bids": [
      ["50000", "0"]  // size=0 means removed
    ],
    "asks": [
      ["50001", "1.5"]  // updated size
    ],
    "sequence": 12346
  }
}
```

**Hummingbot Usage**:
- Real-time order book maintenance
- Order placement decisions
- Market making strategies

#### 8.1.3 Trades
**Channel**: `trades.{market}`

**Purpose**: Public trade feed

**Subscription**:
```python
await ws_client.subscribe(
    channel=f"trades.BTC-USD-PERP",
    callback=on_trade
)
```

**Event Format**:
```json
{
  "channel": "trades.BTC-USD-PERP",
  "data": {
    "trade_id": "TRADE_123",
    "price": "50000.5",
    "size": "0.5",
    "side": "BUY",  // Taker side
    "timestamp": 1699564800000
  }
}
```

**Hummingbot Usage**:
- Recent trades display
- Trade volume analysis

### 8.2 Private Channels (Require Authentication)

#### 8.2.1 Account
**Channel**: `account`

**Purpose**: General account updates

**Subscription**:
```python
await ws_client.subscribe(
    channel="account",
    callback=on_account_update
)
```

**Event Format**:
```json
{
  "channel": "account",
  "data": {
    "account": "0x...",
    "equity": "10000.50",
    "margin_balance": "9500.00",
    "available_balance": "8000.00",
    "initial_margin": "1500.00",
    "maintenance_margin": "1000.00",
    "unrealized_pnl": "500.50"
  }
}
```

**Hummingbot Usage**:
- Account equity monitoring
- Margin checks

#### 8.2.2 Orders
**Channel**: `orders`

**Purpose**: Order lifecycle events

**Subscription**:
```python
await ws_client.subscribe(
    channel="orders",
    callback=on_order_update
)
```

**Event Types**:
1. **Order Created**
```json
{
  "channel": "orders",
  "event": "created",
  "data": {
    "order_id": "ORDER_123",
    "client_id": "my_order_1",
    "market": "BTC-USD-PERP",
    "side": "BUY",
    "order_type": "LIMIT",
    "price": "50000",
    "size": "1.0",
    "filled_size": "0",
    "status": "OPEN",
    "created_at": 1699564800000
  }
}
```

2. **Order Partially Filled**
```json
{
  "channel": "orders",
  "event": "partially_filled",
  "data": {
    "order_id": "ORDER_123",
    "filled_size": "0.5",
    "remaining_size": "0.5",
    "status": "PARTIALLY_FILLED"
  }
}
```

3. **Order Filled**
```json
{
  "channel": "orders",
  "event": "filled",
  "data": {
    "order_id": "ORDER_123",
    "filled_size": "1.0",
    "status": "FILLED",
    "filled_at": 1699564850000
  }
}
```

4. **Order Cancelled**
```json
{
  "channel": "orders",
  "event": "cancelled",
  "data": {
    "order_id": "ORDER_123",
    "status": "CANCELLED",
    "cancelled_at": 1699564900000,
    "reason": "user_requested"
  }
}
```

**Hummingbot Usage**:
- Order state tracking
- Order update events (OrderUpdate objects)

**Mapping to Hummingbot**:
```python
def _parse_order_update(self, event: Dict) -> OrderUpdate:
    return OrderUpdate(
        trading_pair=event["market"],
        update_timestamp=event["created_at"] / 1000,
        new_state=CONSTANTS.ORDER_STATE[event["status"]],
        client_order_id=event["client_id"],
        exchange_order_id=event["order_id"],
        # ... other fields
    )
```

#### 8.2.3 Fills
**Channel**: `fills`

**Purpose**: Trade execution events

**Subscription**:
```python
await ws_client.subscribe(
    channel="fills",
    callback=on_fill
)
```

**Event Format**:
```json
{
  "channel": "fills",
  "data": {
    "fill_id": "FILL_456",
    "order_id": "ORDER_123",
    "trade_id": "TRADE_789",
    "market": "BTC-USD-PERP",
    "side": "BUY",
    "price": "50000",
    "size": "0.5",
    "fee": "0",  // Zero fees for retail
    "fee_asset": "USDC",
    "liquidity": "taker",  // or "maker"
    "timestamp": 1699564850000
  }
}
```

**Hummingbot Usage**:
- Trade execution tracking
- Trade update events (TradeUpdate objects)
- PnL calculation

**Mapping to Hummingbot**:
```python
def _parse_trade_update(self, event: Dict) -> TradeUpdate:
    return TradeUpdate(
        trade_id=event["fill_id"],
        client_order_id=None,  # Need to lookup from order_id
        exchange_order_id=event["order_id"],
        trading_pair=event["market"],
        fill_timestamp=event["timestamp"] / 1000,
        fill_price=Decimal(event["price"]),
        fill_base_amount=Decimal(event["size"]),
        fill_quote_amount=Decimal(event["price"]) * Decimal(event["size"]),
        fee=TokenAmount(event["fee_asset"], Decimal(event["fee"])),
        # ... other fields
    )
```

#### 8.2.4 Positions
**Channel**: `positions`

**Purpose**: Position change events

**Subscription**:
```python
await ws_client.subscribe(
    channel="positions",
    callback=on_position_update
)
```

**Event Format**:
```json
{
  "channel": "positions",
  "data": {
    "market": "BTC-USD-PERP",
    "side": "LONG",  // or "SHORT", "NONE"
    "size": "1.5",
    "entry_price": "49500",
    "mark_price": "50000",
    "liquidation_price": "45000",
    "unrealized_pnl": "750",
    "leverage": "10",
    "initial_margin": "7425",
    "maintenance_margin": "4950"
  }
}
```

**Hummingbot Usage**:
- Position tracking
- Leverage monitoring
- Liquidation risk management

#### 8.2.5 Balance Events
**Channel**: `balance_events`

**Purpose**: Real-time balance changes

**Subscription**:
```python
await ws_client.subscribe(
    channel="balance_events",
    callback=on_balance_event
)
```

**Event Format**:
```json
{
  "channel": "balance_events",
  "data": {
    "asset": "USDC",
    "available": "8500.00",
    "locked": "1500.00",
    "total": "10000.00",
    "change": "+50.00",  // From last update
    "reason": "trade_settled",  // or "deposit", "withdrawal", "funding"
    "timestamp": 1699564900000
  }
}
```

**Hummingbot Usage**:
- Real-time balance updates
- Avoid polling balance endpoint

### 8.3 WebSocket Connection Management

#### Connection Lifecycle
1. **Connect**: Establish WebSocket connection
2. **Authenticate**: Send JWT token in auth message
3. **Subscribe**: Subscribe to required channels
4. **Listen**: Receive and parse events
5. **Heartbeat**: Respond to ping/pong (if required)
6. **Reconnect**: Auto-reconnect on disconnect

#### Error Handling
- **Connection Errors**: Retry with exponential backoff
- **Auth Errors**: Refresh JWT token, reconnect
- **Subscription Errors**: Log and alert, critical for operation

#### Example Connection Flow
```python
async def _connect_and_subscribe(self):
    # Connect
    ws_url = self._get_ws_url()
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ws_url) as ws:
            # Authenticate
            jwt_token = await self._auth.get_jwt_token()
            await ws.send_json({
                "type": "auth",
                "jwt_token": jwt_token
            })

            # Subscribe to channels
            await ws.send_json({
                "type": "subscribe",
                "channels": ["orders", "fills", "positions", "balance_events"]
            })

            # Listen for messages
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    event = json.loads(msg.data)
                    await self._handle_event(event)
```

---

## 9. Testing Strategy

### 9.1 Unit Testing

#### Test Files to Create
```
tests/connector/derivative/paradex_perpetual/
├── test_paradex_perpetual_auth.py
├── test_paradex_perpetual_derivative.py
├── test_paradex_perpetual_api_order_book_data_source.py
└── test_paradex_perpetual_user_stream_data_source.py
```

#### Key Test Cases

**Authentication Tests**:
- JWT token generation
- Token refresh on expiry
- Header injection
- Subkey authentication flow

**Order Tests**:
- Place limit order
- Place market order
- Cancel order
- Order state transitions
- Order validation errors

**Balance/Position Tests**:
- Fetch balances
- Fetch positions
- Parse balance updates
- Parse position updates

**WebSocket Tests**:
- Connection establishment
- Channel subscription
- Message parsing
- Reconnection logic

### 9.2 Integration Testing

#### Testnet Setup
1. Create Paradex testnet account
2. Generate testnet subkey
3. Fund testnet account with test USDC
4. Configure connector with testnet credentials

#### Integration Test Scenarios
1. **Connection Test**
   - Connect to testnet
   - Verify authentication
   - Check balance fetch

2. **Order Lifecycle Test**
   - Place limit buy order
   - Verify order appears in active orders
   - Cancel order
   - Verify cancellation

3. **Market Order Test**
   - Place market order
   - Verify immediate fill
   - Check balance update

4. **WebSocket Test**
   - Subscribe to all channels
   - Verify message reception
   - Test reconnection

5. **Funding Rate Test**
   - Fetch funding rates
   - Verify rate updates
   - Test funding payment tracking

### 9.3 Manual Testing Checklist

**Pre-Deployment**:
- [ ] Testnet connection successful
- [ ] Balance display accurate
- [ ] Position display accurate
- [ ] Order placement works (limit)
- [ ] Order placement works (market)
- [ ] Order cancellation works
- [ ] WebSocket updates received
- [ ] Funding rates display correctly
- [ ] No authentication errors in logs
- [ ] No rate limit errors

**Mainnet Validation** (small amounts first):
- [ ] Connect with real credentials
- [ ] Verify balance display
- [ ] Place small limit order
- [ ] Cancel order
- [ ] Place small market order
- [ ] Monitor for 1 funding cycle (8 hours)
- [ ] Verify all operations for 24 hours

### 9.4 Performance Testing

**Metrics to Monitor**:
- Order placement latency (target: <500ms)
- WebSocket message latency (target: <100ms)
- Balance update frequency
- Memory usage over 24 hours
- CPU usage during high activity

---

## 10. Deployment Checklist

### 10.1 Pre-Deployment

**Code Review**:
- [ ] All 8 files implemented
- [ ] Code follows Extended/Lighter patterns
- [ ] Error handling comprehensive
- [ ] Logging appropriate (info, warning, error)
- [ ] No hardcoded credentials
- [ ] Rate limits configured correctly

**Documentation**:
- [ ] Docstrings complete
- [ ] README updated
- [ ] Configuration guide written
- [ ] API limits documented

**Dependencies**:
- [ ] `paradex_py` added to requirements
- [ ] Version pinned (e.g., `paradex_py>=0.4.6,<0.5`)
- [ ] SDK tested and working

**Testing**:
- [ ] Unit tests pass
- [ ] Integration tests pass (testnet)
- [ ] Manual testing complete

### 10.2 Deployment Steps

1. **Add Connector to Hummingbot Registry**
   ```python
   # In hummingbot/connector/derivative/__init__.py
   from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative import (
       ParadexPerpetualDerivative,
   )
   ```

2. **Update Connector List**
   ```python
   # In hummingbot/client/settings.py or equivalent
   CONNECTOR_SETTINGS = {
       # ... other connectors
       "paradex_perpetual": {
           "connector_class": "ParadexPerpetualDerivative",
           "connector_type": "derivative",
           # ... other settings
       }
   }
   ```

3. **Create Default Config Template**
   ```yaml
   # In hummingbot/templates/conf_paradex_perpetual_TEMPLATE.yml
   connector: paradex_perpetual
   paradex_perpetual_api_secret: ""
   paradex_perpetual_account_address: ""
   ```

4. **Build and Install**
   ```bash
   # From Hummingbot root
   ./compile
   ./install
   ```

5. **Test Installation**
   ```bash
   hummingbot
   > connect paradex_perpetual
   ```

### 10.3 Post-Deployment

**Monitoring** (first 48 hours):
- [ ] Check logs for errors every 4 hours
- [ ] Monitor order execution success rate
- [ ] Track WebSocket stability
- [ ] Watch for rate limit issues

**Documentation**:
- [ ] Update connector docs with any issues found
- [ ] Document any Paradex API quirks
- [ ] Create troubleshooting guide

**Community Support**:
- [ ] Announce connector availability
- [ ] Provide setup guide
- [ ] Monitor Discord/Telegram for issues

---

## 11. Appendix: Code Templates

### 11.1 Sample Order Placement (in derivative.py)

```python
async def _place_order(
    self,
    order_id: str,
    trading_pair: str,
    amount: Decimal,
    trade_type: TradeType,
    order_type: OrderType,
    price: Decimal,
    **kwargs
) -> Tuple[str, float]:
    """
    Place order via paradex_py SDK.

    Args:
        order_id: Internal Hummingbot order ID
        trading_pair: Trading pair (e.g., "BTC-USD-PERP")
        amount: Order size
        trade_type: BUY or SELL
        order_type: LIMIT or MARKET
        price: Limit price (ignored for market orders)
        **kwargs: Additional params (time_in_force, etc.)

    Returns:
        Tuple of (exchange_order_id, created_timestamp)

    Raises:
        Exception: If order placement fails
    """
    try:
        # Get ParadexSubkey client
        client = self._auth.get_paradex_client()

        # Map Hummingbot params to Paradex API
        side = "BUY" if trade_type == TradeType.BUY else "SELL"
        order_type_str = "LIMIT" if order_type == OrderType.LIMIT else "MARKET"

        # Build order request
        order_params = {
            "market": trading_pair,
            "side": side,
            "size": str(amount),
            "order_type": order_type_str,
            "client_id": order_id,  # Use Hummingbot ID as client_id
        }

        # Add price for limit orders
        if order_type == OrderType.LIMIT:
            order_params["price"] = str(price)

        # Add optional params
        time_in_force = kwargs.get("time_in_force", "GTC")
        order_params["time_in_force"] = time_in_force

        # Submit order via SDK (handles signing)
        self.logger().info(f"Placing {side} {order_type_str} order for {amount} {trading_pair} @ {price}")

        order_result = await client.submit_order(**order_params)

        # Extract exchange order ID and timestamp
        exchange_order_id = order_result["id"]
        created_at = order_result["created_at"] / 1000  # Convert ms to seconds

        self.logger().info(
            f"Successfully placed order {order_id} -> {exchange_order_id}"
        )

        return exchange_order_id, created_at

    except Exception as e:
        self.logger().error(
            f"Error placing order {order_id}: {str(e)}",
            exc_info=True
        )
        raise
```

### 11.2 Sample Balance Update (in derivative.py)

```python
async def _update_balances(self):
    """
    Update account balances from Paradex API.

    Fetches balance data from /account/balances endpoint and updates
    internal balance tracking.
    """
    try:
        # Fetch balances from REST API
        response = await self._api_get(
            path_url=CONSTANTS.BALANCES_URL,
            is_auth_required=True,
            limit_id=CONSTANTS.BALANCES_URL
        )

        if not isinstance(response, dict) or "balances" not in response:
            self.logger().warning(f"Invalid balance response: {response}")
            return

        # Parse balance data
        balances = response["balances"]

        for balance_entry in balances:
            asset = balance_entry["asset"]

            # Paradex balance fields (verify exact field names from API):
            # - total: Total balance
            # - available: Available for trading
            # - locked: Locked in orders/positions

            total_balance = Decimal(str(balance_entry.get("total", "0")))
            available_balance = Decimal(str(balance_entry.get("available", "0")))
            locked_balance = Decimal(str(balance_entry.get("locked", "0")))

            # Update Hummingbot's internal balance tracking
            self._account_available_balances[asset] = available_balance
            self._account_balances[asset] = total_balance

            self.logger().debug(
                f"Updated {asset} balance: "
                f"total={total_balance}, available={available_balance}, locked={locked_balance}"
            )

    except Exception as e:
        self.logger().error(
            f"Error updating balances: {str(e)}",
            exc_info=True
        )
        # Don't raise - balance updates are periodic, failures are logged
```

### 11.3 Sample WebSocket Order Update Parser (in user_stream_data_source.py)

```python
def _parse_order_update(self, event: Dict) -> OrderUpdate:
    """
    Parse order update event from Paradex WebSocket into Hummingbot OrderUpdate.

    Args:
        event: Raw event from orders channel

    Returns:
        OrderUpdate object for Hummingbot
    """
    # Extract fields from Paradex event
    order_id = event["order_id"]
    client_id = event.get("client_id")  # May be None for orders not placed by this client
    market = event["market"]
    status = event["status"]

    # Map Paradex status to Hummingbot OrderState
    order_state = CONSTANTS.ORDER_STATE.get(status, OrderState.FAILED)

    # Build OrderUpdate
    order_update = OrderUpdate(
        trading_pair=market,
        update_timestamp=event.get("updated_at", event.get("created_at", 0)) / 1000,
        new_state=order_state,
        client_order_id=client_id,
        exchange_order_id=order_id,
    )

    # Add executed amount if available (for partial/full fills)
    if "filled_size" in event:
        order_update.fill_base_amount = Decimal(str(event["filled_size"]))

        # Calculate fill price (average if multiple fills)
        if "avg_fill_price" in event:
            order_update.fill_price = Decimal(str(event["avg_fill_price"]))

    return order_update
```

### 11.4 Sample Funding Rate Update (in derivative.py)

```python
async def _update_funding_rates(self):
    """
    Update funding rates for all trading pairs.

    Paradex funding rates can be fetched from:
    1. Market summary WebSocket channel (real-time)
    2. REST API /markets/{market}/funding endpoint (fallback)
    """
    try:
        for trading_pair in self._trading_pairs:
            try:
                # Fetch funding rate from REST API
                response = await self._api_get(
                    path_url=CONSTANTS.FUNDING_RATE_URL.format(market=trading_pair),
                    is_auth_required=False,
                    limit_id=CONSTANTS.FUNDING_RATE_URL
                )

                if isinstance(response, dict) and "funding_rate" in response:
                    funding_rate = Decimal(str(response["funding_rate"]))
                    next_funding_time = response.get("next_funding_time", 0)

                    # Update internal tracking
                    self._funding_rates[trading_pair] = funding_rate

                    self.logger().debug(
                        f"Updated funding rate for {trading_pair}: "
                        f"{funding_rate:.6f} (next: {next_funding_time})"
                    )

            except Exception as e:
                self.logger().error(
                    f"Error fetching funding rate for {trading_pair}: {str(e)}"
                )
                # Continue with other pairs

    except Exception as e:
        self.logger().error(
            f"Error in _update_funding_rates: {str(e)}",
            exc_info=True
        )
```

---

## 12. Open Questions & TODOs

### 12.1 API Clarifications Needed

| Question | Source | Priority |
|----------|--------|----------|
| Exact WebSocket URL format | Paradex docs | HIGH |
| WebSocket authentication message format | Paradex docs | HIGH |
| Rate limit details (per endpoint) | Paradex team | MEDIUM |
| Funding rate interval (8hr or custom?) | Paradex docs | MEDIUM |
| Max leverage per market | API response | MEDIUM |
| Order minimum/maximum sizes | API response | MEDIUM |
| Position mode options (one-way/hedge) | Paradex docs | LOW |
| Fee tiers for non-retail traders | Paradex docs | LOW |

### 12.2 Implementation TODOs

**Phase 1 - Core Functionality**:
- [ ] Implement all 8 connector files
- [ ] Add paradex_py dependency
- [ ] Create unit tests
- [ ] Test on Paradex testnet

**Phase 2 - Advanced Features**:
- [ ] Implement funding rate arbitrage support
- [ ] Add position mode switching (if supported)
- [ ] Implement batch order operations
- [ ] Add order modification support

**Phase 3 - Polish**:
- [ ] Optimize WebSocket reconnection
- [ ] Add comprehensive error messages
- [ ] Create user documentation
- [ ] Add example strategies

### 12.3 Future Enhancements

1. **Perpetual Options Support**
   - Extend connector for Paradex's unique perpetual options product
   - New order types, Greeks calculation

2. **Pre-Market Trading**
   - Support for early token access markets
   - Different trading rules

3. **Vault Integration**
   - Integration with Paradex's tokenized high-yield vaults
   - Auto-compounding strategies

4. **Advanced Privacy Features**
   - Leverage zk-encryption for private strategies
   - Stealth order placement

---

## 13. References

### 13.1 Paradex Resources
- **Official Website**: https://paradex.trade
- **API Documentation**: https://docs.paradex.trade
- **Python SDK**: https://github.com/tradeparadex/paradex-py
- **SDK Documentation**: https://tradeparadex.github.io/paradex-py/

### 13.2 Hummingbot Resources
- **Connector Development Guide**: https://docs.hummingbot.org/developers/connectors/
- **PerpetualDerivativePyBase**: Source code reference
- **Extended Connector**: `/hummingbot/connector/derivative/extended_perpetual/`
- **Lighter Connector**: `/hummingbot/connector/derivative/lighter_perpetual/`

### 13.3 Starknet Resources
- **Starknet Documentation**: https://docs.starknet.io
- **Cairo Language**: https://www.cairo-lang.org/
- **Starknet.py**: Python SDK for Starknet

---

---

## 14. Critical Mistakes to Avoid

**🚨 MANDATORY READING**: See **[PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md](PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md)** for complete details.

### Top 5 Critical Mistakes from Extended/Lighter:

1. **❌ Empty Placeholder Implementations**
   - Extended & Lighter deployed with `_update_balances()` = `pass`
   - Result: Balances always showed $0, trading impossible
   - **Prevention**: Implement ALL methods fully before deployment

2. **❌ Wrong API Parameter Names**
   - Lighter used `by="address"` instead of `by="l1_address"`
   - Result: 400 Bad Request on every balance call
   - **Prevention**: Test each API endpoint with curl BEFORE coding

3. **❌ Invalid API Keys in Config**
   - Extended had expired API key in encrypted config
   - Result: 401 Unauthorized despite correct code
   - **Prevention**: Test API keys directly before encrypting

4. **❌ Assuming Undocumented Endpoints Exist**
   - Extended implemented full streaming support for non-existent API
   - Result: All streaming returned 404, had to add REST fallback
   - **Prevention**: Verify every endpoint exists with curl first

5. **❌ UTF-8 Mode Not Enabled**
   - Docker didn't have `PYTHONUTF8=1`
   - Result: Potential Unicode errors in production
   - **Prevention**: Add `PYTHONUTF8=1` to Dockerfile

### Pre-Implementation Checklist:
- [ ] Read lessons learned document completely
- [ ] Test all Paradex endpoints with curl
- [ ] Verify JWT authentication works
- [ ] Test API keys directly before encrypting
- [ ] Enable UTF-8 mode in Dockerfile
- [ ] Implement balance/position updates FULLY
- [ ] Test integration before deployment

---

**Document Version**: 1.1
**Last Updated**: 2025-11-11 (Added Lessons Learned)
**Author**: Claude Code
**Status**: Planning Phase - Ready for Implementation

---


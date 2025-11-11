"""
EdgeX Perpetual Utilities

This file contains utility functions and configuration schemas for the EdgeX Perpetual connector including:
- Fee structure configuration
- Connector configuration map (Pydantic models)
- Domain settings (mainnet/testnet)
- Helper functions for trading pair formatting
"""

from decimal import Decimal
from typing import Any, Dict

from pydantic import Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap, ClientFieldData
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

# ===============================
# Connector Metadata
# ===============================

CENTRALIZED = False  # EdgeX is a decentralized exchange (DEX)
EXAMPLE_PAIR = "BTC-USD-PERP"
BROKER_ID = "HBOT"

# ===============================
# Fee Structure
# ===============================

# EdgeX fee structure (TODO: verify actual fees from EdgeX docs/metadata API)
# Typical perpetual DEX fees: 0.02% maker, 0.05% taker
# Update after fetching from /api/v1/public/meta/getMetaData endpoint

DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.0002"),  # 0.02% maker fee
    taker_percent_fee_decimal=Decimal("0.0005"),  # 0.05% taker fee
    buy_percent_fee_deducted_from_returns=True
)

# ===============================
# Configuration Map - Mainnet
# ===============================

class EdgexPerpetualConfigMap(BaseConnectorConfigMap):
    """
    Configuration schema for EdgeX Perpetual connector (Mainnet).

    EdgeX uses ECDSA signature-based authentication with private keys.
    Unlike Paradex (which uses subkeys), EdgeX requires:
    - Private key for signing requests (L2 private key)
    - Account ID for identifying the account
    """

    connector: str = Field(default="edgex_perpetual", client_data=None)

    # EdgeX private key (L2 private key for signature generation)
    edgex_perpetual_api_secret: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your EdgeX private key (from EdgeX account settings)",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        )
    )

    # EdgeX account ID
    edgex_perpetual_account_id: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your EdgeX account ID",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        )
    )

    class Config:
        title = "edgex_perpetual"


# Singleton instance for mainnet configuration
KEYS = EdgexPerpetualConfigMap.construct()

# ===============================
# Configuration Map - Testnet
# ===============================

class EdgexPerpetualTestnetConfigMap(BaseConnectorConfigMap):
    """
    Configuration schema for EdgeX Perpetual connector (Testnet).

    Same credentials structure as mainnet, but for testnet environment.
    """

    connector: str = Field(default="edgex_perpetual_testnet", client_data=None)

    # EdgeX testnet private key
    edgex_perpetual_testnet_api_secret: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your EdgeX testnet private key",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        )
    )

    # EdgeX testnet account ID
    edgex_perpetual_testnet_account_id: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your EdgeX testnet account ID",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        )
    )

    class Config:
        title = "edgex_perpetual_testnet"


# ===============================
# Domain Settings
# ===============================

# Other domains (testnet)
OTHER_DOMAINS = ["edgex_perpetual_testnet"]

# Domain parameters
OTHER_DOMAINS_PARAMETER = {
    "edgex_perpetual_testnet": "edgex_perpetual_testnet"
}

# Example trading pairs for each domain
OTHER_DOMAINS_EXAMPLE_PAIR = {
    "edgex_perpetual_testnet": EXAMPLE_PAIR
}

# Default fees for each domain
OTHER_DOMAINS_DEFAULT_FEES = {
    "edgex_perpetual_testnet": [
        DEFAULT_FEES.maker_percent_fee_decimal,
        DEFAULT_FEES.taker_percent_fee_decimal
    ]
}

# Configuration keys for each domain
OTHER_DOMAINS_KEYS = {
    "edgex_perpetual_testnet": EdgexPerpetualTestnetConfigMap.construct()
}

# ===============================
# Helper Functions
# ===============================

def is_exchange_information_valid(exchange_info: Dict[str, Any]) -> bool:
    """
    Verifies if exchange information from API is valid and complete.

    Args:
        exchange_info: Exchange information dict from /api/v1/public/meta/getMetaData

    Returns:
        True if valid, False otherwise
    """
    return (
        isinstance(exchange_info, dict)
        and "contractList" in exchange_info
        and "coinList" in exchange_info
        and len(exchange_info["contractList"]) > 0
    )


def convert_from_exchange_trading_pair(exchange_trading_pair: str) -> str:
    """
    Converts EdgeX trading pair format to Hummingbot format.

    EdgeX uses contractId (numeric or string identifier).
    Need to map to standard format: BASE-QUOTE-PERP

    Args:
        exchange_trading_pair: Trading pair in EdgeX format (contractId)

    Returns:
        Trading pair in Hummingbot format (e.g., "BTC-USD-PERP")

    Note: Implementation depends on metadata API response format.
    May need to maintain a mapping dict from contractId to symbol.
    """
    # TODO: Implement after analyzing metadata API response
    # Placeholder implementation
    return exchange_trading_pair


def convert_to_exchange_trading_pair(hb_trading_pair: str) -> str:
    """
    Converts Hummingbot trading pair format to EdgeX format.

    Hummingbot format: BASE-QUOTE-PERP (e.g., "BTC-USD-PERP")
    EdgeX format: contractId (numeric or string identifier)

    Args:
        hb_trading_pair: Trading pair in Hummingbot format

    Returns:
        Trading pair in EdgeX format (contractId)

    Note: Implementation depends on metadata API response format.
    May need to maintain a mapping dict from symbol to contractId.
    """
    # TODO: Implement after analyzing metadata API response
    # Placeholder implementation
    return hb_trading_pair


def get_contract_id_from_trading_pair(hb_trading_pair: str, contract_list: list) -> str:
    """
    Extract EdgeX contractId from Hummingbot trading pair using contract list.

    Args:
        hb_trading_pair: Trading pair in Hummingbot format (e.g., "BTC-USD-PERP")
        contract_list: List of contracts from metadata API

    Returns:
        EdgeX contractId for the trading pair

    Raises:
        ValueError: If trading pair not found in contract list
    """
    # TODO: Implement based on metadata API response structure
    # Example structure from docs shows contractList has contract details
    for contract in contract_list:
        # Need to determine exact field names from metadata API
        # Likely fields: contractId, symbol, baseCoin, quoteCoin
        pass

    raise ValueError(f"Trading pair {hb_trading_pair} not found in contract list")


def get_trading_pair_from_contract_id(contract_id: str, contract_list: list) -> str:
    """
    Convert EdgeX contractId to Hummingbot trading pair format.

    Args:
        contract_id: EdgeX contractId
        contract_list: List of contracts from metadata API

    Returns:
        Trading pair in Hummingbot format (e.g., "BTC-USD-PERP")

    Raises:
        ValueError: If contractId not found in contract list
    """
    # TODO: Implement based on metadata API response structure
    for contract in contract_list:
        # Match contractId and extract symbol/baseCoin/quoteCoin
        pass

    raise ValueError(f"Contract ID {contract_id} not found in contract list")

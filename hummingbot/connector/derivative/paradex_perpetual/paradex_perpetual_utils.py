from decimal import Decimal
from typing import Optional

from pydantic import Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

# Paradex fees: Zero trading fees for retail traders (100+ perpetual markets)
DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0"),
    taker_percent_fee_decimal=Decimal("0"),
    buy_percent_fee_deducted_from_returns=True
)

CENTRALIZED = False  # Paradex is a DEX

EXAMPLE_PAIR = "BTC-USD-PERP"

BROKER_ID = "HBOT"


class ParadexPerpetualConfigMap(BaseConnectorConfigMap):
    """
    Configuration map for Paradex Perpetual connector.

    Uses subkey authentication for trading-only access (recommended for bots).
    Subkeys cannot withdraw funds, providing additional security.
    """
    connector: str = "paradex_perpetual"

    paradex_perpetual_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Paradex API key (JWT token) or L2 private key (0x...)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    paradex_perpetual_account_address: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Paradex L1 account address (Ethereum L1 address, 0x...)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )


KEYS = ParadexPerpetualConfigMap.model_construct()

OTHER_DOMAINS = ["paradex_perpetual_testnet"]
OTHER_DOMAINS_PARAMETER = {"paradex_perpetual_testnet": "paradex_perpetual_testnet"}
OTHER_DOMAINS_EXAMPLE_PAIR = {"paradex_perpetual_testnet": "BTC-USD-PERP"}
OTHER_DOMAINS_DEFAULT_FEES = {"paradex_perpetual_testnet": [0, 0]}


class ParadexPerpetualTestnetConfigMap(BaseConnectorConfigMap):
    """
    Configuration map for Paradex Perpetual testnet connector.
    """
    connector: str = "paradex_perpetual_testnet"

    paradex_perpetual_testnet_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Paradex testnet API key (JWT token) or L2 private key (0x...)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    paradex_perpetual_testnet_account_address: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Paradex testnet L1 account address (Ethereum L1 address, 0x...)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )


OTHER_DOMAINS_KEYS = {"paradex_perpetual_testnet": ParadexPerpetualTestnetConfigMap.model_construct()}

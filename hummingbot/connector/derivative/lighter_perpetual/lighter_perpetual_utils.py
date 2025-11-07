from decimal import Decimal
from typing import Optional

from pydantic import Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

# Lighter fees: 0 trading fees (as advertised)
DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0"),
    taker_percent_fee_decimal=Decimal("0"),
    buy_percent_fee_deducted_from_returns=True
)

CENTRALIZED = False  # Lighter is a DEX

EXAMPLE_PAIR = "KAITO-USD"

BROKER_ID = "HBOT"


class LighterPerpetualConfigMap(BaseConnectorConfigMap):
    connector: str = "lighter_perpetual"
    lighter_perpetual_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Lighter API key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    lighter_perpetual_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Lighter API secret",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )


KEYS = LighterPerpetualConfigMap.model_construct()

OTHER_DOMAINS = ["lighter_perpetual_testnet"]
OTHER_DOMAINS_PARAMETER = {"lighter_perpetual_testnet": "lighter_perpetual_testnet"}
OTHER_DOMAINS_EXAMPLE_PAIR = {"lighter_perpetual_testnet": "KAITO-USD"}
OTHER_DOMAINS_DEFAULT_FEES = {"lighter_perpetual_testnet": [0, 0]}


class LighterPerpetualTestnetConfigMap(BaseConnectorConfigMap):
    connector: str = "lighter_perpetual_testnet"
    lighter_perpetual_testnet_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Lighter testnet API key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    lighter_perpetual_testnet_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Lighter testnet API secret",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )


OTHER_DOMAINS_KEYS = {"lighter_perpetual_testnet": LighterPerpetualTestnetConfigMap.model_construct()}

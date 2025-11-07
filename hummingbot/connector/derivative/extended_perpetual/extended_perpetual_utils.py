from decimal import Decimal
from typing import Optional

from pydantic import Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

# Extended fees: Maker 0.02%, Taker 0.05%
DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.0002"),
    taker_percent_fee_decimal=Decimal("0.0005"),
    buy_percent_fee_deducted_from_returns=True
)

CENTRALIZED = False  # Extended is a DEX

EXAMPLE_PAIR = "KAITO-USD"

BROKER_ID = "HBOT"


class ExtendedPerpetualConfigMap(BaseConnectorConfigMap):
    connector: str = "extended_perpetual"
    extended_perpetual_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Extended API key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    extended_perpetual_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Extended API secret (Stark private key)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )


KEYS = ExtendedPerpetualConfigMap.model_construct()

OTHER_DOMAINS = ["extended_perpetual_testnet"]
OTHER_DOMAINS_PARAMETER = {"extended_perpetual_testnet": "extended_perpetual_testnet"}
OTHER_DOMAINS_EXAMPLE_PAIR = {"extended_perpetual_testnet": "KAITO-USD"}
OTHER_DOMAINS_DEFAULT_FEES = {"extended_perpetual_testnet": [0.0002, 0.0005]}


class ExtendedPerpetualTestnetConfigMap(BaseConnectorConfigMap):
    connector: str = "extended_perpetual_testnet"
    extended_perpetual_testnet_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Extended testnet API key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    extended_perpetual_testnet_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": "Enter your Extended testnet API secret (Stark private key)",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )


OTHER_DOMAINS_KEYS = {"extended_perpetual_testnet": ExtendedPerpetualTestnetConfigMap.model_construct()}

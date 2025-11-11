"""
EdgeX Perpetual Derivative Connector.

EdgeX is a StarkEx Layer 2 perpetual futures DEX built on Ethereum.
This connector enables Hummingbot to trade perpetual futures on EdgeX.
"""

from hummingbot.connector.derivative.edgex_perpetual.edgex_perpetual_derivative import (
    EdgexPerpetualDerivative,
)

__all__ = ["EdgexPerpetualDerivative"]

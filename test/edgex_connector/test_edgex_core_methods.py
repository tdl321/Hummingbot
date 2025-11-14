#!/usr/bin/env python3
"""
Test EdgeX Phase 3 Core Implementation

Tests the core connector methods:
- _update_balances()
- _update_positions()
- _update_trading_rules()
- _update_funding_rates()

Usage:
    python test/edgex_connector/test_edgex_core_methods.py
"""

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.derivative.edgex_perpetual.edgex_perpetual_derivative import EdgexPerpetualDerivative
from hummingbot.connector.derivative.edgex_perpetual import edgex_perpetual_constants as CONSTANTS


async def test_core_methods():
    """Test EdgeX core connector methods"""

    print("=" * 80)
    print("EdgeX Phase 3 Core Methods Test")
    print("=" * 80)
    print()

    # Get credentials from environment
    api_secret = os.getenv("EDGEX_MAINNET_PRIVATE_KEY")
    account_id = os.getenv("EDGEX_MAINNET_ACCOUNT_ID")

    if not api_secret or not account_id:
        print("❌ ERROR: Missing credentials")
        print()
        print("Please set environment variables:")
        print("  export EDGEX_MAINNET_PRIVATE_KEY='your_stark_private_key'")
        print("  export EDGEX_MAINNET_ACCOUNT_ID='your_account_id'")
        return

    print(f"✓ Account ID: {account_id}")
    print(f"✓ Private Key: {api_secret[:10]}...")
    print()

    # Create connector instance
    print("Creating EdgeX connector instance...")
    try:
        client_config = ClientConfigAdapter(None)
        connector = EdgexPerpetualDerivative(
            client_config_map=client_config,
            edgex_perpetual_api_secret=api_secret,
            edgex_perpetual_account_id=account_id,
            trading_pairs=["BTC-USD-PERP", "ETH-USD-PERP"],  # Example pairs
            trading_required=False,
            domain=CONSTANTS.DOMAIN
        )
        print("✅ Connector created successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to create connector: {e}")
        return

    # Start the connector network
    print("Starting connector network...")
    try:
        await connector.start_network()
        print("✅ Network started")
        print()
    except Exception as e:
        print(f"❌ Failed to start network: {e}")
        return

    # Test 1: Update Trading Rules
    print("=" * 80)
    print("TEST 1: Update Trading Rules")
    print("=" * 80)
    try:
        await connector._update_trading_rules()
        print(f"✅ Trading rules updated: {len(connector._trading_rules)} rules loaded")

        # Show first few trading rules
        for i, (trading_pair, rule) in enumerate(list(connector._trading_rules.items())[:5]):
            print(f"  {trading_pair}:")
            print(f"    Min size: {rule.min_order_size}")
            print(f"    Max size: {rule.max_order_size}")
            print(f"    Tick size: {rule.min_price_increment}")
            print(f"    Step size: {rule.min_base_amount_increment}")

        if len(connector._trading_rules) > 5:
            print(f"  ... and {len(connector._trading_rules) - 5} more")
        print()
    except Exception as e:
        print(f"❌ Trading rules update failed: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Test 2: Update Funding Rates
    print("=" * 80)
    print("TEST 2: Update Funding Rates")
    print("=" * 80)
    try:
        await connector._update_funding_rates()
        print(f"✅ Funding rates updated: {len(connector._funding_rates)} rates loaded")

        # Show first few funding rates
        for i, (trading_pair, rate) in enumerate(list(connector._funding_rates.items())[:5]):
            print(f"  {trading_pair}: {rate:.6f}")

        if len(connector._funding_rates) > 5:
            print(f"  ... and {len(connector._funding_rates) - 5} more")
        print()
    except Exception as e:
        print(f"❌ Funding rates update failed: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Test 3: Update Balances
    print("=" * 80)
    print("TEST 3: Update Balances")
    print("=" * 80)
    try:
        await connector._update_balances()
        print(f"✅ Balances updated: {len(connector._account_balances)} assets found")

        if connector._account_balances:
            print("  Balances:")
            for asset, balance in connector._account_balances.items():
                available = connector._account_available_balances.get(asset, Decimal("0"))
                print(f"    {asset}: {balance} (available: {available})")
        else:
            print("  ⚠️  No balances found (account may need funding or whitelisting)")
        print()
    except Exception as e:
        print(f"❌ Balance update failed: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Test 4: Update Positions
    print("=" * 80)
    print("TEST 4: Update Positions")
    print("=" * 80)
    try:
        await connector._update_positions()
        print(f"✅ Positions updated: {len(connector._account_positions)} positions found")

        if connector._account_positions:
            print("  Positions:")
            for trading_pair, position in connector._account_positions.items():
                print(f"    {trading_pair}:")
                print(f"      Side: {position.position_side.name}")
                print(f"      Amount: {position.amount}")
                print(f"      Entry Price: {position.entry_price}")
                print(f"      Unrealized PnL: {position.unrealized_pnl}")
                print(f"      Leverage: {position.leverage}x")
        else:
            print("  ✓ No open positions")
        print()
    except Exception as e:
        print(f"❌ Position update failed: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Stop the connector
    print("Stopping connector...")
    try:
        await connector.stop_network()
        print("✅ Connector stopped")
        print()
    except Exception as e:
        print(f"⚠️  Warning during connector stop: {e}")

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Trading Rules: {len(connector._trading_rules)} loaded")
    print(f"Funding Rates: {len(connector._funding_rates)} loaded")
    print(f"Balances: {len(connector._account_balances)} assets")
    print(f"Positions: {len(connector._account_positions)} open")
    print()
    print("✅ Phase 3 Core Implementation Test Complete!")
    print()
    print("Next Steps:")
    print("1. Implement L2 order signing for _place_order()")
    print("2. Test order placement and cancellation")
    print("3. Implement WebSocket data sources (Phase 4)")


if __name__ == "__main__":
    asyncio.run(test_core_methods())

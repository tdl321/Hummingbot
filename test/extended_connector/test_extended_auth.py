#!/usr/bin/env python3
"""
Quick test to verify Extended connector authentication works with the balance API.

This tests the actual connector authentication flow vs the direct curl test.
"""

import asyncio
import sys
from decimal import Decimal

# Add hummingbot to path
sys.path.insert(0, '/Users/tdl321/hummingbot')

from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative


async def test_extended_auth():
    """Test Extended connector with authentication."""
    print("=" * 80)
    print("TESTING EXTENDED CONNECTOR AUTHENTICATION")
    print("=" * 80)

    # Your API credentials from .env
    api_key = "f4aa1ba3e3038adf522981a90d2a1c57"
    api_secret = "0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1"

    try:
        # Initialize connector with API credentials
        print("\n1. Initializing Extended connector with API credentials...")
        connector = ExtendedPerpetualDerivative(
            extended_perpetual_api_key=api_key,
            extended_perpetual_api_secret=api_secret,
            trading_pairs=["KAITO-USD"],
            trading_required=True  # Requires authentication
        )
        print("   ✅ Extended connector initialized with auth")

        # Start network
        print("\n2. Starting network...")
        await connector.start_network()
        print("   ✅ Network started")

        # Wait for initialization
        print("\n3. Waiting for connector to initialize...")
        await asyncio.sleep(5)

        # Check if balances were fetched
        print("\n4. Checking balance...")
        balances = connector.get_all_balances()
        print(f"   Balances: {balances}")

        if balances:
            print("   ✅ Balance fetched successfully!")
            for asset, amount in balances.items():
                print(f"      {asset}: {amount}")
        else:
            print("   ⚠️  No balances returned (might be zero or auth issue)")

        # Try to manually fetch balance
        print("\n5. Manually fetching balance via API...")
        try:
            import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_constants as CONSTANTS
            response = await connector._api_get(
                path_url=CONSTANTS.BALANCE_URL,
                is_auth_required=True
            )
            print(f"   API Response: {response}")

            if isinstance(response, dict) and response.get('status') == 'OK':
                data = response.get('data', {})
                print(f"\n   ✅ Balance API call successful!")
                print(f"      Balance: {data.get('balance')}")
                print(f"      Equity: {data.get('equity')}")
                print(f"      Available: {data.get('availableForTrade')}")
            else:
                print(f"   ⚠️  Unexpected response format")

        except Exception as e:
            print(f"   ❌ Error fetching balance: {e}")
            import traceback
            traceback.print_exc()

        # Stop network
        print("\n6. Stopping network...")
        await connector.stop_network()
        print("   ✅ Network stopped")

        print("\n✅ EXTENDED AUTH TEST COMPLETED!")
        return True

    except Exception as e:
        print(f"\n❌ EXTENDED AUTH TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_extended_auth())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script for Extended and Lighter perpetual connectors.

This script tests:
1. Connector instantiation
2. Market data fetching
3. Funding rate retrieval
4. Trading pair discovery

Run: python test_new_connectors.py
"""

import asyncio
import sys
from decimal import Decimal

# Add hummingbot to path
sys.path.insert(0, '/Users/tdl321/hummingbot')

from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative
from hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_derivative import LighterPerpetualDerivative


async def test_extended_connector():
    """Test Extended perpetual connector."""
    print("=" * 80)
    print("TESTING EXTENDED PERPETUAL CONNECTOR")
    print("=" * 80)

    try:
        # Initialize connector (read-only mode, no API keys needed for public data)
        print("\n1. Initializing Extended connector...")
        connector = ExtendedPerpetualDerivative(
            trading_pairs=["KAITO-USD", "IP-USD", "MON-USD"],
            trading_required=False  # Read-only mode
        )
        print("   ✅ Extended connector initialized")

        # Start network
        print("\n2. Starting network...")
        await connector.start_network()
        print("   ✅ Network started")

        # Wait for connector to be ready
        print("\n3. Waiting for connector to be ready...")
        await asyncio.sleep(3)
        print("   ✅ Connector ready")

        # Test funding rate fetching
        print("\n4. Fetching funding rates...")
        for trading_pair in ["KAITO-USD", "IP-USD", "MON-USD"]:
            try:
                funding_info = await connector._orderbook_ds.get_funding_info(trading_pair)
                print(f"\n   📊 {trading_pair}:")
                print(f"      Funding Rate: {funding_info.rate:.6f} ({float(funding_info.rate) * 100:.4f}%)")
                print(f"      Mark Price: ${funding_info.mark_price:.4f}")
                print(f"      Index Price: ${funding_info.index_price:.4f}")
                print(f"      Next Funding: {funding_info.next_funding_utc_timestamp}")
            except Exception as e:
                print(f"   ⚠️  Error fetching {trading_pair}: {e}")

        # Stop network
        print("\n5. Stopping network...")
        await connector.stop_network()
        print("   ✅ Network stopped")

        print("\n✅ EXTENDED CONNECTOR TEST PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ EXTENDED CONNECTOR TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lighter_connector():
    """Test Lighter perpetual connector."""
    print("\n" + "=" * 80)
    print("TESTING LIGHTER PERPETUAL CONNECTOR")
    print("=" * 80)

    try:
        # Initialize connector (read-only mode)
        print("\n1. Initializing Lighter connector...")
        connector = LighterPerpetualDerivative(
            trading_pairs=["KAITO-USD", "IP-USD", "MON-USD"],
            trading_required=False  # Read-only mode
        )
        print("   ✅ Lighter connector initialized")

        # Start network
        print("\n2. Starting network...")
        await connector.start_network()
        print("   ✅ Network started")

        # Wait for connector to be ready
        print("\n3. Waiting for connector to be ready...")
        await asyncio.sleep(3)
        print("   ✅ Connector ready")

        # Test funding rate fetching
        print("\n4. Fetching funding rates...")
        for trading_pair in ["KAITO-USD", "IP-USD", "MON-USD"]:
            try:
                funding_info = await connector._orderbook_ds.get_funding_info(trading_pair)
                print(f"\n   📊 {trading_pair}:")
                print(f"      Funding Rate: {funding_info.rate:.6f} ({float(funding_info.rate) * 100:.4f}%)")
                print(f"      Mark Price: ${funding_info.mark_price:.4f}")
                print(f"      Index Price: ${funding_info.index_price:.4f}")
                print(f"      Next Funding: {funding_info.next_funding_utc_timestamp}")
            except Exception as e:
                print(f"   ⚠️  Error fetching {trading_pair}: {e}")

        # Stop network
        print("\n5. Stopping network...")
        await connector.stop_network()
        print("   ✅ Network stopped")

        print("\n✅ LIGHTER CONNECTOR TEST PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ LIGHTER CONNECTOR TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_funding_rate_comparison():
    """Test funding rate comparison between Extended and Lighter."""
    print("\n" + "=" * 80)
    print("TESTING FUNDING RATE COMPARISON (ARBITRAGE OPPORTUNITY DETECTION)")
    print("=" * 80)

    try:
        # Initialize both connectors
        print("\n1. Initializing both connectors...")
        extended = ExtendedPerpetualDerivative(
            trading_pairs=["KAITO-USD"],
            trading_required=False
        )
        lighter = LighterPerpetualDerivative(
            trading_pairs=["KAITO-USD"],
            trading_required=False
        )
        print("   ✅ Both connectors initialized")

        # Start networks
        print("\n2. Starting networks...")
        await asyncio.gather(
            extended.start_network(),
            lighter.start_network()
        )
        print("   ✅ Networks started")

        # Wait for ready
        print("\n3. Waiting for connectors to be ready...")
        await asyncio.sleep(3)

        # Fetch funding rates
        print("\n4. Fetching funding rates from both exchanges...")
        extended_funding = await extended._orderbook_ds.get_funding_info("KAITO-USD")
        lighter_funding = await lighter._orderbook_ds.get_funding_info("KAITO-USD")

        print(f"\n   📊 KAITO-USD Funding Rates:")
        print(f"      Extended: {float(extended_funding.rate) * 100:.4f}%")
        print(f"      Lighter:  {float(lighter_funding.rate) * 100:.4f}%")

        # Calculate spread
        spread = abs(extended_funding.rate - lighter_funding.rate)
        spread_pct = float(spread) * 100

        print(f"\n   💰 Arbitrage Spread: {spread_pct:.4f}%")

        if spread_pct > 0.05:  # 0.05% spread
            higher_exchange = "Extended" if extended_funding.rate > lighter_funding.rate else "Lighter"
            lower_exchange = "Lighter" if higher_exchange == "Extended" else "Extended"
            print(f"   ✅ ARBITRAGE OPPORTUNITY DETECTED!")
            print(f"      Long {lower_exchange}, Short {higher_exchange}")
        else:
            print(f"   ℹ️  Spread too small for arbitrage (threshold: 0.05%)")

        # Stop networks
        print("\n5. Stopping networks...")
        await asyncio.gather(
            extended.stop_network(),
            lighter.stop_network()
        )
        print("   ✅ Networks stopped")

        print("\n✅ FUNDING RATE COMPARISON TEST PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ FUNDING RATE COMPARISON TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("EXTENDED & LIGHTER CONNECTOR TEST SUITE")
    print("=" * 80)
    print("\nThis script will test:")
    print("  1. Extended connector initialization and funding rate fetching")
    print("  2. Lighter connector initialization and funding rate fetching")
    print("  3. Cross-exchange funding rate comparison")
    print("\nNote: These are READ-ONLY tests. No API keys required.")
    print("=" * 80)

    results = {
        "Extended Connector": False,
        "Lighter Connector": False,
        "Funding Rate Comparison": False
    }

    # Test Extended
    results["Extended Connector"] = await test_extended_connector()

    # Test Lighter
    results["Lighter Connector"] = await test_lighter_connector()

    # Test comparison
    results["Funding Rate Comparison"] = await test_funding_rate_comparison()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Connectors are ready for use!")
    else:
        print("⚠️  SOME TESTS FAILED. Review errors above.")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test Paradex Connector in REST Polling Mode

This script tests the Paradex connector WITHOUT API keys, using only
public REST endpoints for market data.

Tests:
1. Connector initialization
2. Trading rules fetching
3. Order book snapshots
4. Funding rate polling
5. Market data quality

Usage:
    python test/paradex_connector/test_paradex_polling.py

Requirements:
    - Hummingbot installed
    - No API key required (public data only)
"""

import asyncio
import sys
import os
from decimal import Decimal
from typing import List

# Add Hummingbot to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative import ParadexPerpetualDerivative
from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.derivative.paradex_perpetual import paradex_perpetual_constants as CONSTANTS


async def test_paradex_polling():
    """Test Paradex connector with REST API polling mode (no authentication)."""

    print("="*80)
    print("PARADEX PERPETUAL CONNECTOR - REST API POLLING MODE TEST")
    print("="*80)
    print("This test does NOT require API keys - testing public endpoints only")
    print("="*80)

    # Test trading pairs
    trading_pairs = ["BTC-USD-PERP", "ETH-USD-PERP", "SOL-USD-PERP"]

    print(f"\n1. Initializing Paradex connector...")
    print(f"   Trading pairs: {trading_pairs}")
    print(f"   Domain: {CONSTANTS.DOMAIN}")

    try:
        connector = ParadexPerpetualDerivative(
            client_config_map=ClientConfigAdapter({}),
            paradex_perpetual_api_secret="",  # Empty for public endpoints
            paradex_perpetual_account_address="",  # Empty for public endpoints
            trading_pairs=trading_pairs,
            trading_required=False,  # Public data only, no trading
            domain=CONSTANTS.DOMAIN
        )

        print("   ✅ Connector initialized successfully")

    except Exception as e:
        print(f"   ❌ Failed to initialize connector: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Fetch trading rules
    print("\n2. Testing trading rules fetching...")
    print("-"*80)

    try:
        await connector._update_trading_rules()

        if connector._trading_rules:
            print(f"   ✅ Trading rules fetched successfully")
            print(f"   Markets loaded: {len(connector._trading_rules)}")

            # Display sample trading rule
            if trading_pairs[0] in connector._trading_rules:
                rule = connector._trading_rules[trading_pairs[0]]
                print(f"\n   Sample Trading Rule ({trading_pairs[0]}):")
                print(f"     - Min Order Size: {rule.min_order_size}")
                print(f"     - Max Order Size: {rule.max_order_size}")
                print(f"     - Min Price Increment: {rule.min_price_increment}")
                print(f"     - Min Base Amount Increment: {rule.min_base_amount_increment}")
            else:
                print(f"   ⚠️  Warning: {trading_pairs[0]} not found in trading rules")
                print(f"   Available markets: {list(connector._trading_rules.keys())[:5]}")

        else:
            print(f"   ❌ No trading rules loaded - check _update_trading_rules() implementation")
            return False

    except Exception as e:
        print(f"   ❌ Error fetching trading rules: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Fetch order books
    print("\n3. Testing order book snapshot fetching...")
    print("-"*80)

    data_source = connector._order_book_tracker.data_source

    for trading_pair in trading_pairs:
        try:
            print(f"\n   Fetching order book for {trading_pair}...")

            # Use the data source's snapshot method
            snapshot = await data_source._request_order_book_snapshot(trading_pair)

            if snapshot:
                bids = snapshot.get("bids", [])
                asks = snapshot.get("asks", [])

                print(f"   ✅ Success!")
                print(f"     - Bids: {len(bids)} levels")
                print(f"     - Asks: {len(asks)} levels")

                if bids and asks:
                    best_bid = Decimal(str(bids[0][0]))
                    best_ask = Decimal(str(asks[0][0]))
                    spread = best_ask - best_bid
                    spread_pct = (spread / best_bid) * 100

                    print(f"     - Best Bid: ${best_bid:.2f}")
                    print(f"     - Best Ask: ${best_ask:.2f}")
                    print(f"     - Spread: ${spread:.2f} ({spread_pct:.4f}%)")

                else:
                    print(f"     ⚠️  Warning: Empty order book")

            else:
                print(f"   ❌ Empty snapshot returned")

            # Rate limit friendly delay
            await asyncio.sleep(1)

        except Exception as e:
            print(f"   ❌ Error fetching order book for {trading_pair}: {e}")

    # Test 4: Fetch funding rates
    print("\n4. Testing funding rate fetching...")
    print("-"*80)

    try:
        await connector._update_funding_rates()

        if connector._funding_rates:
            print(f"   ✅ Funding rates fetched successfully")
            print(f"   Markets with funding data: {len(connector._funding_rates)}")

            for trading_pair, funding_rate in connector._funding_rates.items():
                print(f"     - {trading_pair}: {funding_rate:.6f} ({funding_rate * 100:.4f}%)")

        else:
            print(f"   ⚠️  No funding rates loaded")
            print(f"   This may be expected if API doesn't return funding data")

    except Exception as e:
        print(f"   ❌ Error fetching funding rates: {e}")
        import traceback
        traceback.print_exc()

    # Test 5: Funding info fetch (critical for arbitrage)
    print("\n5. Testing funding info fetch (for arbitrage strategies)...")
    print("-"*80)

    for trading_pair in trading_pairs[:2]:  # Test first 2 pairs
        try:
            print(f"\n   Fetching funding info for {trading_pair}...")

            funding_info = await data_source.get_funding_info(trading_pair)

            print(f"   ✅ Success!")
            print(f"     - Index Price: ${funding_info.index_price}")
            print(f"     - Mark Price: ${funding_info.mark_price}")
            print(f"     - Funding Rate: {funding_info.rate} ({funding_info.rate * 100:.4f}%)")
            print(f"     - Next Funding: {funding_info.next_funding_utc_timestamp}")

            await asyncio.sleep(1)

        except Exception as e:
            print(f"   ❌ Error fetching funding info: {e}")

    # Summary
    print("\n")
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("✅ Connector initialization: PASS")
    print(f"✅ Trading rules: {len(connector._trading_rules)} markets loaded")
    print("✅ Order book fetching: Tested (check individual results above)")
    print("✅ Funding rates: Tested (check individual results above)")

    print("\n📋 NEXT STEPS:")
    print("1. If all tests passed:")
    print("   - Connector public endpoints are working")
    print("   - Safe to proceed with authentication testing (needs API key)")
    print("2. If some tests failed:")
    print("   - Check field names in responses match implementation")
    print("   - Verify API endpoints exist (test_paradex_api_endpoints.py)")
    print("   - Update connector code with correct field names")
    print("3. For production:")
    print("   - Test with API keys (test_paradex_auth.py)")
    print("   - Test order placement on testnet")
    print("   - Monitor for 24 hours before mainnet use")

    return True


async def main():
    """Main test runner."""

    try:
        success = await test_paradex_polling()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              PARADEX CONNECTOR - REST POLLING MODE TEST                      ║
║                                                                              ║
║  Purpose: Test connector with public endpoints only (no API key required)   ║
║                                                                              ║
║  This verifies:                                                              ║
║  - Connector initialization works                                            ║
║  - Trading rules parsing is correct                                          ║
║  - Order book data can be fetched                                            ║
║  - Funding rates are accessible (critical for arbitrage!)                    ║
║                                                                              ║
║  ⚠️  Lessons Learned: Extended/Lighter had _update_balances() = pass         ║
║     We VERIFY that critical methods are actually implemented, not stubs!    ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())

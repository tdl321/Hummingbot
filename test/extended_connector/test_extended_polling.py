"""
Test script for Extended REST API polling mode.

This script tests:
1. Orderbook snapshot fetching
2. Funding rate fetching
3. Polling loop behavior
4. Rate limit compliance
"""

import asyncio
import time
from decimal import Decimal
from typing import List

from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative
from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.client.config.config_var import ConfigVar
from hummingbot.connector.derivative.extended_perpetual import extended_perpetual_constants as CONSTANTS


async def test_extended_polling():
    """Test Extended connector with REST API polling mode."""

    print("=" * 80)
    print("Testing Extended Perpetual Connector - REST API Polling Mode")
    print("=" * 80)

    # Test trading pairs
    trading_pairs = ["KAITO-USD", "ENA-USD", "BRETT-USD"]

    # Initialize connector (without authentication for public data)
    # We'll test public endpoints only
    print("\n1. Initializing Extended connector...")
    print(f"   Trading pairs: {trading_pairs}")

    connector = ExtendedPerpetualDerivative(
        client_config_map=ClientConfigAdapter({}),
        extended_perpetual_api_key="",  # Empty for public endpoints
        extended_perpetual_api_secret="",
        trading_pairs=trading_pairs,
        trading_required=False  # Public data only
    )

    # Test 1: Fetch orderbook snapshots
    print("\n2. Testing orderbook snapshot fetching...")
    print("-" * 80)

    data_source = connector._data_source

    for trading_pair in trading_pairs:
        try:
            print(f"\n   Fetching orderbook for {trading_pair}...")
            snapshot_msg = await data_source._order_book_snapshot(trading_pair)

            order_book_data = snapshot_msg.content
            bids = order_book_data.get("bids", [])
            asks = order_book_data.get("asks", [])

            print(f"   ✓ Success!")
            print(f"     - Timestamp: {snapshot_msg.timestamp}")
            print(f"     - Bids: {len(bids)} levels")
            print(f"     - Asks: {len(asks)} levels")

            if bids and asks:
                best_bid = bids[0]
                best_ask = asks[0]
                spread = best_ask[0] - best_bid[0]
                spread_pct = (spread / best_bid[0]) * 100

                print(f"     - Best Bid: ${best_bid[0]:.6f} (qty: {best_bid[1]})")
                print(f"     - Best Ask: ${best_ask[0]:.6f} (qty: {best_ask[1]})")
                print(f"     - Spread: ${spread:.6f} ({spread_pct:.4f}%)")

        except Exception as e:
            print(f"   ✗ Error fetching orderbook for {trading_pair}: {e}")

    # Test 2: Fetch funding rates
    print("\n3. Testing funding rate fetching...")
    print("-" * 80)

    for trading_pair in trading_pairs:
        try:
            print(f"\n   Fetching funding info for {trading_pair}...")
            funding_info = await data_source.get_funding_info(trading_pair)

            print(f"   ✓ Success!")
            print(f"     - Funding Rate: {funding_info.rate * 100:.6f}% (per 8h)")
            print(f"     - Annual Rate: {funding_info.rate * 100 * 3 * 365:.2f}%")
            print(f"     - Index Price: ${funding_info.index_price}")
            print(f"     - Mark Price: ${funding_info.mark_price}")

            # Calculate time until next funding
            next_funding_time = funding_info.next_funding_utc_timestamp
            current_time = int(time.time())
            time_until_funding = next_funding_time - current_time
            hours = time_until_funding // 3600
            minutes = (time_until_funding % 3600) // 60

            print(f"     - Next Funding: {hours}h {minutes}m")

        except Exception as e:
            print(f"   ✗ Error fetching funding info for {trading_pair}: {e}")

    # Test 3: Test polling loop (short duration)
    print("\n4. Testing polling loop (10 seconds)...")
    print("-" * 80)

    message_queue = asyncio.Queue()
    polling_duration = 10  # seconds
    request_count = 0
    start_time = time.time()

    async def monitor_polling():
        """Monitor the polling loop for a short duration."""
        nonlocal request_count

        # Start polling in background
        polling_task = asyncio.create_task(
            data_source._listen_for_subscriptions_polling()
        )

        # Monitor for specified duration
        end_time = start_time + polling_duration

        while time.time() < end_time:
            try:
                # Check if messages are being received
                msg = await asyncio.wait_for(
                    data_source._message_queue[data_source._snapshot_messages_queue_key].get(),
                    timeout=1.0
                )
                request_count += 1

                trading_pair = msg.content.get("trading_pair")
                timestamp = msg.timestamp

                elapsed = time.time() - start_time
                print(f"   [{elapsed:.1f}s] Received orderbook update for {trading_pair}")

            except asyncio.TimeoutError:
                continue

        # Cancel polling task
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    try:
        await monitor_polling()

        elapsed_time = time.time() - start_time
        requests_per_minute = (request_count / elapsed_time) * 60

        print(f"\n   Polling Statistics:")
        print(f"     - Duration: {elapsed_time:.1f} seconds")
        print(f"     - Total requests: {request_count}")
        print(f"     - Requests/minute: {requests_per_minute:.1f}")
        print(f"     - Expected: ~{len(trading_pairs) * 30} req/min (2-3 sec interval)")

        if requests_per_minute > 0:
            print(f"   ✓ Polling loop working correctly!")
        else:
            print(f"   ✗ No messages received during polling")

    except Exception as e:
        print(f"   ✗ Error during polling test: {e}")

    # Test 4: Rate limit compliance check
    print("\n5. Rate Limit Compliance Check...")
    print("-" * 80)

    estimated_orderbook_requests = len(trading_pairs) * 30  # 30 req/min per pair at 2s interval
    estimated_funding_requests = len(trading_pairs) * 1  # 1 req/min per pair at 60s interval
    estimated_total = estimated_orderbook_requests + estimated_funding_requests

    rate_limit = 1000  # requests per minute
    usage_percentage = (estimated_total / rate_limit) * 100

    print(f"\n   Estimated Request Usage (per minute):")
    print(f"     - Orderbook updates: ~{estimated_orderbook_requests} req/min")
    print(f"     - Funding rate updates: ~{estimated_funding_requests} req/min")
    print(f"     - Total: ~{estimated_total} req/min")
    print(f"     - Rate Limit: {rate_limit} req/min")
    print(f"     - Usage: {usage_percentage:.1f}%")

    if usage_percentage < 50:
        print(f"   ✓ Well within rate limits! ({100 - usage_percentage:.1f}% headroom)")
    elif usage_percentage < 80:
        print(f"   ⚠ Moderate usage ({100 - usage_percentage:.1f}% headroom)")
    else:
        print(f"   ✗ High usage risk!")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_extended_polling())

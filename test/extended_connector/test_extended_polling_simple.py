"""
Simple test script for Extended REST API endpoints.

Tests the REST API directly without requiring full connector initialization.
"""

import asyncio
import aiohttp
import time
from decimal import Decimal


BASE_URL = "https://api.extended.exchange"
# All 12 tokens from the funding arbitrage strategy
MARKETS = ["KAITO-USD", "MON-USD", "IP-USD", "GRASS-USD", "ZEC-USD", "APT-USD",
           "SUI-USD", "TRUMP-USD", "LDO-USD", "OP-USD", "SEI-USD", "MEGA-USD"]


async def test_orderbook_endpoint(session: aiohttp.ClientSession, market: str):
    """Test orderbook snapshot endpoint."""
    url = f"{BASE_URL}/api/v1/info/markets/{market}/orderbook"

    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                if data.get("status") == "OK" and "data" in data:
                    orderbook = data["data"]
                    bids = orderbook.get("bids", [])
                    asks = orderbook.get("asks", [])

                    print(f"\n   ✓ {market} Orderbook:")
                    print(f"     - Status: {response.status}")
                    print(f"     - Bids: {len(bids)} levels")
                    print(f"     - Asks: {len(asks)} levels")

                    if bids and asks:
                        best_bid = float(bids[0][0])
                        best_ask = float(asks[0][0])
                        spread = best_ask - best_bid
                        spread_pct = (spread / best_bid) * 100

                        print(f"     - Best Bid: ${best_bid:.6f}")
                        print(f"     - Best Ask: ${best_ask:.6f}")
                        print(f"     - Spread: ${spread:.6f} ({spread_pct:.4f}%)")

                    return True
                else:
                    print(f"\n   ✗ {market}: Unexpected response format")
                    print(f"     Response: {data}")
                    return False
            else:
                text = await response.text()
                print(f"\n   ✗ {market}: HTTP {response.status}")
                print(f"     Response: {text[:200]}")
                return False

    except Exception as e:
        print(f"\n   ✗ {market}: Error - {e}")
        return False


async def test_market_stats_endpoint(session: aiohttp.ClientSession, market: str):
    """Test market stats endpoint (includes funding rate)."""
    url = f"{BASE_URL}/api/v1/info/markets/{market}/stats"

    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                if data.get("status") == "OK" and "data" in data:
                    stats = data["data"]

                    funding_rate = Decimal(stats.get("fundingRate", "0"))
                    mark_price = Decimal(stats.get("markPrice", "0"))
                    index_price = Decimal(stats.get("indexPrice", "0"))
                    next_funding = int(stats.get("nextFundingRate", 0))
                    open_interest = stats.get("openInterest", "0")

                    # Calculate time until next funding
                    next_funding_sec = next_funding // 1000
                    current_time = int(time.time())
                    time_until = next_funding_sec - current_time
                    hours = time_until // 3600
                    minutes = (time_until % 3600) // 60

                    print(f"\n   ✓ {market} Market Stats:")
                    print(f"     - Status: {response.status}")
                    print(f"     - Funding Rate: {funding_rate * 100:.6f}% (per 8h)")
                    print(f"     - Annual Rate: {funding_rate * 100 * 3 * 365:.2f}%")
                    print(f"     - Mark Price: ${mark_price}")
                    print(f"     - Index Price: ${index_price}")
                    print(f"     - Open Interest: {open_interest}")
                    print(f"     - Next Funding: {hours}h {minutes}m")

                    return True
                else:
                    print(f"\n   ✗ {market}: Unexpected response format")
                    print(f"     Response: {data}")
                    return False
            else:
                text = await response.text()
                print(f"\n   ✗ {market}: HTTP {response.status}")
                print(f"     Response: {text[:200]}")
                return False

    except Exception as e:
        print(f"\n   ✗ {market}: Error - {e}")
        return False


async def test_polling_simulation(session: aiohttp.ClientSession):
    """Simulate continuous polling loop for 1 full minute to test rate limits."""
    print("\n4. Simulating continuous polling loop (60 seconds)...")
    print("-" * 80)

    start_time = time.time()
    duration = 60  # 1 full minute
    polling_interval = 2.0  # seconds
    request_count = 0
    error_count = 0
    rate_limit_errors = 0
    cycle_count = 0

    print(f"   Starting continuous polling of {len(MARKETS)} markets every {polling_interval}s...")
    print(f"   Expected: ~{len(MARKETS) * 30} requests/minute\n")

    while time.time() - start_time < duration:
        loop_start = time.time()
        cycle_count += 1
        cycle_requests = 0

        # Fetch orderbook for each market
        for market in MARKETS:
            try:
                url = f"{BASE_URL}/api/v1/info/markets/{market}/orderbook"
                async with session.get(url) as response:
                    if response.status == 200:
                        request_count += 1
                        cycle_requests += 1
                    elif response.status == 429:
                        rate_limit_errors += 1
                        error_count += 1
                        elapsed = time.time() - start_time
                        print(f"   [{elapsed:.1f}s] ⚠️ RATE LIMIT ERROR (429) for {market}")
                    else:
                        error_count += 1
                        elapsed = time.time() - start_time
                        print(f"   [{elapsed:.1f}s] Error {response.status} for {market}")
            except Exception as e:
                error_count += 1
                elapsed = time.time() - start_time
                print(f"   [{elapsed:.1f}s] Exception fetching {market}: {e}")

        # Report progress every 10 seconds
        elapsed = time.time() - start_time
        if cycle_count % 5 == 0 or elapsed >= duration:  # Every ~10 seconds (5 cycles × 2s)
            current_rate = (request_count / elapsed) * 60
            print(f"   [{elapsed:.1f}s] Cycle {cycle_count}: {cycle_requests} requests | "
                  f"Total: {request_count} | Rate: {current_rate:.1f} req/min")

        # Sleep to maintain polling interval
        loop_elapsed = time.time() - loop_start
        sleep_time = max(0, polling_interval - loop_elapsed)
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

    # Calculate final statistics
    total_time = time.time() - start_time
    requests_per_minute = (request_count / total_time) * 60

    print(f"\n   Final Polling Statistics:")
    print(f"     - Duration: {total_time:.1f} seconds")
    print(f"     - Total cycles: {cycle_count}")
    print(f"     - Successful requests: {request_count}")
    print(f"     - Failed requests: {error_count}")
    print(f"     - Rate limit errors (429): {rate_limit_errors}")
    print(f"     - Average requests/minute: {requests_per_minute:.1f}")
    print(f"     - Expected: ~{len(MARKETS) * 30} req/min (2s interval)")
    print(f"     - Requests per cycle: {request_count / cycle_count:.1f}")

    if rate_limit_errors > 0:
        print(f"     ⚠️ WARNING: {rate_limit_errors} rate limit errors detected!")
    else:
        print(f"     ✅ No rate limit errors!")

    return request_count, requests_per_minute


async def main():
    """Main test function."""
    print("=" * 80)
    print("Testing Extended Perpetual REST API - Polling Mode")
    print("=" * 80)

    async with aiohttp.ClientSession() as session:
        # Test 1: Orderbook endpoints
        print("\n1. Testing Orderbook Endpoints")
        print("-" * 80)

        orderbook_results = []
        for market in MARKETS:
            result = await test_orderbook_endpoint(session, market)
            orderbook_results.append(result)

        # Test 2: Market stats (funding rate) endpoints
        print("\n2. Testing Market Stats Endpoints (Funding Rates)")
        print("-" * 80)

        stats_results = []
        for market in MARKETS:
            result = await test_market_stats_endpoint(session, market)
            stats_results.append(result)

        # Test 3: Last traded prices
        print("\n3. Testing Last Traded Prices")
        print("-" * 80)

        for market in MARKETS:
            url = f"{BASE_URL}/api/v1/info/markets/{market}/stats"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "OK":
                            last_price = data["data"].get("lastPrice", "N/A")
                            print(f"   ✓ {market}: ${last_price}")
                    else:
                        print(f"   ✗ {market}: HTTP {response.status}")
            except Exception as e:
                print(f"   ✗ {market}: Error - {e}")

        # Test 4: Polling simulation
        request_count, req_per_min = await test_polling_simulation(session)

        # Test 5: Rate limit compliance
        print("\n5. Rate Limit Compliance Check")
        print("-" * 80)

        estimated_orderbook_requests = len(MARKETS) * 30  # 30 req/min per pair at 2s interval
        estimated_funding_requests = len(MARKETS) * 1  # 1 req/min per pair at 60s interval
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

        # Summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)

        orderbook_success = sum(orderbook_results)
        stats_success = sum(stats_results)

        print(f"\n   Orderbook Tests: {orderbook_success}/{len(MARKETS)} passed")
        print(f"   Market Stats Tests: {stats_success}/{len(MARKETS)} passed")
        print(f"   Polling Test: {request_count} requests in simulation")

        if orderbook_success == len(MARKETS) and stats_success == len(MARKETS):
            print(f"\n   ✓ All tests passed! Extended REST API polling is working correctly.")
        else:
            print(f"\n   ⚠ Some tests failed. Check the output above for details.")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

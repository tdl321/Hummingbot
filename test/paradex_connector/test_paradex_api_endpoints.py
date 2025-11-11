#!/usr/bin/env python3
"""
Test Paradex API Endpoints

This script verifies that all Paradex API endpoints exist and return expected data.

CRITICAL: This test must be run BEFORE implementing WebSocket or authenticated features
to verify the API is deployed and accessible (Lessons Learned #3.1).

Tests:
1. Public REST endpoints (no authentication required)
2. Response format validation
3. Field name verification
4. API availability check

Usage:
    python test/paradex_connector/test_paradex_api_endpoints.py

Requirements:
    - aiohttp
    - No API key required (public endpoints only)
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, Optional

# Paradex API URLs
MAINNET_BASE_URL = "https://api.prod.paradex.trade/v1"
TESTNET_BASE_URL = "https://api.testnet.paradex.trade/v1"

# Test configuration
USE_TESTNET = True  # Set to False to test mainnet
BASE_URL = TESTNET_BASE_URL if USE_TESTNET else MAINNET_BASE_URL


class ParadexAPITester:
    """Test Paradex API endpoints."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def test_endpoint(
        self,
        name: str,
        path: str,
        expected_fields: Optional[list] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Test a single API endpoint.

        Args:
            name: Test name for display
            path: API endpoint path
            expected_fields: List of expected fields in response
            params: Query parameters

        Returns:
            Test result dictionary
        """
        self.total_tests += 1
        url = f"{self.base_url}{path}"

        print(f"\n{'='*80}")
        print(f"Test: {name}")
        print(f"URL: {url}")
        if params:
            print(f"Params: {params}")
        print(f"{'='*80}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    status = response.status
                    print(f"Status Code: {status}")

                    if status == 200:
                        try:
                            data = await response.json()
                            print(f"✅ SUCCESS - Endpoint exists and returns data")

                            # Display response structure
                            print(f"\nResponse Structure:")
                            if isinstance(data, dict):
                                print(f"  Type: Dictionary")
                                print(f"  Top-level keys: {list(data.keys())}")

                                # Check expected fields
                                if expected_fields:
                                    print(f"\nField Verification:")
                                    for field in expected_fields:
                                        if field in data:
                                            print(f"  ✅ '{field}' - Found")
                                        else:
                                            print(f"  ❌ '{field}' - MISSING (update implementation!)")

                            elif isinstance(data, list):
                                print(f"  Type: List")
                                print(f"  Items: {len(data)}")
                                if data:
                                    print(f"  First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")

                            # Show sample data (limited)
                            print(f"\nSample Response (first 500 chars):")
                            print(json.dumps(data, indent=2)[:500] + "...")

                            self.passed_tests += 1
                            return {
                                "name": name,
                                "status": "PASS",
                                "http_status": status,
                                "data": data
                            }

                        except json.JSONDecodeError as e:
                            print(f"❌ ERROR - Invalid JSON response: {e}")
                            text = await response.text()
                            print(f"Response text: {text[:200]}")
                            self.failed_tests += 1
                            return {
                                "name": name,
                                "status": "FAIL",
                                "error": f"Invalid JSON: {e}"
                            }

                    elif status == 404:
                        print(f"❌ FAIL - Endpoint NOT FOUND (404)")
                        print(f"⚠️  WARNING: This endpoint may not be deployed to production!")
                        print(f"⚠️  Recommendation: Implement REST polling fallback in connector")
                        self.failed_tests += 1
                        return {
                            "name": name,
                            "status": "FAIL",
                            "error": "404 Not Found - Endpoint not deployed"
                        }

                    else:
                        text = await response.text()
                        print(f"❌ FAIL - HTTP {status}")
                        print(f"Response: {text[:200]}")
                        self.failed_tests += 1
                        return {
                            "name": name,
                            "status": "FAIL",
                            "http_status": status,
                            "error": text[:200]
                        }

        except asyncio.TimeoutError:
            print(f"❌ FAIL - Request timed out")
            self.failed_tests += 1
            return {
                "name": name,
                "status": "FAIL",
                "error": "Timeout"
            }
        except Exception as e:
            print(f"❌ FAIL - Exception: {e}")
            self.failed_tests += 1
            return {
                "name": name,
                "status": "FAIL",
                "error": str(e)
            }

    async def run_all_tests(self):
        """Run all API endpoint tests."""

        print("="*80)
        print("PARADEX API ENDPOINT VERIFICATION")
        print("="*80)
        print(f"Environment: {'TESTNET' if USE_TESTNET else 'MAINNET'}")
        print(f"Base URL: {self.base_url}")
        print("="*80)

        # Test 1: System Health
        await self.test_endpoint(
            name="System Health Check",
            path="/system/health",
            expected_fields=[]
        )

        # Test 2: System Config
        await self.test_endpoint(
            name="System Configuration",
            path="/system/config",
            expected_fields=[]
        )

        # Test 3: Markets List
        result = await self.test_endpoint(
            name="Markets List",
            path="/markets",
            expected_fields=["markets"]  # Verify if response has 'markets' field
        )

        # Extract a sample market for subsequent tests
        sample_market = None
        if result.get("status") == "PASS" and result.get("data"):
            data = result["data"]
            if isinstance(data, dict) and "markets" in data and data["markets"]:
                sample_market = data["markets"][0].get("market")
            elif isinstance(data, list) and data:
                sample_market = data[0].get("market") or data[0].get("symbol")

        if not sample_market:
            sample_market = "BTC-USD-PERP"  # Fallback
            print(f"\n⚠️  Using fallback market: {sample_market}")

        print(f"\n📊 Using sample market for remaining tests: {sample_market}")

        # Test 4: Market Summary
        await self.test_endpoint(
            name="Market Summary",
            path=f"/markets/{sample_market}/summary",
            expected_fields=["last_price", "mark_price", "funding_rate"]
        )

        # Test 5: Order Book
        await self.test_endpoint(
            name="Order Book Snapshot",
            path=f"/markets/{sample_market}/orderbook",
            expected_fields=["bids", "asks"]
        )

        # Test 6: Recent Trades
        await self.test_endpoint(
            name="Recent Trades",
            path=f"/markets/{sample_market}/trades",
            expected_fields=[]
        )

        # Test 7: Funding Rate
        await self.test_endpoint(
            name="Funding Rate",
            path=f"/markets/{sample_market}/funding",
            expected_fields=["funding_rate", "next_funding_time"]
        )

        # Test 8: Candles/OHLCV (optional)
        await self.test_endpoint(
            name="Candles/OHLCV Data",
            path=f"/markets/{sample_market}/candles",
            params={"interval": "1h", "limit": 10}
        )

    def print_summary(self):
        """Print test summary."""
        print("\n")
        print("="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("="*80)

        if self.failed_tests > 0:
            print("\n⚠️  CRITICAL RECOMMENDATIONS:")
            print("1. Verify failed endpoint URLs from Paradex documentation")
            print("2. Check if API version has changed (currently using /v1)")
            print("3. For 404 errors: Implement REST polling fallback in connector")
            print("4. Update field names in connector implementation if response format differs")
            print("5. Consider reaching out to Paradex support for API clarification")

        print("\n📋 NEXT STEPS:")
        if self.failed_tests == 0:
            print("✅ All endpoints verified! Safe to proceed with:")
            print("   - WebSocket testing (test_paradex_websocket.py)")
            print("   - Polling mode testing (test_paradex_polling.py)")
        else:
            print("⚠️  Fix endpoint issues before proceeding")
            print("   - Update connector implementation with correct URLs/fields")
            print("   - Add REST polling fallback for missing endpoints")

        return self.failed_tests == 0


async def main():
    """Main test runner."""
    tester = ParadexAPITester(BASE_URL)

    try:
        await tester.run_all_tests()
        success = tester.print_summary()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   PARADEX API ENDPOINT VERIFICATION TEST                     ║
║                                                                              ║
║  Purpose: Verify Paradex API endpoints exist before connector deployment    ║
║  Lessons Learned: Extended connector assumed endpoints existed (they didn't)║
║                                                                              ║
║  This test requires NO API KEY - testing public endpoints only              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())

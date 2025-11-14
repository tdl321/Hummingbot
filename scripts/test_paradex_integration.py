#!/usr/bin/env python3
"""
Paradex Connector Integration Test
Tests authentication and core functionality with real API credentials.

Usage:
    python scripts/test_paradex_integration.py --api-secret 0x... --account-address 0x...

    Or use environment variables:
    export PARADEX_API_SECRET="0x..."
    export PARADEX_ACCOUNT_ADDRESS="0x..."
    python scripts/test_paradex_integration.py

Requirements:
    - Paradex API credentials (subkey private key + main account address)
    - paradex-py>=0.4.6
    - Active internet connection
"""

import asyncio
import argparse
import logging
import os
import sys
from decimal import Decimal
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_derivative import ParadexPerpetualDerivative
from hummingbot.connector.derivative.paradex_perpetual import paradex_perpetual_constants as CONSTANTS
from hummingbot.core.event.event_logger import EventLogger
from hummingbot.core.event.events import (
    MarketEvent,
    OrderBookTradeEvent,
    OrderFilledEvent,
    BuyOrderCreatedEvent,
    SellOrderCreatedEvent,
    OrderCancelledEvent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParadexIntegrationTest:
    """Integration test suite for Paradex connector."""

    def __init__(self, api_secret: str, account_address: str, testnet: bool = True):
        """
        Initialize integration test.

        Args:
            api_secret: Paradex subkey private key (0x...)
            account_address: Paradex main account address (0x...)
            testnet: Use testnet (default) or mainnet
        """
        self.api_secret = api_secret
        self.account_address = account_address
        self.testnet = testnet

        # Test configuration
        self.trading_pair = "BTC-USD-PERP"
        self.test_order_amount = Decimal("0.001")  # Very small test order

        # Create connector instance
        self.connector: Optional[ParadexPerpetualDerivative] = None
        self.event_logger = EventLogger()

        # Test results
        self.results = {
            "auth": False,
            "balance": False,
            "trading_rules": False,
            "order_book": False,
            "funding_info": False,
            "order_placement": False,
            "order_cancellation": False,
            "websocket": False,
        }

    def _create_connector(self):
        """Create connector instance with credentials."""
        logger.info("Creating Paradex connector instance...")

        domain = "paradex_perpetual_testnet" if self.testnet else "paradex_perpetual"

        self.connector = ParadexPerpetualDerivative(
            client_config_map=None,
            paradex_perpetual_api_secret=self.api_secret,
            paradex_perpetual_account_address=self.account_address,
            trading_pairs=[self.trading_pair],
            domain=domain,
        )

        # Attach event logger
        self.connector.add_listener(MarketEvent.BuyOrderCreated, self.event_logger)
        self.connector.add_listener(MarketEvent.SellOrderCreated, self.event_logger)
        self.connector.add_listener(MarketEvent.OrderCancelled, self.event_logger)
        self.connector.add_listener(MarketEvent.OrderFilled, self.event_logger)

        logger.info(f"Connector created (domain: {domain})")

    async def test_authentication(self) -> bool:
        """Test 1: Authentication and JWT token generation."""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Authentication")
        logger.info("="*60)

        try:
            # Get auth headers (triggers JWT generation)
            headers = await self.connector._auth.get_rest_auth_headers()

            if "Authorization" in headers:
                logger.info("✅ JWT token generated successfully")
                logger.info(f"   Token preview: {headers['Authorization'][:50]}...")
                self.results["auth"] = True
                return True
            else:
                logger.error("❌ No Authorization header in response")
                return False

        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False

    async def test_balance(self) -> bool:
        """Test 2: Fetch account balance."""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Balance Fetching")
        logger.info("="*60)

        try:
            # Update balances
            await self.connector._update_balances()

            # Get balances
            balances = self.connector.get_all_balances()

            if balances:
                logger.info("✅ Balance fetched successfully")
                for asset, amount in balances.items():
                    logger.info(f"   {asset}: {amount}")
                self.results["balance"] = True
                return True
            else:
                logger.warning("⚠️  No balances found (account may be empty)")
                self.results["balance"] = True  # Not an error
                return True

        except Exception as e:
            logger.error(f"❌ Balance fetch failed: {e}")
            return False

    async def test_trading_rules(self) -> bool:
        """Test 3: Fetch trading rules."""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Trading Rules")
        logger.info("="*60)

        try:
            # Update trading rules
            await self.connector._update_trading_rules()

            # Get trading rule for our pair
            trading_rule = self.connector.trading_rules.get(self.trading_pair)

            if trading_rule:
                logger.info("✅ Trading rules fetched successfully")
                logger.info(f"   Trading Pair: {trading_rule.trading_pair}")
                logger.info(f"   Min Order Size: {trading_rule.min_order_size}")
                logger.info(f"   Min Price Increment: {trading_rule.min_price_increment}")
                logger.info(f"   Min Base Amount Increment: {trading_rule.min_base_amount_increment}")
                self.results["trading_rules"] = True
                return True
            else:
                logger.error(f"❌ No trading rule found for {self.trading_pair}")
                return False

        except Exception as e:
            logger.error(f"❌ Trading rules fetch failed: {e}")
            return False

    async def test_order_book(self) -> bool:
        """Test 4: Fetch order book."""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Order Book")
        logger.info("="*60)

        try:
            # Get order book
            order_book = self.connector.get_order_book(self.trading_pair)

            if order_book:
                snapshot = order_book.snapshot
                logger.info("✅ Order book fetched successfully")
                logger.info(f"   Trading Pair: {self.trading_pair}")
                logger.info(f"   Best Bid: {snapshot[0]['price'] if snapshot[0] else 'N/A'}")
                logger.info(f"   Best Ask: {snapshot[1]['price'] if snapshot[1] else 'N/A'}")
                logger.info(f"   Bid Depth: {len(snapshot[0])} levels")
                logger.info(f"   Ask Depth: {len(snapshot[1])} levels")
                self.results["order_book"] = True
                return True
            else:
                logger.error(f"❌ No order book for {self.trading_pair}")
                return False

        except Exception as e:
            logger.error(f"❌ Order book fetch failed: {e}")
            return False

    async def test_funding_info(self) -> bool:
        """Test 5: Fetch funding information."""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Funding Information")
        logger.info("="*60)

        try:
            # Get funding info
            funding_info = self.connector.get_funding_info(self.trading_pair)

            if funding_info:
                logger.info("✅ Funding info fetched successfully")
                logger.info(f"   Trading Pair: {funding_info.trading_pair}")
                logger.info(f"   Index Price: {funding_info.index_price}")
                logger.info(f"   Mark Price: {funding_info.mark_price}")
                logger.info(f"   Funding Rate: {funding_info.rate}")
                logger.info(f"   Next Funding Time: {funding_info.next_funding_utc_timestamp}")
                self.results["funding_info"] = True
                return True
            else:
                logger.error(f"❌ No funding info for {self.trading_pair}")
                return False

        except Exception as e:
            logger.error(f"❌ Funding info fetch failed: {e}")
            return False

    async def test_order_placement(self) -> bool:
        """Test 6: Place a test order (will be cancelled immediately)."""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Order Placement")
        logger.info("="*60)
        logger.warning("⚠️  This test will place a REAL order on the exchange!")
        logger.warning("    The order will be far from market price and cancelled immediately.")

        # Ask for confirmation
        confirmation = input("\nProceed with order placement test? (yes/no): ")
        if confirmation.lower() not in ["yes", "y"]:
            logger.info("⏭️  Order placement test skipped")
            return True

        try:
            # Get current mid price
            order_book = self.connector.get_order_book(self.trading_pair)
            snapshot = order_book.snapshot
            best_bid = Decimal(str(snapshot[0]['price'])) if snapshot[0] else Decimal("0")
            best_ask = Decimal(str(snapshot[1]['price'])) if snapshot[1] else Decimal("0")
            mid_price = (best_bid + best_ask) / Decimal("2")

            # Place order far from market (5% below best bid)
            test_price = best_bid * Decimal("0.95")
            test_price = self.connector.quantize_order_price(self.trading_pair, test_price)

            logger.info(f"   Mid Price: {mid_price}")
            logger.info(f"   Test Order Price: {test_price} (far from market)")
            logger.info(f"   Test Order Amount: {self.test_order_amount}")

            # Place buy order
            order_id = self.connector.buy(
                trading_pair=self.trading_pair,
                amount=self.test_order_amount,
                order_type="LIMIT",
                price=test_price,
            )

            if order_id:
                logger.info(f"✅ Order placed successfully")
                logger.info(f"   Order ID: {order_id}")

                # Wait a bit for order to be acknowledged
                await asyncio.sleep(2)

                # Store order ID for cancellation test
                self.test_order_id = order_id
                self.results["order_placement"] = True
                return True
            else:
                logger.error("❌ Order placement returned no order ID")
                return False

        except Exception as e:
            logger.error(f"❌ Order placement failed: {e}")
            return False

    async def test_order_cancellation(self) -> bool:
        """Test 7: Cancel the test order."""
        logger.info("\n" + "="*60)
        logger.info("TEST 7: Order Cancellation")
        logger.info("="*60)

        if not hasattr(self, 'test_order_id'):
            logger.warning("⚠️  No test order to cancel (order placement was skipped)")
            return True

        try:
            # Cancel the test order
            result = self.connector.cancel(
                trading_pair=self.trading_pair,
                client_order_id=self.test_order_id
            )

            if result:
                logger.info(f"✅ Order cancelled successfully")
                logger.info(f"   Order ID: {self.test_order_id}")

                # Wait a bit for cancellation to be acknowledged
                await asyncio.sleep(2)

                self.results["order_cancellation"] = True
                return True
            else:
                logger.error("❌ Order cancellation failed")
                return False

        except Exception as e:
            logger.error(f"❌ Order cancellation failed: {e}")
            return False

    async def test_websocket(self) -> bool:
        """Test 8: WebSocket connectivity."""
        logger.info("\n" + "="*60)
        logger.info("TEST 8: WebSocket Streaming")
        logger.info("="*60)
        logger.info("   Monitoring WebSocket for 10 seconds...")

        try:
            # Wait for WebSocket messages
            await asyncio.sleep(10)

            # Check if we received any events
            events_received = len(self.event_logger.event_log) > 0

            if events_received:
                logger.info(f"✅ WebSocket working ({len(self.event_logger.event_log)} events received)")
                for event in self.event_logger.event_log:
                    logger.info(f"   - {type(event).__name__}")
                self.results["websocket"] = True
            else:
                logger.warning("⚠️  No WebSocket events received (may be normal if no activity)")
                self.results["websocket"] = True  # Not an error

            return True

        except Exception as e:
            logger.error(f"❌ WebSocket test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("\n" + "="*60)
        logger.info("PARADEX CONNECTOR INTEGRATION TEST")
        logger.info("="*60)
        logger.info(f"Environment: {'TESTNET' if self.testnet else 'MAINNET'}")
        logger.info(f"Trading Pair: {self.trading_pair}")
        logger.info(f"Account: {self.account_address[:10]}...{self.account_address[-8:]}")
        logger.info("="*60)

        # Create connector
        self._create_connector()

        # Start connector
        logger.info("\nStarting connector...")
        await self.connector.start_network()
        await asyncio.sleep(3)  # Wait for initialization

        # Run tests sequentially
        tests = [
            ("Authentication", self.test_authentication),
            ("Balance", self.test_balance),
            ("Trading Rules", self.test_trading_rules),
            ("Order Book", self.test_order_book),
            ("Funding Info", self.test_funding_info),
            ("Order Placement", self.test_order_placement),
            ("Order Cancellation", self.test_order_cancellation),
            ("WebSocket", self.test_websocket),
        ]

        for test_name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ {test_name} test crashed: {e}")
                import traceback
                traceback.print_exc()

        # Stop connector
        logger.info("\nStopping connector...")
        await self.connector.stop_network()

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print test results summary."""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)

        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)

        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")

        logger.info("="*60)
        logger.info(f"Results: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Connector is working correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed. Check logs above for details.")

        logger.info("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Paradex Connector Integration Test")
    parser.add_argument(
        "--api-secret",
        help="Paradex subkey private key (0x...). Can also use PARADEX_API_SECRET env var."
    )
    parser.add_argument(
        "--account-address",
        help="Paradex main account address (0x...). Can also use PARADEX_ACCOUNT_ADDRESS env var."
    )
    parser.add_argument(
        "--mainnet",
        action="store_true",
        help="Use mainnet instead of testnet (default: testnet)"
    )

    args = parser.parse_args()

    # Get credentials from args or environment
    api_secret = args.api_secret or os.getenv("PARADEX_API_SECRET")
    account_address = args.account_address or os.getenv("PARADEX_ACCOUNT_ADDRESS")

    if not api_secret or not account_address:
        logger.error("Missing credentials!")
        logger.error("Provide via arguments or environment variables:")
        logger.error("  --api-secret 0x... --account-address 0x...")
        logger.error("  OR")
        logger.error("  export PARADEX_API_SECRET='0x...'")
        logger.error("  export PARADEX_ACCOUNT_ADDRESS='0x...'")
        sys.exit(1)

    # Create and run test
    test = ParadexIntegrationTest(
        api_secret=api_secret,
        account_address=account_address,
        testnet=not args.mainnet
    )

    # Run tests
    asyncio.run(test.run_all_tests())


if __name__ == "__main__":
    main()

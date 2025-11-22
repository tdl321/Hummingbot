#!/usr/bin/env python3
"""
Test Extended connector with WebSocket streaming for balance updates.

This script verifies that the updated connector properly:
1. Connects to WebSocket
2. Receives balance updates
3. Updates internal balance tracking
"""

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

# Add hummingbot to path
HUMMINGBOT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(HUMMINGBOT_ROOT))

from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import (
    ExtendedPerpetualDerivative,
)


async def test_connector_websocket():
    """Test Extended connector with WebSocket balance updates."""

    # Load environment variables
    env_path = HUMMINGBOT_ROOT / ".env"
    if not env_path.exists():
        print(f"❌ .env file not found: {env_path}")
        return

    load_dotenv(env_path)

    api_key = os.getenv("EXTENDED_API_KEY")
    api_secret = os.getenv("EXTENDED_STARK_PRIVATE_KEY")

    if not api_key or not api_secret:
        print("❌ Missing Extended credentials in .env file")
        return

    print(f"{'='*80}")
    print(f"Extended Connector WebSocket Test")
    print(f"{'='*80}")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"{'='*80}\n")

    # Initialize connector
    print("1. Initializing Extended connector...")
    connector = ExtendedPerpetualDerivative(
        extended_perpetual_api_key=api_key,
        extended_perpetual_api_secret=api_secret,
        trading_pairs=["BTC-USD", "ETH-USD"],
        trading_required=True,
    )

    try:
        # Start connector
        print("2. Starting connector (initializing WebSocket)...")
        await connector.start()
        print("✅ Connector started\n")

        # Wait a bit for WebSocket to connect and receive initial snapshot
        print("3. Waiting for WebSocket connection and initial messages...")
        await asyncio.sleep(5)

        # Check if balance was received
        print("\n4. Checking balance updates...")
        print(f"{'─'*80}")

        if "USD" in connector._account_balances:
            total_balance = connector._account_balances["USD"]
            available_balance = connector._account_available_balances.get("USD", Decimal("0"))

            print(f"✅ Balance received via WebSocket!")
            print(f"   Total Balance: {total_balance} USD")
            print(f"   Available Balance: {available_balance} USD")
        else:
            print(f"⚠️  No balance received yet")
            print(f"   Account balances: {connector._account_balances}")

        # Monitor for 30 more seconds
        print(f"\n5. Monitoring WebSocket for 30 seconds...")
        print(f"{'─'*80}")
        print("   (Try placing an order on Extended to see real-time updates)\n")

        for i in range(6):
            await asyncio.sleep(5)

            if "USD" in connector._account_balances:
                balance = connector._account_balances["USD"]
                available = connector._account_available_balances.get("USD", Decimal("0"))
                print(f"   [{(i+1)*5}s] Balance: {balance} USD, Available: {available} USD")
            else:
                print(f"   [{(i+1)*5}s] No balance update yet")

        print(f"\n{'='*80}")
        print("Test Complete!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Error during test: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Stop connector
        print("\n6. Stopping connector...")
        await connector.stop()
        print("✅ Connector stopped")


if __name__ == "__main__":
    try:
        asyncio.run(test_connector_websocket())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)

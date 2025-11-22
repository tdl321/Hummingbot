#!/usr/bin/env python3
"""
Test Extended user stream data source with WebSocket.

This directly tests the user stream to verify WebSocket connectivity
and balance message processing.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add hummingbot to path
HUMMINGBOT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(HUMMINGBOT_ROOT))

from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_user_stream_data_source import (
    ExtendedPerpetualUserStreamDataSource,
)
from hummingbot.connector.derivative.extended_perpetual import extended_perpetual_web_utils as web_utils


class MockConnector:
    """Mock connector for testing user stream."""

    def __init__(self, api_key: str):
        self.extended_perpetual_api_key = api_key
        self._domain = "extended_perpetual"


async def test_user_stream():
    """Test Extended user stream WebSocket connection."""

    # Load environment variables
    env_path = HUMMINGBOT_ROOT / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("EXTENDED_API_KEY")
    if not api_key:
        print("❌ EXTENDED_API_KEY not found in .env")
        return

    print(f"{'='*80}")
    print(f"Extended User Stream WebSocket Test")
    print(f"{'='*80}")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"{'='*80}\n")

    # Create mock connector
    mock_connector = MockConnector(api_key)

    # Create API factory
    api_factory = web_utils.build_api_factory(throttler=web_utils.create_throttler())

    # Create user stream data source
    print("1. Creating user stream data source...")
    user_stream = ExtendedPerpetualUserStreamDataSource(
        connector=mock_connector,
        api_factory=api_factory,
        domain="extended_perpetual"
    )
    print("✅ User stream created\n")

    # Create output queue
    output_queue = asyncio.Queue()

    # Start listening in background
    print("2. Starting WebSocket listener (40 second test)...")
    print(f"{'─'*80}\n")

    listen_task = asyncio.create_task(user_stream.listen_for_user_stream(output_queue))

    try:
        # Monitor messages for 40 seconds
        message_count = 0
        balance_count = 0
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < 40:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(output_queue.get(), timeout=5)
                message_count += 1

                msg_type = message.get("type", "")
                print(f"📨 Message #{message_count}: type={msg_type}")

                if msg_type == "BALANCE":
                    balance_count += 1
                    data = message.get("data", {})
                    balance_data = data.get("balance", {})

                    if balance_data:
                        print(f"   💰 Balance Update:")
                        print(f"      Equity: {balance_data.get('equity')}")
                        print(f"      Available: {balance_data.get('availableForTrade')}")
                        print(f"      Unrealized PnL: {balance_data.get('unrealisedPnl')}")
                    else:
                        print(f"   Data: {data}")

                elif msg_type == "ORDER":
                    print(f"   📋 Order Update")
                elif msg_type == "POSITION":
                    print(f"   📊 Position Update")
                else:
                    print(f"   ℹ️  Other: {message}")

                print()

            except asyncio.TimeoutError:
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"⏳ No message in last 5s (elapsed: {elapsed:.1f}s)")
                continue

        print(f"\n{'='*80}")
        print("Test Summary")
        print(f"{'='*80}")
        print(f"Total messages: {message_count}")
        print(f"Balance updates: {balance_count}")
        print(f"{'='*80}\n")

        if balance_count > 0:
            print("✅ SUCCESS - WebSocket balance updates working!")
        else:
            print("⚠️  No balance updates received (connection might be idle)")

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cancel listening task
        listen_task.cancel()
        try:
            await listen_task
        except asyncio.CancelledError:
            pass

        print("\n✅ Test complete")


if __name__ == "__main__":
    try:
        asyncio.run(test_user_stream())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(0)

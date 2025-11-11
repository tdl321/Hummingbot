#!/usr/bin/env python3
"""
Test Paradex WebSocket Connection

This script tests Paradex WebSocket connectivity and public channels.

CRITICAL: Many exchanges document WebSocket APIs that aren't deployed (Lessons Learned #3.1).
This test verifies WebSocket is actually available before implementing streaming features.

Tests:
1. WebSocket connection establishment
2. Public channel subscriptions (no auth required)
3. Message format verification
4. Connection stability

Usage:
    python test/paradex_connector/test_paradex_websocket.py

Requirements:
    - websockets or aiohttp
    - No API key required (public channels only)
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Optional

# Paradex WebSocket URLs (Verified from official docs)
MAINNET_WS_URL = "wss://ws.api.prod.paradex.trade/v1"
TESTNET_WS_URL = "wss://ws.api.testnet.paradex.trade/v1"

# Test configuration
USE_TESTNET = True  # Set to False to test mainnet
WS_URL = TESTNET_WS_URL if USE_TESTNET else MAINNET_WS_URL

# Test duration
TEST_DURATION_SECONDS = 30  # Listen for 30 seconds
SAMPLE_MARKET = "BTC-USD-PERP"  # Market to test


class ParadexWebSocketTester:
    """Test Paradex WebSocket connection."""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.connected = False
        self.messages_received = 0
        self.channels_tested = []
        self.sample_messages = {}

    async def test_connection(self):
        """Test WebSocket connection and message reception."""

        print("="*80)
        print("PARADEX WEBSOCKET CONNECTION TEST")
        print("="*80)
        print(f"Environment: {'TESTNET' if USE_TESTNET else 'MAINNET'}")
        print(f"WebSocket URL: {self.ws_url}")
        print(f"Test Duration: {TEST_DURATION_SECONDS} seconds")
        print(f"Sample Market: {SAMPLE_MARKET}")
        print("="*80)

        try:
            print(f"\n[{self._timestamp()}] Connecting to WebSocket...")

            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    self.ws_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as ws:

                    self.connected = True
                    print(f"[{self._timestamp()}] ✅ Connected successfully!")

                    # Subscribe to public channels
                    await self._subscribe_to_channels(ws)

                    # Listen for messages
                    await self._listen_for_messages(ws, duration=TEST_DURATION_SECONDS)

        except aiohttp.ClientConnectorError as e:
            print(f"\n[{self._timestamp()}] ❌ Connection FAILED - Cannot reach WebSocket server")
            print(f"Error: {e}")
            print(f"\n⚠️  CRITICAL: WebSocket endpoint is NOT available!")
            print(f"⚠️  This is similar to Extended connector issue (documented but not deployed)")
            return False

        except aiohttp.WSServerHandshakeError as e:
            print(f"\n[{self._timestamp()}] ❌ Handshake FAILED - WebSocket not accepting connections")
            print(f"Error: {e}")
            print(f"\n⚠️  CRITICAL: WebSocket endpoint exists but rejects connections!")
            return False

        except asyncio.TimeoutError:
            print(f"\n[{self._timestamp()}] ❌ Connection TIMEOUT")
            print(f"\n⚠️  WebSocket is not responding within timeout")
            return False

        except Exception as e:
            print(f"\n[{self._timestamp()}] ❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True

    async def _subscribe_to_channels(self, ws):
        """Subscribe to public channels."""

        print(f"\n[{self._timestamp()}] Subscribing to public channels...")

        # Paradex uses JSON-RPC 2.0 format (verified from docs)
        # Format: {"jsonrpc": "2.0", "id": 1, "method": "subscribe", "params": {"channel": "..."}}

        subscription_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribe",
            "params": {
                "channel": "markets_summary"
            }
        }

        print(f"[{self._timestamp()}] Sending subscription:")
        print(f"  {json.dumps(subscription_msg, indent=2)}")

        try:
            await ws.send_json(subscription_msg)
            print(f"[{self._timestamp()}] ✅ Subscription sent")

        except Exception as e:
            print(f"[{self._timestamp()}] ❌ Failed to send subscription: {e}")

    async def _listen_for_messages(self, ws, duration: int):
        """Listen for WebSocket messages."""

        print(f"\n[{self._timestamp()}] Listening for messages ({duration} seconds)...")
        print("="*80)

        start_time = asyncio.get_event_loop().time()
        end_time = start_time + duration

        try:
            while asyncio.get_event_loop().time() < end_time:
                try:
                    msg = await asyncio.wait_for(ws.receive(), timeout=1.0)

                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self.messages_received += 1
                        self._process_message(msg.data)

                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print(f"\n[{self._timestamp()}] ⚠️  WebSocket closed by server")
                        break

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"\n[{self._timestamp()}] ❌ WebSocket error")
                        break

                except asyncio.TimeoutError:
                    # No message received, continue listening
                    continue

        except Exception as e:
            print(f"\n[{self._timestamp()}] Error during message listening: {e}")

        print("\n" + "="*80)
        print(f"[{self._timestamp()}] Listening completed")
        print(f"Total messages received: {self.messages_received}")

    def _process_message(self, message_data: str):
        """Process and display WebSocket message."""

        try:
            data = json.loads(message_data)

            # Extract channel info
            channel = data.get("channel") or data.get("type") or "unknown"

            # Track channels
            if channel not in self.channels_tested:
                self.channels_tested.append(channel)
                print(f"\n[{self._timestamp()}] 📨 New channel received: {channel}")

            # Store sample message for each channel (first message only)
            if channel not in self.sample_messages:
                self.sample_messages[channel] = data
                print(f"[{self._timestamp()}] Sample message structure:")
                print(json.dumps(data, indent=2)[:500] + "...")

            # Display message count
            if self.messages_received % 10 == 0:
                print(f"[{self._timestamp()}] Messages received: {self.messages_received}")

        except json.JSONDecodeError:
            print(f"[{self._timestamp()}] ⚠️  Non-JSON message: {message_data[:100]}")

    def _timestamp(self) -> str:
        """Get formatted timestamp."""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def print_summary(self):
        """Print test summary."""

        print("\n")
        print("="*80)
        print("WEBSOCKET TEST SUMMARY")
        print("="*80)
        print(f"Connection: {'✅ SUCCESS' if self.connected else '❌ FAILED'}")
        print(f"Messages Received: {self.messages_received}")
        print(f"Channels Active: {len(self.channels_tested)}")

        if self.channels_tested:
            print(f"\nChannels Tested:")
            for channel in self.channels_tested:
                print(f"  ✅ {channel}")

        print("\n" + "="*80)

        # Recommendations
        print("\n📋 RECOMMENDATIONS:")

        if not self.connected:
            print("❌ WebSocket NOT AVAILABLE")
            print("   Action Required:")
            print("   1. Verify WebSocket URL from Paradex documentation")
            print("   2. Check if WebSocket API version has changed")
            print("   3. IMPLEMENT REST POLLING FALLBACK in connector (MANDATORY)")
            print("   4. Update paradex_perpetual_api_order_book_data_source.py:")
            print("      - Set _ws_endpoint_verified = False")
            print("      - Ensure _listen_for_subscriptions_polling() is functional")
            return False

        elif self.messages_received == 0:
            print("⚠️  WebSocket connects but NO MESSAGES received")
            print("   Possible Issues:")
            print("   1. Subscription message format incorrect")
            print("   2. Authentication required for all channels (check docs)")
            print("   3. Market symbol format wrong")
            print("   Action Required:")
            print("   1. Verify subscription message format from Paradex docs")
            print("   2. Test with different market symbols")
            print("   3. Check if public channels actually exist")
            print("   4. IMPLEMENT REST POLLING FALLBACK as safety net")
            return False

        else:
            print("✅ WebSocket WORKING!")
            print("   Next Steps:")
            print("   1. Verify message formats match connector implementation")
            print("   2. Update field names in data source if needed")
            print("   3. Test private channels with authentication (needs API key)")
            print("   4. Still implement REST polling fallback (best practice)")
            return True


async def main():
    """Main test runner."""

    tester = ParadexWebSocketTester(WS_URL)

    try:
        success = await tester.test_connection()
        success = tester.print_summary() and success

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        tester.print_summary()
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PARADEX WEBSOCKET CONNECTION TEST                         ║
║                                                                              ║
║  Purpose: Verify WebSocket is deployed before implementing streaming        ║
║  Lessons Learned: Extended connector's WebSocket returned 404 (not deployed)║
║                                                                              ║
║  This test requires NO API KEY - testing public channels only               ║
║                                                                              ║
║  If WebSocket fails: Connector MUST use REST polling fallback               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    print(f"\n⏱️  This test will run for {TEST_DURATION_SECONDS} seconds...")
    print(f"   Press Ctrl+C to stop early\n")

    asyncio.run(main())

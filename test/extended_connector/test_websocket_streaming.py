#!/usr/bin/env python3
"""
Extended Exchange WebSocket Account Stream Test Script

This script tests the Extended exchange WebSocket connection for real-time account updates,
including balance updates, order updates, position updates, and funding payments.

Based on Extended API documentation:
- WebSocket URL: wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account
- Authentication: X-API-KEY as query parameter
- Server sends pings every 15 seconds, expects pong within 10 seconds
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import websockets
from dotenv import load_dotenv

# Add hummingbot to path
HUMMINGBOT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(HUMMINGBOT_ROOT))


class ExtendedWebSocketTester:
    """Test Extended exchange WebSocket account streaming."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None
        self.message_count = 0
        self.balance_updates = []
        self.order_updates = []
        self.position_updates = []
        self.funding_payments = []
        self.raw_messages = []

    def get_websocket_url(self) -> str:
        """
        Construct WebSocket URL with API key authentication.

        Testing multiple URL formats:
        1. Query parameter authentication: ?X-API-KEY=...
        2. Base URL variations
        """
        base_urls = [
            "wss://starknet.app.extended.exchange/stream.extended.exchange/v1/account",
            "wss://api.starknet.extended.exchange/stream.extended.exchange/v1/account",
        ]

        # Try with query parameter first
        return f"{base_urls[0]}?X-API-KEY={self.api_key}"

    async def connect(self) -> bool:
        """
        Connect to Extended WebSocket with authentication.

        Returns:
            bool: True if connection successful
        """
        url = self.get_websocket_url()

        print(f"\n{'='*80}")
        print(f"Extended WebSocket Connection Test")
        print(f"{'='*80}")
        print(f"URL: {url[:60]}...{url[-20:]}")  # Partially hide API key
        print(f"Time: {datetime.now().isoformat()}")
        print(f"{'='*80}\n")

        try:
            # Connect with custom headers
            headers = {
                "User-Agent": "HummingbotExtendedConnector/1.0",
            }

            print("Connecting to WebSocket...")
            self.ws = await websockets.connect(
                url,
                extra_headers=headers,
                ping_interval=None,  # We'll handle pings manually
                ping_timeout=None,
                close_timeout=10,
            )

            print(f"✅ Connected successfully!")
            print(f"Connection state: {self.ws.state.name}")
            return True

        except websockets.exceptions.InvalidStatusCode as e:
            print(f"❌ Connection failed with HTTP status: {e.status_code}")
            print(f"Response headers: {e.response_headers}")
            return False
        except Exception as e:
            print(f"❌ Connection error: {type(e).__name__}: {e}")
            return False

    async def send_pong(self, ping_data: str = ""):
        """Send pong response to server ping."""
        if self.ws:
            try:
                await self.ws.pong(ping_data.encode() if ping_data else b"")
                print(f"📤 Sent pong response")
            except Exception as e:
                print(f"❌ Error sending pong: {e}")

    async def process_message(self, message: str):
        """
        Process incoming WebSocket message.

        Expected message types from Extended:
        - ORDER: Order status updates
        - TRADE: Trade execution updates
        - BALANCE: Balance updates
        - POSITION: Position updates
        - FUNDING: Funding payment updates
        """
        try:
            self.message_count += 1
            timestamp = datetime.now().isoformat()

            # Try to parse as JSON
            try:
                data = json.loads(message)
                is_json = True
            except json.JSONDecodeError:
                data = message
                is_json = False

            # Store raw message
            self.raw_messages.append({
                "timestamp": timestamp,
                "message": data,
                "is_json": is_json
            })

            print(f"\n{'─'*80}")
            print(f"📨 Message #{self.message_count} at {timestamp}")
            print(f"{'─'*80}")

            if is_json:
                # Pretty print JSON
                print(json.dumps(data, indent=2))

                # Categorize by message type
                msg_type = data.get("type", "").upper()

                if msg_type == "BALANCE" or "balance" in str(data).lower():
                    self.balance_updates.append(data)
                    print(f"💰 BALANCE UPDATE detected!")
                    self._print_balance_info(data)

                elif msg_type == "ORDER" or "order" in str(data).lower():
                    self.order_updates.append(data)
                    print(f"📋 ORDER UPDATE detected!")
                    self._print_order_info(data)

                elif msg_type == "POSITION" or "position" in str(data).lower():
                    self.position_updates.append(data)
                    print(f"📊 POSITION UPDATE detected!")
                    self._print_position_info(data)

                elif msg_type == "FUNDING" or "funding" in str(data).lower():
                    self.funding_payments.append(data)
                    print(f"💸 FUNDING PAYMENT detected!")
                    self._print_funding_info(data)
                else:
                    print(f"ℹ️  Message type: {msg_type or 'UNKNOWN'}")
            else:
                # Non-JSON message (possibly SSE format)
                print(f"Raw message: {message}")

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            print(f"Raw message: {message}")

    def _print_balance_info(self, data: dict):
        """Print formatted balance information."""
        print(f"\nBalance Details:")
        if "balance" in data:
            print(f"  Balance: {data.get('balance')}")
        if "equity" in data:
            print(f"  Equity: {data.get('equity')}")
        if "availableForTrade" in data:
            print(f"  Available for Trade: {data.get('availableForTrade')}")
        if "availableForWithdrawal" in data:
            print(f"  Available for Withdrawal: {data.get('availableForWithdrawal')}")

    def _print_order_info(self, data: dict):
        """Print formatted order information."""
        print(f"\nOrder Details:")
        if "orderId" in data:
            print(f"  Order ID: {data.get('orderId')}")
        if "status" in data:
            print(f"  Status: {data.get('status')}")
        if "market" in data:
            print(f"  Market: {data.get('market')}")
        if "side" in data:
            print(f"  Side: {data.get('side')}")
        if "size" in data:
            print(f"  Size: {data.get('size')}")
        if "price" in data:
            print(f"  Price: {data.get('price')}")

    def _print_position_info(self, data: dict):
        """Print formatted position information."""
        print(f"\nPosition Details:")
        if "market" in data:
            print(f"  Market: {data.get('market')}")
        if "size" in data:
            print(f"  Size: {data.get('size')}")
        if "entryPrice" in data:
            print(f"  Entry Price: {data.get('entryPrice')}")
        if "unrealisedPnl" in data:
            print(f"  Unrealized PnL: {data.get('unrealisedPnl')}")

    def _print_funding_info(self, data: dict):
        """Print formatted funding payment information."""
        print(f"\nFunding Details:")
        if "market" in data:
            print(f"  Market: {data.get('market')}")
        if "fundingRate" in data:
            print(f"  Funding Rate: {data.get('fundingRate')}")
        if "payment" in data:
            print(f"  Payment: {data.get('payment')}")

    async def listen(self, duration: int = 60):
        """
        Listen for messages from WebSocket.

        Args:
            duration: How long to listen in seconds (default: 60)
        """
        if not self.ws:
            print("❌ Not connected to WebSocket")
            return

        print(f"\n{'='*80}")
        print(f"Listening for messages (duration: {duration}s)...")
        print(f"{'='*80}\n")
        print("💡 Tip: Perform actions on Extended exchange (place orders, check balance)")
        print("   to trigger account update messages.\n")

        try:
            start_time = asyncio.get_event_loop().time()

            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= duration:
                    print(f"\n⏱️  Timeout reached ({duration}s), stopping...")
                    break

                try:
                    # Wait for message with timeout
                    remaining = duration - elapsed
                    message = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=min(remaining, 30)  # Check every 30s
                    )

                    await self.process_message(message)

                except asyncio.TimeoutError:
                    # No message received in timeout period
                    print(f"⏳ No messages in last 30s (elapsed: {elapsed:.1f}s)")
                    continue

                except websockets.exceptions.ConnectionClosed as e:
                    print(f"\n❌ Connection closed: {e.code} {e.reason}")
                    break

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted by user (Ctrl+C)")
        except Exception as e:
            print(f"\n❌ Error during listening: {type(e).__name__}: {e}")
        finally:
            await self.print_summary()

    async def print_summary(self):
        """Print summary of received messages."""
        print(f"\n\n{'='*80}")
        print(f"Test Summary")
        print(f"{'='*80}")
        print(f"Total messages received: {self.message_count}")
        print(f"  - Balance updates: {len(self.balance_updates)}")
        print(f"  - Order updates: {len(self.order_updates)}")
        print(f"  - Position updates: {len(self.position_updates)}")
        print(f"  - Funding payments: {len(self.funding_payments)}")
        print(f"  - Other messages: {self.message_count - len(self.balance_updates) - len(self.order_updates) - len(self.position_updates) - len(self.funding_payments)}")
        print(f"{'='*80}\n")

        # Offer to save raw messages
        if self.raw_messages:
            response = input("Save raw messages to file? (y/n): ").strip().lower()
            if response == 'y':
                filename = f"extended_ws_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = HUMMINGBOT_ROOT / filename
                with open(filepath, 'w') as f:
                    json.dump(self.raw_messages, f, indent=2)
                print(f"✅ Messages saved to: {filepath}")

    async def close(self):
        """Close WebSocket connection."""
        if self.ws:
            try:
                await self.ws.close()
                print(f"\n✅ WebSocket connection closed")
            except Exception as e:
                print(f"\n⚠️  Error closing connection: {e}")


async def test_alternative_url(api_key: str):
    """Test alternative WebSocket URL format with header authentication."""
    print(f"\n\n{'='*80}")
    print(f"Testing Alternative URL Format (Header Authentication)")
    print(f"{'='*80}\n")

    url = "wss://api.starknet.extended.exchange/stream.extended.exchange/v1/account"

    try:
        headers = {
            "User-Agent": "HummingbotExtendedConnector/1.0",
            "X-Api-Key": api_key,
        }

        print(f"URL: {url}")
        print(f"Headers: User-Agent, X-Api-Key")
        print("Connecting...")

        ws = await websockets.connect(
            url,
            extra_headers=headers,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=10,
        )

        print(f"✅ Connected successfully with header auth!")
        print(f"Connection state: {ws.state.name}")

        # Try to receive one message
        print("\nWaiting for first message (10s timeout)...")
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=10)
            print(f"📨 Received message: {message[:200]}...")
        except asyncio.TimeoutError:
            print("⏳ No message received in 10s (connection might be idle)")

        await ws.close()
        return True

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with HTTP status: {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {type(e).__name__}: {e}")
        return False


async def main():
    """Main test function."""
    # Load environment variables
    env_path = HUMMINGBOT_ROOT / ".env"
    if not env_path.exists():
        print(f"❌ .env file not found at: {env_path}")
        print("Please ensure .env file exists with EXTENDED_API_KEY")
        sys.exit(1)

    load_dotenv(env_path)

    api_key = os.getenv("EXTENDED_API_KEY")
    if not api_key:
        print("❌ EXTENDED_API_KEY not found in .env file")
        sys.exit(1)

    print(f"✅ Loaded API key: {api_key[:8]}...{api_key[-4:]}")

    # Test primary URL format (query parameter auth)
    tester = ExtendedWebSocketTester(api_key)

    connected = await tester.connect()

    if connected:
        # Listen for messages
        await tester.listen(duration=60)  # Listen for 60 seconds
        await tester.close()
    else:
        print("\n⚠️  Primary connection method failed")
        print("Trying alternative URL format...\n")
        await test_alternative_url(api_key)

    print("\n✅ Test completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)

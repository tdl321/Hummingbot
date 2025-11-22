#!/usr/bin/env python3
"""
Extended Exchange HTTP Streaming (SSE) Account Stream Test Script

This script tests the CURRENT implementation using HTTP Server-Sent Events
for comparison with WebSocket implementation.

Based on Extended API documentation:
- Stream URL: https://stream.extended.exchange/v1/account
- Authentication: X-Api-Key header
- Format: Server-Sent Events (SSE)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

# Add hummingbot to path
HUMMINGBOT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(HUMMINGBOT_ROOT))


class ExtendedHTTPStreamTester:
    """Test Extended exchange HTTP streaming (SSE) for account updates."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.message_count = 0
        self.balance_updates = []
        self.order_updates = []
        self.position_updates = []
        self.raw_messages = []

    async def test_stream(self, duration: int = 60):
        """
        Test HTTP streaming connection.

        Args:
            duration: How long to stream in seconds
        """
        url = "https://stream.extended.exchange/v1/account"

        print(f"\n{'='*80}")
        print(f"Extended HTTP Streaming (SSE) Test")
        print(f"{'='*80}")
        print(f"URL: {url}")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"{'='*80}\n")

        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "text/event-stream",
            "User-Agent": "HummingbotExtendedConnector/1.0",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=None, sock_read=duration)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                print("Connecting to HTTP stream...")

                async with session.get(url, headers=headers) as response:
                    print(f"✅ Connected! Status: {response.status}")
                    print(f"Content-Type: {response.headers.get('Content-Type')}")
                    print(f"{'='*80}\n")

                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ Error response: {error_text}")
                        return

                    print("Listening for messages...")
                    print("💡 Tip: Perform actions on Extended exchange to trigger updates\n")

                    start_time = asyncio.get_event_loop().time()

                    # Read stream line by line
                    async for line in response.content:
                        # Check timeout
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed >= duration:
                            print(f"\n⏱️  Timeout reached ({duration}s)")
                            break

                        line = line.decode('utf-8').strip()

                        # Skip empty lines and SSE comments
                        if not line or line.startswith(':'):
                            continue

                        # Parse SSE data format: "data: {json}"
                        if line.startswith('data: '):
                            json_str = line[6:]  # Remove 'data: ' prefix
                            await self.process_message(json_str, elapsed)

        except aiohttp.ClientError as e:
            print(f"❌ HTTP error: {type(e).__name__}: {e}")
        except asyncio.TimeoutError:
            print(f"❌ Connection timeout")
        except KeyboardInterrupt:
            print(f"\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
        finally:
            await self.print_summary()

    async def process_message(self, json_str: str, elapsed: float):
        """Process incoming SSE message."""
        try:
            self.message_count += 1
            timestamp = datetime.now().isoformat()

            data = json.loads(json_str)

            # Store raw message
            self.raw_messages.append({
                "timestamp": timestamp,
                "elapsed": elapsed,
                "message": data,
            })

            print(f"\n{'─'*80}")
            print(f"📨 Message #{self.message_count} at {timestamp} (t+{elapsed:.1f}s)")
            print(f"{'─'*80}")
            print(json.dumps(data, indent=2))

            # Categorize by message type
            msg_type = data.get("type", "").upper()

            if msg_type == "BALANCE" or "balance" in str(data).lower():
                self.balance_updates.append(data)
                print(f"💰 BALANCE UPDATE")
            elif msg_type == "ORDER" or "order" in str(data).lower():
                self.order_updates.append(data)
                print(f"📋 ORDER UPDATE")
            elif msg_type == "POSITION" or "position" in str(data).lower():
                self.position_updates.append(data)
                print(f"📊 POSITION UPDATE")

        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Raw data: {json_str}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")

    async def print_summary(self):
        """Print test summary."""
        print(f"\n\n{'='*80}")
        print(f"HTTP Streaming Test Summary")
        print(f"{'='*80}")
        print(f"Total messages: {self.message_count}")
        print(f"  - Balance updates: {len(self.balance_updates)}")
        print(f"  - Order updates: {len(self.order_updates)}")
        print(f"  - Position updates: {len(self.position_updates)}")
        print(f"{'='*80}\n")

        if self.raw_messages:
            response = input("Save messages to file? (y/n): ").strip().lower()
            if response == 'y':
                filename = f"extended_http_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = HUMMINGBOT_ROOT / filename
                with open(filepath, 'w') as f:
                    json.dump(self.raw_messages, f, indent=2)
                print(f"✅ Saved to: {filepath}")


async def main():
    """Main test function."""
    env_path = HUMMINGBOT_ROOT / ".env"
    if not env_path.exists():
        print(f"❌ .env file not found: {env_path}")
        sys.exit(1)

    load_dotenv(env_path)

    api_key = os.getenv("EXTENDED_API_KEY")
    if not api_key:
        print("❌ EXTENDED_API_KEY not found in .env")
        sys.exit(1)

    print(f"✅ API key loaded: {api_key[:8]}...{api_key[-4:]}")

    tester = ExtendedHTTPStreamTester(api_key)
    await tester.test_stream(duration=60)

    print("\n✅ Test completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(0)

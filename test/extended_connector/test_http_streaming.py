#!/usr/bin/env python3
"""
Test script for Extended HTTP streaming implementation.

This script tests the HTTP streaming (Server-Sent Events) functionality
by directly testing the stream connection and message reading logic.
"""
import asyncio
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_web_utils as web_utils
from hummingbot.core.web_assistant.connections.data_types import RESTMethod


async def read_sse_messages(response, max_messages=3):
    """
    Read Server-Sent Events from HTTP streaming response.

    Args:
        response: aiohttp ClientResponse object
        max_messages: Maximum number of messages to read

    Returns:
        List of parsed JSON messages
    """
    messages = []
    try:
        while len(messages) < max_messages:
            # Read one line from the stream
            line = await response.content.readline()

            if not line:
                # Connection closed
                break

            line = line.decode('utf-8').strip()

            # Skip empty lines and SSE comments
            if not line or line.startswith(':'):
                continue

            # Parse SSE data format: "data: {json}"
            if line.startswith('data: '):
                json_str = line[6:]  # Remove 'data: ' prefix
                try:
                    message = json.loads(json_str)
                    messages.append(message)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse SSE message: {line}")
                    continue
    except Exception as e:
        print(f"Error reading stream: {e}")

    return messages


async def test_orderbook_stream():
    """Test orderbook HTTP streaming."""
    print("\n=== Testing Orderbook HTTP Streaming ===\n")

    try:
        # Build stream URL
        market = "KAITO-USD"
        path_url = CONSTANTS.STREAM_ORDERBOOK_URL.format(market=market)
        url = web_utils.stream_url(path_url, CONSTANTS.DOMAIN)

        print(f"Stream URL: {url}")
        print(f"Testing connection to {market} orderbook stream...")

        # Create aiohttp session and make streaming request
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Accept": "text/event-stream"}) as response:
                print(f"✓ Connected (status={response.status})")

                if response.status == 200:
                    # Read first few messages
                    print("\nReading first 3 orderbook messages...")
                    messages = await read_sse_messages(response, max_messages=3)

                    print(f"✓ Successfully received {len(messages)} messages from orderbook stream")
                    for i, msg in enumerate(messages, 1):
                        print(f"  Message {i}: {msg}")

                    return len(messages) > 0
                else:
                    print(f"✗ Bad response status: {response.status}")
                    body = await response.text()
                    print(f"  Response: {body}")
                    return False

    except Exception as e:
        print(f"✗ Error testing orderbook stream: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_account_stream():
    """Test account HTTP streaming (requires API credentials)."""
    print("\n=== Testing Account HTTP Streaming ===\n")

    api_key = os.getenv("EXTENDED_API_KEY")

    if not api_key:
        print("⚠ Skipping account stream test - API credentials not found in environment")
        print("  Set EXTENDED_API_KEY to test account streaming")
        return True

    try:
        # Build stream URL
        path_url = CONSTANTS.STREAM_ACCOUNT_URL
        url = web_utils.stream_url(path_url, CONSTANTS.DOMAIN)

        print(f"Stream URL: {url}")
        print(f"Testing authenticated connection to account stream...")

        # Create aiohttp session and make authenticated streaming request
        import aiohttp
        headers = {
            "Accept": "text/event-stream",
            "X-Api-Key": api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"✓ Connected (status={response.status})")

                if response.status == 200:
                    # Read first few messages
                    print("\nReading first 3 account messages...")
                    messages = await read_sse_messages(response, max_messages=3)

                    print(f"✓ Successfully received {len(messages)} messages from account stream")
                    for i, msg in enumerate(messages, 1):
                        msg_type = msg.get("type", "UNKNOWN")
                        print(f"  Message {i} (type={msg_type}): {msg}")

                    return len(messages) > 0
                else:
                    print(f"✗ Bad response status: {response.status}")
                    body = await response.text()
                    print(f"  Response: {body}")
                    return False

    except Exception as e:
        print(f"✗ Error testing account stream: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Extended HTTP Streaming Test Suite")
    print("=" * 60)

    results = []

    # Test orderbook streaming
    result = await test_orderbook_stream()
    results.append(("Orderbook Stream", result))

    # Test account streaming
    result = await test_account_stream()
    results.append(("Account Stream", result))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

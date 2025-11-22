#!/usr/bin/env python3
"""
Extended Exchange REST API Balance Test

Tests the REST API balance endpoint to compare with streaming methods.
This helps determine if balance data is available via REST but not streaming.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

HUMMINGBOT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(HUMMINGBOT_ROOT))


async def test_rest_balance(api_key: str):
    """Test REST API balance endpoint."""
    url = "https://api.starknet.extended.exchange/api/v1/user/balance"

    print(f"\n{'='*80}")
    print(f"Extended REST API Balance Test")
    print(f"{'='*80}")
    print(f"URL: {url}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")

    headers = {
        "X-Api-Key": api_key,
        "User-Agent": "HummingbotExtendedConnector/1.0",
    }

    try:
        async with aiohttp.ClientSession() as session:
            print("Making GET request to balance endpoint...")

            async with session.get(url, headers=headers) as response:
                print(f"\n{'─'*80}")
                print(f"Response Status: {response.status} {response.reason}")
                print(f"{'─'*80}")

                # Print response headers
                print("\nResponse Headers:")
                for key, value in response.headers.items():
                    print(f"  {key}: {value}")

                # Read response body
                text = await response.text()

                print(f"\n{'─'*80}")
                print("Response Body:")
                print(f"{'─'*80}")

                if response.status == 200:
                    # Success - parse and display balance
                    try:
                        data = json.loads(text)
                        print(json.dumps(data, indent=2))

                        if isinstance(data, dict) and data.get('status') == 'OK':
                            balance_data = data.get('data', {})
                            print(f"\n{'='*80}")
                            print("✅ Balance Retrieved Successfully")
                            print(f"{'='*80}")
                            print(f"Balance:                 {balance_data.get('balance', 'N/A')}")
                            print(f"Equity:                  {balance_data.get('equity', 'N/A')}")
                            print(f"Available for Trade:     {balance_data.get('availableForTrade', 'N/A')}")
                            print(f"Available for Withdraw:  {balance_data.get('availableForWithdrawal', 'N/A')}")
                            print(f"{'='*80}\n")
                            return True
                        else:
                            print(f"\n⚠️  Unexpected response format")
                            return False

                    except json.JSONDecodeError:
                        print(text)
                        print(f"\n⚠️  Response is not valid JSON")
                        return False

                elif response.status == 404:
                    # 404 = Zero balance (Extended returns this for new accounts)
                    print(text)
                    print(f"\n{'='*80}")
                    print("ℹ️  404 Response (Zero Balance Account)")
                    print(f"{'='*80}")
                    print("Extended returns 404 for accounts with zero balance.")
                    print("This is expected behavior for new/unfunded accounts.")
                    print(f"{'='*80}\n")
                    return True

                elif response.status == 401:
                    # Authentication error
                    print(text)
                    print(f"\n{'='*80}")
                    print("❌ 401 Unauthorized - Authentication Failed")
                    print(f"{'='*80}")
                    print("Possible causes:")
                    print("  1. Invalid API key")
                    print("  2. API key has been revoked")
                    print("  3. Whitespace in API key (check .env)")
                    print("  4. API key lacks balance read permission")
                    print(f"{'='*80}\n")
                    return False

                else:
                    # Other error
                    print(text)
                    print(f"\n❌ Unexpected status code: {response.status}")
                    return False

    except aiohttp.ClientError as e:
        print(f"❌ HTTP error: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_account_info(api_key: str):
    """Test account info endpoint (alternative to balance)."""
    url = "https://api.starknet.extended.exchange/api/v1/user/account/info"

    print(f"\n{'='*80}")
    print(f"Extended REST API Account Info Test")
    print(f"{'='*80}")
    print(f"URL: {url}")
    print(f"{'='*80}\n")

    headers = {
        "X-Api-Key": api_key,
        "User-Agent": "HummingbotExtendedConnector/1.0",
    }

    try:
        async with aiohttp.ClientSession() as session:
            print("Making GET request to account info endpoint...")

            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status} {response.reason}\n")

                text = await response.text()

                if response.status == 200:
                    try:
                        data = json.loads(text)
                        print(json.dumps(data, indent=2))

                        if isinstance(data, dict) and data.get('status') == 'OK':
                            print(f"\n✅ Account info retrieved successfully")
                            return True

                    except json.JSONDecodeError:
                        print(text)

                elif response.status == 404:
                    print(f"404 - Account not found or not activated")
                elif response.status == 401:
                    print(f"401 - Authentication failed")
                else:
                    print(text)

                return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


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

    # Check for whitespace (common issue causing 401)
    if api_key != api_key.strip():
        print("⚠️  WARNING: API key has leading/trailing whitespace!")
        print(f"Original: '{api_key}'")
        api_key = api_key.strip()
        print(f"Stripped: '{api_key}'")
        print("")

    print(f"✅ API key loaded: {api_key[:8]}...{api_key[-4:]}")

    # Test balance endpoint
    balance_success = await test_rest_balance(api_key)

    # Test account info endpoint
    account_success = await test_account_info(api_key)

    # Summary
    print(f"\n{'='*80}")
    print("Test Summary")
    print(f"{'='*80}")
    print(f"Balance endpoint:      {'✅ Success' if balance_success else '❌ Failed'}")
    print(f"Account info endpoint: {'✅ Success' if account_success else '❌ Failed'}")
    print(f"{'='*80}\n")

    if not balance_success and not account_success:
        print("⚠️  Both endpoints failed - check API key and authentication")
        print("\nTroubleshooting steps:")
        print("1. Verify API key in Extended dashboard")
        print("2. Check for whitespace in .env file")
        print("3. Ensure API key has read permissions")
        print("4. Try regenerating API key")
    elif balance_success or account_success:
        print("✅ At least one endpoint works - REST API is functional")
        print("\nIf balance streaming still fails, the issue is with:")
        print("- WebSocket authentication method")
        print("- Streaming endpoint URL")
        print("- Streaming endpoint permissions")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(0)

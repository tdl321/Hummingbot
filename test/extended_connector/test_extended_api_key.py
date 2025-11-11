#!/usr/bin/env python3
"""
Test Extended API Key Authentication

This script tests if the API key is valid by making a simple authenticated request
to the Extended balance endpoint.
"""

import asyncio
import aiohttp


async def test_extended_api_key(api_key: str, use_testnet: bool = False):
    """
    Test Extended API key by attempting to fetch balance.

    Args:
        api_key: Extended API key to test
        use_testnet: If True, test against testnet; otherwise mainnet
    """
    # Set base URL based on environment
    if use_testnet:
        base_url = "https://api.starknet.sepolia.extended.exchange"
        env_name = "TESTNET"
    else:
        base_url = "https://api.starknet.extended.exchange"
        env_name = "MAINNET"

    endpoint = "/api/v1/user/balance"
    url = f"{base_url}{endpoint}"

    # Prepare headers
    headers = {
        "X-Api-Key": api_key,
        "User-Agent": "hummingbot-extended-test",
        "Content-Type": "application/json"
    }

    print(f"\n{'='*70}")
    print(f"Testing Extended API Key on {env_name}")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
    print(f"Headers: {headers}")
    print(f"{'='*70}\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                content_type = response.headers.get('Content-Type', '')

                print(f"Response Status: {status}")
                print(f"Content-Type: {content_type}")

                # Try to read response body
                try:
                    if 'application/json' in content_type:
                        data = await response.json()
                        print(f"Response Body (JSON):")
                        import json
                        print(json.dumps(data, indent=2))
                    else:
                        text = await response.text()
                        print(f"Response Body (Text):")
                        print(text)
                except Exception as e:
                    print(f"Could not parse response body: {e}")

                print(f"\n{'='*70}")

                # Interpret results
                if status == 200:
                    print("✅ SUCCESS: API key is VALID and authenticated!")
                    print("   Balance data retrieved successfully.")
                    return True
                elif status == 404:
                    print("✅ SUCCESS: API key is VALID!")
                    print("   404 means account has zero balance (this is expected for new accounts)")
                    return True
                elif status == 401:
                    print("❌ FAILURE: API key is INVALID or UNAUTHORIZED")
                    print("   Possible reasons:")
                    print("   1. API key is wrong/expired/revoked")
                    print("   2. API key is for wrong environment (testnet vs mainnet)")
                    print("   3. API key is for different sub-account")
                    return False
                elif status == 403:
                    print("❌ FAILURE: API key is valid but FORBIDDEN")
                    print("   The key may lack necessary permissions")
                    return False
                else:
                    print(f"⚠️  UNEXPECTED: HTTP {status}")
                    return False

    except aiohttp.ClientError as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run API key tests."""
    # API key to test
    API_KEY = "f4aa1ba3e3038adf522981a90d2a1c57"

    print("\n" + "="*70)
    print("Extended API Key Validation Test")
    print("="*70)

    # Test on mainnet first
    print("\n📍 Testing on MAINNET...")
    mainnet_valid = await test_extended_api_key(API_KEY, use_testnet=False)

    # If mainnet fails, test on testnet
    if not mainnet_valid:
        print("\n📍 Since mainnet failed, testing on TESTNET...")
        testnet_valid = await test_extended_api_key(API_KEY, use_testnet=True)

        if testnet_valid:
            print("\n" + "="*70)
            print("⚠️  CONFIGURATION ISSUE DETECTED!")
            print("="*70)
            print("Your API key is valid for TESTNET, but you're configured for MAINNET.")
            print("Update your Hummingbot configuration to use testnet domain.")
        else:
            print("\n" + "="*70)
            print("❌ API KEY INVALID ON BOTH ENVIRONMENTS")
            print("="*70)
            print("You need to regenerate your API key from Extended UI:")
            print("  Mainnet: https://app.extended.exchange/perp")
            print("  Testnet: https://starknet.sepolia.extended.exchange/perp")
    else:
        print("\n" + "="*70)
        print("✅ API KEY IS VALID FOR MAINNET")
        print("="*70)
        print("The 401 error should not occur with this API key.")
        print("If you're still seeing 401 errors, check:")
        print("  1. Hummingbot configuration is using the correct API key")
        print("  2. Hummingbot is configured for mainnet domain")
        print("  3. No typos in the configuration file")


if __name__ == "__main__":
    asyncio.run(main())

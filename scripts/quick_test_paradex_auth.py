#!/usr/bin/env python3
"""
Quick Paradex Authentication Test
Tests only authentication to verify credentials are working.

Usage:
    python scripts/quick_test_paradex_auth.py

    Set environment variables first:
    export PARADEX_API_SECRET="0x..."
    export PARADEX_ACCOUNT_ADDRESS="0x..."
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hummingbot.connector.derivative.paradex_perpetual.paradex_perpetual_auth import ParadexPerpetualAuth


async def test_auth():
    """Test Paradex authentication."""
    print("="*60)
    print("PARADEX AUTHENTICATION TEST")
    print("="*60)

    # Get credentials from environment (multiple options for convenience)
    # Priority: explicit env vars > mainnet .env > testnet .env
    api_secret = (
        os.getenv("PARADEX_API_SECRET") or
        os.getenv("PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY") or
        os.getenv("PARADEX_TESTNET_L2_SUBKEY_PRIVATE_KEY")
    )
    account_address = (
        os.getenv("PARADEX_ACCOUNT_ADDRESS") or
        os.getenv("PARADEX_MAINNET_L1_ADDRESS") or
        os.getenv("PARADEX_TESTNET_L1_ADDRESS")
    )

    # Determine which environment we're using
    if os.getenv("PARADEX_MAINNET_L1_ADDRESS") or os.getenv("PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY"):
        environment = "MAINNET (Production)"
    elif os.getenv("PARADEX_TESTNET_L1_ADDRESS") or os.getenv("PARADEX_TESTNET_L2_SUBKEY_PRIVATE_KEY"):
        environment = "TESTNET (Testing)"
    else:
        environment = "Unknown"

    if not api_secret or not account_address:
        print("\n❌ Missing credentials!")
        print("Set environment variables (option 1):")
        print("  export PARADEX_API_SECRET='0x...'")
        print("  export PARADEX_ACCOUNT_ADDRESS='0x...'")
        print("\nOr use .env file (option 2 - MAINNET):")
        print("  PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY=0x...")
        print("  PARADEX_MAINNET_L1_ADDRESS=0x...")
        print("\nOr use .env file (option 3 - TESTNET):")
        print("  PARADEX_TESTNET_L2_SUBKEY_PRIVATE_KEY=0x...")
        print("  PARADEX_TESTNET_L1_ADDRESS=0x...")
        sys.exit(1)

    print(f"\nEnvironment: {environment}")
    print(f"Account: {account_address[:10]}...{account_address[-8:]}")
    print("Testing authentication...\n")

    try:
        # Determine domain based on which credentials are set
        if os.getenv("PARADEX_MAINNET_L1_ADDRESS") or os.getenv("PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY"):
            domain = "paradex_perpetual"
            print("🔴 Using MAINNET - Real money at risk!")
        else:
            domain = "paradex_perpetual_testnet"
            print("🟢 Using TESTNET - Safe testing environment")

        print()

        # Create auth instance
        auth = ParadexPerpetualAuth(
            api_secret=api_secret,
            account_address=account_address,
            domain=domain
        )

        print("Step 1: Getting JWT token...")
        # Get auth headers (triggers JWT generation)
        headers = await auth.get_rest_auth_headers()

        if "Authorization" in headers:
            print("✅ JWT token generated successfully!")
            print(f"   Token preview: {headers['Authorization'][:70]}...")

            # Test making an authenticated request
            print("\nStep 2: Testing API call...")
            import aiohttp
            from hummingbot.connector.derivative.paradex_perpetual import paradex_perpetual_constants as CONSTANTS

            # Use correct base URL based on domain
            base_url = CONSTANTS.PERPETUAL_BASE_URL if domain == "paradex_perpetual" else CONSTANTS.TESTNET_BASE_URL

            async with aiohttp.ClientSession() as session:
                url = f"{base_url}/account"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ API call successful!")
                        print(f"   Account data received")
                        if "account_address" in data:
                            print(f"   Account: {data['account_address']}")
                    else:
                        text = await response.text()
                        print(f"❌ API call failed: {response.status}")
                        print(f"   Response: {text[:200]}")

            print("\n" + "="*60)
            print("🎉 AUTHENTICATION TEST PASSED!")
            print("="*60)
            print(f"\n✅ Your {environment} credentials are working correctly.")

            if domain == "paradex_perpetual":
                print("\n⚠️  MAINNET MODE - Using real money!")
                print("You can now run the full integration test:")
                print("  python scripts/test_paradex_integration.py --mainnet")
            else:
                print("\nYou can now run the full integration test:")
                print("  python scripts/test_paradex_integration.py")

        else:
            print("❌ No Authorization header generated")
            print("   Check your credentials")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_auth())

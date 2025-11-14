#!/usr/bin/env python3
"""
Standalone Paradex Authentication Test
Tests authentication directly using paradex-py SDK without Hummingbot imports.
"""

import asyncio
import sys

async def test_paradex_auth():
    """Test Paradex authentication with mainnet credentials."""

    # Credentials
    L1_ADDRESS = "0x83708EC79b59C8DBc4Bd1EB8d1F791341b119444"
    L2_PRIVATE_KEY = "0x132a1d83171997287b72cc89ca1158737f19e79fa34b1d19734a3ab49d8c7a1"

    print("="*60)
    print("PARADEX MAINNET AUTHENTICATION TEST")
    print("="*60)
    print(f"\n🔴 MAINNET MODE - Using real production environment!")
    print(f"\nL1 Address: {L1_ADDRESS[:10]}...{L1_ADDRESS[-8:]}")
    print(f"L2 Subkey: {L2_PRIVATE_KEY[:10]}...{L2_PRIVATE_KEY[-8:]}")
    print("\nTesting authentication...\n")

    try:
        # Import paradex-py SDK
        print("Step 1: Importing paradex-py SDK...")
        from paradex_py import Paradex
        print("✅ SDK imported successfully")

        # Initialize Paradex client
        print("\nStep 2: Initializing Paradex client...")
        client = Paradex(
            env="prod",  # MAINNET
            l2_private_key=L2_PRIVATE_KEY,
        )
        print("✅ Client created")

        # Initialize account
        print("\nStep 3: Initializing account with L1 address...")
        client.init_account(
            l1_address=L1_ADDRESS,
            l2_private_key=L2_PRIVATE_KEY,
        )
        print("✅ Account initialized")

        # Get JWT token
        print("\nStep 4: Generating JWT token...")
        auth_headers = client.account.auth_headers()

        if "Authorization" in auth_headers:
            jwt_token = auth_headers["Authorization"]
            print("✅ JWT token generated successfully!")
            print(f"   Token preview: {jwt_token[:70]}...")
        else:
            print("❌ No Authorization header found")
            return False

        # Test API call
        print("\nStep 5: Testing authenticated API call...")
        import aiohttp

        async with aiohttp.ClientSession() as session:
            url = "https://api.prod.paradex.trade/v1/account"
            async with session.get(url, headers=auth_headers) as response:
                status = response.status

                if status == 200:
                    data = await response.json()
                    print("✅ API call successful!")
                    print(f"   Status: {status}")
                    if "account_address" in data:
                        print(f"   Account verified: {data['account_address'][:10]}...{data['account_address'][-8:]}")

                    # Check balance
                    print("\nStep 6: Fetching account balance...")
                    balance_url = "https://api.prod.paradex.trade/v1/account/balance"
                    async with session.get(balance_url, headers=auth_headers) as balance_response:
                        if balance_response.status == 200:
                            balance_data = await balance_response.json()
                            print("✅ Balance fetched successfully!")
                            if "results" in balance_data:
                                for asset in balance_data["results"]:
                                    asset_name = asset.get("asset", "Unknown")
                                    available = asset.get("available_balance", "0")
                                    print(f"   {asset_name}: {available}")
                            elif balance_data:
                                print(f"   Balance data: {balance_data}")
                        else:
                            balance_text = await balance_response.text()
                            print(f"⚠️  Balance fetch returned: {balance_response.status}")
                            print(f"   Response: {balance_text[:200]}")

                    print("\n" + "="*60)
                    print("🎉 AUTHENTICATION TEST PASSED!")
                    print("="*60)
                    print("\n✅ Your MAINNET credentials are working correctly!")
                    print("✅ Connected to Paradex production environment")
                    print("\nNext steps:")
                    print("  1. Run full integration test:")
                    print("     python scripts/test_paradex_integration.py --mainnet")
                    print("  2. Connect via Hummingbot CLI:")
                    print("     ./start")
                    print("     > connect paradex_perpetual")
                    return True

                else:
                    text = await response.text()
                    print(f"❌ API call failed: {status}")
                    print(f"   Response: {text[:300]}")
                    return False

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nMake sure paradex-py is installed:")
        print("  pip install paradex-py>=0.4.6")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_paradex_auth())
    sys.exit(0 if result else 1)

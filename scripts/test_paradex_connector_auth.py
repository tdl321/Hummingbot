#!/usr/bin/env python3
"""
Test Paradex connector authentication with API key.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add hummingbot to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def test_connector_auth():
    """Test authentication using ParadexPerpetualAuth class."""

    # Load credentials from .env
    load_dotenv()

    L1_ADDRESS = os.getenv("PARADEX_MAINNET_L1_ADDRESS")
    API_KEY = os.getenv("PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY")

    if not L1_ADDRESS or not API_KEY:
        print("❌ Missing credentials in .env file")
        return False

    print("="*60)
    print("PARADEX CONNECTOR AUTH TEST")
    print("="*60)
    print(f"\n🔴 MAINNET MODE")
    print(f"L1 Address: {L1_ADDRESS[:10]}...{L1_ADDRESS[-8:]}")
    print(f"API Secret: {API_KEY[:20]}...")
    print()

    try:
        # Import auth class directly to avoid circular imports
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "paradex_perpetual_auth",
            os.path.join(os.path.dirname(__file__), "../hummingbot/connector/derivative/paradex_perpetual/paradex_perpetual_auth.py")
        )
        auth_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auth_module)
        ParadexPerpetualAuth = auth_module.ParadexPerpetualAuth

        print("Step 1: Creating ParadexPerpetualAuth instance...")
        auth = ParadexPerpetualAuth(
            api_secret=API_KEY,
            account_address=L1_ADDRESS,
            domain="paradex_perpetual"
        )
        print(f"✅ Auth instance created")
        print(f"   Auth method: {'API Key' if auth._is_api_key else 'L2 Subkey'}")

        print("\nStep 2: Getting JWT token...")
        jwt_token = await auth.get_jwt_token()
        print(f"✅ JWT token retrieved")
        print(f"   Token: {jwt_token[:50]}...")
        print(f"   Expires at: {auth._jwt_expires_at}")

        print("\nStep 3: Getting REST auth headers...")
        headers = await auth.get_rest_auth_headers()
        print(f"✅ Headers generated:")
        for key, value in headers.items():
            if key == "Authorization":
                print(f"   {key}: Bearer {value[:30]}...")
            else:
                print(f"   {key}: {value}")

        print("\nStep 4: Testing API call with auth headers...")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = "https://api.prod.paradex.trade/v1/account"
            async with session.get(url, headers=headers) as response:
                status = response.status
                print(f"   Response status: {status}")

                if status == 200:
                    data = await response.json()
                    print("✅ API call successful!")
                    print(f"   Account: {data.get('account_address', 'N/A')[:20]}...")

                    # Test balance
                    print("\nStep 5: Testing balance fetch...")
                    balance_url = "https://api.prod.paradex.trade/v1/balance"
                    async with session.get(balance_url, headers=headers) as balance_response:
                        if balance_response.status == 200:
                            balance_data = await balance_response.json()
                            print("✅ Balance fetched successfully!")
                            if "results" in balance_data and balance_data["results"]:
                                print("\n   Balances:")
                                for asset in balance_data["results"][:5]:  # Show first 5
                                    asset_name = asset.get("asset", "Unknown")
                                    available = asset.get("available_balance", "0")
                                    print(f"   • {asset_name}: {available}")
                            else:
                                print("   No balances found (empty account)")

                    print("\n" + "="*60)
                    print("🎉 CONNECTOR AUTH TEST PASSED!")
                    print("="*60)
                    print("\n✅ ParadexPerpetualAuth is working correctly!")
                    print("✅ API key authentication successful")
                    print("✅ Ready for full Hummingbot integration")
                    return True

                else:
                    text = await response.text()
                    print(f"❌ API call failed: {status}")
                    print(f"   Response: {text[:300]}")
                    return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_connector_auth())
    sys.exit(0 if result else 1)

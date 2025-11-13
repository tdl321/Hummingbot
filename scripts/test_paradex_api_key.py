#!/usr/bin/env python3
"""
Test Paradex API Key Authentication
Tests if the JWT token from .env file works directly.
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

async def test_api_key_auth():
    """Test authentication using API key from .env file."""

    # Load credentials from .env
    load_dotenv()

    L1_ADDRESS = os.getenv("PARADEX_MAINNET_L1_ADDRESS")
    API_KEY = os.getenv("PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY")

    if not L1_ADDRESS or not API_KEY:
        print("❌ Missing credentials in .env file")
        return False

    print("="*60)
    print("PARADEX API KEY AUTHENTICATION TEST")
    print("="*60)
    print(f"\n🔴 MAINNET MODE")
    print(f"L1 Address: {L1_ADDRESS[:10]}...{L1_ADDRESS[-8:]}")
    print(f"API Key: {API_KEY[:50]}...")
    print()

    # Check if this is a JWT token (starts with eyJ)
    if API_KEY.startswith("eyJ"):
        print("✅ Detected JWT token format (API key)")
    elif API_KEY.startswith("0x"):
        print("⚠️  Detected private key format (not API key)")
        print("   This test requires a JWT token/API key")
        return False
    else:
        print("⚠️  Unknown credential format")

    print("\nStep 1: Testing API key with account endpoint...")

    try:
        async with aiohttp.ClientSession() as session:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "PARADEX-STARKNET-ACCOUNT": L1_ADDRESS,
                "Content-Type": "application/json"
            }

            # Test account endpoint
            url = "https://api.prod.paradex.trade/v1/account"
            async with session.get(url, headers=headers) as response:
                status = response.status
                print(f"   Response status: {status}")

                if status == 200:
                    data = await response.json()
                    print("✅ API key authentication successful!")
                    print(f"   Account: {data.get('account_address', 'N/A')[:20]}...")

                    # Test balance endpoint
                    print("\nStep 2: Testing balance endpoint...")
                    balance_url = "https://api.prod.paradex.trade/v1/balance"
                    async with session.get(balance_url, headers=headers) as balance_response:
                        if balance_response.status == 200:
                            balance_data = await balance_response.json()
                            print("✅ Balance fetched successfully!")

                            if "results" in balance_data and balance_data["results"]:
                                print("\n   Balances:")
                                for asset in balance_data["results"]:
                                    asset_name = asset.get("asset", "Unknown")
                                    available = asset.get("available_balance", "0")
                                    print(f"   • {asset_name}: {available}")
                            else:
                                print("   No balances found (empty account)")
                        else:
                            text = await balance_response.text()
                            print(f"⚠️  Balance fetch: {balance_response.status}")
                            print(f"   {text[:200]}")

                    # Test markets endpoint
                    print("\nStep 3: Testing markets endpoint...")
                    markets_url = "https://api.prod.paradex.trade/v1/markets"
                    async with session.get(markets_url, headers=headers) as markets_response:
                        if markets_response.status == 200:
                            markets_data = await markets_response.json()
                            num_markets = len(markets_data.get("results", []))
                            print(f"✅ Markets fetched: {num_markets} available")
                        else:
                            print(f"⚠️  Markets fetch: {markets_response.status}")

                    print("\n" + "="*60)
                    print("🎉 API KEY AUTHENTICATION WORKING!")
                    print("="*60)
                    print("\n✅ Your Paradex API key is valid and working!")
                    print("✅ Connected to mainnet production environment")
                    print("\nAuthentication method: API Key (pre-generated JWT)")
                    print("Token usage: readonly" if "readonly" in API_KEY else "full access")
                    print("\n📝 NOTE: API keys are simpler than subkey authentication")
                    print("   • No need to generate JWTs on every request")
                    print("   • Token is long-lived (check expiry in decoded JWT)")
                    print("   • Can be revoked via Paradex UI if compromised")

                    return True

                elif status == 401:
                    text = await response.text()
                    print(f"❌ Authentication failed: {status}")
                    print(f"   Response: {text[:300]}")
                    print("\nPossible issues:")
                    print("   • API key expired")
                    print("   • API key revoked")
                    print("   • L1 address mismatch")
                    print("\nTo fix:")
                    print("   1. Go to https://paradex.trade")
                    print("   2. Connect wallet")
                    print("   3. Settings → API Management")
                    print("   4. Generate new API key")
                    print("   5. Update .env file")
                    return False

                elif status == 404:
                    print(f"❌ Account not found: {status}")
                    print("\nYou need to onboard first:")
                    print("   1. Go to https://paradex.trade")
                    print("   2. Connect wallet")
                    print("   3. Complete onboarding (deposit)")
                    return False

                else:
                    text = await response.text()
                    print(f"❌ Unexpected status: {status}")
                    print(f"   Response: {text[:300]}")
                    return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_api_key_auth())

    if result:
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("\n✅ API key authentication works!")
        print("\nYou can now:")
        print("1. Update connector to use API key authentication")
        print("2. Test full integration via Hummingbot CLI")
        print("3. Place test orders (start small!)")
        print()
    else:
        print("\n" + "="*60)
        print("TROUBLESHOOTING")
        print("="*60)
        print("\nIf API key doesn't work:")
        print("1. Check expiry (decode JWT at jwt.io)")
        print("2. Verify L1 address matches")
        print("3. Generate new API key on Paradex")
        print()

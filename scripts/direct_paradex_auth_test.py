#!/usr/bin/env python3
"""
Direct Paradex Authentication Test
Bypasses SDK onboarding and tests JWT generation directly.
"""

import asyncio
import aiohttp
import time
import hashlib
import json
from typing import Dict

L1_ADDRESS = "0x83708EC79b59C8DBc4Bd1EB8d1F791341b119444"
L2_PRIVATE_KEY = "0x132a1d83171997287b72cc89ca1158737f19e79fa34b1d19734a3ab49d8c7a1"

async def test_direct_auth():
    """Test authentication by directly generating JWT."""

    print("="*60)
    print("PARADEX DIRECT AUTHENTICATION TEST")
    print("="*60)
    print("\n🔴 MAINNET MODE")
    print(f"L1 Address: {L1_ADDRESS[:10]}...{L1_ADDRESS[-8:]}")
    print()

    try:
        # Step 1: Get system config (contains necessary info for auth)
        print("Step 1: Getting system configuration...")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.prod.paradex.trade/v1/system/config") as response:
                if response.status != 200:
                    print(f"❌ Failed to get system config: {response.status}")
                    return False

                config = await response.json()
                print("✅ System config retrieved")

                paraclear_address = config.get("paraclear_account_address")
                chain_id = config.get("starknet_chain_id")
                print(f"   Chain ID: {chain_id}")
                print(f"   Paraclear: {paraclear_address[:20] if paraclear_address else 'N/A'}...")

            # Step 2: Try to get JWT token via auth endpoint
            print("\nStep 2: Requesting JWT token from /auth endpoint...")

            # Prepare auth request
            timestamp = int(time.time())

            # Try the /auth endpoint
            auth_url = "https://api.prod.paradex.trade/v1/auth"

            # We need to sign a message with our L2 private key
            # Let's try using starkware signature
            try:
                from starkware.crypto.signature.signature import sign, private_to_stark_key

                l2_private_int = int(L2_PRIVATE_KEY, 16)
                l2_public_int = private_to_stark_key(l2_private_int)
                l2_public_key = f"0x{l2_public_int:064x}"

                print(f"   L2 Public Key: {l2_public_key[:20]}...{l2_public_key[-10:]}")

                # Create a message to sign (timestamp-based)
                message_hash = hashlib.sha256(f"{L1_ADDRESS}:{timestamp}".encode()).hexdigest()
                message_int = int(message_hash, 16)

                # Sign the message
                r, s = sign(message_int, l2_private_int)

                print("   ✅ Message signed")

                # Try auth request
                auth_payload = {
                    "address": L1_ADDRESS,
                    "signature": {
                        "r": hex(r),
                        "s": hex(s)
                    },
                    "timestamp": timestamp
                }

                async with session.post(auth_url, json=auth_payload) as auth_response:
                    print(f"   Auth response: {auth_response.status}")

                    if auth_response.status == 200:
                        auth_data = await auth_response.json()
                        print("✅ JWT token received!")
                        jwt_token = auth_data.get("jwt_token")

                        if jwt_token:
                            print(f"   Token: {jwt_token[:50]}...")

                            # Test the token
                            print("\nStep 3: Testing JWT token...")
                            headers = {
                                "Authorization": f"Bearer {jwt_token}",
                                "PARADEX-STARKNET-ACCOUNT": L1_ADDRESS
                            }

                            async with session.get("https://api.prod.paradex.trade/v1/account", headers=headers) as test_response:
                                if test_response.status == 200:
                                    account_data = await test_response.json()
                                    print("✅ Authentication successful!")
                                    print(f"   Account verified: {account_data.get('account_address', 'N/A')[:20]}...")
                                    return True
                                else:
                                    text = await test_response.text()
                                    print(f"❌ Token test failed: {test_response.status}")
                                    print(f"   Response: {text[:200]}")
                    else:
                        text = await auth_response.text()
                        print(f"❌ Auth failed: {auth_response.status}")
                        print(f"   Response: {text[:500]}")

                        if auth_response.status == 404:
                            print("\n⚠️  Account not found - You need to onboard first:")
                            print("   1. Go to https://paradex.trade")
                            print("   2. Connect your wallet")
                            print("   3. Make a deposit (complete onboarding)")
                            print("   4. Register your subkey")

            except ImportError:
                print("❌ starkware.crypto not available")
                print("   Cannot generate signature")
                return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return False


if __name__ == "__main__":
    result = asyncio.run(test_direct_auth())

    if not result:
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("\nIf you haven't onboarded yet:")
        print("1. Go to https://paradex.trade")
        print("2. Connect wallet: 0x83708EC79b59C8DBc4Bd1EB8d1F791341b119444")
        print("3. Complete onboarding (make a deposit)")
        print("4. Register subkey:")
        print("   Public Key: 0x057e89e31646150224cbccfc60c46c9bc297ccf8d8c0dbb485f75c67f1b97c26")
        print("\nIf you HAVE onboarded:")
        print("→ The authentication flow may need adjustment")
        print("→ Try testing through Hummingbot CLI directly")
        print()

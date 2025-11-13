#!/usr/bin/env python3
"""
Check if Paradex subkey is properly registered and configured.
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

async def check_subkey():
    """Check subkey registration status."""

    # Load credentials from .env
    load_dotenv()
    L1_ADDRESS = os.getenv("PARADEX_MAINNET_L1_ADDRESS")
    L2_PRIVATE_KEY = os.getenv("PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY")

    if not L1_ADDRESS or not L2_PRIVATE_KEY:
        print("❌ Missing credentials in .env file")
        print("   Required: PARADEX_MAINNET_L1_ADDRESS and PARADEX_MAINNET_L2_SUBKEY_PRIVATE_KEY")
        return

    print("="*60)
    print("PARADEX SUBKEY VERIFICATION")
    print("="*60)
    print(f"\nL1 Address: {L1_ADDRESS}")

    # Check if API key or L2 private key
    is_api_key = L2_PRIVATE_KEY.startswith("eyJ")

    if is_api_key:
        print(f"Credential Type: API Key (JWT token)")
        print(f"API Key: {L2_PRIVATE_KEY[:50]}...")
        print()
        print("✅ Using API key authentication")
        print("   No subkey registration needed - API key already includes permissions")
        print("   This script is for L2 subkey verification only")
        print()
        l2_public_key = None
    else:
        print(f"Credential Type: L2 Private Key")
        print(f"L2 Subkey: {L2_PRIVATE_KEY[:20]}...{L2_PRIVATE_KEY[-10:]}")
        print()

        # Calculate L2 public key from private key
        try:
            from starkware.crypto.signature.signature import private_to_stark_key

            # Remove 0x prefix and convert to int
            l2_private_int = int(L2_PRIVATE_KEY, 16)
            l2_public_int = private_to_stark_key(l2_private_int)
            l2_public_key = f"0x{l2_public_int:064x}"

            print(f"Derived L2 Public Key: {l2_public_key}")
            print()
        except ImportError:
            print("⚠️  Could not derive L2 public key (starkware not available)")
            l2_public_key = None
        except ValueError as e:
            print(f"⚠️  Could not derive L2 public key: {e}")
            l2_public_key = None

    # Check if we can access Paradex API
    print("Checking Paradex API connectivity...")
    async with aiohttp.ClientSession() as session:
        # Check system health
        try:
            async with session.get("https://api.prod.paradex.trade/v1/system/health") as response:
                if response.status == 200:
                    print("✅ Paradex API is accessible")
                else:
                    print(f"⚠️  Paradex API health check: {response.status}")
        except Exception as e:
            print(f"❌ Cannot reach Paradex API: {e}")
            return

        # Try to get system config
        try:
            async with session.get("https://api.prod.paradex.trade/v1/system/config") as response:
                if response.status == 200:
                    config = await response.json()
                    print(f"✅ System config retrieved")
                    print(f"   Starknet chain ID: {config.get('starknet_chain_id', 'N/A')}")
                    print(f"   Paradex account: {config.get('paraclear_account_address', 'N/A')[:20]}...")
        except Exception as e:
            print(f"⚠️  Could not get system config: {e}")

    print("\n" + "="*60)
    print("SUBKEY REGISTRATION CHECK")
    print("="*60)
    print("\nTo verify your subkey is registered:")
    print("1. Go to: https://paradex.trade")
    print("2. Connect with your wallet (L1 address above)")
    print("3. Navigate to: Account Settings → API Management")
    print("4. Check if you see your L2 public key listed")

    if l2_public_key:
        print(f"\nLook for this public key: {l2_public_key[:20]}...{l2_public_key[-10:]}")

    print("\nIf NOT listed:")
    print("  → Click 'Register Existing Subkey'")
    print(f"  → Paste public key: {l2_public_key if l2_public_key else 'See above'}")
    print("  → Enable 'Trading' permission")
    print("  → Confirm registration")

    print("\nIf you haven't onboarded your main account yet:")
    print("  → You need to onboard first on Paradex website")
    print("  → Make a small deposit to activate your account")
    print("  → Then register the subkey")
    print()


if __name__ == "__main__":
    asyncio.run(check_subkey())

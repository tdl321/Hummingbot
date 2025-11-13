#!/usr/bin/env python3
"""
Check Paradex account onboarding status.
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

async def check_account_status():
    """Check if account is onboarded on Paradex."""

    # Load credentials from .env
    load_dotenv()
    L1_ADDRESS = os.getenv("PARADEX_MAINNET_L1_ADDRESS")

    if not L1_ADDRESS:
        print("❌ Missing PARADEX_MAINNET_L1_ADDRESS in .env file")
        return

    print("="*60)
    print("PARADEX ACCOUNT STATUS CHECK")
    print("="*60)
    print(f"\nL1 Address: {L1_ADDRESS}")
    print()

    async with aiohttp.ClientSession() as session:
        # Try to get account info (public endpoint)
        print("Checking account onboarding status...")
        try:
            # Try to fetch account summary (this endpoint may work without auth for public info)
            url = f"https://api.prod.paradex.trade/v1/account/{L1_ADDRESS}"

            async with session.get(url) as response:
                print(f"Response status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print("✅ Account found on Paradex!")
                    print(f"   Data: {json.dumps(data, indent=2)}")
                elif response.status == 404:
                    print("❌ Account NOT found - Account not onboarded")
                    print("\n📋 You need to onboard your account first:")
                    print("   1. Go to https://paradex.trade")
                    print(f"   2. Connect with: {L1_ADDRESS}")
                    print("   3. Complete the onboarding process")
                    print("   4. Make a small deposit (even 1 USDC)")
                    print("   5. Wait for confirmation")
                    print("   6. Then register your subkey")
                elif response.status == 401:
                    print("⚠️  401 Unauthorized - Account may exist but requires auth")
                    print("   This is normal if account exists")
                else:
                    text = await response.text()
                    print(f"⚠️  Unexpected status: {response.status}")
                    print(f"   Response: {text[:300]}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Try to check system state
        print("\nChecking Paradex system...")
        try:
            async with session.get("https://api.prod.paradex.trade/v1/system/state") as response:
                if response.status == 200:
                    state = await response.json()
                    print(f"✅ System state: {state.get('l2_block_number', 'N/A')}")
        except Exception as e:
            print(f"⚠️  Could not get system state: {e}")

        # Try markets endpoint (should work without auth)
        print("\nChecking markets endpoint...")
        try:
            async with session.get("https://api.prod.paradex.trade/v1/markets") as response:
                if response.status == 200:
                    markets = await response.json()
                    num_markets = len(markets.get('results', []))
                    print(f"✅ Markets endpoint working ({num_markets} markets available)")
                else:
                    print(f"⚠️  Markets endpoint: {response.status}")
        except Exception as e:
            print(f"⚠️  Error: {e}")

    print("\n" + "="*60)
    print("DIAGNOSIS")
    print("="*60)
    print("\nMost likely issue:")
    print("❌ Your account has NOT been onboarded to Paradex yet")
    print("\nRequired steps:")
    print("1. ✅ Have Ethereum wallet with L1 address")
    print("2. ❌ Onboard to Paradex (deposit funds)")
    print("3. ❌ Register L2 subkey")
    print("\nTo onboard:")
    print("→ Visit: https://paradex.trade")
    print(f"→ Connect wallet: {L1_ADDRESS}")
    print("→ Follow onboarding prompts")
    print("→ Deposit some USDC (minimum: check Paradex docs)")
    print("→ Wait for confirmation (~15 min for L1→L2 bridge)")
    print("\nAfter onboarding, register your subkey:")
    print("→ Account Settings → API Management → Register Subkey")
    print("→ Public Key: 0x057e89e31646150224cbccfc60c46c9bc297ccf8d8c0dbb485f75c67f1b97c26")
    print()


if __name__ == "__main__":
    asyncio.run(check_account_status())

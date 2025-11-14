"""
Test Extended DEX Balance Fetch

Quick script to verify your Extended API credentials work.
Tests the balance endpoint to confirm no 401 errors.
"""

import asyncio
import aiohttp
from getpass import getpass


async def test_extended_balance(api_key: str):
    """
    Test Extended balance endpoint with API key.

    Args:
        api_key: Your Extended API key

    Returns:
        True if successful, False if 401 error
    """
    url = "https://api.starknet.extended.exchange/api/v1/user/balance"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    print(f"\n{'='*70}")
    print("🧪 Testing Extended DEX API Credentials")
    print(f"{'='*70}\n")
    print(f"🔑 API Key: {api_key[:15]}...{api_key[-10:]}")
    print(f"🌐 Endpoint: {url}")
    print(f"\n⏳ Fetching balance...\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                text = await response.text()

                print(f"{'='*70}")
                print(f"📊 Response Status: {status}")
                print(f"{'='*70}\n")

                if status == 200:
                    print("✅ SUCCESS! Your credentials are working!\n")
                    print(f"Response: {text}\n")
                    print("="*70)
                    print("🎉 No 401 errors! You're good to go!")
                    print("="*70)
                    return True

                elif status == 401:
                    print("❌ FAILED: 401 Unauthorized Error\n")
                    print(f"Response: {text}\n")
                    print("="*70)
                    print("⚠️  Your API key is invalid or not working.")
                    print("="*70)
                    print("\n💡 Solutions:")
                    print("   1. Generate a new API key using:")
                    print("      python scripts/run_extended_subaccount.py")
                    print("   2. Verify you copied the key correctly")
                    print("   3. Check you're using the right network (mainnet/testnet)")
                    return False

                elif status == 404:
                    print("⚠️  404 Not Found (likely zero balance)\n")
                    print(f"Response: {text}\n")
                    print("="*70)
                    print("✅ Good news: Your API key IS valid!")
                    print("   404 means your account has zero balance, not an auth error.")
                    print("="*70)
                    print("\n💡 Your $8 should show up after it's settled on-chain.")
                    return True

                else:
                    print(f"⚠️  Unexpected status: {status}\n")
                    print(f"Response: {text}\n")
                    print("="*70)
                    return False

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        print("="*70)
        print("⚠️  Connection error. Check your internet connection.")
        print("="*70)
        return False


async def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("🧪 Extended DEX Credentials Tester")
    print("="*70)
    print("\nThis script tests if your Extended API credentials work.")
    print("It will fetch your balance to verify there are no 401 errors.\n")

    # Get API key
    api_key = input("🔑 Enter your Extended API key: ").strip()

    if not api_key:
        print("\n❌ No API key provided. Exiting.")
        return

    # Test credentials
    success = await test_extended_balance(api_key)

    if success:
        print("\n✅ Your Extended credentials are working correctly!")
        print("   You can now use them in Hummingbot without 401 errors.\n")
    else:
        print("\n❌ Your credentials are NOT working.")
        print("   Run: python scripts/run_extended_subaccount.py")
        print("   to generate new credentials.\n")


if __name__ == "__main__":
    asyncio.run(main())

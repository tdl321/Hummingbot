"""
Test Extended UI API Keys Directly

This script tests the EXACT keys from Extended UI to see if they work,
bypassing Hummingbot's encryption/decryption.

SCENARIO:
- You copied keys from Extended UI ✅
- Put them in Hummingbot ✅
- Still getting 401 errors ❌

POSSIBLE CAUSES:
1. Keys are corrupted during Hummingbot encryption/decryption
2. Keys have wrong format (0x prefix issues)
3. Config file not being read correctly
4. Testnet vs Mainnet mismatch
5. API key not fully activated
"""

import asyncio
import aiohttp
from getpass import getpass


async def test_extended_api_key_raw(api_key: str):
    """
    Test Extended API key with direct HTTP request.

    This bypasses Hummingbot entirely to see if keys work.

    Args:
        api_key: Your Extended API key (from UI)
    """
    print("\n" + "="*70)
    print("🧪 Testing Extended API Key (Direct HTTP)")
    print("="*70)

    # Test both mainnet and testnet
    endpoints = [
        ("MAINNET", "https://api.starknet.extended.exchange/api/v1/user/balance"),
        ("TESTNET", "https://api.starknet.sepolia.extended.exchange/api/v1/user/balance"),
    ]

    for network, url in endpoints:
        print(f"\n{'─'*70}")
        print(f"Testing {network}")
        print(f"{'─'*70}")
        print(f"URL: {url}")
        print(f"API Key: {api_key[:15]}...{api_key[-10:]}")

        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Extended-Test-Script/1.0"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    text = await response.text()

                    print(f"\nResponse Status: {status}")
                    print(f"Response Body: {text[:200]}...")

                    if status == 200:
                        print(f"\n✅ ✅ ✅ SUCCESS on {network}! ✅ ✅ ✅")
                        print(f"\n🎯 YOUR API KEY WORKS!")
                        print(f"\nThis means:")
                        print(f"  ✅ API key is valid")
                        print(f"  ✅ Network is {network}")
                        print(f"  ✅ Keys are not the problem")
                        print(f"\n⚠️  BUT you're getting 401 in Hummingbot?")
                        print(f"\n🔍 Possible causes:")
                        print(f"  1. Hummingbot encryption/decryption corrupting keys")
                        print(f"  2. Hummingbot using wrong network config")
                        print(f"  3. Keys not being read from config file correctly")
                        print(f"  4. Hummingbot connector has hardcoded wrong endpoints")
                        return True, network

                    elif status == 401:
                        print(f"\n❌ 401 Unauthorized on {network}")
                        print(f"  → API key not valid for this network")

                    elif status == 404:
                        print(f"\n⚠️  404 Not Found on {network}")
                        print(f"  → Might be zero balance (not an auth error)")
                        print(f"  → API key might actually be valid!")
                        return True, network

                    else:
                        print(f"\n⚠️  Unexpected status: {status}")

        except Exception as e:
            print(f"\n❌ Error: {e}")

    print(f"\n{'='*70}")
    print(f"❌ API key doesn't work on MAINNET or TESTNET")
    print(f"{'='*70}")
    print(f"\n🔍 Possible reasons:")
    print(f"  1. API key was revoked/deleted")
    print(f"  2. API key not fully activated yet")
    print(f"  3. Copy/paste error (extra spaces, wrong key)")
    print(f"  4. Account has issues")

    return False, None


async def test_with_format_variations(api_key: str):
    """
    Test different format variations of the API key.
    """
    print("\n" + "="*70)
    print("🔧 Testing Format Variations")
    print("="*70)

    variations = [
        ("Original", api_key),
        ("Trimmed", api_key.strip()),
        ("No spaces", api_key.replace(" ", "")),
    ]

    url = "https://api.starknet.extended.exchange/api/v1/user/balance"

    for name, key_variant in variations:
        print(f"\n Testing: {name}")
        print(f"   Key: {key_variant[:15]}...{key_variant[-10:]}")

        headers = {"X-Api-Key": key_variant, "Accept": "application/json"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    if status == 200:
                        print(f"   ✅ SUCCESS with {name}!")
                        return key_variant
                    elif status == 404:
                        print(f"   ⚠️  404 (might be valid, just zero balance)")
                        return key_variant
                    else:
                        print(f"   ❌ {status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    return None


async def check_hummingbot_config():
    """
    Check what's actually in the Hummingbot config file.
    """
    print("\n" + "="*70)
    print("📋 Checking Hummingbot Config File")
    print("="*70)

    config_path = "/Users/tdl321/hummingbot/conf/connectors/extended_perpetual.yml"

    try:
        with open(config_path, 'r') as f:
            content = f.read()

        print(f"\nConfig file contents:")
        print(f"{'─'*70}")
        print(content)
        print(f"{'─'*70}")

        # Check for common issues
        if "extended_perpetual_api_key:" in content:
            print(f"\n✅ API key field exists")
        else:
            print(f"\n❌ API key field missing!")

        if "extended_perpetual_api_secret:" in content:
            print(f"✅ API secret field exists")
        else:
            print(f"❌ API secret field missing!")

        # Check if values look encrypted
        if '"crypto":' in content or '"cipher":' in content:
            print(f"\n🔐 Keys appear to be ENCRYPTED")
            print(f"   This is normal for Hummingbot")
            print(f"   BUT encryption/decryption might be corrupting them!")
        else:
            print(f"\n⚠️  Keys might be in plaintext")

    except FileNotFoundError:
        print(f"\n❌ Config file not found: {config_path}")
    except Exception as e:
        print(f"\n❌ Error reading config: {e}")


async def main():
    """Main diagnostic routine."""
    print("\n" + "="*70)
    print("🔍 Extended UI Keys Direct Test")
    print("="*70)
    print("\nPURPOSE: Test if your Extended UI API keys actually work")
    print("         (bypassing Hummingbot to isolate the problem)")
    print("\nSCENARIO:")
    print("  ✅ You copied keys from Extended UI")
    print("  ✅ Put them in Hummingbot")
    print("  ❌ Still getting 401 errors")
    print("\nLet's test if the keys themselves work...")

    # Get API key
    print("\n" + "="*70)
    api_key = input("\n🔑 Paste your Extended API Key (from UI): ").strip()

    if not api_key:
        print("❌ No API key provided. Exiting.")
        return

    # Test the key directly
    works, network = await test_extended_api_key_raw(api_key)

    if works:
        print(f"\n" + "="*70)
        print(f"🎯 DIAGNOSIS: Keys ARE Valid!")
        print(f"="*70)
        print(f"\n✅ Your API key works on {network}")
        print(f"✅ The problem is NOT the keys themselves")
        print(f"\n❌ The problem is HOW Hummingbot uses them")
        print(f"\nPossible issues:")
        print(f"  1. Hummingbot encrypts keys → Decryption corrupts them")
        print(f"  2. Hummingbot connector uses wrong network endpoints")
        print(f"  3. Hummingbot not reading config correctly")
        print(f"  4. Extended connector code has bugs")

        print(f"\n🔧 SOLUTIONS:")
        print(f"\n  Option A: Check Hummingbot connector code")
        print(f"    → Check what endpoints it's using")
        print(f"    → Check if it's testnet vs mainnet")
        print(f"    → Check if API key is being sent correctly")

        print(f"\n  Option B: Test decryption")
        print(f"    → Run: python test/extended_connector/test_decrypt_with_hummingbot.py")
        print(f"    → See if decrypted key matches what you entered")

        print(f"\n  Option C: Bypass encryption (temporary test)")
        print(f"    → Temporarily put plaintext keys in config")
        print(f"    → See if that works")
        print(f"    → (Not for production!)")

    else:
        print(f"\n" + "="*70)
        print(f"🎯 DIAGNOSIS: Keys DON'T Work")
        print(f"="*70)
        print(f"\n❌ Your API key doesn't work via direct HTTP")
        print(f"❌ This means the keys from UI are invalid")
        print(f"\nPossible reasons:")
        print(f"  1. Key was revoked/deleted after you copied it")
        print(f"  2. Copy/paste error (check for extra spaces)")
        print(f"  3. Wrong key (test key vs production key)")
        print(f"  4. API key not fully activated")

        print(f"\n🔧 SOLUTION:")
        print(f"  1. Go back to Extended UI")
        print(f"  2. DELETE the current API key")
        print(f"  3. Generate a FRESH API key")
        print(f"  4. Copy it IMMEDIATELY")
        print(f"  5. Test it with this script again")

    # Check Hummingbot config
    await check_hummingbot_config()

    print(f"\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())

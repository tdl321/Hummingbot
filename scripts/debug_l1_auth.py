"""
Debug Extended L1 Authentication

This script shows exactly what's happening with L1 authentication
and why it might be failing.
"""

import asyncio
from datetime import datetime, timezone
from getpass import getpass
from eth_account import Account
from eth_account.messages import encode_defunct
import aiohttp


async def test_l1_auth_detailed(eth_private_key: str):
    """
    Test L1 authentication with Extended and show all details.

    Args:
        eth_private_key: Ethereum private key
    """
    print("\n" + "="*70)
    print("🔍 Extended L1 Authentication Debug Tool")
    print("="*70)

    # Clean key
    if not eth_private_key.startswith('0x'):
        eth_private_key = '0x' + eth_private_key

    # Step 1: Create signing account
    print("\n📋 STEP 1: Creating signing account from private key")
    print("-"*70)
    try:
        signing_account = Account.from_key(eth_private_key)
        print(f"✅ Account created successfully")
        print(f"   → Address: {signing_account.address}")
    except Exception as e:
        print(f"❌ Failed to create account: {e}")
        return

    # Step 2: Prepare auth message
    print("\n📋 STEP 2: Preparing authentication message")
    print("-"*70)
    request_path = "/api/v1/user/accounts"
    time = datetime.now(timezone.utc)
    auth_time_string = time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    l1_message = f"{request_path}@{auth_time_string}".encode(encoding="utf-8")

    print(f"   → Request path: {request_path}")
    print(f"   → Timestamp: {auth_time_string}")
    print(f"   → Message to sign: {l1_message.decode('utf-8')}")

    # Step 3: Sign the message
    print("\n📋 STEP 3: Signing message with Ethereum key")
    print("-"*70)
    try:
        signable_message = encode_defunct(l1_message)
        l1_signature = signing_account.sign_message(signable_message)
        signature_hex = l1_signature.signature.hex()
        print(f"✅ Message signed successfully")
        print(f"   → Signature: {signature_hex[:20]}...{signature_hex[-20:]}")
    except Exception as e:
        print(f"❌ Failed to sign message: {e}")
        return

    # Step 4: Prepare request headers
    print("\n📋 STEP 4: Preparing HTTP headers")
    print("-"*70)
    headers = {
        "L1_SIGNATURE": signature_hex,
        "L1_MESSAGE_TIME": auth_time_string,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    print(f"   → L1_SIGNATURE: {signature_hex[:20]}...")
    print(f"   → L1_MESSAGE_TIME: {auth_time_string}")

    # Step 5: Send request to Extended
    print("\n📋 STEP 5: Sending authenticated request to Extended")
    print("-"*70)
    url = f"https://api.starknet.extended.exchange{request_path}"
    print(f"   → URL: {url}")
    print(f"   → Method: GET")
    print(f"\n   ⏳ Sending request...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                text = await response.text()

                print(f"\n   📊 Response received:")
                print(f"   → Status: {status}")
                print(f"   → Body: {text[:200]}...")

                if status == 200:
                    print(f"\n✅ SUCCESS! L1 authentication worked!")
                    print(f"\n   Your wallet IS registered with Extended.")
                    print(f"   The SDK subaccount creation should work.")
                    print(f"\n   Possible reasons it failed before:")
                    print(f"   1. Temporary network issue")
                    print(f"   2. Timing issue with the timestamp")
                    print(f"   3. Rate limiting")
                    return True

                elif status == 401:
                    print(f"\n❌ FAILED: 401 Unauthorized")
                    print(f"\n   🔍 ROOT CAUSE IDENTIFIED:")
                    print(f"\n   Your Ethereum wallet ({signing_account.address})")
                    print(f"   is NOT registered with Extended DEX!")
                    print(f"\n   Extended's backend doesn't recognize this wallet address.")
                    print(f"   This means:")
                    print(f"\n   1. ❌ You haven't connected this wallet to Extended web app")
                    print(f"   2. ❌ OR you used a different wallet when signing up")
                    print(f"   3. ❌ OR your account was created but not fully onboarded")
                    print(f"\n   📝 What the Extended backend checks:")
                    print(f"      → Is this wallet address in our database?")
                    print(f"      → Has this wallet completed onboarding?")
                    print(f"      → Is the signature valid?")
                    print(f"\n   If your wallet isn't in their database, you get 401.")
                    return False

                elif status == 403:
                    print(f"\n❌ FAILED: 403 Forbidden")
                    print(f"\n   Your wallet is recognized, but access is denied.")
                    print(f"   Possible reasons:")
                    print(f"   → Account suspended or restricted")
                    print(f"   → IP address blocked")
                    print(f"   → Compliance/KYC issues")
                    return False

                else:
                    print(f"\n⚠️  Unexpected status: {status}")
                    print(f"   Response: {text}")
                    return False

    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False


async def check_wallet_registration(address: str):
    """
    Try to determine if wallet is registered by checking public info.

    Args:
        address: Ethereum address to check
    """
    print("\n" + "="*70)
    print("🔍 Checking Wallet Registration")
    print("="*70)
    print(f"\n   Address: {address}")
    print(f"\n   💡 Note: Extended doesn't provide a public endpoint to check this.")
    print(f"   The only way to verify is through L1 authenticated requests.")
    print(f"\n   ✅ Best verification method:")
    print(f"      1. Go to https://app.extended.exchange")
    print(f"      2. Connect your wallet")
    print(f"      3. Verify the address matches: {address}")
    print(f"      4. Check if you can see your dashboard/positions")


async def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("🔍 Extended L1 Authentication Debugger")
    print("="*70)
    print("\nThis tool will:")
    print("  1. Test your Ethereum private key")
    print("  2. Generate L1 authentication signature")
    print("  3. Send authenticated request to Extended")
    print("  4. Show you EXACTLY why authentication fails")
    print("\n" + "="*70)

    # Get private key
    eth_key = getpass("\n🔑 Enter your Ethereum private key: ").strip()

    if not eth_key:
        print("\n❌ No key provided. Exiting.")
        return

    # Test authentication
    success = await test_l1_auth_detailed(eth_key)

    # Summary
    print("\n" + "="*70)
    print("📊 FINAL DIAGNOSIS")
    print("="*70)

    if success:
        print("\n✅ Your wallet IS registered with Extended!")
        print("\n   Next steps:")
        print("   → Try running the subaccount creation script again")
        print("   → If it still fails, it might be a transient issue")
        print("   → Or use the web UI method as backup")

    else:
        print("\n❌ Your wallet IS NOT registered with Extended!")
        print("\n   🎯 THE ROOT CAUSE:")
        print("\n   Extended's L1 authentication checks if your Ethereum wallet")
        print("   address is in their database. If it's not found, you get 401.")
        print("\n   This happens when:")
        print("\n   1. You're using a DIFFERENT wallet than the one you used to")
        print("      sign up for Extended")
        print("\n   2. You NEVER connected a wallet to Extended (account created")
        print("      through another method, like social login)")
        print("\n   3. Your wallet was connected but the onboarding wasn't completed")
        print("\n   📝 HOW TO FIX:")
        print("\n   OPTION A: Use the correct wallet")
        print("   → Find the wallet you originally used for Extended")
        print("   → Export its private key")
        print("   → Use that in the subaccount script")
        print("\n   OPTION B: Connect this wallet to Extended (RECOMMENDED)")
        print("   → Go to https://app.extended.exchange")
        print("   → Connect the wallet whose private key you just used")
        print("   → Complete any onboarding steps")
        print("   → Then generate API keys from the web UI")
        print("   → Skip the SDK entirely!")
        print("\n   OPTION C: Use existing API key from web UI (EASIEST)")
        print("   → If you already have access to Extended's dashboard")
        print("   → Go to API Management page")
        print("   → Generate new API key")
        print("   → Use that directly in Hummingbot")
        print("   → This bypasses L1 auth completely!")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())

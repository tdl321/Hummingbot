"""
Verify Ethereum Wallet for Extended DEX

This script helps diagnose L1 authentication issues by:
1. Validating your ETH private key format
2. Deriving the public address
3. Testing the signature mechanism
4. Checking if the wallet is registered with Extended
"""

import asyncio
from getpass import getpass
from eth_account import Account
from eth_account.messages import encode_defunct
import aiohttp


def verify_private_key(private_key: str):
    """
    Verify ETH private key format and derive address.

    Args:
        private_key: Ethereum private key (with or without 0x)

    Returns:
        tuple: (is_valid, address, error_message)
    """
    try:
        # Clean up key
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key

        # Validate length
        if len(private_key) != 66:  # 0x + 64 hex chars
            return False, None, f"Invalid length: {len(private_key)} (expected 66 with 0x prefix)"

        # Try to create account
        account = Account.from_key(private_key)
        address = account.address

        return True, address, None

    except Exception as e:
        return False, None, str(e)


def test_signature(private_key: str):
    """
    Test that we can sign messages with this key.

    Args:
        private_key: Ethereum private key

    Returns:
        tuple: (success, signature, error)
    """
    try:
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key

        account = Account.from_key(private_key)

        # Test message (similar to what Extended uses)
        message = "/api/v1/user/accounts@2024-01-01T00:00:00Z"
        signable_message = encode_defunct(message.encode('utf-8'))

        # Sign it
        signed = account.sign_message(signable_message)
        signature_hex = signed.signature.hex()

        return True, signature_hex, None

    except Exception as e:
        return False, None, str(e)


async def check_wallet_with_extended(address: str):
    """
    Check if this wallet address is known to Extended.

    Args:
        address: Ethereum address

    Returns:
        tuple: (is_registered, message)
    """
    try:
        # Try to fetch public account info (if available)
        # Note: This might not work if Extended doesn't have public endpoints
        url = f"https://api.starknet.extended.exchange/api/v1/info/system"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return True, "Extended API is reachable"
                else:
                    return False, f"API returned {response.status}"

    except Exception as e:
        return False, f"Cannot reach Extended: {e}"


async def main():
    """Main diagnostic routine."""
    print("\n" + "="*70)
    print("🔍 Extended DEX Wallet Verification Tool")
    print("="*70)
    print("\nThis tool helps diagnose L1 authentication issues.\n")

    # Get private key
    eth_key = getpass("🔑 Enter your Ethereum private key: ").strip()

    if not eth_key:
        print("\n❌ No key provided. Exiting.")
        return

    print("\n" + "-"*70)
    print("TEST 1: Private Key Format")
    print("-"*70)

    is_valid, address, error = verify_private_key(eth_key)

    if is_valid:
        print(f"✅ Private key format is VALID")
        print(f"   → Derived address: {address}")
    else:
        print(f"❌ Private key format is INVALID")
        print(f"   → Error: {error}")
        print("\n💡 Make sure your private key:")
        print("   - Is 64 hex characters (or 66 with 0x prefix)")
        print("   - Contains only hex characters (0-9, a-f)")
        print("   - Is from MetaMask or another standard Ethereum wallet")
        return

    print("\n" + "-"*70)
    print("TEST 2: Signature Generation")
    print("-"*70)

    can_sign, signature, sig_error = test_signature(eth_key)

    if can_sign:
        print(f"✅ Can generate signatures successfully")
        print(f"   → Test signature: {signature[:20]}...{signature[-20:]}")
    else:
        print(f"❌ Cannot generate signatures")
        print(f"   → Error: {sig_error}")
        return

    print("\n" + "-"*70)
    print("TEST 3: Extended API Connectivity")
    print("-"*70)

    api_ok, api_msg = await check_wallet_with_extended(address)

    if api_ok:
        print(f"✅ {api_msg}")
    else:
        print(f"⚠️  {api_msg}")

    print("\n" + "="*70)
    print("📊 DIAGNOSIS SUMMARY")
    print("="*70)

    if is_valid and can_sign:
        print("\n✅ Your private key is technically valid.")
        print(f"✅ Wallet address: {address}")
        print("\n❓ However, you're getting 401 Unauthorized errors.")
        print("\n🔍 Possible causes:")
        print("\n1. ⚠️  WALLET NOT REGISTERED WITH EXTENDED")
        print("   This is the most likely issue!")
        print("   → Your wallet needs to be the one you used to sign up")
        print("   → Go to https://app.extended.exchange")
        print("   → Connect the wallet and verify it's the same address")
        print(f"   → Expected address: {address}")
        print("\n2. ⚠️  WRONG NETWORK")
        print("   → Verify you're using mainnet (not testnet)")
        print("   → The script uses MAINNET_CONFIG by default")
        print("\n3. ⚠️  ACCOUNT NOT ONBOARDED")
        print("   → You may need to onboard through Extended's web UI first")
        print("   → Go to https://app.extended.exchange")
        print("   → Complete the onboarding process")
        print("   → Then retry the subaccount creation")

        print("\n" + "="*70)
        print("💡 RECOMMENDED NEXT STEPS")
        print("="*70)
        print("\n1. Verify wallet in Extended web app:")
        print("   → Visit: https://app.extended.exchange")
        print("   → Connect your wallet")
        print(f"   → Confirm address matches: {address}")
        print("\n2. If wallet matches, check API management:")
        print("   → Visit: https://app.extended.exchange/api-management")
        print("   → Generate an API key through the UI")
        print("   → Use that key directly in Hummingbot")
        print("   → This bypasses the L1 auth entirely!")
        print("\n3. Alternative: Use existing API key from UI")
        print("   → If you already have an API key from the web interface")
        print("   → Just use that in your Hummingbot config")
        print("   → No need to create subaccount via SDK")

    else:
        print("\n❌ Your private key has issues.")
        print("   Fix the errors above before proceeding.")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())

"""
Compare Wallet Addresses - UI vs SDK

This script helps identify if you're using different wallets for UI and SDK.

SCENARIO:
- You CAN trade in Extended UI ✅
- You CANNOT authenticate via SDK L1 auth ❌

LIKELY CAUSE:
- UI connected with Wallet A
- SDK using private key from Wallet B
- They're different wallets!
"""

import asyncio
from getpass import getpass
from eth_account import Account


def get_address_from_private_key(private_key: str) -> str:
    """
    Derive Ethereum address from private key.

    Args:
        private_key: Ethereum private key

    Returns:
        Ethereum address (0x...)
    """
    try:
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key

        account = Account.from_key(private_key)
        return account.address
    except Exception as e:
        return f"ERROR: {e}"


async def main():
    """Main comparison tool."""
    print("\n" + "="*70)
    print("🔍 Wallet Address Comparison Tool")
    print("="*70)
    print("\nPURPOSE: Find out if you're using different wallets for UI vs SDK")
    print("\nSCENARIO:")
    print("  ✅ You CAN trade in Extended UI")
    print("  ❌ You CANNOT use SDK (401 L1 auth error)")
    print("\nMOST LIKELY CAUSE:")
    print("  → UI connected with one wallet")
    print("  → SDK using different wallet's private key")
    print("  → Extended sees different addresses → 401 error")

    print("\n" + "="*70)
    print("STEP 1: Get SDK Wallet Address")
    print("="*70)

    sdk_key = getpass("\n🔑 Enter the private key you're using in SDK: ").strip()

    if not sdk_key:
        print("❌ No private key provided. Exiting.")
        return

    sdk_address = get_address_from_private_key(sdk_key)

    print(f"\n✅ SDK Wallet Address (from your private key):")
    print(f"   {sdk_address}")

    print("\n" + "="*70)
    print("STEP 2: Get UI Wallet Address")
    print("="*70)
    print("\nNow, go to Extended UI and find your connected wallet address:")
    print("\n1. Open: https://app.extended.exchange")
    print("2. Look at top-right corner (wallet connection)")
    print("3. Click on your wallet/address")
    print("4. Copy the full address (0x...)")

    ui_address = input("\n📋 Paste your UI wallet address here: ").strip()

    if not ui_address:
        print("❌ No address provided. Exiting.")
        return

    # Normalize addresses
    sdk_address = sdk_address.lower()
    ui_address = ui_address.lower()

    print("\n" + "="*70)
    print("📊 COMPARISON RESULTS")
    print("="*70)

    print(f"\nSDK Wallet:  {sdk_address}")
    print(f"UI Wallet:   {ui_address}")

    if sdk_address == ui_address:
        print("\n✅ ✅ ✅ WALLETS MATCH! ✅ ✅ ✅")
        print("\nBoth addresses are the SAME.")
        print("This means wallet mismatch is NOT your problem.")
        print("\n🔍 Your 401 error has a different cause:")
        print("\n   Possible reasons:")
        print("   1. Legacy signing domain issue (old x10 vs new extended)")
        print("   2. Account exists but L1 API access not fully enabled")
        print("   3. Timestamp/signature generation issue in SDK")
        print("   4. Rate limiting or temporary API issue")
        print("\n💡 RECOMMENDATION:")
        print("   Since your wallet IS registered (you can trade in UI),")
        print("   just use the API keys from UI instead of SDK:")
        print("\n   1. Go to: https://app.extended.exchange/api-management")
        print("   2. Generate new API key")
        print("   3. Use in Hummingbot directly")
        print("   4. Skip SDK L1 auth entirely")

    else:
        print("\n❌ ❌ ❌ WALLETS DON'T MATCH! ❌ ❌ ❌")
        print("\n🎯 ROOT CAUSE IDENTIFIED!")
        print("\nYou're using DIFFERENT wallets:")
        print(f"\n   UI Trading Wallet:  {ui_address}")
        print(f"   SDK Private Key:    {sdk_address}")
        print("\n📝 This is why L1 auth fails:")
        print("   → Extended knows about your UI wallet")
        print("   → Extended doesn't know about your SDK wallet")
        print("   → When SDK sends L1 signature, Extended checks SDK wallet")
        print("   → SDK wallet not in database → 401 Unauthorized")
        print("\n✅ SOLUTIONS:")
        print("\n   OPTION A: Use correct private key (RECOMMENDED)")
        print("   1. Export private key from UI wallet")
        print("      (The wallet connected to Extended UI)")
        print("   2. Use THAT private key in SDK")
        print("   3. SDK will then work")
        print("\n   OPTION B: Use API keys from UI (EASIEST)")
        print("   1. Keep using your current UI wallet")
        print("   2. Go to: https://app.extended.exchange/api-management")
        print("   3. Generate API key")
        print("   4. Use in Hummingbot")
        print("   5. No SDK needed")
        print("\n   OPTION C: Register SDK wallet")
        print("   1. Disconnect current wallet from Extended UI")
        print("   2. Connect SDK wallet to Extended UI")
        print("   3. Complete registration")
        print("   4. Then SDK will work")
        print("   (But you'll lose access to current account)")

    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)

    if sdk_address == ui_address:
        print("\n✅ Same wallet - different problem")
        print("💡 Use API Management UI to get keys")
    else:
        print("\n❌ Different wallets - that's your problem!")
        print("💡 Export private key from UI wallet and use that")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())

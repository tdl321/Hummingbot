"""
Run Extended Subaccount Creation

This wrapper script prompts for your ETH private key and creates a subaccount.
"""

import asyncio
import sys
from getpass import getpass
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.user_client.user_client import UserClient


async def create_subaccount_with_key(eth_private_key: str, account_index: int = 1):
    """Create Extended subaccount with API key."""

    # Clean up private key
    if not eth_private_key.startswith('0x'):
        eth_private_key = '0x' + eth_private_key

    print(f"\n{'='*70}")
    print("🚀 Extended DEX Subaccount Creator")
    print(f"{'='*70}\n")

    # Initialize user client
    user_client = UserClient(
        endpoint_config=MAINNET_CONFIG,
        l1_private_key=lambda: eth_private_key
    )

    try:
        # Step 1: Check existing accounts
        print("📋 Step 1/3: Checking existing accounts...")
        accounts = await user_client.get_accounts()
        print(f"   ✅ Found {len(accounts)} existing account(s)")

        for acc in accounts:
            print(f"      - Account #{acc.account.account_index} (ID: {acc.account.id}, Vault: {acc.account.vault})")

        # Determine next available index
        used_indices = [a.account.account_index for a in accounts]
        suggested_index = max(used_indices) + 1 if used_indices else 1

        if account_index in used_indices:
            print(f"\n   ⚠️  Account #{account_index} already exists!")
            account_index = suggested_index
            print(f"   → Using next available index: {account_index}")

        # Step 2: Create subaccount
        print(f"\n🏗️  Step 2/3: Creating subaccount #{account_index}...")
        try:
            onboarded = await user_client.onboard_subaccount(
                account_index=account_index,
                description=f"Hummingbot Trading Account #{account_index}"
            )
            print(f"   ✅ Subaccount #{account_index} created successfully!")
        except Exception as e:
            if "409" in str(e) or "exists" in str(e).lower():
                print(f"   ⚠️  Subaccount already exists, fetching...")
                accounts = await user_client.get_accounts()
                onboarded = [a for a in accounts if a.account.account_index == account_index][0]
                print(f"   ✅ Retrieved existing subaccount #{account_index}")
            else:
                raise

        account = onboarded.account
        l2_keys = onboarded.l2_key_pair

        # Step 3: Create API key
        print(f"\n🔑 Step 3/3: Creating API key...")
        api_key = await user_client.create_account_api_key(
            account=account,
            description=f"Hummingbot API Key - Account {account_index}"
        )
        print(f"   ✅ API key created successfully!")

        # Display results
        print(f"\n{'='*70}")
        print("✅ SUCCESS! Your Extended DEX Credentials")
        print(f"{'='*70}\n")
        print("📝 Copy these to your Hummingbot configuration:\n")
        print(f"   extended_perpetual_api_key: {api_key}")
        print(f"   extended_perpetual_api_secret: {l2_keys.private_hex}")
        print(f"\n📊 Account Details:")
        print(f"   - Account Index: {account.account_index}")
        print(f"   - Account ID: {account.id}")
        print(f"   - Vault ID: {account.vault}")
        print(f"   - L2 Public Key: {l2_keys.public_hex}")
        print(f"\n{'='*70}")
        print("⚠️  SECURITY: Keep your api_secret secure! Never share it.")
        print(f"{'='*70}\n")

        # Save to file
        filename = f"extended_credentials_account_{account_index}.txt"
        with open(filename, 'w') as f:
            f.write(f"Extended DEX Credentials - Account #{account_index}\n")
            f.write(f"Generated: {__import__('datetime').datetime.now()}\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"Hummingbot Configuration:\n")
            f.write(f"extended_perpetual_api_key: {api_key}\n")
            f.write(f"extended_perpetual_api_secret: {l2_keys.private_hex}\n\n")
            f.write(f"Account Details:\n")
            f.write(f"Account Index: {account.account_index}\n")
            f.write(f"Account ID: {account.id}\n")
            f.write(f"Vault ID: {account.vault}\n")
            f.write(f"L2 Public Key: {l2_keys.public_hex}\n")

        print(f"💾 Credentials saved to: {filename}")
        print(f"\n✅ All done! You can now update your Hummingbot config with these credentials.\n")

        await user_client.close_session()

        return {
            'api_key': api_key,
            'api_secret': l2_keys.private_hex,
            'vault_id': str(account.vault),
            'account_id': account.id,
            'public_key': l2_keys.public_hex
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await user_client.close_session()
        raise


async def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("🌟 Extended DEX Subaccount & API Key Creator")
    print("="*70)
    print("\nThis script will create a new Extended DEX subaccount with API key.")
    print("You'll need your Ethereum L1 private key (the wallet that owns your")
    print("Extended account).\n")

    # Get private key securely
    eth_key = getpass("🔑 Enter your Ethereum private key (input hidden): ").strip()

    if not eth_key:
        print("\n❌ No private key provided. Exiting.")
        return 1

    # Get account index
    index_input = input("\n📊 Enter account index for new subaccount (press Enter for auto): ").strip()
    account_index = int(index_input) if index_input else 1

    print(f"\n🚀 Creating subaccount #{account_index}...\n")

    try:
        result = await create_subaccount_with_key(eth_key, account_index)
        return 0
    except Exception as e:
        print(f"\n💥 Failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

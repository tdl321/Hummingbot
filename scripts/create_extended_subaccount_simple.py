"""
Simple Extended DEX Subaccount Creator

Quick script to create a new subaccount with API key.
No prompts - just set your Ethereum private key and run.
"""

import asyncio
import os
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.user_client.user_client import UserClient


async def create_new_subaccount(eth_private_key: str, account_index: int = 1):
    """
    Create a new Extended subaccount with API key.

    Args:
        eth_private_key: Your Ethereum L1 private key (with or without 0x)
        account_index: Index for the subaccount (default: 1)

    Returns:
        Dict with all credentials
    """
    # Clean up private key
    if not eth_private_key.startswith('0x'):
        eth_private_key = '0x' + eth_private_key

    print(f"\n{'='*70}")
    print("🚀 Creating Extended DEX Subaccount")
    print(f"{'='*70}\n")

    # Initialize user client
    user_client = UserClient(
        endpoint_config=MAINNET_CONFIG,
        l1_private_key=lambda: eth_private_key
    )

    try:
        # Step 1: Check existing accounts
        print("📋 Step 1: Checking existing accounts...")
        accounts = await user_client.get_accounts()
        print(f"   Found {len(accounts)} existing account(s)")

        # Step 2: Create subaccount (or get existing)
        print(f"\n🏗️  Step 2: Creating subaccount #{account_index}...")
        try:
            onboarded = await user_client.onboard_subaccount(
                account_index=account_index,
                description=f"Hummingbot Trading Account #{account_index}"
            )
            print(f"   ✅ Subaccount #{account_index} created!")
        except Exception as e:
            if "409" in str(e) or "exists" in str(e).lower():
                print(f"   ⚠️  Subaccount #{account_index} already exists, using existing...")
                accounts = await user_client.get_accounts()
                onboarded = [a for a in accounts if a.account.account_index == account_index][0]
            else:
                raise

        account = onboarded.account
        l2_keys = onboarded.l2_key_pair

        # Step 3: Create API key
        print(f"\n🔑 Step 3: Creating API key...")
        api_key = await user_client.create_account_api_key(
            account=account,
            description=f"Hummingbot API Key (created {asyncio.get_event_loop().time()})"
        )
        print(f"   ✅ API key created!")

        # Display results
        print(f"\n{'='*70}")
        print("✅ SUCCESS! Your Extended DEX credentials:")
        print(f"{'='*70}\n")
        print("📝 Copy these to your Hummingbot config:\n")
        print(f"extended_perpetual_api_key: {api_key}")
        print(f"extended_perpetual_api_secret: {l2_keys.private_hex}")
        print(f"\n📊 Additional Info:")
        print(f"   - Vault ID: {account.vault}")
        print(f"   - Account ID: {account.id}")
        print(f"   - Account Index: {account.account_index}")
        print(f"   - L2 Public Key: {l2_keys.public_hex}")
        print(f"\n{'='*70}")

        # Save to file
        filename = f"extended_creds_account_{account_index}.txt"
        with open(filename, 'w') as f:
            f.write(f"Extended DEX Credentials - Account #{account_index}\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"extended_perpetual_api_key: {api_key}\n")
            f.write(f"extended_perpetual_api_secret: {l2_keys.private_hex}\n\n")
            f.write(f"Vault ID: {account.vault}\n")
            f.write(f"Account ID: {account.id}\n")
            f.write(f"L2 Public Key: {l2_keys.public_hex}\n")

        print(f"💾 Credentials saved to: {filename}\n")

        await user_client.close_session()

        return {
            'api_key': api_key,
            'api_secret': l2_keys.private_hex,
            'vault_id': account.vault,
            'account_id': account.id,
            'public_key': l2_keys.public_hex
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        await user_client.close_session()
        raise


if __name__ == "__main__":
    # ⚠️ SET YOUR ETHEREUM PRIVATE KEY HERE ⚠️
    # This is the L1 wallet that owns your Extended account
    ETH_PRIVATE_KEY = os.environ.get('ETH_PRIVATE_KEY', '')

    if not ETH_PRIVATE_KEY:
        print("\n❌ ERROR: ETH_PRIVATE_KEY not set!")
        print("\nTwo ways to provide your private key:\n")
        print("1. Set environment variable:")
        print("   export ETH_PRIVATE_KEY='0x1234...your key...'")
        print("   python scripts/create_extended_subaccount_simple.py\n")
        print("2. Edit this file and set ETH_PRIVATE_KEY variable directly (line 108)")
        exit(1)

    # Account index (change if you want a different subaccount number)
    ACCOUNT_INDEX = 1

    print(f"\nCreating subaccount #{ACCOUNT_INDEX}...")
    asyncio.run(create_new_subaccount(ETH_PRIVATE_KEY, ACCOUNT_INDEX))

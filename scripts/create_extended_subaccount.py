"""
Create Extended DEX Subaccount with API Key

This script uses the x10 SDK to:
1. Create a new subaccount on Extended DEX
2. Generate an API key for the subaccount
3. Export all credentials for use in Hummingbot

Requirements:
- Ethereum private key (L1 wallet that owns your Extended account)
- Must have already onboarded to Extended DEX (if not, script will onboard you)

The script will generate:
- Vault ID
- Stark Private Key (L2 key)
- Stark Public Key
- API Key
"""

import asyncio
import os
from getpass import getpass
from typing import Optional

from x10.perpetual.configuration import MAINNET_CONFIG, TESTNET_CONFIG
from x10.perpetual.user_client.user_client import UserClient


class ExtendedSubaccountCreator:
    """Create Extended DEX subaccounts with API keys."""

    def __init__(self, ethereum_private_key: str, testnet: bool = False):
        """
        Initialize the subaccount creator.

        Args:
            ethereum_private_key: Your Ethereum L1 private key (with or without 0x prefix)
            testnet: True for testnet, False for mainnet
        """
        # Clean up private key format
        self.eth_private_key = ethereum_private_key
        if not self.eth_private_key.startswith('0x'):
            self.eth_private_key = '0x' + self.eth_private_key

        # Choose config
        self.config = TESTNET_CONFIG if testnet else MAINNET_CONFIG
        self.network = "TESTNET" if testnet else "MAINNET"

        # Initialize user client
        self.user_client = UserClient(
            endpoint_config=self.config,
            l1_private_key=lambda: self.eth_private_key
        )

    async def list_existing_accounts(self):
        """List all existing subaccounts."""
        print(f"\n🔍 Fetching existing accounts on {self.network}...")
        try:
            accounts = await self.user_client.get_accounts()

            if not accounts:
                print("   ⚠️  No accounts found. You need to onboard first!")
                return []

            print(f"\n   ✅ Found {len(accounts)} account(s):")
            for onboarded in accounts:
                account = onboarded.account
                print(f"\n   Account #{account.account_index}:")
                print(f"      - Account ID: {account.id}")
                print(f"      - Vault ID: {account.vault}")
                print(f"      - L2 Public Key: {onboarded.l2_key_pair.public_hex}")
                print(f"      - Status: {account.status if hasattr(account, 'status') else 'Active'}")

            return accounts

        except Exception as e:
            print(f"   ❌ Error fetching accounts: {e}")
            return []

    async def onboard_main_account(self, referral_code: Optional[str] = None):
        """
        Onboard the main account (account index 0).

        Args:
            referral_code: Optional referral code

        Returns:
            OnBoardedAccount object
        """
        print(f"\n🚀 Onboarding main account on {self.network}...")
        try:
            onboarded = await self.user_client.onboard(referral_code=referral_code)
            account = onboarded.account

            print(f"\n   ✅ Main account created successfully!")
            print(f"      - Account ID: {account.id}")
            print(f"      - Account Index: {account.account_index}")
            print(f"      - Vault ID: {account.vault}")
            print(f"      - L2 Public Key: {onboarded.l2_key_pair.public_hex}")

            return onboarded

        except Exception as e:
            print(f"   ❌ Onboarding failed: {e}")
            raise

    async def create_subaccount(self, account_index: int, description: Optional[str] = None):
        """
        Create a new subaccount.

        Args:
            account_index: Index for the subaccount (must be unique, typically 1, 2, 3, etc.)
            description: Optional description for the subaccount

        Returns:
            OnBoardedAccount object
        """
        if description is None:
            description = f"Hummingbot Trading Account #{account_index}"

        print(f"\n🏗️  Creating subaccount #{account_index} on {self.network}...")
        print(f"   Description: {description}")

        try:
            onboarded = await self.user_client.onboard_subaccount(
                account_index=account_index,
                description=description
            )
            account = onboarded.account

            print(f"\n   ✅ Subaccount created successfully!")
            print(f"      - Account ID: {account.id}")
            print(f"      - Account Index: {account.account_index}")
            print(f"      - Vault ID: {account.vault}")
            print(f"      - L2 Public Key: {onboarded.l2_key_pair.public_hex}")
            print(f"      - L2 Private Key: {onboarded.l2_key_pair.private_hex}")

            return onboarded

        except Exception as e:
            if "409" in str(e) or "already exists" in str(e).lower():
                print(f"   ⚠️  Subaccount #{account_index} already exists. Fetching existing account...")
                accounts = await self.user_client.get_accounts()
                for onboarded in accounts:
                    if onboarded.account.account_index == account_index:
                        print(f"   ✅ Found existing subaccount #{account_index}")
                        return onboarded
                raise ValueError(f"Subaccount {account_index} exists but couldn't be retrieved")
            else:
                print(f"   ❌ Failed to create subaccount: {e}")
                raise

    async def create_api_key(self, onboarded_account, description: Optional[str] = None):
        """
        Create an API key for an account.

        Args:
            onboarded_account: OnBoardedAccount object
            description: Optional description for the API key

        Returns:
            API key string
        """
        account = onboarded_account.account

        if description is None:
            description = f"Hummingbot API Key for Account #{account.account_index}"

        print(f"\n🔑 Creating API key for account #{account.account_index}...")
        print(f"   Description: {description}")

        try:
            api_key = await self.user_client.create_account_api_key(
                account=account,
                description=description
            )

            print(f"\n   ✅ API key created successfully!")
            print(f"      - API Key: {api_key}")

            return api_key

        except Exception as e:
            print(f"   ❌ Failed to create API key: {e}")
            raise

    def export_credentials(self, onboarded_account, api_key: str):
        """
        Export credentials in a format ready for Hummingbot config.

        Args:
            onboarded_account: OnBoardedAccount object
            api_key: API key string
        """
        account = onboarded_account.account
        l2_keys = onboarded_account.l2_key_pair

        print("\n" + "=" * 70)
        print("📋 EXTENDED DEX CREDENTIALS FOR HUMMINGBOT")
        print("=" * 70)
        print(f"\nNetwork: {self.network}")
        print(f"Account Index: {account.account_index}")
        print(f"\n🔐 Copy these values to your Hummingbot configuration:\n")
        print(f"extended_perpetual_api_key: {api_key}")
        print(f"extended_perpetual_api_secret: {l2_keys.private_hex}")
        print(f"\n📝 Additional Information (for reference):")
        print(f"   - Account ID: {account.id}")
        print(f"   - Vault ID: {account.vault}")
        print(f"   - L2 Public Key: {l2_keys.public_hex}")
        print("\n" + "=" * 70)
        print("\n⚠️  IMPORTANT: Keep your API secret (L2 private key) secure!")
        print("   Never share it or commit it to version control.")
        print("=" * 70)

        # Optionally save to file
        save = input("\n💾 Save credentials to file? (yes/no): ").strip().lower()
        if save in ['yes', 'y']:
            filename = f"extended_credentials_account_{account.account_index}_{self.network.lower()}.txt"
            with open(filename, 'w') as f:
                f.write(f"Extended DEX Credentials\n")
                f.write(f"Network: {self.network}\n")
                f.write(f"Account Index: {account.account_index}\n")
                f.write(f"Account ID: {account.id}\n")
                f.write(f"Vault ID: {account.vault}\n\n")
                f.write(f"Hummingbot Configuration:\n")
                f.write(f"extended_perpetual_api_key: {api_key}\n")
                f.write(f"extended_perpetual_api_secret: {l2_keys.private_hex}\n\n")
                f.write(f"L2 Public Key: {l2_keys.public_hex}\n")
            print(f"   ✅ Credentials saved to: {filename}")

    async def run_interactive(self):
        """Run the interactive subaccount creation wizard."""
        print("\n" + "=" * 70)
        print("🚀 EXTENDED DEX SUBACCOUNT CREATOR")
        print("=" * 70)
        print(f"\nNetwork: {self.network}")
        print("\nThis script will:")
        print("  1. Check your existing accounts")
        print("  2. Create a new subaccount (or use existing)")
        print("  3. Generate an API key for the subaccount")
        print("  4. Export credentials for Hummingbot")

        # List existing accounts
        existing_accounts = await self.list_existing_accounts()

        # Check if main account exists
        if not existing_accounts:
            onboard = input("\n❓ No accounts found. Onboard main account? (yes/no): ").strip().lower()
            if onboard not in ['yes', 'y']:
                print("❌ Cannot continue without onboarding. Exiting.")
                return

            referral = input("   Enter referral code (or press Enter to skip): ").strip()
            referral = referral if referral else None

            main_account = await self.onboard_main_account(referral_code=referral)
            existing_accounts = [main_account]

        # Determine next account index
        used_indices = [acc.account.account_index for acc in existing_accounts]
        next_index = max(used_indices) + 1 if used_indices else 1

        print(f"\n❓ Used account indices: {used_indices}")
        index_input = input(f"   Enter account index for new subaccount (suggested: {next_index}): ").strip()

        if index_input:
            account_index = int(index_input)
        else:
            account_index = next_index

        # Check if account already exists
        existing = [acc for acc in existing_accounts if acc.account.account_index == account_index]
        if existing:
            use_existing = input(f"\n⚠️  Account #{account_index} already exists. Use it? (yes/no): ").strip().lower()
            if use_existing in ['yes', 'y']:
                onboarded_account = existing[0]
                print(f"   ✅ Using existing account #{account_index}")
            else:
                print("❌ Cancelled. Choose a different account index.")
                return
        else:
            # Create new subaccount
            description = input(f"   Enter description (or press Enter for default): ").strip()
            onboarded_account = await self.create_subaccount(
                account_index=account_index,
                description=description if description else None
            )

        # Create API key
        api_key_desc = input(f"\n   Enter API key description (or press Enter for default): ").strip()
        api_key = await self.create_api_key(
            onboarded_account=onboarded_account,
            description=api_key_desc if api_key_desc else None
        )

        # Export credentials
        self.export_credentials(onboarded_account, api_key)

        # Close session
        await self.user_client.close_session()

        print("\n✅ All done! You can now use these credentials in Hummingbot.")


async def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("🌟 EXTENDED DEX SUBACCOUNT & API KEY CREATOR")
    print("=" * 70)

    # Get Ethereum private key
    print("\n🔑 Enter your Ethereum L1 private key:")
    print("   (This is the wallet that owns your Extended account)")
    print("   (It will NOT be stored or transmitted anywhere)")
    eth_key = getpass("   Private Key (input hidden): ").strip()

    if not eth_key:
        print("\n❌ No private key provided. Exiting.")
        return

    # Choose network
    network_choice = input("\n🌐 Choose network (mainnet/testnet) [mainnet]: ").strip().lower()
    testnet = network_choice == 'testnet'

    # Create subaccount creator
    creator = ExtendedSubaccountCreator(
        ethereum_private_key=eth_key,
        testnet=testnet
    )

    # Run interactive wizard
    await creator.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())

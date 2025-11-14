"""
Delete Extended DEX API Key

This script attempts to delete your Extended API key using HTTP DELETE request.
Since the SDK doesn't provide a delete method, we'll try the API endpoint directly.

WARNING: API key deletion may only be available through the Extended web UI.
This script tries the most common REST API patterns for key deletion.
"""

import asyncio
import aiohttp
from typing import Optional


class ExtendedAPIKeyDeleter:
    """Delete Extended API keys using HTTP requests."""

    BASE_URL = "https://api.extended.exchange"
    ONBOARDING_URL = "https://onboarding.extended.exchange"

    def __init__(self, api_key: str):
        """
        Initialize with the API key you want to delete.

        Args:
            api_key: The Extended API key to delete
        """
        self.api_key = api_key

    async def delete_api_key_method_1(self) -> tuple[bool, str]:
        """
        Try Method 1: DELETE /api/v1/user/account/api-key

        This is the most common REST pattern for deleting API keys.
        """
        url = f"{self.BASE_URL}/api/v1/user/account/api-key"
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    text = await response.text()

                    if response.status == 200:
                        return True, f"✅ API key deleted successfully! Response: {text}"
                    elif response.status == 204:
                        return True, "✅ API key deleted successfully (no content returned)"
                    elif response.status == 401:
                        return False, "❌ 401 Unauthorized - API key is invalid or already deleted"
                    elif response.status == 404:
                        return False, "❌ 404 Not Found - Endpoint doesn't exist or key already deleted"
                    else:
                        return False, f"❌ Failed with status {response.status}: {text}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    async def delete_api_key_method_2(self) -> tuple[bool, str]:
        """
        Try Method 2: DELETE /api/v1/user/account/api-key/{key}

        Some APIs require the key to be in the URL path.
        """
        url = f"{self.BASE_URL}/api/v1/user/account/api-key/{self.api_key}"
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    text = await response.text()

                    if response.status in [200, 204]:
                        return True, f"✅ API key deleted successfully! Response: {text}"
                    elif response.status == 401:
                        return False, "❌ 401 Unauthorized - API key is invalid"
                    elif response.status == 404:
                        return False, "❌ 404 Not Found - Endpoint doesn't exist"
                    else:
                        return False, f"❌ Failed with status {response.status}: {text}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    async def delete_api_key_method_3(self) -> tuple[bool, str]:
        """
        Try Method 3: POST /api/v1/user/account/api-key/revoke

        Some APIs use POST with /revoke instead of DELETE.
        """
        url = f"{self.BASE_URL}/api/v1/user/account/api-key/revoke"
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers) as response:
                    text = await response.text()

                    if response.status == 200:
                        return True, f"✅ API key revoked successfully! Response: {text}"
                    elif response.status == 401:
                        return False, "❌ 401 Unauthorized - API key is invalid"
                    elif response.status == 404:
                        return False, "❌ 404 Not Found - Endpoint doesn't exist"
                    else:
                        return False, f"❌ Failed with status {response.status}: {text}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    async def delete_all_methods(self):
        """Try all deletion methods."""
        print("=" * 70)
        print("EXTENDED DEX API KEY DELETION TOOL")
        print("=" * 70)
        print(f"\nAPI Key: {self.api_key[:10]}...{self.api_key[-10:]}")
        print("\nAttempting to delete API key using multiple methods...\n")

        methods = [
            ("Method 1: DELETE /api/v1/user/account/api-key", self.delete_api_key_method_1),
            ("Method 2: DELETE /api/v1/user/account/api-key/{key}", self.delete_api_key_method_2),
            ("Method 3: POST /api/v1/user/account/api-key/revoke", self.delete_api_key_method_3),
        ]

        for method_name, method_func in methods:
            print(f"\n🔄 Trying {method_name}...")
            success, message = await method_func()
            print(f"   {message}")

            if success:
                print(f"\n✅ SUCCESS! API key has been deleted.")
                return True

        print("\n" + "=" * 70)
        print("❌ ALL METHODS FAILED")
        print("=" * 70)
        print("\n⚠️  Extended DEX likely doesn't support API key deletion via REST API.")
        print("📝 You need to delete it manually through the web interface:")
        print("\n   1. Go to: https://app.extended.exchange/api-management")
        print("   2. Log in to your account")
        print("   3. Find your API key in the list")
        print("   4. Click the delete/revoke button next to it")
        print("\n" + "=" * 70)

        return False


async def main():
    """Main function to delete Extended API key."""
    print("\n" + "=" * 70)
    print("EXTENDED DEX API KEY DELETION")
    print("=" * 70)

    # Get API key from user
    api_key = input("\n🔑 Enter the Extended API key you want to delete: ").strip()

    if not api_key:
        print("❌ No API key provided. Exiting.")
        return

    # Confirm deletion
    confirm = input(f"\n⚠️  Are you sure you want to delete API key {api_key[:10]}...? (yes/no): ").strip().lower()

    if confirm not in ['yes', 'y']:
        print("❌ Deletion cancelled.")
        return

    # Create deleter and attempt deletion
    deleter = ExtendedAPIKeyDeleter(api_key)
    success = await deleter.delete_all_methods()

    if not success:
        print("\n💡 TIP: If you're getting 401 errors, your API key might already be invalid.")
        print("   You can try creating a new API key from the web interface instead.")


if __name__ == "__main__":
    asyncio.run(main())

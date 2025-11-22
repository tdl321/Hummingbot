#!/usr/bin/env python3
"""
Check for whitespace in decrypted Extended connector credentials.
"""

import sys
sys.path.insert(0, '/Users/tdl321/hummingbot')

import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger


def main():
    """Check for whitespace in decrypted credentials."""
    print("="*80)
    print("CHECKING FOR WHITESPACE IN EXTENDED CREDENTIALS")
    print("="*80)

    # Get password from environment
    password = os.getenv('HUMMINGBOT_PASSWORD')
    if not password:
        print("\n❌ Please set HUMMINGBOT_PASSWORD environment variable")
        print("   Example: HUMMINGBOT_PASSWORD='your_password' python test/extended_connector/check_key_whitespace.py")
        return False

    # Path to encrypted config
    config_path = Path("/Users/tdl321/hummingbot/conf/connectors/extended_perpetual.yml")

    if not config_path.exists():
        print(f"\n❌ Config file not found: {config_path}")
        return False

    # Read config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Get encrypted values
    api_key_encrypted = config.get('extended_perpetual_api_key')
    api_secret_encrypted = config.get('extended_perpetual_api_secret')

    if not api_key_encrypted or not api_secret_encrypted:
        print("\n❌ Missing credentials in config!")
        return False

    # Create secrets manager
    secrets_manager = ETHKeyFileSecretManger(password)

    # Decrypt and check API key
    print("\n1. Checking API Key...")
    try:
        decrypted_api_key = secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_key",
            api_key_encrypted
        )

        print(f"   Decrypted API Key length: {len(decrypted_api_key)}")
        print(f"   First 20 chars: '{decrypted_api_key[:20]}'")
        print(f"   Last 20 chars: '{decrypted_api_key[-20:]}'")

        # Check for whitespace
        if decrypted_api_key != decrypted_api_key.strip():
            print(f"\n   ⚠️  WHITESPACE DETECTED IN API KEY!")
            print(f"   Original length: {len(decrypted_api_key)}")
            print(f"   Stripped length: {len(decrypted_api_key.strip())}")
            print(f"   Leading whitespace: {len(decrypted_api_key) - len(decrypted_api_key.lstrip())} chars")
            print(f"   Trailing whitespace: {len(decrypted_api_key) - len(decrypted_api_key.rstrip())} chars")
            print(f"\n   Raw representation: {repr(decrypted_api_key)}")
            print(f"\n   🔍 THIS IS LIKELY THE ROOT CAUSE OF YOUR 401 ERROR!")
        else:
            print(f"   ✅ No whitespace detected in API key")

    except Exception as e:
        print(f"   ❌ Failed to decrypt API key: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Decrypt and check API secret
    print("\n2. Checking API Secret (Stark Private Key)...")
    try:
        decrypted_api_secret = secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_secret",
            api_secret_encrypted
        )

        print(f"   Decrypted API Secret length: {len(decrypted_api_secret)}")
        print(f"   First 20 chars: '{decrypted_api_secret[:20]}'")
        print(f"   Last 20 chars: '{decrypted_api_secret[-20:]}'")

        # Check for whitespace
        if decrypted_api_secret != decrypted_api_secret.strip():
            print(f"\n   ⚠️  WHITESPACE DETECTED IN API SECRET!")
            print(f"   Original length: {len(decrypted_api_secret)}")
            print(f"   Stripped length: {len(decrypted_api_secret.strip())}")
            print(f"   Leading whitespace: {len(decrypted_api_secret) - len(decrypted_api_secret.lstrip())} chars")
            print(f"   Trailing whitespace: {len(decrypted_api_secret) - len(decrypted_api_secret.rstrip())} chars")
            print(f"\n   Raw representation: {repr(decrypted_api_secret[:50])}...")
            print(f"\n   🔍 THIS COULD CAUSE AUTHENTICATION ISSUES!")
        else:
            print(f"   ✅ No whitespace detected in API secret")

    except Exception as e:
        print(f"   ❌ Failed to decrypt API secret: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("Even though we added .strip() in the auth code, the whitespace is still")
    print("stored in the encrypted config. The fix should work, but if you continue")
    print("to see 401 errors, you may need to:")
    print("1. Delete the config: rm conf/connectors/extended_perpetual.yml")
    print("2. Reconnect in Hummingbot with 'connect extended_perpetual'")
    print("3. Ensure you paste keys without any extra whitespace")
    print("="*80)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

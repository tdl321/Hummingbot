#!/usr/bin/env python3
"""
Test how Extended connector loads credentials from encrypted config.
Check if there's whitespace added during the decryption process.
"""

import sys
sys.path.insert(0, '/Users/tdl321/hummingbot')

import os
from pathlib import Path
import yaml

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger
from hummingbot.client.config.security import Security
from pydantic import SecretStr


def main():
    """Test credential loading from encrypted config."""
    print("="*80)
    print("TESTING CONNECTOR CREDENTIAL LOADING")
    print("="*80)

    # Set password
    password = "eudaimonia"
    Security.secrets_manager = ETHKeyFileSecretManger(password)

    # Path to encrypted config
    config_path = Path("/Users/tdl321/hummingbot/conf/connectors/extended_perpetual.yml")

    if not config_path.exists():
        print(f"\n❌ Config file not found: {config_path}")
        return False

    # Read config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print(f"\n1. Config file found: {config_path}")
    print(f"   Keys in config: {list(config.keys())}")

    # Get encrypted values
    api_key_encrypted = config.get('extended_perpetual_api_key')
    api_secret_encrypted = config.get('extended_perpetual_api_secret')

    if not api_key_encrypted or not api_secret_encrypted:
        print("\n❌ Missing credentials in config!")
        return False

    print(f"\n2. Found encrypted values:")
    print(f"   API Key encrypted length: {len(api_key_encrypted)} chars")
    print(f"   API Secret encrypted length: {len(api_secret_encrypted)} chars")

    # Decrypt API key
    print(f"\n3. Decrypting API key...")
    try:
        decrypted_api_key = Security.secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_key",
            api_key_encrypted
        )
        print(f"   ✅ Decrypted API Key: '{decrypted_api_key}'")
        print(f"   Length: {len(decrypted_api_key)}")
        print(f"   Raw representation: {repr(decrypted_api_key)}")
        print(f"   Has leading whitespace: {decrypted_api_key != decrypted_api_key.lstrip()}")
        print(f"   Has trailing whitespace: {decrypted_api_key != decrypted_api_key.rstrip()}")

        if decrypted_api_key != decrypted_api_key.strip():
            print(f"\n   ⚠️  WHITESPACE DETECTED!")
            print(f"   Original: {repr(decrypted_api_key)}")
            print(f"   Stripped: {repr(decrypted_api_key.strip())}")

    except Exception as e:
        print(f"   ❌ Failed to decrypt API key: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Decrypt API secret
    print(f"\n4. Decrypting API secret...")
    try:
        decrypted_api_secret = Security.secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_secret",
            api_secret_encrypted
        )
        print(f"   ✅ Decrypted API Secret: '{decrypted_api_secret[:20]}...'")
        print(f"   Length: {len(decrypted_api_secret)}")
        print(f"   Raw representation: {repr(decrypted_api_secret[:30])}...")
        print(f"   Has leading whitespace: {decrypted_api_secret != decrypted_api_secret.lstrip()}")
        print(f"   Has trailing whitespace: {decrypted_api_secret != decrypted_api_secret.rstrip()}")

        if decrypted_api_secret != decrypted_api_secret.strip():
            print(f"\n   ⚠️  WHITESPACE DETECTED!")
            print(f"   Original length: {len(decrypted_api_secret)}")
            print(f"   Stripped length: {len(decrypted_api_secret.strip())}")

    except Exception as e:
        print(f"   ❌ Failed to decrypt API secret: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Now test how SecretStr wraps it
    print(f"\n5. Testing SecretStr wrapping...")
    secret_str_api_key = SecretStr(decrypted_api_key)
    unwrapped_api_key = secret_str_api_key.get_secret_value()

    print(f"   Original decrypted: {repr(decrypted_api_key)}")
    print(f"   After SecretStr wrap/unwrap: {repr(unwrapped_api_key)}")
    print(f"   Are they identical: {decrypted_api_key == unwrapped_api_key}")

    if decrypted_api_key != unwrapped_api_key:
        print(f"\n   ⚠️  SecretStr MODIFIED THE VALUE!")
        print(f"   This is the bug!")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)

    if decrypted_api_key != decrypted_api_key.strip():
        print("❌ API key has whitespace AFTER decryption")
        print("   Root cause: Credentials were encrypted WITH whitespace")
        print("   Solution: Re-enter credentials without whitespace OR")
        print("   Solution: Ensure .strip() is called on decrypted values")
    else:
        print("✅ API key has NO whitespace after decryption")
        print("   The connector should work correctly")

    print("="*80)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

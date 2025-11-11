#!/usr/bin/env python3
"""
Test decryption of Extended connector config using Hummingbot's encryption method.
"""

import sys
sys.path.insert(0, '/Users/tdl321/hummingbot')

import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger


def main():
    """Test decryption of Extended config."""
    print("="*80)
    print("TESTING EXTENDED CONFIG DECRYPTION WITH HUMMINGBOT'S METHOD")
    print("="*80)

    # Load .env for comparison
    load_dotenv()
    env_api_key = os.getenv('EXTENDED_API_KEY')
    env_stark_private = os.getenv('EXTENDED_STARK_PRIVATE_KEY')

    print(f"\n1. Values from .env file:")
    print(f"   EXTENDED_API_KEY: {env_api_key}")
    print(f"   EXTENDED_STARK_PRIVATE_KEY: {env_stark_private}")

    # Path to encrypted config
    config_path = Path("/Users/tdl321/hummingbot/conf/connectors/extended_perpetual.yml")

    if not config_path.exists():
        print(f"\n❌ Config file not found: {config_path}")
        return False

    # Read config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print(f"\n2. Config file found: {config_path}")
    print(f"   Keys in config: {list(config.keys())}")

    # Get encrypted values
    api_key_encrypted = config.get('extended_perpetual_api_key')
    api_secret_encrypted = config.get('extended_perpetual_api_secret')

    if not api_key_encrypted:
        print("\n❌ extended_perpetual_api_key not found in config!")
        return False

    if not api_secret_encrypted:
        print("\n❌ extended_perpetual_api_secret not found in config!")
        return False

    print(f"\n3. Found encrypted values:")
    print(f"   API Key length: {len(api_key_encrypted)} chars")
    print(f"   API Secret length: {len(api_secret_encrypted)} chars")

    # Get password from environment or prompt
    password = os.getenv('HUMMINGBOT_PASSWORD')
    if not password:
        import getpass
        try:
            password = getpass.getpass("\n4. Enter your Hummingbot password: ")
        except (EOFError, OSError):
            print("\n❌ Cannot prompt for password in non-interactive mode")
            print("   Please set HUMMINGBOT_PASSWORD environment variable")
            print("   Example: HUMMINGBOT_PASSWORD='your_password' python test/extended_connector/test_decrypt_with_hummingbot.py")
            return False
    else:
        print("\n4. Using password from HUMMINGBOT_PASSWORD environment variable")

    # Create secrets manager
    secrets_manager = ETHKeyFileSecretManger(password)

    # Decrypt API key
    print("\n5. Decrypting API key...")
    try:
        decrypted_api_key = secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_key",
            api_key_encrypted
        )
        print(f"   ✅ Decrypted API Key: {decrypted_api_key}")

        # Compare with .env
        if decrypted_api_key == env_api_key:
            print(f"   ✅ API key MATCHES .env file!")
        else:
            print(f"   ❌ API key DOES NOT MATCH .env file!")
            print(f"   \n   Expected (from .env): {env_api_key}")
            print(f"   Actual (from config):  {decrypted_api_key}")
            print(f"\n   🔍 THIS IS THE ROOT CAUSE OF YOUR 401 ERROR!")
            print(f"   The encrypted config has a different API key than your .env")

    except Exception as e:
        print(f"   ❌ Failed to decrypt API key: {e}")
        print(f"   This could mean:")
        print(f"   1. Wrong password")
        print(f"   2. Corrupted config file")
        import traceback
        traceback.print_exc()
        return False

    # Decrypt API secret (Stark private key)
    print("\n6. Decrypting API secret (Stark private key)...")
    try:
        decrypted_api_secret = secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_secret",
            api_secret_encrypted
        )
        print(f"   ✅ Decrypted API Secret: {decrypted_api_secret[:20]}...")

        # Compare with .env
        if decrypted_api_secret == env_stark_private:
            print(f"   ✅ API secret MATCHES .env file!")
        else:
            print(f"   ❌ API secret DOES NOT MATCH .env file!")
            print(f"   \n   Expected (from .env): {env_stark_private}")
            print(f"   Actual (from config):  {decrypted_api_secret}")
            print(f"\n   🔍 Stark private key mismatch detected!")

    except Exception as e:
        print(f"   ❌ Failed to decrypt API secret: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("If the decrypted values don't match .env, you need to:")
    print("1. Delete the encrypted config file:")
    print(f"   rm {config_path}")
    print("2. Run Hummingbot and use 'connect extended_perpetual' command")
    print("3. Enter your correct API key and Stark private key when prompted")
    print("="*80)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Debug Extended Connector Config Decryption

This script decrypts the Extended connector configuration file and displays
what API credentials are actually stored, helping diagnose 401 auth errors.
"""

import sys
import getpass
from pathlib import Path

# Add hummingbot to path
sys.path.insert(0, '/Users/tdl321/hummingbot')

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger, validate_password
from hummingbot.client.config.config_helpers import (
    get_connector_config_yml_path,
    read_yml_file,
    connector_name_from_file
)
from hummingbot.client.config.security import Security


def mask_secret(value: str, show_chars: int = 8) -> str:
    """Mask a secret value showing only first and last few characters."""
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    return f"{value[:show_chars]}...{value[-show_chars:]}"


def main():
    print("="*80)
    print("EXTENDED CONNECTOR CONFIG DECRYPTION DEBUGGER")
    print("="*80)

    # Known valid credentials for comparison
    KNOWN_VALID_API_KEY = "f4aa1ba3e3038adf522981a90d2a1c57"
    KNOWN_VALID_API_SECRET = "0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1"

    print(f"\nKnown valid API key: {mask_secret(KNOWN_VALID_API_KEY)}")
    print(f"Known valid API secret: {mask_secret(KNOWN_VALID_API_SECRET)}")

    # Step 1: Check if config file exists
    print("\n" + "="*80)
    print("STEP 1: Checking Config File")
    print("="*80)

    config_path = get_connector_config_yml_path("extended_perpetual")
    print(f"\nConfig path: {config_path}")

    if not config_path.exists():
        print("❌ ERROR: Config file does not exist!")
        print(f"   Expected location: {config_path}")
        print("\nTo create config:")
        print("   1. Run Hummingbot: docker exec -it <container> bin/hummingbot.py")
        print("   2. Execute: connect extended_perpetual")
        print("   3. Enter your API credentials")
        return 1

    print("✅ Config file exists")

    # Step 2: Read raw YAML
    print("\n" + "="*80)
    print("STEP 2: Reading Raw YAML")
    print("="*80)

    try:
        raw_config = read_yml_file(config_path)
        print(f"\nConfig structure:")
        print(f"  Connector: {raw_config.get('connector')}")

        # Show encrypted values (hex format)
        api_key_encrypted = raw_config.get('extended_perpetual_api_key', 'NOT FOUND')
        api_secret_encrypted = raw_config.get('extended_perpetual_api_secret', 'NOT FOUND')

        print(f"\n  Encrypted API key (first 100 chars):")
        print(f"    {str(api_key_encrypted)[:100]}...")
        print(f"\n  Encrypted API secret (first 100 chars):")
        print(f"    {str(api_secret_encrypted)[:100]}...")

        # Check if values are encrypted (should be long hex strings)
        if isinstance(api_key_encrypted, str) and len(api_key_encrypted) > 200:
            print("\n✅ Values appear to be encrypted (long hex strings)")
        else:
            print("\n⚠️  WARNING: Values don't look encrypted!")

    except Exception as e:
        print(f"❌ ERROR reading config: {e}")
        return 1

    # Step 3: Get password and validate
    print("\n" + "="*80)
    print("STEP 3: Password Validation")
    print("="*80)

    print("\nEnter your Hummingbot password to decrypt the config:")
    password = getpass.getpass("Password: ")

    if not password:
        print("❌ ERROR: Password is required")
        return 1

    # Create secrets manager
    try:
        secrets_manager = ETHKeyFileSecretManger(password)
        print("\n✅ Secrets manager created")

        # Validate password
        is_valid = validate_password(secrets_manager)
        if not is_valid:
            print("❌ ERROR: Invalid password!")
            print("   The password does not match the one used to encrypt configs.")
            print("   Common issues:")
            print("   - Wrong password")
            print("   - Password file corrupted")
            print("   - Using different password than when config was created")
            return 1

        print("✅ Password is valid")

    except Exception as e:
        print(f"❌ ERROR validating password: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 4: Decrypt API credentials
    print("\n" + "="*80)
    print("STEP 4: Decrypting API Credentials")
    print("="*80)

    try:
        # Decrypt API key
        print("\nDecrypting API key...")
        decrypted_api_key = secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_key",
            api_key_encrypted
        )
        print(f"✅ Decrypted API key: {mask_secret(decrypted_api_key)}")
        print(f"   Full (first 20 chars): {decrypted_api_key[:20]}...")

        # Decrypt API secret
        print("\nDecrypting API secret...")
        decrypted_api_secret = secrets_manager.decrypt_secret_value(
            "extended_perpetual_api_secret",
            api_secret_encrypted
        )
        print(f"✅ Decrypted API secret: {mask_secret(decrypted_api_secret)}")
        print(f"   Full (first 20 chars): {decrypted_api_secret[:20]}...")

    except Exception as e:
        print(f"❌ ERROR decrypting credentials: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 5: Compare with known valid credentials
    print("\n" + "="*80)
    print("STEP 5: Validation Against Known Credentials")
    print("="*80)

    print("\n🔍 Comparing decrypted values with known valid credentials:")

    # Compare API key
    print(f"\nAPI Key Comparison:")
    print(f"  Known valid:  {KNOWN_VALID_API_KEY}")
    print(f"  From config:  {decrypted_api_key}")

    if decrypted_api_key == KNOWN_VALID_API_KEY:
        print("  ✅ MATCH - API key is correct!")
    else:
        print("  ❌ MISMATCH - API key in config is WRONG!")
        print(f"     Config has: {decrypted_api_key}")
        print(f"     Should be:  {KNOWN_VALID_API_KEY}")

    # Compare API secret
    print(f"\nAPI Secret Comparison:")
    print(f"  Known valid:  {mask_secret(KNOWN_VALID_API_SECRET)}")
    print(f"  From config:  {mask_secret(decrypted_api_secret)}")

    if decrypted_api_secret == KNOWN_VALID_API_SECRET:
        print("  ✅ MATCH - API secret is correct!")
    else:
        print("  ❌ MISMATCH - API secret in config is WRONG!")
        print(f"     Config has: {mask_secret(decrypted_api_secret)}")
        print(f"     Should be:  {mask_secret(KNOWN_VALID_API_SECRET)}")

    # Final diagnosis
    print("\n" + "="*80)
    print("DIAGNOSIS")
    print("="*80)

    api_key_matches = decrypted_api_key == KNOWN_VALID_API_KEY
    api_secret_matches = decrypted_api_secret == KNOWN_VALID_API_SECRET

    if api_key_matches and api_secret_matches:
        print("\n✅ CONCLUSION: Encrypted config contains CORRECT credentials!")
        print("\n   The 401 errors are NOT due to wrong credentials in config.")
        print("   Possible other causes:")
        print("   1. Connector not loading credentials correctly")
        print("   2. Headers not being set properly")
        print("   3. API key revoked on Extended's side")
        print("   4. Rate limiting or temporary API issues")
        print("\n   Next step: Run debug_connector_init.py to trace credential flow")

    elif not api_key_matches:
        print("\n❌ CONCLUSION: Encrypted config has WRONG API KEY!")
        print(f"\n   Stored in config: {decrypted_api_key}")
        print(f"   Valid key:        {KNOWN_VALID_API_KEY}")
        print("\n   This explains the 401 Unauthorized errors!")
        print("\n   SOLUTION: Update the config with correct credentials")
        print("   Run: docker exec -it <container> bin/hummingbot.py")
        print("   Then: connect extended_perpetual")
        print(f"   Enter API key: {KNOWN_VALID_API_KEY}")

    elif not api_secret_matches:
        print("\n❌ CONCLUSION: Encrypted config has WRONG API SECRET!")
        print(f"\n   Stored in config: {mask_secret(decrypted_api_secret)}")
        print(f"   Valid secret:     {mask_secret(KNOWN_VALID_API_SECRET)}")
        print("\n   SOLUTION: Update the config with correct credentials")
        print("   Run: docker exec -it <container> bin/hummingbot.py")
        print("   Then: connect extended_perpetual")
        print(f"   Enter API secret: {KNOWN_VALID_API_SECRET}")

    print("\n" + "="*80)
    print("DEBUG COMPLETE")
    print("="*80)

    return 0 if (api_key_matches and api_secret_matches) else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
Fix Extended Connector Configuration

This script updates the Extended connector configuration with correct API credentials,
re-encrypting them with the Hummingbot password.

SAFETY: Creates backup before making changes.
"""

import sys
import getpass
import shutil
from pathlib import Path
from datetime import datetime

# Add hummingbot to path
sys.path.insert(0, '/Users/tdl321/hummingbot')

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger, validate_password
from hummingbot.client.config.config_helpers import (
    get_connector_config_yml_path,
    read_yml_file,
    save_to_yml,
    load_connector_config_map_from_file
)
from hummingbot.client.config.security import Security


def mask_secret(value: str, show_chars: int = 8) -> str:
    """Mask a secret value showing only first and last few characters."""
    if not value:
        return "NONE"
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    return f"{value[:show_chars]}...{value[-show_chars:]}"


def backup_config(config_path: Path) -> Path:
    """Create a backup of the config file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"{config_path.stem}_backup_{timestamp}{config_path.suffix}"
    shutil.copy2(config_path, backup_path)
    return backup_path


def main():
    print("="*80)
    print("EXTENDED CONNECTOR CONFIG FIX TOOL")
    print("="*80)

    # Correct credentials
    CORRECT_API_KEY = "f4aa1ba3e3038adf522981a90d2a1c57"
    CORRECT_API_SECRET = "0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1"

    print("\n⚠️  WARNING: This script will modify your encrypted configuration!")
    print("   A backup will be created before any changes are made.")
    print("\n   Correct credentials to be set:")
    print(f"   API Key: {mask_secret(CORRECT_API_KEY)}")
    print(f"   API Secret: {mask_secret(CORRECT_API_SECRET)}")

    # Confirm
    print("\n" + "-"*80)
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted by user.")
        return 0

    # Get config path
    config_path = get_connector_config_yml_path("extended_perpetual")
    print(f"\nConfig path: {config_path}")

    if not config_path.exists():
        print("❌ ERROR: Config file does not exist!")
        print(f"   Expected location: {config_path}")
        print("\nYou need to create the config first:")
        print("   1. Run Hummingbot: docker exec -it <container> bin/hummingbot.py")
        print("   2. Execute: connect extended_perpetual")
        print("   3. Enter placeholder credentials (will be fixed by this script)")
        return 1

    print("✅ Config file found")

    # Get password
    print("\n" + "="*80)
    print("PASSWORD VERIFICATION")
    print("="*80)

    print("\nEnter your Hummingbot password:")
    password = getpass.getpass("Password: ")

    if not password:
        print("❌ ERROR: Password is required")
        return 1

    # Validate password
    try:
        secrets_manager = ETHKeyFileSecretManger(password)
        is_valid = validate_password(secrets_manager)

        if not is_valid:
            print("❌ ERROR: Invalid password!")
            return 1

        print("✅ Password validated")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Backup config
    print("\n" + "="*80)
    print("BACKING UP CONFIG")
    print("="*80)

    try:
        backup_path = backup_config(config_path)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"❌ ERROR creating backup: {e}")
        return 1

    # Read current config
    print("\n" + "="*80)
    print("READING CURRENT CONFIG")
    print("="*80)

    try:
        raw_config = read_yml_file(config_path)
        print(f"✅ Config loaded")
        print(f"   Connector: {raw_config.get('connector')}")

        # Decrypt current values to show what's being replaced
        if 'extended_perpetual_api_key' in raw_config:
            try:
                old_key = secrets_manager.decrypt_secret_value(
                    'extended_perpetual_api_key',
                    raw_config['extended_perpetual_api_key']
                )
                print(f"\n   Current API key: {mask_secret(old_key)}")
            except:
                print(f"\n   Current API key: (unable to decrypt)")

        if 'extended_perpetual_api_secret' in raw_config:
            try:
                old_secret = secrets_manager.decrypt_secret_value(
                    'extended_perpetual_api_secret',
                    raw_config['extended_perpetual_api_secret']
                )
                print(f"   Current API secret: {mask_secret(old_secret)}")
            except:
                print(f"   Current API secret: (unable to decrypt)")

    except Exception as e:
        print(f"❌ ERROR reading config: {e}")
        return 1

    # Encrypt new credentials
    print("\n" + "="*80)
    print("ENCRYPTING NEW CREDENTIALS")
    print("="*80)

    try:
        print(f"\nEncrypting API key: {mask_secret(CORRECT_API_KEY)}")
        encrypted_api_key = secrets_manager.encrypt_secret_value(
            'extended_perpetual_api_key',
            CORRECT_API_KEY
        )
        print(f"✅ API key encrypted ({len(encrypted_api_key)} chars)")

        print(f"\nEncrypting API secret: {mask_secret(CORRECT_API_SECRET)}")
        encrypted_api_secret = secrets_manager.encrypt_secret_value(
            'extended_perpetual_api_secret',
            CORRECT_API_SECRET
        )
        print(f"✅ API secret encrypted ({len(encrypted_api_secret)} chars)")

    except Exception as e:
        print(f"❌ ERROR encrypting credentials: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Update config
    print("\n" + "="*80)
    print("UPDATING CONFIG FILE")
    print("="*80)

    try:
        # Update the dictionary
        raw_config['extended_perpetual_api_key'] = encrypted_api_key
        raw_config['extended_perpetual_api_secret'] = encrypted_api_secret

        # Write back to file
        import ruamel.yaml
        yaml = ruamel.yaml.YAML()
        with open(config_path, 'w') as f:
            yaml.dump(raw_config, f)

        print(f"✅ Config file updated: {config_path}")

    except Exception as e:
        print(f"❌ ERROR writing config: {e}")
        print(f"\nRestoring backup...")
        try:
            shutil.copy2(backup_path, config_path)
            print(f"✅ Backup restored")
        except Exception as restore_error:
            print(f"❌ ERROR restoring backup: {restore_error}")
        return 1

    # Verify the update
    print("\n" + "="*80)
    print("VERIFYING UPDATE")
    print("="*80)

    try:
        # Re-read the config
        print("\nRe-reading config...")
        verification_config = read_yml_file(config_path)

        # Decrypt to verify
        print("Decrypting to verify...")
        verified_key = secrets_manager.decrypt_secret_value(
            'extended_perpetual_api_key',
            verification_config['extended_perpetual_api_key']
        )
        verified_secret = secrets_manager.decrypt_secret_value(
            'extended_perpetual_api_secret',
            verification_config['extended_perpetual_api_secret']
        )

        print(f"\nVerified API key: {mask_secret(verified_key)}")
        print(f"Verified API secret: {mask_secret(verified_secret)}")

        # Check if they match
        if verified_key == CORRECT_API_KEY:
            print("\n✅ API key verified correctly!")
        else:
            print(f"\n❌ API key mismatch!")
            print(f"   Expected: {CORRECT_API_KEY}")
            print(f"   Got: {verified_key}")
            return 1

        if verified_secret == CORRECT_API_SECRET:
            print("✅ API secret verified correctly!")
        else:
            print(f"❌ API secret mismatch!")
            print(f"   Expected: {CORRECT_API_SECRET}")
            print(f"   Got: {verified_secret}")
            return 1

    except Exception as e:
        print(f"❌ ERROR verifying update: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Success!
    print("\n" + "="*80)
    print("SUCCESS!")
    print("="*80)

    print("\n✅ Extended connector config has been updated with correct credentials!")
    print(f"\n   Config file: {config_path}")
    print(f"   Backup: {backup_path}")
    print(f"\n   API Key: {mask_secret(CORRECT_API_KEY)}")
    print(f"   API Secret: {mask_secret(CORRECT_API_SECRET)}")

    print("\n📋 Next steps:")
    print("   1. If running in Docker, copy this config to Docker container:")
    print(f"      docker cp {config_path} <container>:/conf/connectors/extended_perpetual.yml")
    print("   2. Restart Hummingbot")
    print("   3. Verify no more 401 errors in logs")
    print("   4. Run validate_extended_docker.py to confirm")

    print("\n" + "="*80)

    return 0


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

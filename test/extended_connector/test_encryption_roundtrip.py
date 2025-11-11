#!/usr/bin/env python3
"""
Test Encryption/Decryption Round-Trip

This script verifies that Hummingbot's encryption system works correctly
by encrypting and decrypting test values.
"""

import sys
import getpass

# Add hummingbot to path
sys.path.insert(0, '/Users/tdl321/hummingbot')

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger, validate_password


def mask_secret(value: str, show_chars: int = 8) -> str:
    """Mask a secret value showing only first and last few characters."""
    if not value:
        return "NONE"
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    return f"{value[:show_chars]}...{value[-show_chars:]}"


def test_roundtrip(secrets_manager: ETHKeyFileSecretManger, test_name: str, test_value: str):
    """Test encryption and decryption of a value."""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")

    print(f"Original value: {mask_secret(test_value)}")
    print(f"Original length: {len(test_value)} chars")

    try:
        # Encrypt
        print("\n1. Encrypting...")
        encrypted = secrets_manager.encrypt_secret_value(test_name, test_value)
        print(f"   ✅ Encrypted successfully")
        print(f"   Encrypted length: {len(encrypted)} chars")
        print(f"   Encrypted (first 100 chars): {encrypted[:100]}...")

        # Decrypt
        print("\n2. Decrypting...")
        decrypted = secrets_manager.decrypt_secret_value(test_name, encrypted)
        print(f"   ✅ Decrypted successfully")
        print(f"   Decrypted: {mask_secret(decrypted)}")

        # Compare
        print("\n3. Comparing...")
        if decrypted == test_value:
            print(f"   ✅ SUCCESS: Round-trip preserves value perfectly!")
            return True
        else:
            print(f"   ❌ FAILURE: Round-trip changed the value!")
            print(f"   Original:  {test_value}")
            print(f"   Decrypted: {decrypted}")
            return False

    except Exception as e:
        print(f"\n   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*80)
    print("ENCRYPTION/DECRYPTION ROUND-TRIP TEST")
    print("="*80)

    # Get password
    print("\nEnter your Hummingbot password:")
    password = getpass.getpass("Password: ")

    if not password:
        print("❌ ERROR: Password is required")
        return 1

    # Validate password
    print("\nValidating password...")
    try:
        secrets_manager = ETHKeyFileSecretManger(password)
        is_valid = validate_password(secrets_manager)

        if not is_valid:
            print("❌ ERROR: Invalid password!")
            print("   The password does not match your Hummingbot password.")
            return 1

        print("✅ Password validated successfully")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test cases
    print("\n" + "="*80)
    print("RUNNING ROUND-TRIP TESTS")
    print("="*80)

    test_cases = [
        ("Simple ASCII", "test123"),
        ("Extended API Key", "f4aa1ba3e3038adf522981a90d2a1c57"),
        ("Extended API Secret", "0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1"),
        ("Long hex string", "0x" + "a" * 64),
        ("Special chars", "test!@#$%^&*()_+-=[]{}|;:',.<>?"),
        ("Empty string", ""),
        ("Unicode", "Hello 世界 🌍"),
    ]

    results = []
    for test_name, test_value in test_cases:
        success = test_roundtrip(secrets_manager, test_name, test_value)
        results.append((test_name, success))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")
    print("\nResults:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("   Hummingbot's encryption/decryption system is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED!")
        print("   There may be an issue with the encryption system.")
        return 1


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

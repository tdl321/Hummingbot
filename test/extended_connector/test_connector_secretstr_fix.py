#!/usr/bin/env python3
"""
Test that connector properly unwraps SecretStr and strips whitespace.
"""

import sys
sys.path.insert(0, '/Users/tdl321/hummingbot')

from pydantic import SecretStr
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative


def main():
    """Test connector with SecretStr credentials containing whitespace."""
    print("="*80)
    print("TESTING CONNECTOR WITH SECRETSTR CREDENTIALS")
    print("="*80)

    # Simulate credentials with whitespace (like from config)
    api_key_with_whitespace = "  f4aa1ba3e3038adf522981a90d2a1c57  "
    stark_key_with_whitespace = "  0x1234567890abcdef  "

    print(f"\n1. Creating SecretStr credentials with whitespace:")
    print(f"   API Key: '{api_key_with_whitespace}' (length: {len(api_key_with_whitespace)})")
    print(f"   Stark Key: '{stark_key_with_whitespace}' (length: {len(stark_key_with_whitespace)})")

    secret_api_key = SecretStr(api_key_with_whitespace)
    secret_stark_key = SecretStr(stark_key_with_whitespace)

    print(f"\n2. Wrapped in SecretStr:")
    print(f"   API Key type: {type(secret_api_key)}")
    print(f"   Stark Key type: {type(secret_stark_key)}")

    # Create connector instance (like Hummingbot does from config)
    print(f"\n3. Creating connector with SecretStr credentials...")
    connector = ExtendedPerpetualDerivative(
        extended_perpetual_api_key=secret_api_key,
        extended_perpetual_api_secret=secret_stark_key,
        trading_pairs=["BTC-USD"],
        trading_required=True
    )

    print(f"\n4. Checking stored credentials in connector:")
    print(f"   API Key type: {type(connector.extended_perpetual_api_key)}")
    print(f"   API Key value: '{connector.extended_perpetual_api_key}'")
    print(f"   API Key length: {len(connector.extended_perpetual_api_key)}")

    print(f"\n   Stark Key type: {type(connector.extended_perpetual_api_secret)}")
    print(f"   Stark Key value: '{connector.extended_perpetual_api_secret}'")
    print(f"   Stark Key length: {len(connector.extended_perpetual_api_secret)}")

    # Check if unwrapping worked
    if isinstance(connector.extended_perpetual_api_key, str):
        print(f"\n   ✅ API Key was unwrapped from SecretStr to str")
    else:
        print(f"\n   ❌ API Key is still SecretStr!")

    # Now test authenticator creation
    print(f"\n5. Creating authenticator...")
    try:
        auth = connector.authenticator
        if auth is None:
            print(f"   ❌ Authenticator is None (trading_required might be False)")
        else:
            print(f"   ✅ Authenticator created successfully")
            print(f"   API Key in auth: '{auth._api_key}'")
            print(f"   API Key length in auth: {len(auth._api_key)}")

            # Check if whitespace was stripped
            expected_stripped = "f4aa1ba3e3038adf522981a90d2a1c57"
            if auth._api_key == expected_stripped:
                print(f"\n   ✅ WHITESPACE WAS STRIPPED! Key matches expected value.")
            elif auth._api_key == api_key_with_whitespace.strip():
                print(f"\n   ✅ WHITESPACE WAS STRIPPED!")
            else:
                print(f"\n   ❌ WHITESPACE NOT STRIPPED!")
                print(f"   Expected: '{expected_stripped}'")
                print(f"   Got: '{auth._api_key}'")
                print(f"   Raw repr: {repr(auth._api_key)}")

    except Exception as e:
        print(f"   ❌ Failed to create authenticator: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    if isinstance(connector.extended_perpetual_api_key, str) and auth._api_key == expected_stripped:
        print("✅ FIX SUCCESSFUL!")
        print("   - SecretStr was unwrapped to str")
        print("   - Whitespace was stripped in auth constructor")
        print("   - Connector should now work in Docker")
    else:
        print("❌ FIX FAILED - Something is still wrong")
    print("="*80)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

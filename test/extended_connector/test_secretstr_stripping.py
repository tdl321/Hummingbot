#!/usr/bin/env python3
"""
Test how SecretStr interacts with .strip() method.
"""

import sys
sys.path.insert(0, '/Users/tdl321/hummingbot')

from pydantic import SecretStr


def main():
    """Test SecretStr with whitespace."""
    print("="*80)
    print("TESTING SECRETSTR WITH WHITESPACE")
    print("="*80)

    # Simulate what happens when credentials are loaded from config
    api_key_with_whitespace = "  f4aa1ba3e3038adf522981a90d2a1c57  "

    print(f"\n1. Original API key:")
    print(f"   Value: '{api_key_with_whitespace}'")
    print(f"   Length: {len(api_key_with_whitespace)}")

    # Wrap in SecretStr (like config does)
    secret_api_key = SecretStr(api_key_with_whitespace)

    print(f"\n2. Wrapped in SecretStr:")
    print(f"   Type: {type(secret_api_key)}")
    print(f"   Can call .strip() directly? {hasattr(secret_api_key, 'strip')}")

    # Try to strip SecretStr directly (this WON'T work!)
    try:
        if hasattr(secret_api_key, 'strip'):
            stripped_secret = secret_api_key.strip()
            print(f"   ✅ Direct .strip() worked: {type(stripped_secret)}")
        else:
            print(f"   ❌ SecretStr has no .strip() method!")
            print(f"   Available methods: {[m for m in dir(secret_api_key) if not m.startswith('_')]}")
    except Exception as e:
        print(f"   ❌ Error calling .strip(): {e}")

    # The CORRECT way: unwrap first, then strip
    print(f"\n3. Correct approach - unwrap then strip:")
    unwrapped = secret_api_key.get_secret_value()
    print(f"   Unwrapped value: '{unwrapped}'")
    print(f"   Unwrapped length: {len(unwrapped)}")
    print(f"   Unwrapped type: {type(unwrapped)}")

    stripped = unwrapped.strip()
    print(f"   Stripped value: '{stripped}'")
    print(f"   Stripped length: {len(stripped)}")

    # Test what the auth code does
    print(f"\n4. Testing what auth code does:")
    print(f"   Code: api_key.strip() if api_key else api_key")

    # If api_key is a SecretStr object
    if isinstance(secret_api_key, SecretStr):
        print(f"   ⚠️  Input is SecretStr - .strip() will FAIL!")
        print(f"   Need to unwrap first with .get_secret_value()")

    # If api_key is already a string (like in test scripts)
    if isinstance(api_key_with_whitespace, str):
        result = api_key_with_whitespace.strip()
        print(f"   ✅ Input is str - .strip() works: '{result}'")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("The auth code assumes api_key is a STRING.")
    print("But when loaded from config, api_key is a SECRETSTR object!")
    print("")
    print("The fix needed in extended_perpetual_derivative.py:")
    print("  Line 84-85 should unwrap SecretStr before storing:")
    print("")
    print("  self.extended_perpetual_api_key = (")
    print("      extended_perpetual_api_key.get_secret_value()")
    print("      if isinstance(extended_perpetual_api_key, SecretStr)")
    print("      else extended_perpetual_api_key")
    print("  )")
    print("="*80)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

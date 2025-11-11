#!/usr/bin/env python3
"""
Test Extended connector header generation to debug 401 errors.

This script tests if headers are being added correctly by the connector's authentication system.
"""

import asyncio
import sys

sys.path.insert(0, '/Users/tdl321/hummingbot')

from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_auth import ExtendedPerpetualAuth
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, RESTMethod
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_web_utils import ExtendedPerpetualRESTPreProcessor


async def test_header_generation():
    """Test if headers are generated correctly."""
    print("="*80)
    print("TESTING EXTENDED HEADER GENERATION")
    print("="*80)

    # Test credentials
    api_key = "f4aa1ba3e3038adf522981a90d2a1c57"
    api_secret = "0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1"

    print("\n1. Testing ExtendedPerpetualAuth...")
    print(f"   API Key: {api_key}")
    print(f"   API Secret: {api_secret[:20]}...")

    try:
        auth = ExtendedPerpetualAuth(api_key, api_secret)
        print("   ✅ Auth object created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create auth object: {e}")
        return False

    print("\n2. Testing rest_authenticate() method...")

    # Create a test request
    test_request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.starknet.extended.exchange/api/v1/user/balance",
        headers={},
        is_auth_required=True
    )

    print(f"   Original headers: {test_request.headers}")

    # Apply authentication
    try:
        authenticated_request = await auth.rest_authenticate(test_request)
        print(f"   ✅ After auth headers: {authenticated_request.headers}")

        # Check if X-Api-Key is present
        if "X-Api-Key" in authenticated_request.headers:
            print(f"   ✅ X-Api-Key header present: {authenticated_request.headers['X-Api-Key']}")
        else:
            print("   ❌ X-Api-Key header MISSING!")
            return False

    except Exception as e:
        print(f"   ❌ Failed to authenticate request: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n3. Testing ExtendedPerpetualRESTPreProcessor...")

    # Create another test request
    test_request2 = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.starknet.extended.exchange/api/v1/user/balance",
        headers={},
        is_auth_required=True
    )

    print(f"   Original headers: {test_request2.headers}")

    # Apply pre-processor
    try:
        preprocessor = ExtendedPerpetualRESTPreProcessor()
        processed_request = await preprocessor.pre_process(test_request2)
        print(f"   ✅ After preprocessing: {processed_request.headers}")

        # Check required headers
        required_headers = ["Content-Type", "User-Agent"]
        for header in required_headers:
            if header in processed_request.headers:
                print(f"   ✅ {header}: {processed_request.headers[header]}")
            else:
                print(f"   ❌ {header} header MISSING!")
                return False

    except Exception as e:
        print(f"   ❌ Failed to preprocess request: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. Testing combined flow (preprocessor + auth)...")

    # Create final test request
    test_request3 = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.starknet.extended.exchange/api/v1/user/balance",
        headers={},
        is_auth_required=True
    )

    try:
        # Apply preprocessor first
        processed = await preprocessor.pre_process(test_request3)
        # Then apply auth
        final_request = await auth.rest_authenticate(processed)

        print(f"   Final headers: {final_request.headers}")
        print("\n   Expected headers for Extended API:")
        print("   - Content-Type: application/json")
        print("   - User-Agent: hummingbot-extended-connector")
        print("   - X-Api-Key: <api_key>")

        print("\n   Header verification:")
        checks = {
            "Content-Type": "application/json",
            "User-Agent": "hummingbot-extended-connector",
            "X-Api-Key": api_key
        }

        all_good = True
        for header, expected_value in checks.items():
            actual_value = final_request.headers.get(header)
            if actual_value == expected_value:
                print(f"   ✅ {header}: {actual_value}")
            else:
                print(f"   ❌ {header}: Expected '{expected_value}', got '{actual_value}'")
                all_good = False

        if all_good:
            print("\n✅ ALL HEADERS CORRECT!")
            print("="*80)
            print("CONCLUSION: Header generation is working correctly.")
            print("The 401 error in Docker must be due to:")
            print("1. Wrong/expired API key in encrypted config")
            print("2. Failed decryption of encrypted config")
            print("3. API key not being passed to connector constructor")
            return True
        else:
            print("\n❌ HEADER GENERATION HAS ISSUES!")
            return False

    except Exception as e:
        print(f"   ❌ Failed combined flow: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_header_generation())
    sys.exit(0 if success else 1)

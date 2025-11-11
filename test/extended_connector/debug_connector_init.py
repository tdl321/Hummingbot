#!/usr/bin/env python3
"""
Debug Extended Connector Initialization

This script traces how the Extended connector receives and uses API credentials
from the encrypted config through the Security system.
"""

import asyncio
import sys
import getpass
from pathlib import Path

# Add hummingbot to path
sys.path.insert(0, '/Users/tdl321/hummingbot')

from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger, validate_password
from hummingbot.client.config.security import Security
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_derivative import ExtendedPerpetualDerivative
import hummingbot.connector.derivative.extended_perpetual.extended_perpetual_constants as CONSTANTS


def mask_secret(value: str, show_chars: int = 8) -> str:
    """Mask a secret value showing only first and last few characters."""
    if not value:
        return "NONE"
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    return f"{value[:show_chars]}...{value[-show_chars:]}"


async def test_connector_initialization():
    """Test how connector receives credentials through the Security system."""
    print("="*80)
    print("EXTENDED CONNECTOR INITIALIZATION DEBUGGER")
    print("="*80)

    # Step 1: Login to Security system
    print("\n" + "="*80)
    print("STEP 1: Security System Login")
    print("="*80)

    print("\nEnter your Hummingbot password:")
    password = getpass.getpass("Password: ")

    if not password:
        print("❌ ERROR: Password is required")
        return False

    try:
        secrets_manager = ETHKeyFileSecretManger(password)
        is_valid = validate_password(secrets_manager)

        if not is_valid:
            print("❌ ERROR: Invalid password!")
            return False

        print("✅ Password validated")

        # Login to Security system (this decrypts all configs)
        success = Security.login(secrets_manager)
        if not success:
            print("❌ ERROR: Security.login() failed!")
            return False

        print("✅ Security system logged in")
        print(f"   Decryption done: {Security.is_decryption_done()}")

    except Exception as e:
        print(f"❌ ERROR during login: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Retrieve decrypted connector config
    print("\n" + "="*80)
    print("STEP 2: Retrieving Decrypted Config")
    print("="*80)

    try:
        # Wait for decryption to complete
        await Security.wait_til_decryption_done()
        print("✅ Decryption completed")

        # Get decrypted config for extended_perpetual
        connector_config = Security.decrypted_value("extended_perpetual")

        if connector_config is None:
            print("❌ ERROR: No config found for 'extended_perpetual'")
            print("\nAvailable configs:")
            all_configs = Security.all_decrypted_values()
            for name in all_configs.keys():
                print(f"  - {name}")
            return False

        print("✅ Extended perpetual config found")

        # Extract API keys
        api_keys = Security.api_keys("extended_perpetual")
        print(f"\nDecrypted API keys from Security system:")
        for key_name, key_value in api_keys.items():
            print(f"  {key_name}: {mask_secret(key_value)}")
            if key_name == "extended_perpetual_api_key":
                stored_api_key = key_value
            elif key_name == "extended_perpetual_api_secret":
                stored_api_secret = key_value

    except Exception as e:
        print(f"❌ ERROR retrieving config: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Compare with known valid credentials
    print("\n" + "="*80)
    print("STEP 3: Validating Against Known Credentials")
    print("="*80)

    KNOWN_VALID_API_KEY = "f4aa1ba3e3038adf522981a90d2a1c57"
    KNOWN_VALID_API_SECRET = "0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1"

    print(f"\nAPI Key:")
    print(f"  From Security: {mask_secret(stored_api_key)}")
    print(f"  Known valid:   {mask_secret(KNOWN_VALID_API_KEY)}")
    api_key_matches = stored_api_key == KNOWN_VALID_API_KEY
    print(f"  Match: {'✅ YES' if api_key_matches else '❌ NO'}")

    print(f"\nAPI Secret:")
    print(f"  From Security: {mask_secret(stored_api_secret)}")
    print(f"  Known valid:   {mask_secret(KNOWN_VALID_API_SECRET)}")
    api_secret_matches = stored_api_secret == KNOWN_VALID_API_SECRET
    print(f"  Match: {'✅ YES' if api_secret_matches else '❌ NO'}")

    # Step 4: Initialize connector with decrypted credentials
    print("\n" + "="*80)
    print("STEP 4: Initializing Connector")
    print("="*80)

    try:
        print(f"\nCreating ExtendedPerpetualDerivative with:")
        print(f"  API Key: {mask_secret(stored_api_key)}")
        print(f"  API Secret: {mask_secret(stored_api_secret)}")

        connector = ExtendedPerpetualDerivative(
            extended_perpetual_api_key=stored_api_key,
            extended_perpetual_api_secret=stored_api_secret,
            trading_pairs=["KAITO-USD"],
            trading_required=True
        )

        print("✅ Connector created successfully")

        # Check authenticator
        if connector.authenticator:
            print(f"\n✅ Authenticator exists:")
            print(f"   API key: {mask_secret(connector.authenticator._api_key)}")
            print(f"   Has public key: {'Yes' if connector.authenticator._public_key else 'No'}")
        else:
            print("\n❌ WARNING: No authenticator!")

    except Exception as e:
        print(f"❌ ERROR initializing connector: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Test authentication header generation
    print("\n" + "="*80)
    print("STEP 5: Testing Auth Header Generation")
    print("="*80)

    try:
        from hummingbot.core.web_assistant.connections.data_types import RESTRequest, RESTMethod

        # Create test request
        test_request = RESTRequest(
            method=RESTMethod.GET,
            url=f"{CONSTANTS.PERPETUAL_BASE_URL}{CONSTANTS.BALANCE_URL}",
            headers={},
            is_auth_required=True
        )

        print(f"\nTest request URL: {test_request.url}")
        print(f"Original headers: {test_request.headers}")

        # Apply authentication
        authenticated_request = await connector.authenticator.rest_authenticate(test_request)

        print(f"\nAfter authentication:")
        print(f"  Headers: {authenticated_request.headers}")

        # Check X-Api-Key
        if "X-Api-Key" in authenticated_request.headers:
            header_api_key = authenticated_request.headers["X-Api-Key"]
            print(f"\n  ✅ X-Api-Key header present: {mask_secret(header_api_key)}")

            # Verify it matches what was passed to connector
            if header_api_key == stored_api_key:
                print(f"  ✅ Header matches stored API key")
            else:
                print(f"  ❌ Header DOES NOT match stored API key!")
                print(f"     Stored: {mask_secret(stored_api_key)}")
                print(f"     Header: {mask_secret(header_api_key)}")

            # Verify it matches known valid key
            if header_api_key == KNOWN_VALID_API_KEY:
                print(f"  ✅ Header matches known valid API key")
            else:
                print(f"  ❌ Header DOES NOT match known valid API key!")
                print(f"     Known valid: {mask_secret(KNOWN_VALID_API_KEY)}")
                print(f"     Header:      {mask_secret(header_api_key)}")
        else:
            print(f"\n  ❌ X-Api-Key header MISSING!")

    except Exception as e:
        print(f"❌ ERROR testing auth headers: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 6: Test actual API call
    print("\n" + "="*80)
    print("STEP 6: Testing Actual API Call")
    print("="*80)

    try:
        print("\nStarting connector network...")
        await connector.start_network()
        print("✅ Network started")

        print("\nWaiting 3 seconds for initialization...")
        await asyncio.sleep(3)

        print("\nAttempting balance fetch...")
        response = await connector._api_get(
            path_url=CONSTANTS.BALANCE_URL,
            is_auth_required=True,
            limit_id=CONSTANTS.BALANCE_URL
        )

        print(f"\n✅ API call successful!")
        print(f"Response: {response}")

        if isinstance(response, dict) and response.get('status') == 'OK':
            data = response.get('data', {})
            print(f"\nBalance data:")
            print(f"  Balance: {data.get('balance')}")
            print(f"  Equity: {data.get('equity')}")
            print(f"  Available: {data.get('availableForTrade')}")

        print("\nStopping connector...")
        await connector.stop_network()
        print("✅ Network stopped")

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ API call failed: {error_msg}")

        if "401" in error_msg:
            print("\n🔍 401 UNAUTHORIZED ERROR DETECTED!")
            print("\nThis means:")
            print("  1. Headers were sent correctly")
            print("  2. But the API key is rejected by Extended API")
            print("\nPossible causes:")
            print("  a) API key in config is wrong/expired")
            print("  b) API key is for wrong environment (testnet vs mainnet)")
            print("  c) API key belongs to different sub-account")

        import traceback
        traceback.print_exc()

        try:
            await connector.stop_network()
        except:
            pass

        return False

    # Final diagnosis
    print("\n" + "="*80)
    print("DIAGNOSIS")
    print("="*80)

    if api_key_matches and api_secret_matches:
        print("\n✅ Credentials flow correctly from config to connector")
        print("   The 401 error must be due to:")
        print("   1. API key revoked on Extended's side")
        print("   2. Environment mismatch (testnet key on mainnet)")
        print("   3. Sub-account mismatch")
    else:
        print("\n❌ Credentials in config DO NOT match valid credentials")
        print("   Need to update encrypted config with correct values")

    return api_key_matches and api_secret_matches


def main():
    try:
        result = asyncio.run(test_connector_initialization())
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

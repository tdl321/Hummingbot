#!/usr/bin/env python3
"""
Test Extended balance endpoint with actual headers to debug 401 error.
"""

import sys
sys.path.insert(0, '/Users/tdl321/hummingbot')

import asyncio
import os
from dotenv import load_dotenv

from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_auth import ExtendedPerpetualAuth
from hummingbot.connector.derivative.extended_perpetual import extended_perpetual_web_utils as web_utils
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest


async def test_balance_request():
    """Test the actual balance request with all headers."""
    print("="*80)
    print("TESTING EXTENDED BALANCE REQUEST WITH ACTUAL HEADERS")
    print("="*80)

    # Load .env
    load_dotenv()
    api_key = os.getenv('EXTENDED_API_KEY')
    stark_private_key = os.getenv('EXTENDED_STARK_PRIVATE_KEY')

    if not api_key:
        print("\n❌ EXTENDED_API_KEY not found in .env file!")
        return False

    if not stark_private_key:
        print("\n❌ EXTENDED_STARK_PRIVATE_KEY not found in .env file!")
        return False

    print(f"\n1. API Key from .env:")
    print(f"   Length: {len(api_key)}")
    print(f"   First 10 chars: '{api_key[:10]}'")
    print(f"   Last 10 chars: '{api_key[-10:]}'")
    print(f"   Has leading whitespace: {api_key != api_key.lstrip()}")
    print(f"   Has trailing whitespace: {api_key != api_key.rstrip()}")
    print(f"   Raw representation: {repr(api_key)}")

    # Create auth instance (will strip whitespace)
    print(f"\n2. Creating ExtendedPerpetualAuth instance...")
    auth = ExtendedPerpetualAuth(
        api_key=api_key,
        api_secret=stark_private_key,
        vault_id=None
    )

    # Create request
    print(f"\n3. Creating REST request for balance endpoint...")
    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.starknet.extended.exchange/api/v1/user/balance",
        headers={}
    )

    print(f"   Initial headers: {request.headers}")

    # Apply pre-processor (adds User-Agent and Content-Type)
    print(f"\n4. Applying REST pre-processor...")
    from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_web_utils import ExtendedPerpetualRESTPreProcessor
    pre_processor = ExtendedPerpetualRESTPreProcessor()
    request = await pre_processor.pre_process(request)

    print(f"   Headers after pre-processor:")
    for key, value in request.headers.items():
        print(f"     {key}: {value}")

    # Apply authentication (adds X-Api-Key)
    print(f"\n5. Applying authentication...")
    request = await auth.rest_authenticate(request)

    print(f"   Final headers:")
    for key, value in request.headers.items():
        if key == "X-Api-Key":
            print(f"     {key}: {value[:10]}...{value[-10:]} (length: {len(value)})")
        else:
            print(f"     {key}: {value}")

    # Now make the actual request
    print(f"\n6. Making actual HTTP request...")
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                request.url,
                headers=request.headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                status = response.status
                text = await response.text()

                print(f"   Response status: {status}")
                print(f"   Response body: {text[:500]}")

                if status == 200:
                    print(f"\n   ✅ SUCCESS! Balance endpoint returned 200")
                    return True
                elif status == 401:
                    print(f"\n   ❌ 401 UNAUTHORIZED!")
                    print(f"\n   Possible causes:")
                    print(f"   1. API key is invalid or expired")
                    print(f"   2. API key is from wrong sub-account")
                    print(f"   3. API key was revoked in Extended UI")
                    print(f"   4. Headers are being modified after auth")
                    return False
                elif status == 404:
                    print(f"\n   ℹ️  404 - Zero balance (this is OK per Extended API docs)")
                    return True
                else:
                    print(f"\n   ⚠️  Unexpected status code: {status}")
                    return False

    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_balance_request())
    sys.exit(0 if success else 1)

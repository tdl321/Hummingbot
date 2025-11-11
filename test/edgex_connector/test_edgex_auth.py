#!/usr/bin/env python3
"""
EdgeX Connector Authentication Test Script

This script tests the EdgeX authentication implementation including:
1. Public API endpoints (no authentication)
2. Server time synchronization
3. Private API authentication with StarkEx signatures
4. Signature generation validation

Usage:
    # Set credentials in .env or environment:
    export EDGEX_PRIVATE_KEY="your_stark_private_key"
    export EDGEX_ACCOUNT_ID="your_account_id"

    # Run tests
    python test/edgex_connector/test_edgex_auth.py

    # Or use testnet
    python test/edgex_connector/test_edgex_auth.py --testnet
"""

import sys
import os
import asyncio
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal

# Add hummingbot to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
import aiohttp


# ============================================================================
# Configuration
# ============================================================================

class EdgeXTestConfig:
    """Test configuration for EdgeX API."""

    # API URLs (from official Python SDK)
    MAINNET_BASE_URL = "https://pro.edgex.exchange"
    MAINNET_WS_URL = "wss://quote.edgex.exchange"

    TESTNET_BASE_URL = "https://testnet.edgex.exchange"
    TESTNET_WS_URL = "wss://quote-testnet.edgex.exchange"

    # API endpoints
    SERVER_TIME_PATH = "/api/v1/public/meta/getServerTime"
    METADATA_PATH = "/api/v1/public/meta/getMetaData"
    ACCOUNT_ASSET_PATH = "/api/v1/private/account/getAccountAsset"
    POSITION_BY_CONTRACT_PATH = "/api/v1/private/account/getPositionByContractId"

    # Authentication headers
    HEADER_TIMESTAMP = "X-edgeX-Api-Timestamp"
    HEADER_SIGNATURE = "X-edgeX-Api-Signature"


# ============================================================================
# StarkEx Signature Implementation
# ============================================================================

from starkware.crypto.signature.signature import sign, private_to_stark_key, FIELD_PRIME


class StarkExSigner:
    """
    StarkEx signature implementation for EdgeX authentication.

    Uses starkware.crypto.signature for proper StarkEx ECDSA signing.
    """

    def __init__(self, private_key: str):
        """
        Initialize StarkEx signer.

        Args:
            private_key: Stark private key (hex string, with or without 0x)
        """
        # Remove 0x prefix if present
        private_key_hex = private_key if not private_key.startswith('0x') else private_key[2:]

        # Convert to integer
        self.private_key_int = int(private_key_hex, 16)

        # Calculate public key
        self.public_key = private_to_stark_key(self.private_key_int)

    def sign_message(self, message: str) -> str:
        """
        Sign message with StarkEx ECDSA signature.

        Args:
            message: Message string to sign

        Returns:
            Hex signature string (r + s concatenated, 128 chars)
        """
        # 1. Hash message with SHA3-256
        message_hash = hashlib.sha3_256(message.encode('utf-8')).digest()

        # 2. Convert to integer (field element)
        message_hash_int = int.from_bytes(message_hash, byteorder='big')

        # 3. Reduce modulo FIELD_PRIME
        message_hash_int = message_hash_int % FIELD_PRIME

        # 4. Sign with StarkEx
        r, s = sign(msg_hash=message_hash_int, priv_key=self.private_key_int)

        # 5. Format as hex (64 chars each)
        r_hex = hex(r)[2:].zfill(64)
        s_hex = hex(s)[2:].zfill(64)

        # 6. Concatenate
        signature = r_hex + s_hex

        return signature


# ============================================================================
# EdgeX Authentication
# ============================================================================

class EdgeXAuth:
    """EdgeX API authentication handler."""

    def __init__(self, private_key: str, account_id: str):
        """
        Initialize authentication.

        Args:
            private_key: Stark private key
            account_id: EdgeX account ID
        """
        self.private_key = private_key
        self.account_id = account_id
        self.signer = StarkExSigner(private_key)

    def get_timestamp_ms(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)

    def generate_signature_message(
        self,
        timestamp: int,
        method: str,
        path: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate signature message according to EdgeX spec.

        Format: {timestamp}{METHOD}{path}{sorted_params}

        Example from EdgeX docs:
        1735542383256GET/api/v1/private/account/getPositionTransactionPageaccountId=543429922991899150&filterTypeList=SETTLE_FUNDING_FEE&size=10

        Args:
            timestamp: Timestamp in milliseconds
            method: HTTP method (GET, POST, etc.)
            path: Request path
            params: Query parameters or body

        Returns:
            Signature message string
        """
        # Sort parameters alphabetically
        if params:
            sorted_params = "&".join(
                f"{k}={v}" for k, v in sorted(params.items())
            )
        else:
            sorted_params = ""

        # Construct message: timestamp + METHOD + path + params
        message = f"{timestamp}{method.upper()}{path}{sorted_params}"
        return message

    def sign_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate authentication headers for request.

        Args:
            method: HTTP method
            path: Request path
            params: Query parameters or body

        Returns:
            Dict with authentication headers
        """
        params = params or {}
        timestamp = self.get_timestamp_ms()

        # Generate signature message
        message = self.generate_signature_message(timestamp, method, path, params)

        # Sign message
        signature = self.signer.sign_message(message)

        return {
            EdgeXTestConfig.HEADER_TIMESTAMP: str(timestamp),
            EdgeXTestConfig.HEADER_SIGNATURE: signature
        }


# ============================================================================
# Test Client
# ============================================================================

class EdgeXTestClient:
    """Test client for EdgeX API."""

    def __init__(
        self,
        base_url: str,
        private_key: Optional[str] = None,
        account_id: Optional[str] = None
    ):
        """
        Initialize test client.

        Args:
            base_url: Base API URL
            private_key: Stark private key (optional, for private endpoints)
            account_id: Account ID (optional, for private endpoints)
        """
        self.base_url = base_url
        self.auth = None

        if private_key and account_id:
            self.auth = EdgeXAuth(private_key, account_id)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """
        Make API request.

        Args:
            method: HTTP method
            path: Request path
            params: Query parameters or body
            authenticated: Whether to add authentication headers

        Returns:
            Response JSON
        """
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}

        # Add authentication if required
        if authenticated:
            if not self.auth:
                raise ValueError("Authentication required but no credentials provided")
            auth_headers = self.auth.sign_request(method, path, params)
            headers.update(auth_headers)

        # Make request
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params, headers=headers) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=params, headers=headers) as response:
                    return await response.json()

    async def get_server_time(self) -> Dict[str, Any]:
        """Get server time (public endpoint)."""
        return await self._request("GET", EdgeXTestConfig.SERVER_TIME_PATH)

    async def get_metadata(self) -> Dict[str, Any]:
        """Get exchange metadata (public endpoint)."""
        return await self._request("GET", EdgeXTestConfig.METADATA_PATH)

    async def get_account_asset(self) -> Dict[str, Any]:
        """Get account assets (private endpoint)."""
        params = {"accountId": self.auth.account_id}
        return await self._request(
            "GET",
            EdgeXTestConfig.ACCOUNT_ASSET_PATH,
            params=params,
            authenticated=True
        )

    async def get_position(self, contract_id: str) -> Dict[str, Any]:
        """Get position by contract (private endpoint)."""
        params = {
            "accountId": self.auth.account_id,
            "contractId": contract_id
        }
        return await self._request(
            "GET",
            EdgeXTestConfig.POSITION_BY_CONTRACT_PATH,
            params=params,
            authenticated=True
        )


# ============================================================================
# Test Suite
# ============================================================================

class EdgeXAuthTest:
    """EdgeX authentication test suite."""

    def __init__(self, testnet: bool = False):
        """
        Initialize test suite.

        Args:
            testnet: Whether to use testnet
        """
        self.testnet = testnet
        self.base_url = (
            EdgeXTestConfig.TESTNET_BASE_URL if testnet
            else EdgeXTestConfig.MAINNET_BASE_URL
        )

        # Load credentials
        load_dotenv()
        prefix = "EDGEX_TESTNET_" if testnet else "EDGEX_"
        self.private_key = os.getenv(f"{prefix}PRIVATE_KEY")
        self.account_id = os.getenv(f"{prefix}ACCOUNT_ID")

        self.client = EdgeXTestClient(
            self.base_url,
            self.private_key,
            self.account_id
        )

    def print_header(self, title: str):
        """Print test section header."""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)

    def print_result(self, test_name: str, success: bool, details: str = ""):
        """Print test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status}: {test_name}")
        if details:
            print(f"   {details}")

    async def test_public_endpoints(self):
        """Test public API endpoints (no authentication)."""
        self.print_header("TEST 1: Public API Endpoints (No Authentication)")

        # Test 1.1: Server Time
        print("\n1.1 Testing Server Time Endpoint...")
        try:
            response = await self.client.get_server_time()
            print(f"   Response: {response}")

            if response.get("code") == "SUCCESS":
                data = response.get("data", {})
                server_time = data.get("timeMillis") or data.get("time")
                if server_time:
                    server_time = int(server_time)
                local_time = int(time.time() * 1000)
                time_diff = abs(server_time - local_time) if server_time else 0

                self.print_result(
                    "Server Time",
                    time_diff < 5000,
                    f"Server: {server_time}, Local: {local_time}, Diff: {time_diff}ms"
                )
            else:
                self.print_result("Server Time", False, f"Error: {response}")
        except Exception as e:
            self.print_result("Server Time", False, f"Exception: {e}")

        # Test 1.2: Metadata
        print("\n1.2 Testing Metadata Endpoint...")
        try:
            response = await self.client.get_metadata()
            print(f"   Response keys: {list(response.keys())}")

            if response.get("code") == "SUCCESS":
                data = response.get("data", {})
                contract_count = len(data.get("contractList", []))
                coin_count = len(data.get("coinList", []))

                self.print_result(
                    "Metadata",
                    contract_count > 0,
                    f"Contracts: {contract_count}, Coins: {coin_count}"
                )

                # Show first contract as example
                if contract_count > 0:
                    first_contract = data["contractList"][0]
                    print(f"   Example contract: {first_contract.get('symbol', 'N/A')}")
            else:
                self.print_result("Metadata", False, f"Error: {response}")
        except Exception as e:
            self.print_result("Metadata", False, f"Exception: {e}")

    async def test_authentication(self):
        """Test authentication with private endpoints."""
        self.print_header("TEST 2: Private API Authentication")

        if not self.private_key or not self.account_id:
            print("\n⚠️  SKIPPED: No credentials found")
            print(f"   Set {('EDGEX_TESTNET_' if self.testnet else 'EDGEX_')}PRIVATE_KEY")
            print(f"   Set {('EDGEX_TESTNET_' if self.testnet else 'EDGEX_')}ACCOUNT_ID")
            return

        print(f"\n   Using Account ID: {self.account_id}")
        print(f"   Using Private Key: {self.private_key[:10]}...")

        # Test 2.1: Get Account Assets
        print("\n2.1 Testing Get Account Assets...")
        try:
            response = await self.client.get_account_asset()
            print(f"   Response: {response}")

            if response.get("code") == "SUCCESS":
                self.print_result("Get Account Assets", True, "Authentication successful")

                # Show account data
                data = response.get("data", {})
                print(f"   Account data: {data}")
            else:
                error_msg = response.get("msg", "Unknown error")
                self.print_result("Get Account Assets", False, f"Error: {error_msg}")

                if "signature" in error_msg.lower() or "auth" in error_msg.lower():
                    print("\n   🚨 SIGNATURE ERROR DETECTED!")
                    print("   This confirms we need to implement proper StarkEx signing")
        except Exception as e:
            self.print_result("Get Account Assets", False, f"Exception: {e}")

    async def run_all_tests(self):
        """Run all tests."""
        env_name = "TESTNET" if self.testnet else "MAINNET"
        self.print_header(f"EdgeX Authentication Test Suite ({env_name})")
        print(f"\nBase URL: {self.base_url}")

        # Run tests
        await self.test_public_endpoints()
        await self.test_authentication()

        # Summary
        self.print_header("Test Summary")
        print("\n📋 Next Steps:")
        print("   1. Install StarkEx crypto library:")
        print("      pip install starkex-resources")
        print("\n   2. Update edgex_perpetual_auth.py to use StarkEx signing")
        print("\n   3. Create EdgeX testnet account:")
        print("      - Visit EdgeX exchange testnet")
        print("      - Generate Stark key pair")
        print("      - Get account ID")
        print("\n   4. Re-run tests with real credentials")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Test EdgeX authentication")
    parser.add_argument("--testnet", action="store_true", help="Use testnet")
    args = parser.parse_args()

    test = EdgeXAuthTest(testnet=args.testnet)
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

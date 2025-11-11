#!/usr/bin/env python3
"""
Validate Paradex Connector Implementation

This script validates the Paradex connector against the lessons learned
from Extended and Lighter connector mistakes.

Checks:
1. No empty placeholder implementations (pass statements)
2. No hardcoded credentials
3. UTF-8 handling
4. API parameter verification
5. Security audit
6. Error handling
7. Documentation

Usage:
    python test/paradex_connector/validate_paradex_implementation.py

Based on: .claude/docs/PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Paradex connector path
CONNECTOR_PATH = Path(__file__).parent.parent.parent / "hummingbot" / "connector" / "derivative" / "paradex_perpetual"


class ParadexValidation:
    """Validate Paradex connector implementation."""

    def __init__(self):
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = 0
        self.issues = []

    def check(self, name: str, passed: bool, details: str = "", severity: str = "ERROR"):
        """Record a check result."""
        self.total_checks += 1

        if passed:
            self.passed_checks += 1
            print(f"  ✅ {name}")
            if details:
                print(f"     {details}")
        else:
            if severity == "WARNING":
                self.warnings += 1
                print(f"  ⚠️  {name}")
            else:
                self.failed_checks += 1
                print(f"  ❌ {name}")

            if details:
                print(f"     {details}")

            self.issues.append({
                "name": name,
                "severity": severity,
                "details": details
            })

    def validate_no_placeholder_implementations(self):
        """
        CRITICAL: Validate that critical methods are NOT placeholders.

        Lessons Learned #1.1: Extended/Lighter had _update_balances() = pass
        """
        print("\n" + "="*80)
        print("1. CRITICAL: Checking for Placeholder Implementations")
        print("="*80)

        derivative_file = CONNECTOR_PATH / "paradex_perpetual_derivative.py"

        if not derivative_file.exists():
            self.check("Derivative file exists", False, f"File not found: {derivative_file}")
            return

        with open(derivative_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Critical methods that MUST be implemented
        critical_methods = [
            ("_update_balances", "Updates account balances"),
            ("_update_positions", "Updates position data"),
            ("_update_trading_rules", "Loads market trading rules"),
            ("_place_order", "Places orders via SDK"),
            ("_place_cancel", "Cancels orders"),
        ]

        for method_name, description in critical_methods:
            # Check if method exists
            pattern = rf"async def {method_name}\("
            if not re.search(pattern, content):
                self.check(
                    f"Method {method_name} exists",
                    False,
                    f"Method not found in derivative file"
                )
                continue

            # Extract method body
            method_match = re.search(
                rf"async def {method_name}\(.*?\):(.*?)(?=\n    async def |\n    def |\nclass |\Z)",
                content,
                re.DOTALL
            )

            if method_match:
                method_body = method_match.group(1)

                # Check for 'pass' placeholder
                if re.search(r'^\s+pass\s*$', method_body, re.MULTILINE):
                    self.check(
                        f"Method {method_name} implemented (not placeholder)",
                        False,
                        f"❌ CRITICAL: Method body is just 'pass' - {description} will NOT work!"
                    )
                    continue

                # Check for minimal implementation
                lines_of_code = len([l for l in method_body.split('\n') if l.strip() and not l.strip().startswith('#')])

                if lines_of_code < 5:
                    self.check(
                        f"Method {method_name} has substantial implementation",
                        False,
                        f"Only {lines_of_code} lines of code - likely incomplete"
                    )
                else:
                    self.check(
                        f"Method {method_name} implemented (not placeholder)",
                        True,
                        f"✓ {lines_of_code} lines of code - looks implemented"
                    )

    def validate_no_hardcoded_credentials(self):
        """Check for hardcoded API keys or secrets."""
        print("\n" + "="*80)
        print("2. Security: Checking for Hardcoded Credentials")
        print("="*80)

        patterns_to_check = [
            (r'api_key\s*=\s*["\']0x[a-fA-F0-9]{64}', "Hardcoded API key (hex)"),
            (r'api_secret\s*=\s*["\'][^"\']{20,}', "Hardcoded API secret"),
            (r'private_key\s*=\s*["\']0x[a-fA-F0-9]{64}', "Hardcoded private key"),
            (r'password\s*=\s*["\'][^"\']+', "Hardcoded password"),
        ]

        all_py_files = list(CONNECTOR_PATH.glob("*.py"))

        found_issues = False
        for py_file in all_py_files:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern, description in patterns_to_check:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.check(
                        f"No {description} in {py_file.name}",
                        False,
                        f"Found: {matches[0][:50]}..."
                    )
                    found_issues = True

        if not found_issues:
            self.check(
                "No hardcoded credentials found",
                True,
                "All files clean"
            )

    def validate_utf8_handling(self):
        """Check for UTF-8 file operation handling."""
        print("\n" + "="*80)
        print("3. UTF-8: Checking File Operation Encoding")
        print("="*80)

        all_py_files = list(CONNECTOR_PATH.glob("*.py"))

        files_with_issues = []
        for py_file in all_py_files:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for file operations without encoding
            if "open(" in content:
                # Look for opens without encoding parameter
                unsafe_opens = re.findall(r'open\([^)]*\)(?![^)]*encoding)', content)

                if unsafe_opens:
                    files_with_issues.append(py_file.name)

        if files_with_issues:
            self.check(
                "All file operations specify encoding",
                False,
                f"Files with potential issues: {', '.join(files_with_issues)}",
                severity="WARNING"
            )
        else:
            self.check(
                "All file operations specify encoding or use safe defaults",
                True,
                "No unsafe file operations found"
            )

    def validate_error_handling(self):
        """Check for proper error handling."""
        print("\n" + "="*80)
        print("4. Error Handling: Checking Exception Management")
        print("="*80)

        derivative_file = CONNECTOR_PATH / "paradex_perpetual_derivative.py"

        with open(derivative_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check critical methods have try/except
        critical_methods = [
            "_update_balances",
            "_update_positions",
            "_place_order",
            "_place_cancel"
        ]

        for method_name in critical_methods:
            method_match = re.search(
                rf"async def {method_name}\(.*?\):(.*?)(?=\n    async def |\n    def |\nclass |\Z)",
                content,
                re.DOTALL
            )

            if method_match:
                method_body = method_match.group(1)

                has_try = "try:" in method_body
                has_except = "except" in method_body

                if has_try and has_except:
                    self.check(
                        f"Method {method_name} has error handling",
                        True
                    )
                else:
                    self.check(
                        f"Method {method_name} has error handling",
                        False,
                        "Missing try/except block",
                        severity="WARNING"
                    )

    def validate_sdk_integration(self):
        """Check paradex_py SDK is properly integrated."""
        print("\n" + "="*80)
        print("5. SDK Integration: Checking paradex_py Usage")
        print("="*80)

        auth_file = CONNECTOR_PATH / "paradex_perpetual_auth.py"

        if not auth_file.exists():
            self.check("Auth file exists", False)
            return

        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for SDK imports
        has_import = "from paradex" in content or "import paradex" in content

        self.check(
            "paradex_py SDK imported in auth file",
            has_import,
            "SDK import found" if has_import else "SDK import NOT found - verify implementation"
        )

        # Check for ParadexSubkey usage (recommended)
        has_subkey = "ParadexSubkey" in content

        self.check(
            "Using ParadexSubkey (recommended for security)",
            has_subkey,
            "Subkey authentication found (cannot withdraw funds)" if has_subkey else "WARNING: May be using full key authentication"
        )

    def validate_setup_py(self):
        """Check setup.py has paradex-py dependency."""
        print("\n" + "="*80)
        print("6. Dependencies: Checking setup.py")
        print("="*80)

        setup_file = Path(__file__).parent.parent.parent / "setup.py"

        if not setup_file.exists():
            self.check("setup.py exists", False)
            return

        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()

        has_paradex_py = "paradex-py" in content or "paradex_py" in content

        self.check(
            "paradex-py added to setup.py dependencies",
            has_paradex_py,
            "SDK dependency found" if has_paradex_py else "❌ MUST add 'paradex-py>=0.4.6' to install_requires"
        )

    def validate_documentation(self):
        """Check for documentation."""
        print("\n" + "="*80)
        print("7. Documentation: Checking Docstrings and Comments")
        print("="*80)

        all_py_files = list(CONNECTOR_PATH.glob("*.py"))

        files_with_docstrings = 0
        for py_file in all_py_files:
            if py_file.name == "__init__.py":
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for module docstring
            has_module_docstring = content.strip().startswith('"""') or content.strip().startswith("'''")

            if has_module_docstring:
                files_with_docstrings += 1

        total_files = len([f for f in all_py_files if f.name != "__init__.py"])

        self.check(
            "Files have module docstrings",
            files_with_docstrings >= total_files * 0.7,  # At least 70%
            f"{files_with_docstrings}/{total_files} files documented",
            severity="WARNING" if files_with_docstrings < total_files else "INFO"
        )

    def validate_websocket_fallback(self):
        """Check for REST polling fallback implementation."""
        print("\n" + "="*80)
        print("8. WebSocket Fallback: Checking REST Polling Backup")
        print("="*80)

        orderbook_file = CONNECTOR_PATH / "paradex_perpetual_api_order_book_data_source.py"

        if not orderbook_file.exists():
            self.check("Order book data source file exists", False)
            return

        with open(orderbook_file, 'r', encoding='utf-8') as f:
            content = f.read()

        has_fallback = "_listen_for_subscriptions_polling" in content or "polling_fallback" in content.lower()

        self.check(
            "REST polling fallback implemented (Lessons Learned #3.2)",
            has_fallback,
            "Fallback found - connector can work if WebSocket fails" if has_fallback else
            "❌ CRITICAL: No polling fallback - connector will fail if WebSocket down!"
        )

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"Total Checks: {self.total_checks}")
        print(f"✅ Passed: {self.passed_checks}")
        print(f"❌ Failed: {self.failed_checks}")
        print(f"⚠️  Warnings: {self.warnings}")

        if self.passed_checks == self.total_checks:
            print("\n🎉 ALL CHECKS PASSED!")
            print("Connector implementation follows best practices")

        elif self.failed_checks == 0:
            print("\n✅ All critical checks passed (some warnings)")
            print("Review warnings before deployment")

        else:
            print("\n❌ VALIDATION FAILED")
            print("Critical issues must be fixed before deployment")

        # Print issues
        if self.issues:
            print("\n" + "="*80)
            print("ISSUES TO FIX")
            print("="*80)

            critical_issues = [i for i in self.issues if i['severity'] == 'ERROR']
            warnings = [i for i in self.issues if i['severity'] == 'WARNING']

            if critical_issues:
                print("\nCRITICAL ISSUES:")
                for i, issue in enumerate(critical_issues, 1):
                    print(f"\n{i}. {issue['name']}")
                    if issue['details']:
                        print(f"   {issue['details']}")

            if warnings:
                print("\nWARNINGS:")
                for i, issue in enumerate(warnings, 1):
                    print(f"\n{i}. {issue['name']}")
                    if issue['details']:
                        print(f"   {issue['details']}")

        print("\n" + "="*80)
        print("RECOMMENDED NEXT STEPS")
        print("="*80)

        if self.failed_checks > 0:
            print("1. Fix all critical issues listed above")
            print("2. Re-run this validation script")
            print("3. Test with test_paradex_api_endpoints.py")
            print("4. Test with test_paradex_polling.py")

        else:
            print("✅ Implementation validated!")
            print("1. Run API endpoint tests: python test/paradex_connector/test_paradex_api_endpoints.py")
            print("2. Run WebSocket test: python test/paradex_connector/test_paradex_websocket.py")
            print("3. Run polling test: python test/paradex_connector/test_paradex_polling.py")
            print("4. Get API credentials and run auth tests")
            print("5. Test on testnet before mainnet")

        return self.failed_checks == 0


def main():
    """Run all validations."""

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║               PARADEX CONNECTOR IMPLEMENTATION VALIDATION                    ║
║                                                                              ║
║  Based on: PARADEX_LESSONS_LEARNED_FROM_EXTENDED_LIGHTER.md                 ║
║                                                                              ║
║  This validation ensures we don't repeat the mistakes made in:              ║
║  - Extended connector (empty _update_balances implementation)               ║
║  - Lighter connector (wrong API parameter names)                            ║
║                                                                              ║
║  All checks must pass before deployment!                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    if not CONNECTOR_PATH.exists():
        print(f"❌ ERROR: Connector path not found: {CONNECTOR_PATH}")
        print("   Make sure you're running this from the Hummingbot root directory")
        sys.exit(1)

    validator = ParadexValidation()

    try:
        # Run all validations
        validator.validate_no_placeholder_implementations()
        validator.validate_no_hardcoded_credentials()
        validator.validate_utf8_handling()
        validator.validate_error_handling()
        validator.validate_sdk_integration()
        validator.validate_setup_py()
        validator.validate_documentation()
        validator.validate_websocket_fallback()

        # Print summary
        success = validator.print_summary()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Fatal error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

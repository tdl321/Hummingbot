#!/usr/bin/env python3
"""
Validate Extended Connector in Docker

This script performs end-to-end validation of the Extended connector
configuration and authentication in the Docker environment.
"""

import subprocess
import sys
import time


def run_docker_command(container_name: str, command: str) -> tuple:
    """
    Run a command in Docker container.

    Returns:
        tuple: (success: bool, output: str, error: str)
    """
    try:
        result = subprocess.run(
            ["docker", "exec", container_name, "bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=30
        )
        return (result.returncode == 0, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (False, "", "Command timed out")
    except Exception as e:
        return (False, "", str(e))


def check_docker_container(container_name: str) -> bool:
    """Check if Docker container exists and is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        return container_name in result.stdout
    except:
        return False


def tail_logs(container_name: str, lines: int = 50) -> str:
    """Get recent Hummingbot logs from Docker container."""
    try:
        result = subprocess.run(
            ["docker", "exec", container_name, "tail", "-n", str(lines), "/logs/logs_hummingbot.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.returncode == 0 else ""
    except:
        return ""


def main():
    print("="*80)
    print("EXTENDED CONNECTOR DOCKER VALIDATION")
    print("="*80)

    # Get container name
    print("\nEnter your Docker container name")
    print("(Hint: Run 'docker ps' to see running containers)")
    container_name = input("Container name: ").strip()

    if not container_name:
        print("❌ ERROR: Container name is required")
        return 1

    # Check if container exists and is running
    print("\n" + "="*80)
    print("STEP 1: Checking Docker Container")
    print("="*80)

    if not check_docker_container(container_name):
        print(f"❌ ERROR: Container '{container_name}' not found or not running")
        print("\nAvailable running containers:")
        try:
            result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
            for name in result.stdout.strip().split('\n'):
                if name:
                    print(f"  - {name}")
        except:
            pass
        return 1

    print(f"✅ Container '{container_name}' is running")

    # Check if config file exists in container
    print("\n" + "="*80)
    print("STEP 2: Checking Config File")
    print("="*80)

    success, output, error = run_docker_command(
        container_name,
        "test -f /conf/connectors/extended_perpetual.yml && echo 'EXISTS' || echo 'NOT_FOUND'"
    )

    if "EXISTS" in output:
        print("✅ Extended connector config exists in container")
    else:
        print("❌ ERROR: Extended connector config not found in container")
        print("   Expected location: /conf/connectors/extended_perpetual.yml")
        print("\n   To create config:")
        print(f"   docker exec -it {container_name} bash")
        print("   bin/hummingbot.py")
        print("   connect extended_perpetual")
        return 1

    # Show config content (masked)
    print("\nReading config...")
    success, output, error = run_docker_command(
        container_name,
        "head -n 10 /conf/connectors/extended_perpetual.yml"
    )

    if success:
        print("Config preview (first 10 lines):")
        for line in output.split('\n')[:10]:
            if line.strip():
                # Mask encrypted values
                if any(key in line for key in ['api_key', 'api_secret']):
                    if ':' in line:
                        key_part = line.split(':')[0]
                        print(f"{key_part}: [ENCRYPTED]")
                else:
                    print(line)

    # Check recent logs for 401 errors
    print("\n" + "="*80)
    print("STEP 3: Checking Recent Logs")
    print("="*80)

    print("\nFetching recent logs...")
    logs = tail_logs(container_name, lines=100)

    if logs:
        # Count 401 errors
        error_401_lines = [line for line in logs.split('\n') if '401' in line and 'extended' in line.lower()]
        other_errors = [line for line in logs.split('\n') if 'ERROR' in line and 'extended' in line.lower() and '401' not in line]

        print(f"\nLog analysis (last 100 lines):")
        print(f"  401 Unauthorized errors: {len(error_401_lines)}")
        print(f"  Other Extended errors: {len(other_errors)}")

        if error_401_lines:
            print(f"\n  ❌ Found {len(error_401_lines)} 401 error(s)!")
            print(f"\n  Most recent 401 error:")
            for line in error_401_lines[-3:]:
                print(f"    {line[:120]}")

            print("\n  This indicates API key authentication is still failing.")
            print("  Possible causes:")
            print("    1. Config not updated with correct credentials")
            print("    2. Hummingbot not restarted after config update")
            print("    3. Wrong password used for decryption")
        else:
            print(f"\n  ✅ No 401 errors found in recent logs!")

        if other_errors:
            print(f"\n  ⚠️  Found {len(other_errors)} other error(s):")
            for line in other_errors[-3:]:
                print(f"    {line[:120]}")

    else:
        print("⚠️  Could not fetch logs")

    # Test direct API call from container
    print("\n" + "="*80)
    print("STEP 4: Testing Direct API Call")
    print("="*80)

    print("\nAttempting to read API key from config...")

    # Try to extract and test the API key
    test_script = """
python3 -c "
import yaml
import sys
sys.path.insert(0, '/home/hummingbot')
from hummingbot.client.config.config_crypt import ETHKeyFileSecretManger
import getpass

try:
    with open('/conf/connectors/extended_perpetual.yml', 'r') as f:
        config = yaml.safe_load(f)

    api_key_encrypted = config.get('extended_perpetual_api_key')

    # For security, just check if key exists and is encrypted format
    if api_key_encrypted and len(str(api_key_encrypted)) > 200:
        print('API key found and appears encrypted')
        sys.exit(0)
    else:
        print('API key missing or not encrypted')
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"
"""

    success, output, error = run_docker_command(container_name, test_script)

    if success and "found and appears encrypted" in output:
        print("✅ API key is properly encrypted in config")
    else:
        print("⚠️  Could not verify API key encryption")
        if output:
            print(f"   Output: {output}")
        if error:
            print(f"   Error: {error}")

    # Check if Hummingbot process is running
    print("\n" + "="*80)
    print("STEP 5: Checking Hummingbot Process")
    print("="*80)

    success, output, error = run_docker_command(
        container_name,
        "ps aux | grep -i hummingbot | grep -v grep"
    )

    if output.strip():
        print("✅ Hummingbot process is running")
        print(f"   Process info: {output.strip().split()[0:6]}")
    else:
        print("⚠️  Hummingbot process not running")
        print("   Start Hummingbot:")
        print(f"   docker exec -it {container_name} bin/hummingbot.py")

    # Final summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    print("\nChecklist:")
    print(f"  {'✅' if check_docker_container(container_name) else '❌'} Container running")
    print(f"  {'✅' if 'EXISTS' in output else '❌'} Config file exists")

    has_401_errors = len(error_401_lines) > 0 if logs else None

    if has_401_errors is None:
        print(f"  ⚠️  Could not check for 401 errors")
    elif has_401_errors:
        print(f"  ❌ Still getting 401 errors - auth not fixed")
    else:
        print(f"  ✅ No 401 errors in recent logs")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    if has_401_errors:
        print("\n❌ Extended connector authentication is still failing!")
        print("\nTo fix:")
        print("1. Run fix_extended_config.py on your local machine")
        print("2. Copy updated config to Docker:")
        print(f"   docker cp conf/connectors/extended_perpetual.yml {container_name}:/conf/connectors/")
        print("3. Restart Hummingbot in Docker")
        print("4. Run this validation script again")
        return 1

    elif has_401_errors is False:
        print("\n✅ Extended connector appears to be working correctly!")
        print("\nValidation passed. You can now:")
        print("1. Use Extended connector in your strategies")
        print("2. Monitor logs to ensure continued success")
        print("3. Test with small trades first")
        return 0

    else:
        print("\n⚠️  Unable to fully validate")
        print("\nManual verification needed:")
        print(f"1. Check logs: docker exec {container_name} tail -f /logs/logs_hummingbot.log")
        print("2. Look for Extended connector initialization")
        print("3. Verify no 401 errors appear")
        return 2


if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\nExit code: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

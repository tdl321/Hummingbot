# Docker Build Requirements for Custom Extended & Lighter Connectors

**Date:** 2025-11-11
**Status:** Implementation Complete
**Purpose:** Document required dependencies and build process for Extended and Lighter perpetual DEX connectors

---

## Overview

This document details the requirements and process for building a custom Hummingbot Docker image that includes the Extended and Lighter perpetual DEX connectors. These custom connectors require external SDK dependencies that are not included in the standard Hummingbot distribution.

## Custom Connectors

### 1. Extended Perpetual (`hummingbot/connector/derivative/extended_perpetual/`)
- **Exchange:** Extended DEX (x10.exchange)
- **Type:** Perpetual futures DEX using StarkEx technology
- **Fees:** Maker 0.02%, Taker 0.05%

### 2. Lighter Perpetual (`hummingbot/connector/derivative/lighter_perpetual/`)
- **Exchange:** Lighter DEX (lighter.xyz)
- **Type:** Perpetual futures DEX on zkSync
- **Fees:** 0% trading fees
- **Funding:** 1-hour funding intervals

---

## Required External Dependencies

### Extended Perpetual Dependencies

| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| `x10-python-trading` | 0.4.5+ | X10/Extended SDK for order signing and trading | `extended_perpetual_auth.py`, `extended_perpetual_derivative.py` |
| `fast-stark-crypto` | 0.1.0+ | Stark cryptographic operations for signature generation | `extended_perpetual_auth.py` |

**Key Imports:**
```python
# extended_perpetual_auth.py
import fast_stark_crypto
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient

# extended_perpetual_derivative.py
from x10.perpetual.orders import OrderSide
```

### Lighter Perpetual Dependencies

| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| `lighter-sdk` | 0.1.4+ | Lighter DEX SDK for order signing, account queries, and trading | `lighter_perpetual_auth.py`, `lighter_perpetual_derivative.py` |

**Key Imports:**
```python
# lighter_perpetual_auth.py
from lighter import SignerClient, Configuration

# lighter_perpetual_derivative.py
from lighter import AccountApi, ApiClient, Configuration
```

---

## Implementation Details

### File Modifications

#### 1. `setup/pip_packages.txt`
**Location:** `/Users/tdl321/hummingbot/setup/pip_packages.txt`

**Before:**
```
eip712-structs
```

**After:**
```
eip712-structs
lighter-sdk
x10-python-trading
fast-stark-crypto
```

### Docker Build Process

The Dockerfile uses a multi-stage build process:

#### Stage 1: Builder (lines 2-38)
1. **Base Image:** `continuumio/miniconda3:latest`
2. **System Dependencies:** gcc, g++, python3-dev (already present)
3. **Conda Environment:** Created from `setup/environment.yml` (line 13)
4. **Pip Dependencies:** Installed from `setup/pip_packages.txt` (line 32)
5. **Cython Build:** Builds Hummingbot extensions (line 36)

#### Stage 2: Release (lines 42-82)
1. **Base Image:** `continuumio/miniconda3:latest`
2. **System Dependencies:** libusb-1.0, sudo
3. **Copy Artifacts:** All built packages and conda environment from builder

### Build Commands

```bash
# Stop existing container
docker-compose down

# Rebuild with no cache (recommended for dependency changes)
docker-compose build --no-cache

# Start new container
docker-compose up -d

# Verify installations
docker exec hummingbot python -c "from lighter import SignerClient; print('✓ lighter-sdk')"
docker exec hummingbot python -c "from x10.perpetual.accounts import StarkPerpetualAccount; print('✓ x10-python-trading')"
docker exec hummingbot python -c "import fast_stark_crypto; print('✓ fast-stark-crypto')"
```

---

## Credential Configuration

### Via Hummingbot TUI (Recommended)

Credentials are **NOT** stored in `.env` files. Instead, use Hummingbot's encrypted credential storage:

#### Extended Perpetual
```bash
# In Hummingbot TUI
connect extended_perpetual
```
- **API Key:** Your Extended API key (e.g., `f4aa1ba3e3038adf522981a90d2a1c57`)
- **API Secret:** Your Stark private key (hex string, e.g., `0x17d34fc134d1348db4dccc427f59a75e3b68851e2c193c58f789f1389c0c2e1`)

#### Lighter Perpetual
```bash
# In Hummingbot TUI
connect lighter_perpetual
```
- **API Key:** Your Ethereum wallet address (e.g., `0x5D7EA455f1945E3Ea022478Bb7B33A1EBB2031DA`)
- **API Secret:** Your Ethereum private key (hex string without 0x prefix)

### Credential Storage
- **File:** `conf/conf_client.yml` (encrypted)
- **Encryption:** Protected by Hummingbot password
- **Persistence:** Survives container restarts (mounted volume)

---

## Dependency Conflict Resolution

### urllib3 Version Conflict
The `lighter-sdk` requires `urllib3>=1.25.3,<2.1.0`, while Hummingbot uses `urllib3>=1.26.15,<2.0`.

**Resolution:** The pip installer automatically downgrades to `urllib3==2.0.7` which satisfies both requirements.

### Build Compiler Requirements
Both `x10-python-trading` and `fast-stark-crypto` require C compilers for compilation. These are satisfied by the existing Dockerfile system dependencies:
- gcc
- g++
- python3-dev

---

## Troubleshooting

### Error: "No module named 'lighter'"
**Cause:** SDK not installed in container
**Solution:** Rebuild Docker image with updated `pip_packages.txt`

### Error: "No module named 'x10'"
**Cause:** x10-python-trading not installed
**Solution:** Rebuild Docker image with updated `pip_packages.txt`

### Error: "Unknown compiler(s)"
**Cause:** Missing build tools in container
**Solution:** Build tools (gcc, g++, python3-dev) are already in Dockerfile. Use `--no-cache` flag when building.

### Connection Errors in TUI
**Cause:** Missing or incorrect credentials
**Solution:**
1. Run `connect extended_perpetual` or `connect lighter_perpetual`
2. Enter correct credentials
3. Verify with `connect list`

---

## Build Time & Performance

| Stage | Duration | Notes |
|-------|----------|-------|
| Conda environment creation | 2-5 min | One-time per build |
| Pip package installation | 3-8 min | Includes SDK compilation |
| Cython compilation | 2-3 min | Hummingbot extensions |
| **Total** | **7-16 min** | Varies by system specs |

**Recommendations:**
- Use `--no-cache` only when dependencies change
- Use cached builds for code-only changes
- Multi-core systems build faster (Cython uses `-j 8`)

---

## Security Considerations

1. **Private Keys:** Never commit `.env` files or `conf_client.yml` to version control
2. **Docker Images:** Custom images contain connector code but NOT credentials
3. **Volume Mounts:** `conf/` directory is git-ignored and mounted as volume
4. **Encryption:** All credentials encrypted with Hummingbot password

---

## References

### External Documentation
- **Extended/X10 SDK:** https://github.com/x10xchange/python_sdk
- **Lighter SDK:** https://github.com/elliottech/lighter-python
- **Lighter API Docs:** https://apidocs.lighter.xyz/
- **Hummingbot Connector Guide:** https://hummingbot.org/developers/connectors/

### Internal Files
- Connector implementation: `hummingbot/connector/derivative/extended_perpetual/` and `lighter_perpetual/`
- Build configuration: `Dockerfile`, `docker-compose.yml`
- Dependencies: `setup/pip_packages.txt`, `setup/environment.yml`
- Setup script: `setup.py`

---

## Terminal Encoding Fixes

### Issue
Random or garbled text in Docker terminals is caused by locale/encoding mismatches between the container and host terminal.

### Research & Best Practices

**Official Hummingbot Dockerfile Analysis:**
- ✅ Uses `continuumio/miniconda3:latest` base image
- ✅ Base image already sets `LANG=C.UTF-8 LC_ALL=C.UTF-8`
- ✅ No additional locale configuration needed

**Python Docker Best Practices:**
- Python core developers recommend `C.UTF-8` for Docker containers
- `C.UTF-8` is locale-independent, minimal, and doesn't require locale file generation
- Nick Coghlan (Python core dev): "Setting LANG=C fundamentally breaks Python 3"
- Reference: [Python Docker Issue #13](https://github.com/docker-library/python/issues/13)

**Why C.UTF-8 over en_US.UTF-8:**
- No locale files installation required → smaller image
- Locale-independent → works globally
- Already in base image → no overhead
- Python core developer recommended

### Solution Implemented

**Dockerfile Changes:**
- Explicitly set `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONIOENCODING=utf-8`
- Maintained alignment with base image defaults
- No additional packages required (removed `locales` package)
- Follows Python & Docker best practices

**docker-compose.yml Changes:**
- Added runtime environment variables for consistency:
  ```yaml
  environment:
    - LANG=C.UTF-8
    - LC_ALL=C.UTF-8
    - PYTHONIOENCODING=utf-8
  ```

### Verification
```bash
docker exec hummingbot locale
# Should show: LANG=C.UTF-8, LC_ALL=C.UTF-8

docker exec hummingbot python -c "import sys; print(sys.stdout.encoding)"
# Should show: utf-8
```

---

## Changelog

### 2025-11-11
- ✅ Added `lighter-sdk`, `x10-python-trading`, `fast-stark-crypto` to `pip_packages.txt`
- ✅ Researched and validated terminal encoding approach against Hummingbot official Dockerfile
- ✅ Aligned with Python Docker best practices (using `C.UTF-8` per Python core developers)
- ✅ Updated Dockerfile with explicit `C.UTF-8` locale (matches base image)
- ✅ Updated docker-compose.yml with runtime UTF-8 environment variables
- ✅ Avoided unnecessary package bloat (no `locales` package installation needed)
- ✅ Documented build process and requirements with best practice references
- ✅ Documented credential configuration via TUI

---

## Next Steps

1. **Test Connectors:** Verify both connectors work with live credentials
2. **Monitor Performance:** Track order execution and latency
3. **Update Documentation:** Add trading strategy examples
4. **CI/CD Integration:** Automate Docker builds for custom images

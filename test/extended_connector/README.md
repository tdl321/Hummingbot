# Extended Connector Test & Debug Tools

This directory contains test and debugging tools for the Extended Perpetual connector.

## Test Files

### API & Authentication Tests
- **`test_extended_api_key.py`** - Direct API key validation test
- **`test_extended_auth.py`** - Connector authentication flow test
- **`test_extended_headers.py`** - HTTP header generation test

### Polling & Streaming Tests
- **`test_extended_polling.py`** - REST polling implementation test
- **`test_extended_polling_simple.py`** - Simplified polling test
- **`test_http_streaming.py`** - HTTP streaming (SSE) test

### Encryption Tests
- **`test_encryption_roundtrip.py`** - Encryption/decryption system test

## Debug Tools

### Diagnostic Tools (Read-Only)
- **`debug_config_decryption.py`** - Decrypt and inspect encrypted config
- **`debug_connector_init.py`** - Trace credential flow through connector

### Fix Tools
- **`fix_extended_config.py`** - Update encrypted config with correct credentials
- **`validate_extended_docker.py`** - End-to-end Docker validation

## Usage

### Quick Diagnosis
```bash
# 1. Check what credentials are in encrypted config
python test/extended_connector/debug_config_decryption.py

# 2. Fix if needed
python test/extended_connector/fix_extended_config.py

# 3. Validate in Docker
python test/extended_connector/validate_extended_docker.py
```

### Run Individual Tests
```bash
# Test API key directly
python test/extended_connector/test_extended_api_key.py

# Test connector authentication
python test/extended_connector/test_extended_auth.py

# Test encryption system
python test/extended_connector/test_encryption_roundtrip.py
```

## Documentation

Full documentation is available in `.claude/docs/`:
- `2025-11-11_DEBUG_INDEX.md` - Master index
- `2025-11-11_RUN_DEBUG_TESTS.md` - Step-by-step guide
- `2025-11-11_ENCRYPTION_DEBUG_SUMMARY.md` - Complete analysis
- `2025-11-11_DEBUG_TOOLS_README.md` - Detailed tool docs

## Requirements

- Python 3.10+
- Hummingbot dependencies installed
- `aioprocessing` module
- Valid Hummingbot password (for encryption tests)

## Common Issues

### "Invalid password"
- Ensure you're using the correct Hummingbot password
- Password is case-sensitive

### "ModuleNotFoundError: aioprocessing"
```bash
pip install aioprocessing
```

### "Config file not found"
- Create config first: `connect extended_perpetual` in Hummingbot
- Check path: `conf/connectors/extended_perpetual.yml`

## Support

See documentation in `.claude/docs/` for:
- Troubleshooting tips
- Common scenarios
- Detailed explanations
- Usage examples

---

**Last Updated**: 2025-11-11
**Purpose**: Debug 401 authentication errors in Extended connector

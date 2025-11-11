# Project Documentation Index

This directory contains chronologically organized documentation for the Extended & Lighter DEX connector implementation and funding rate arbitrage strategy development.

---

## Documentation Timeline

### 2025-11-03: Initial Planning
- **2025-11-03_FUNDING_RATE_ARB_BACKTEST_PLAN.md**
  - Initial backtesting strategy planning
  - Data collection requirements
  - Architecture design

### 2025-11-04: Refined Planning
- **2025-11-04_FUNDING_RATE_ARB_BACKTEST_PLAN_V2.md**
  - Updated plan with Extended DEX historical API discovery
  - Modular data source architecture
  - Timeline adjustments (can backtest immediately vs waiting 30 days)

### 2025-11-05: Deployment Guide
- **2025-11-05_FUNDING_ARB_PAPER_TRADE_DEPLOYMENT.md** (1,477 lines)
  - Comprehensive paper trading deployment guide
  - Strategy configuration details
  - Docker setup and troubleshooting
  - Risk management checklist

### 2025-11-07: Connector Implementation
- **2025-11-07_CONNECTOR_SIGNATURE_IMPLEMENTATION_GUIDE.md**
  - Step-by-step guide for implementing order signing
  - Extended: x10 SDK + Stark signatures
  - Lighter: lighter SDK + Ethereum signatures

- **2025-11-07_IMPLEMENTATION_SUMMARY.md**
  - Summary of completed work
  - SDK integration status
  - Files modified
  - Testing status

- **2025-11-07_API_ENDPOINTS_REFERENCE.md**
  - Complete API endpoint documentation
  - Request/response schemas
  - WebSocket message formats
  - Authentication requirements

- **2025-11-07_API_VERIFICATION_SUMMARY.md**
  - API endpoint verification results
  - Extended & Lighter API validation
  - Critical parameters identified
  - SDK verification

- **2025-11-07_API_STATUS_REPORT.md**
  - Live API testing results
  - Token availability check
  - Funding rate endpoint validation
  - Credential verification
  - Ready-for-testing status

- **2025-11-07_SECURITY_AUDIT_REPORT.md**
  - Security audit of connector implementations
  - Balance checking and API validation
  - Critical issues identified and resolved

- **2025-11-07_01_HEALTH_CHECK_REPORT.md**
  - System health check results
  - Connector validation status

- **2025-11-07_02_BALANCE_CHECKING_IMPLEMENTATION.md**
  - Balance checking implementation details
  - API integration verification

- **2025-11-07_03_BALANCE_CHECK_RESULTS.md**
  - Balance check test results
  - Validation outcomes

- **2025-11-07_04_CRITICAL_ISSUE_FOUND.md**
  - Critical issues discovered during testing
  - Resolution steps

- **TESTING_STATUS_2025-11-07.md**
  - Complete testing status summary
  - Automated testing results (syntax validation, code review)
  - Manual testing requirements and checklist
  - Success criteria and expected outcomes
  - Quick start testing guide

- **MANUAL_TESTING_GUIDE_2025-11-07.md**
  - Step-by-step manual testing instructions
  - Phase 1: Connector configuration & balance verification
  - Phase 2: Strategy balance checking
  - Phase 3: Live trading validation
  - Troubleshooting guide and safety reminders
  - Validation checklist

### 2025-11-10: Infrastructure Setup
- **HUMMINGBOT_MCP_SETUP_2025-11-10.md**
  - Complete Hummingbot Model Context Protocol (MCP) server setup guide
  - Claude CLI integration with Docker
  - Docker networking configuration for Mac
  - Environment configuration and troubleshooting
  - Available MCP tools and capabilities
  - Security considerations and best practices

### 2025-11-11: Authentication & Debugging
- **2025-11-11_CONNECTOR_AUTH_FIXES.md**
  - Authentication error fixes for Extended and Lighter connectors
  - Root cause analysis and solutions
  - API parameter corrections

- **2025-11-11_EXTENDED_AUTH_DEBUG_RESULTS.md**
  - Extended connector authentication test results
  - API key validation and header generation tests
  - Conclusion: Connector code is correct, issue is encrypted config

- **2025-11-11_EXTENDED_HTTP_STREAMING_IMPLEMENTATION.md**
  - HTTP streaming (SSE) implementation for Extended connector
  - Server-Sent Events integration
  - Account and orderbook streaming

- **2025-11-11_EXTENDED_REST_POLLING_WORKAROUND.md**
  - REST polling fallback implementation
  - Workaround for streaming endpoint issues
  - Polling intervals and optimization

- **2025-11-11_EXTENDED_STREAMING_ENDPOINTS_NOT_DEPLOYED.md**
  - Analysis of Extended streaming endpoint deployment status
  - DNS resolution issues
  - Recommendation to use REST polling

- **2025-11-11_DEBUG_INDEX.md** ⭐
  - Master index for all debug tools and documentation
  - Quick reference guide
  - Usage scenarios and workflows

- **2025-11-11_DEBUG_TOOLS_README.md**
  - Comprehensive debug tools documentation
  - Tool descriptions and use cases
  - Common scenarios and solutions

- **2025-11-11_ENCRYPTION_DEBUG_SUMMARY.md**
  - Complete encryption/decryption system analysis
  - Root cause identification (wrong credentials in encrypted config)
  - How the encryption system works
  - Fix workflow and expected outcomes

- **2025-11-11_RUN_DEBUG_TESTS.md**
  - Step-by-step guide for running debug tests
  - Test sequence and expected outputs
  - Troubleshooting tips

- **2025-11-11_DOCKER_BUILD_CUSTOM_CONNECTORS.md**
  - Docker build process for custom connectors
  - Dependency management (lighter-sdk, x10-python-trading)
  - Build verification and testing

---

## Quick Reference

### Connector Status
- ✅ Extended Perpetual: Fully implemented with x10 SDK
- ✅ Lighter Perpetual: Fully implemented with lighter SDK
- ✅ Order signing: Complete for both exchanges
- ✅ Funding rates: Accessible on both exchanges

### Strategy Configuration
- **Exchanges**: Extended + Lighter DEX
- **Tokens**: 12 tokens (KAITO, MON, IP, GRASS, ZEC, APT, SUI, TRUMP, LDO, OP, SEI, MEGA)
- **Leverage**: 5x
- **Min Entry Spread**: 0.3%
- **Exit Logic**: Compression-based + time-based + stop-loss

### API Endpoints
- **Extended**: `https://api.starknet.extended.exchange`
- **Lighter**: `https://mainnet.zklighter.elliot.ai`
- **Status**: Both operational (91 Extended markets, 102 Lighter markets)

---

## File Organization

All documentation files are prefixed with their creation date (YYYY-MM-DD) for chronological tracking.

Standard repository files (README, CONTRIBUTING, CODE_OF_CONDUCT, etc.) remain in the root directory.

---

## Infrastructure & Tools

### MCP Server Setup
- **Hummingbot MCP Server**: Enables Claude CLI to interact with Hummingbot for automated trading
- **Transport**: stdio via Docker
- **Docker Image**: `hummingbot/hummingbot-mcp:latest`
- **Configuration**: `/Users/tdl321/mcp/.env`
- **Status**: ✓ Connected to Claude CLI

---

## Test Files

Debug and test tools are located in `/test/extended_connector/`:
- **Diagnostic Tools**: `debug_config_decryption.py`, `debug_connector_init.py`
- **Fix Tools**: `fix_extended_config.py`, `validate_extended_docker.py`
- **API Tests**: `test_extended_api_key.py`, `test_extended_auth.py`, `test_extended_headers.py`
- **Encryption Tests**: `test_encryption_roundtrip.py`
- **Polling Tests**: `test_extended_polling.py`, `test_extended_polling_simple.py`

See `/test/extended_connector/README.md` for usage instructions.

---

**Last Updated**: 2025-11-11

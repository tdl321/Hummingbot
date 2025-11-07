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

**Last Updated**: 2025-11-07

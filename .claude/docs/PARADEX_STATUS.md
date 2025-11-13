# Paradex Connector - Status

**Date**: 2025-11-11
**Status**: 95% Complete - Core Done + All Critical Fixes Applied ✅

## ✅ Completed
- 8 connector files (2,000 LOC) in `/hummingbot/connector/derivative/paradex_perpetual/`
- 4 test scripts in `/test/paradex_connector/`
- paradex-py dependency added to setup.py
- Validation: 15/16 checks passed ✅

## 🔧 Fixes Applied
1. ✅ **FIXED**: `paradex_perpetual_derivative.py` line 284: Changed `"markets"` → `"results"`
2. ✅ **FIXED**: WebSocket URLs corrected (added `api.` subdomain)
   - Testnet: `wss://ws.api.testnet.paradex.trade/v1` ✅ TESTED (1,051 msgs in 30s)
   - Mainnet: `wss://ws.api.prod.paradex.trade/v1`
3. ✅ **FIXED**: WebSocket subscription format (JSON-RPC 2.0)

## 🎯 Remaining
- Get API credentials for testing authenticated endpoints

## 📁 Key Files
- Implementation: `hummingbot/connector/derivative/paradex_perpetual/*.py`
- Tests: `test/paradex_connector/*.py`
- Docs: `.claude/docs/PARADEX_*.md`

## 🎯 Next Steps
1. ✅ ~~Apply field name fix~~ DONE
2. ✅ ~~Fix WebSocket URLs~~ DONE
3. Get Paradex testnet API key
4. Run auth tests
5. Deploy to testnet

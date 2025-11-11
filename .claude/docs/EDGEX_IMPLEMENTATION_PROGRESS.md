# EdgeX Connector Implementation Progress

**Start Date**: 2025-01-15
**Current Phase**: Phase 1 - Project Setup
**Overall Progress**: 15% complete

---

## Completed Work

### ✅ Phase 0: Pre-Implementation (COMPLETE)

**Duration**: 45 minutes
**Status**: ✅ COMPLETE

**Deliverables:**
- [x] API Verification Report created (`.claude/docs/EDGEX_API_VERIFICATION_REPORT.md`)
- [x] Authentication mechanism verified (ECDSA signature-based)
- [x] REST API endpoints documented
- [x] WebSocket channels documented
- [x] Order states mapped to Hummingbot

**Key Findings:**
1. **Authentication**: ECDSA signature per request (NOT JWT like Paradex)
   - Headers: `X-edgeX-Api-Timestamp`, `X-edgeX-Api-Signature`
   - Signature: SHA3(timestamp + method + path + sorted_params) signed with ECDSA

2. **API Style**: RPC-style endpoints (`/getAccountAsset`, `/createOrder`)
   - Different from Paradex's RESTful style
   - Query parameters for GET, JSON body for POST

3. **No Public Python SDK**: Critical difference from Paradex
   - Must implement authentication manually
   - Must implement L2 signature logic
   - More complex implementation required

4. **Order Creation**: Requires L2 StarkEx fields
   - `l2Nonce`, `l2Value`, `l2Size`, `l2LimitFee`, `l2ExpireTime`, `l2Signature`
   - Need to calculate these fields for each order

**Exit Criteria Met:**
- ✅ Authentication mechanism documented
- ✅ REST API endpoints documented
- ✅ WebSocket channels documented
- ✅ Order states mapped

---

### 🔄 Phase 1: Project Setup (IN PROGRESS)

**Duration**: 2-3 hours (estimated)
**Progress**: 50% complete
**Status**: 🔄 IN PROGRESS

**Completed:**
- [x] Created connector directory structure
- [x] Created `__init__.py` with module exports
- [x] Created `edgex_perpetual_constants.py` with all constants
- [x] Created `edgex_perpetual_utils.py` with config schema

**Remaining:**
- [ ] Create `edgex_perpetual_auth.py` (skeleton)
- [ ] Create `edgex_perpetual_web_utils.py` (skeleton)
- [ ] Create `edgex_perpetual_derivative.py` (skeleton)
- [ ] Create `edgex_perpetual_api_order_book_data_source.py` (skeleton)
- [ ] Create `edgex_perpetual_user_stream_data_source.py` (skeleton)

**Files Created:**
1. `/hummingbot/connector/derivative/edgex_perpetual/__init__.py`
2. `/hummingbot/connector/derivative/edgex_perpetual/edgex_perpetual_constants.py`
3. `/hummingbot/connector/derivative/edgex_perpetual/edgex_perpetual_utils.py`

**Key Implementation Notes:**

#### Constants File (`edgex_perpetual_constants.py`)
- All endpoints verified from EdgeX API documentation
- Rate limits conservative (20 req/sec, 1200 req/min) pending verification
- Order state mapping: EdgeX status → Hummingbot OrderState
- WebSocket channels documented for both public and private
- Authentication headers defined: `X-edgeX-Api-Timestamp`, `X-edgeX-Api-Signature`
- L2 order fields constants added for StarkEx integration

#### Utils File (`edgex_perpetual_utils.py`)
- Configuration schema using Pydantic BaseConnectorConfigMap
- Mainnet and testnet configurations
- Required credentials:
  - `edgex_perpetual_api_secret` (private key)
  - `edgex_perpetual_account_id` (account identifier)
- Fee structure defined (0.02% maker, 0.05% taker - pending verification)
- Helper functions for trading pair conversion (TODO: implement after metadata API testing)

---

## Next Steps

### Phase 1 Remaining Tasks

1. **Create auth skeleton** (`edgex_perpetual_auth.py`):
   - Class structure with method signatures
   - TODO comments for signature generation
   - Placeholder for ECDSA signing

2. **Create web utils skeleton** (`edgex_perpetual_web_utils.py`):
   - API factory creation
   - Throttler setup
   - URL building functions

3. **Create derivative skeleton** (`edgex_perpetual_derivative.py`):
   - Class inheriting from `PerpetualDerivativePyBase`
   - All abstract method signatures
   - TODO comments for each method

4. **Create data source skeletons**:
   - Order book data source class structure
   - User stream data source class structure

5. **Phase 1 Exit Criteria Verification**:
   - All 8 files created
   - No import errors
   - Can instantiate connector class (even if methods not implemented)

### Phase 2 Preview: Authentication Layer

**Challenges Identified:**
1. **No SDK Available**: Must implement ECDSA signature generation manually
2. **StarkEx L2 Fields**: Must calculate L2-specific order fields
3. **Signature Algorithm**: SHA3 hashing + ECDSA signing
4. **Research Needed**: StarkEx documentation for L2 field calculation

**Potential Solutions:**
- Use `eth_account` library for ECDSA signing
- Use `hashlib` or `Crypto.Hash` for SHA3
- Research StarkEx L2 nonce, value, size calculations
- May need `starknet.py` library for L2-specific functions

---

## Critical Reminders from Lessons Learned

### ⚠️ Top 5 Mistakes to Avoid

1. **Empty Placeholder Implementations** (Mistake #1)
   - DO NOT deploy with `pass` in critical methods
   - Fully implement `_update_balances()`, `_update_positions()`, etc.
   - Test each method before moving to next phase

2. **Wrong API Parameter Names** (Mistake #2.1)
   - Use EXACT parameter names from API verification
   - Test each endpoint with curl before full integration
   - Save example responses for reference

3. **Invalid API Keys in Config** (Mistake #2.2)
   - Test API key independently before encryption
   - Verify authentication works before full integration
   - Clear error messages for authentication failures

4. **Assuming Undocumented Endpoints Exist** (Mistake #3.1)
   - Only use endpoints verified in Phase 0
   - Mark TODO items for unverified endpoints
   - Implement REST fallback for critical features

5. **UTF-8 Mode Not Enabled** (Mistake #4.1)
   - Add `PYTHONUTF8=1` to Dockerfile in Phase 6
   - Use `encoding='utf-8'` in all file operations
   - Test in Docker environment before deployment

---

## Implementation Timeline

| Phase | Duration | Progress | Status |
|-------|----------|----------|--------|
| Phase 0: Pre-Implementation | 0.5-0.75 hours | 100% | ✅ COMPLETE |
| Phase 1: Project Setup | 2-3 hours | 50% | 🔄 IN PROGRESS |
| Phase 2: Authentication | 3-4 hours | 0% | ⏳ PENDING |
| Phase 3: Core Connector | 8-10 hours | 0% | ⏳ PENDING |
| Phase 4: Data Sources | 6-8 hours | 0% | ⏳ PENDING |
| Phase 5: Testing | 4-6 hours | 0% | ⏳ PENDING |
| Phase 6: QA & Deployment | 2-3 hours | 0% | ⏳ PENDING |
| **TOTAL** | **26-34 hours** | **15%** | |

**Time Spent**: ~1.5 hours
**Time Remaining**: ~24.5-32.5 hours

---

## Open Questions & TODOs

### High Priority
1. [ ] **EdgeX Base URL**: Verify production API base URL (currently assumed: `https://api.edgex.exchange`)
2. [ ] **Testnet URL**: Find testnet API URL
3. [ ] **Fee Structure**: Verify actual maker/taker fees from metadata API
4. [ ] **Contract ID Mapping**: Understand metadata API response structure for trading pair conversion
5. [ ] **L2 Field Calculation**: Research StarkEx documentation for order field calculation

### Medium Priority
1. [ ] **Private WebSocket Channels**: Verify exact channel names and authentication method
2. [ ] **Funding Rate Endpoint**: Determine exact endpoint for funding rate data
3. [ ] **Rate Limits**: Test actual rate limits and update constants
4. [ ] **Position Mode**: Verify if EdgeX supports hedge mode vs one-way mode
5. [ ] **Leverage Setting**: Determine how to set leverage per contract

### Low Priority
1. [ ] **Asset API Endpoints**: Document specific asset management endpoints
2. [ ] **Transfer API Endpoints**: Document specific transfer endpoints
3. [ ] **Withdraw API Endpoints**: Document specific withdrawal endpoints

---

## Risk Assessment

### High Risk Items
1. **L2 Signature Implementation**: No SDK means complex custom implementation
   - **Mitigation**: Research StarkEx docs, reference other StarkEx DEX implementations
   - **Fallback**: Consider reaching out to EdgeX team for SDK or examples

2. **Authentication Complexity**: Per-request signatures more complex than JWT
   - **Mitigation**: Implement caching where possible, test thoroughly
   - **Fallback**: Reference Paradex implementation for patterns

3. **Trading Pair Conversion**: Need metadata API to map contractId ↔ symbol
   - **Mitigation**: Fetch and cache metadata at startup
   - **Fallback**: Manual mapping table if API structure unclear

### Medium Risk Items
1. **WebSocket Private Channels**: Not fully documented
   - **Mitigation**: Test with live connection, capture message formats
   - **Fallback**: REST API polling for user data

2. **Order Creation L2 Fields**: Complex StarkEx requirements
   - **Mitigation**: Study StarkEx documentation, test on testnet
   - **Fallback**: Simplify to basic order types first

---

## Success Metrics

### Phase 1 Exit Criteria
- [ ] All 8 connector files created
- [ ] No Python import errors
- [ ] Constants file has all verified endpoints
- [ ] Configuration schema complete
- [ ] Code review confirms structure matches Paradex pattern

### Overall Success Criteria (End of Phase 6)
- [ ] Balance fetch returns real data (NOT $0)
- [ ] Position fetch works correctly
- [ ] Orders can be placed and cancelled
- [ ] WebSocket stable for 1+ hour
- [ ] All integration tests pass
- [ ] Security audit passed
- [ ] Testnet validation complete (24+ hours)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Next Update**: After Phase 1 completion

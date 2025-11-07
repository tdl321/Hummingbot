# Funding Rate Arbitrage Backtest System - Strategic Plan V2

**Date**: 2025-11-04 (Updated)
**Status**: Phases 1-3 Complete, Phase 4 In Progress

---

## 📝 Change Log from V1

### **Major Discovery**
✅ **Extended DEX provides historical funding rate API** with time-range parameters
- Can download 30-90 days of data immediately
- No need to wait for data collection
- Can backtest TODAY instead of in 30 days

### **Architecture Change**
- **V1**: Poll CoinGecko hourly → Build dataset over 30 days
- **V2**: Download Extended historical → Backtest immediately + Optional ongoing CoinGecko collection

### **Components Updated**
- ✅ Component 1: Modular data source interface
- ✅ Component 2: Multi-source collector (works with any source)
- ✅ Component 3: Source-agnostic backtest provider
- ⏸️ Component 4: Strategy adapter (next)

---

## 🎯 Revised Overview

Build a modular funding rate arbitrage backtesting system that:
1. **Downloads historical data** from Extended DEX API (30-90 days instantly)
2. **Optionally collects ongoing data** from CoinGecko (aggregates both exchanges)
3. **Stores in unified format** (parquet files)
4. **Provides time-series access** for backtesting
5. **Enables strategy validation** and optimization

**Tokens**: 10 available on both exchanges (KAITO, IP, GRASS, ZEC, APT, SUI, TRUMP, LDO, OP, SEI)
**Exchanges**: Extended, Lighter (via Extended API or CoinGecko aggregation)
**Data Sources**: Extended API (historical), CoinGecko API (real-time aggregation)

---

## 🏗️ Updated Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCE LAYER (Modular)                   │
├─────────────────────────────────────────────────────────────────┤
│  BaseFundingDataSource (Abstract Interface)                      │
│    ├─→ ExtendedFundingDataSource (historical bulk download)      │
│    ├─→ CoinGeckoFundingDataSource (real-time aggregation)        │
│    └─→ LighterFundingDataSource (future)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│               COLLECTION & STORAGE LAYER (Unified)               │
├─────────────────────────────────────────────────────────────────┤
│  FundingRateCollector (accepts any BaseFundingDataSource)        │
│    ↓                                                              │
│  Parquet Storage (app/data/cache/funding/raw/)                   │
│    - Extended historical: 2025-10-*.parquet                       │
│    - CoinGecko ongoing: 2025-11-*.parquet                         │
│    - Unified format regardless of source                          │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│              BACKTEST DATA PROVIDER (Source-Agnostic)            │
├─────────────────────────────────────────────────────────────────┤
│  FundingRateBacktestDataProvider                                 │
│    - Loads all parquet files (any source)                        │
│    - Time-based queries                                          │
│    - Spread calculations                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                  BACKTESTING ENGINE (Future)                     │
├─────────────────────────────────────────────────────────────────┤
│  FundingArbBacktestStrategy                                      │
│    - Position simulation                                         │
│    - Funding payment tracking                                    │
│    - PNL calculation                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Status & Details

### **Component 0: Base Data Source Interface** ✅ DESIGNED

**File**: `/Users/tdl321/quants-lab/core/data_sources/base_funding_source.py`
**Status**: ⏸️ Not Yet Implemented

**Purpose**: Abstract interface ensuring all data sources are compatible

**Key Methods**:
```python
class BaseFundingDataSource(ABC):
    @abstractmethod
    async def start()
    @abstractmethod
    async def stop()
    @abstractmethod
    async def get_funding_rates(exchange, tokens) -> DataFrame
    @abstractmethod
    async def get_funding_rates_multi_exchange(exchanges, tokens) -> DataFrame
    def calculate_spreads(funding_df) -> DataFrame  # Shared implementation
```

**Effort**: 30 minutes
**Priority**: HIGH (needed for modular design)

---

### **Component 1: CoinGecko Data Source** ✅ COMPLETE

**File**: `/Users/tdl321/quants-lab/core/data_sources/coingecko_funding.py`
**Status**: ✅ Complete and Tested

**What Changed**:
- Minor update needed to inherit from `BaseFundingDataSource`
- Logic stays exactly the same

**Features**:
- ✅ Demo API authentication (query parameter)
- ✅ Fetches current funding rates
- ✅ Aggregates Lighter + Extended
- ✅ Rate limiting with sequential requests
- ✅ Spread calculation

**Use Case**: Ongoing real-time collection (aggregates both DEXs)

---

### **Component 1b: Extended Data Source** ⏸️ DESIGNED

**File**: `/Users/tdl321/quants-lab/core/data_sources/extended_funding.py`
**Status**: ⏸️ Not Yet Implemented

**Purpose**: Fetch historical + current funding rates from Extended API

**Key Features**:
- Historical data with time range (`startTime`, `endTime`)
- Up to 10,000 records per request
- Pagination support
- Bulk download method for initial backfill

**Key Endpoint**:
```
GET /api/v1/info/{market}/funding?startTime={start}&endTime={end}
```

**Key Method**:
```python
async def bulk_download_historical(
    tokens: List[str],
    days: int = 30,
    quote: str = "USD"
) -> DataFrame
```

**Effort**: 2 hours
**Priority**: HIGH (enables immediate backtesting)

**Use Case**:
- One-time: Bulk download 30-90 days of historical data
- Optional: Ongoing direct collection from Extended

---

### **Component 1c: Lighter Data Source** ⏸️ FUTURE

**File**: `/Users/tdl321/quants-lab/core/data_sources/lighter_funding.py`
**Status**: ⏸️ Future Work

**Purpose**: Direct Lighter API access (if historical data available)

**Effort**: 2 hours (when needed)
**Priority**: LOW (CoinGecko aggregates Lighter already)

---

### **Component 2: Data Collector** ✅ COMPLETE (Needs Minor Update)

**File**: `/Users/tdl321/quants-lab/core/data_sources/funding_rate_collector.py`
**Status**: ✅ Complete, ⚠️ Minor Update Needed

**What Changed**:
- Accept `BaseFundingDataSource` instead of hardcoded `CoinGeckoFundingDataSource`
- Rest of logic unchanged

**Update**:
```python
def __init__(
    self,
    data_source: BaseFundingDataSource,  # ← Accept any source
    ...
)
```

**Effort**: 5 minutes
**Features**: All existing features work unchanged

---

### **Component 3: Backtest Data Provider** ✅ COMPLETE

**File**: `/Users/tdl321/quants-lab/core/backtesting/funding_rate_data_provider.py`
**Status**: ✅ Complete and Tested

**What Changed**: NOTHING - already source-agnostic!

**Features**:
- ✅ Loads parquet files (any source)
- ✅ Time-based queries
- ✅ Spread calculations
- ✅ Best opportunity detection
- ✅ Data quality validation

**Testing**: ✅ Validated with 17 records, found 6 arbitrage opportunities

---

### **Component 4: Backtesting Strategy Adapter** ⏸️ NOT STARTED

**File**: `/Users/tdl321/quants-lab/core/backtesting/funding_arb_strategy.py`
**Status**: ⏸️ Not Yet Implemented

**Purpose**: Simulate v2_funding_rate_arb strategy execution

**Key Features**:
- Position opening/closing simulation
- Funding payment tracking
- PNL calculation (trading fees + funding)
- Delta neutrality validation

**Effort**: 4-6 hours
**Priority**: MEDIUM (can manually analyze data first)

---

### **Component 5: Data Collection Notebook** ✅ COMPLETE

**File**: `/Users/tdl321/quants-lab/research_notebooks/data_collection/download_funding_rates_coingecko.ipynb`
**Status**: ✅ Complete

**What Changed**: Nothing - still useful for CoinGecko collection

**Use Case**: Interactive ongoing data collection from CoinGecko

---

### **Component 6: Backtesting Notebook** ⏸️ NOT STARTED

**File**: `/Users/tdl321/quants-lab/research_notebooks/eda_strategies/funding_rate_arb/01_backtest_funding_rate_arb.ipynb`
**Status**: ⏸️ Not Yet Created

**Purpose**: Run backtests and analyze results

**Sections** (Planned):
1. Load historical data from Extended
2. Configure strategy parameters
3. Run backtest simulation
4. Analyze PNL and metrics
5. Visualize results
6. Parameter optimization

**Effort**: 3-4 hours
**Priority**: HIGH (needed for analysis)

---

## 🔄 Revised Implementation Workflow

### **Phase 1: Foundation** ✅ COMPLETE
1. ✅ Create directory structure
2. ✅ Build `CoinGeckoFundingDataSource` class
3. ✅ Build `FundingRateCollector` class
4. ✅ Build `FundingRateBacktestDataProvider` class
5. ✅ Test API connectivity
6. ✅ Validate exchange IDs and token availability

**Duration**: 4 hours
**Result**: Working CoinGecko-based collection system

---

### **Phase 2: Data Collection Testing** ✅ COMPLETE
1. ✅ Create data collection notebook
2. ✅ Set up storage structure
3. ✅ Run test collection (17 records)
4. ✅ Validate data quality (100% completeness)
5. ✅ Test backtest data provider
6. ✅ Identify arbitrage opportunities (KAITO: 1.6% spread, 140% APR)

**Duration**: 2 hours
**Result**: Validated end-to-end pipeline with sample data

---

### **Phase 3: API Research & Planning** ✅ COMPLETE
1. ✅ Research CoinGecko historical capabilities (not available)
2. ✅ Discover Extended API historical endpoints (available!)
3. ✅ Design modular data source architecture
4. ✅ Create implementation plan
5. ✅ Update strategic plan (this document)

**Duration**: 2 hours
**Result**: Clear path to 30-90 days of historical data

---

### **Phase 4: Modular Data Sources** ⏸️ IN PROGRESS
1. ⏸️ Create `BaseFundingDataSource` interface (30 min)
2. ⏸️ Update `CoinGeckoFundingDataSource` to inherit (15 min)
3. ⏸️ Update `FundingRateCollector` to accept base (5 min)
4. ⏸️ Create `ExtendedFundingDataSource` class (2 hours)
5. ⏸️ Test Extended API connectivity (15 min)

**Duration**: 3 hours
**Priority**: HIGH
**Blocker**: None
**Next Step**: Create base interface

---

### **Phase 5: Historical Data Download** ⏸️ NOT STARTED
1. ⏸️ Query Extended markets to map token symbols (15 min)
2. ⏸️ Test download 7 days for 1 token (15 min)
3. ⏸️ Bulk download 30-90 days for 10 tokens (30 min)
4. ⏸️ Validate and save to parquet (15 min)
5. ⏸️ Load in BacktestDataProvider and verify (15 min)

**Duration**: 1.5 hours
**Priority**: HIGH
**Blocker**: Needs Phase 4 complete
**Deliverable**: 30-90 days of backtest-ready data

---

### **Phase 6: Backtesting** ⏸️ NOT STARTED
1. ⏸️ Create backtesting notebook (2 hours)
2. ⏸️ Manual PNL analysis of historical opportunities (1 hour)
3. ⏸️ Build strategy simulator (4 hours) - OR -
4. ⏸️ Parameter optimization analysis (2 hours)
5. ⏸️ Generate performance reports (1 hour)

**Duration**: 6-10 hours (depending on approach)
**Priority**: MEDIUM
**Blocker**: Needs Phase 5 complete (historical data)

---

## 📊 Data Collection Strategy (Revised)

### **Option 1: Extended Historical + CoinGecko Ongoing** ✅ RECOMMENDED

**Historical Backfill**:
```python
Duration: Instant (download existing data)
Source: Extended API
Time Range: Last 30-90 days
Records: ~2,160 per token (90 days × 24 hours)
Total: ~21,600 records for 10 tokens
Cost: Free (public API)
```

**Ongoing Collection**:
```python
Duration: Continuous
Source: CoinGecko API
Interval: 60 minutes (hourly)
Purpose: Keep data current + aggregate both exchanges
Cost: Free (Demo API key)
```

**Benefits**:
- ✅ Immediate historical data (don't wait 30 days)
- ✅ Proven CoinGecko collection works
- ✅ Redundancy (multiple sources)
- ✅ Best of both worlds

---

### **Option 2: Extended Only**

**All Data from Extended**:
```python
Historical: Bulk download 30-90 days
Ongoing: Poll Extended API hourly
```

**Benefits**:
- ✅ Single data source (simpler)
- ✅ Direct from exchange (no aggregator)

**Drawbacks**:
- ❌ Only Extended data (no Lighter comparison)
- ❌ More implementation work

---

### **Option 3: Hybrid Multi-Source** (Future)

**Extended + Lighter + CoinGecko**:
```python
Extended: Historical + current
Lighter: Historical + current
CoinGecko: Validation/reconciliation
```

**Benefits**:
- ✅ Most comprehensive
- ✅ Cross-validation

**Drawbacks**:
- ❌ Complex
- ❌ Overkill for now

**Recommendation**: Start with Option 1, evolve to Option 3 if needed

---

## 📁 Updated File Structure

```
/Users/tdl321/quants-lab/
├── core/
│   ├── data_sources/
│   │   ├── base_funding_source.py          ← NEW (Phase 4)
│   │   ├── coingecko_funding.py            ← ✅ COMPLETE (minor update Phase 4)
│   │   ├── extended_funding.py             ← NEW (Phase 4)
│   │   ├── lighter_funding.py              ← FUTURE
│   │   └── funding_rate_collector.py       ← ✅ COMPLETE (minor update Phase 4)
│   │
│   └── backtesting/
│       ├── funding_rate_data_provider.py   ← ✅ COMPLETE
│       └── funding_arb_strategy.py         ← NOT STARTED (Phase 6)
│
├── scripts/
│   ├── download_extended_historical.py     ← NEW (Phase 5)
│   ├── final_collection_test.py            ← ✅ COMPLETE
│   └── test_backtest_provider.py           ← ✅ COMPLETE
│
├── research_notebooks/
│   ├── data_collection/
│   │   └── download_funding_rates_coingecko.ipynb  ← ✅ COMPLETE
│   │
│   └── eda_strategies/funding_rate_arb/
│       └── 01_backtest_funding_rate_arb.ipynb      ← NOT STARTED (Phase 6)
│
└── app/data/cache/funding/
    ├── raw/
    │   ├── 2025-10-*.parquet               ← Extended historical (Phase 5)
    │   └── 2025-11-*.parquet               ← CoinGecko ongoing
    ├── processed/                           ← Future
    └── metadata.json                        ← ✅ Working
```

---

## ✅ Updated Validation Checklist

### **1. API Access**
   - [x] CoinGecko Demo API key working
   - [x] CoinGecko derivatives endpoints accessible
   - [ ] Extended API accessible (need to test)
   - [ ] Extended markets endpoint working
   - [ ] Extended funding endpoint working

### **2. Exchange & Token Availability**
   - [x] Extended on CoinGecko ✅
   - [x] Lighter on CoinGecko ✅
   - [x] 10 tokens on both exchanges ✅
   - [ ] Map tokens to Extended market IDs
   - [ ] Verify Extended has historical data for our tokens

### **3. Data Quality**
   - [x] CoinGecko funding rates correct format ✅
   - [x] Timestamps consistent ✅
   - [ ] Extended funding rates correct format
   - [ ] Extended historical data complete
   - [ ] Data from both sources compatible

### **4. System Validation**
   - [x] CoinGecko collection works ✅
   - [x] Storage system works ✅
   - [x] Backtest provider works ✅
   - [ ] Extended download works
   - [ ] Merged data loads correctly
   - [ ] Backtest runs successfully

---

## 🎯 Success Metrics

### **Phase Completion**
- [x] Phase 1: Foundation ✅
- [x] Phase 2: Data Collection Testing ✅
- [x] Phase 3: API Research ✅
- [ ] Phase 4: Modular Sources (50% - planned but not implemented)
- [ ] Phase 5: Historical Download (0%)
- [ ] Phase 6: Backtesting (0%)

### **Data Availability**
- [x] Sample data: 17 records ✅
- [ ] Historical data: 30-90 days
- [ ] Ongoing data: Continuous collection

### **Arbitrage Opportunities**
- [x] Identified in sample: 6 opportunities ✅
- [x] Best spread: KAITO 1.6% = 140% APR ✅
- [ ] Validated over 30+ days
- [ ] Backtested with realistic execution

---

## 📊 Timeline Estimate

| Phase | Status | Duration | Total Hours |
|-------|--------|----------|-------------|
| 1. Foundation | ✅ Complete | 4 hours | 4 |
| 2. Collection Testing | ✅ Complete | 2 hours | 6 |
| 3. API Research | ✅ Complete | 2 hours | 8 |
| 4. Modular Sources | ⏸️ Next | 3 hours | 11 |
| 5. Historical Download | ⏸️ Pending | 1.5 hours | 12.5 |
| 6. Backtesting | ⏸️ Pending | 6-10 hours | 18.5-22.5 |
| **TOTAL TO BACKTEST** | - | **12.5 hours** | - |
| **TOTAL WITH SIMULATOR** | - | **18.5-22.5 hours** | - |

**Current Progress**: 8 hours / ~20 hours total = **40% complete**

**To Backtest**: 4.5 hours remaining (Phases 4-5)

---

## 🚀 Next Immediate Steps

### **Right Now** (Phase 4):
1. Create `BaseFundingDataSource` abstract interface
2. Update `CoinGeckoFundingDataSource` to inherit from base
3. Update `FundingRateCollector` to accept base class
4. Create `ExtendedFundingDataSource` class
5. Test Extended API connectivity

**Duration**: 3 hours
**Blocker**: None - can start immediately

### **After Phase 4** (Phase 5):
1. Download 30-90 days of Extended historical data
2. Validate and merge with existing storage
3. Load in backtest provider
4. Manual analysis of opportunities

**Duration**: 1.5 hours
**Blocker**: Phase 4

### **After Phase 5** (Phase 6 - Choose One):

**Option A**: Manual Analysis First (Faster)
- Analyze historical opportunities without simulator
- Calculate theoretical PNL
- Validate strategy parameters
- **Duration**: 2-3 hours

**Option B**: Full Simulator (More Robust)
- Build position execution simulator
- Track funding payments over time
- Calculate realized PNL with fees
- **Duration**: 6-10 hours

---

## 📝 Key Learnings & Changes from V1

1. **Don't wait for data** - Extended API has historical data ✅
2. **Modular design** - Easy to add sources ✅
3. **Reuse infrastructure** - Collector/Provider unchanged ✅
4. **Multiple sources** - CoinGecko + Extended = best coverage ✅
5. **Start simple** - Manual analysis before building simulator ✅

---

**Last Updated**: 2025-11-04
**Next Review**: After Phase 4 completion
**Version**: 2.0


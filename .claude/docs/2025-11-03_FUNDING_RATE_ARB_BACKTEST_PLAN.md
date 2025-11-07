# OPTION A: CoinGecko Data Source for Backtesting - Implementation Plan

## Overview

Build a complete CoinGecko-based data collection and backtesting system that:
1. Fetches funding rate data from CoinGecko API
2. Stores historical data locally for backtesting
3. Integrates with quants-lab backtesting engine
4. Enables parameter optimization and strategy validation

**Tokens:** KAITO, MON, IP, GRASS, ZEC, APT, SUI, TRUMP, LDO, OP, SEI, MEGA, YZY (13 total)
**Exchanges:** Extended, Lighter, Variational (Perp DEXs)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKTESTING PIPELINE                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  1. DATA COLLECTION (CoinGecko API)                         │
│     - CoinGeckoDataSource class                             │
│     - Fetch funding rates for Extended/Lighter/Variational  │
│     - Poll every 2-60 minutes                               │
│     - Store raw data to CSV                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. DATA PROCESSING & CACHING                               │
│     - Clean and normalize data                              │
│     - Calculate spreads between exchanges                   │
│     - Store in quants-lab cache format                      │
│     - Path: app/data/cache/funding/                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. BACKTEST DATA PROVIDER                                  │
│     - FundingRateBacktestDataProvider class                 │
│     - Load cached funding data                              │
│     - Provide time-series funding rates                     │
│     - Interface with BacktestingEngine                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. STRATEGY BACKTESTING                                    │
│     - Modified v2_funding_rate_arb for backtest mode        │
│     - Simulated position execution                          │
│     - Track funding payments over time                      │
│     - Generate performance metrics                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. ANALYSIS & VISUALIZATION                                │
│     - Jupyter notebooks for analysis                        │
│     - PNL charts, spread analysis                           │
│     - Parameter optimization                                │
│     - Export results                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Breakdown

### **Component 1: CoinGecko Data Source**

**Location:** `/Users/tdl321/quants-lab/core/data_sources/coingecko_funding.py`

**Purpose:** Interface with CoinGecko API to fetch funding rate data

**Key Features:**
- Async API calls with rate limiting
- Multi-exchange support (Extended, Lighter, Variational)
- Token filtering
- Error handling and retries
- Session management

**Methods:**
```python
class CoinGeckoFundingDataSource:
    - __init__(api_key)
    - get_exchange_list() -> List[str]
    - get_funding_rates(exchange_id, tokens) -> pd.DataFrame
    - get_funding_rates_multi_exchange(exchanges, tokens) -> pd.DataFrame
    - collect_funding_snapshot() -> pd.DataFrame
    - validate_exchange_availability(exchange_id) -> bool
```

**Data Schema:**
```python
{
    'timestamp': int,           # Unix timestamp
    'exchange': str,            # 'extended', 'lighter', 'variational'
    'token': str,               # 'KAITO', 'MON', etc.
    'funding_rate': float,      # Hourly funding rate
    'funding_rate_8h': float,   # Normalized to 8h (for Extended)
    'index_price': float,       # Index/reference price
    'mark_price': float,        # Mark price for PNL calculation
    'next_funding_time': int,   # Timestamp of next funding payment
    'contract_type': str        # 'perpetual'
}
```

---

### **Component 2: Data Collection System**

**Location:** `/Users/tdl321/quants-lab/core/data_sources/funding_rate_collector.py`

**Purpose:** Automated collection and storage of historical funding data

**Key Features:**
- Scheduled polling (configurable interval)
- Data persistence to CSV/Parquet
- Incremental updates (append new data)
- Data validation and cleaning
- Cache management

**Methods:**
```python
class FundingRateCollector:
    - __init__(coingecko_source, storage_path)
    - start_collection(duration_hours, interval_minutes)
    - collect_single_snapshot() -> pd.DataFrame
    - save_snapshot(data, append=True)
    - load_historical_data(start_date, end_date) -> pd.DataFrame
    - calculate_spreads(data) -> pd.DataFrame
    - validate_data_quality(data) -> bool
```

**Storage Structure:**
```
/Users/tdl321/quants-lab/app/data/cache/funding/
├── raw/
│   ├── 2024-11-01.parquet      # Daily raw data
│   ├── 2024-11-02.parquet
│   └── ...
├── processed/
│   ├── spreads_2024-11.parquet  # Monthly spread data
│   └── metrics_2024-11.parquet  # Calculated metrics
└── metadata.json                # Collection metadata
```

**Metadata Schema:**
```json
{
    "collection_start": "2024-11-01T00:00:00Z",
    "collection_end": "2024-11-30T23:59:59Z",
    "exchanges": ["extended", "lighter", "variational"],
    "tokens": ["KAITO", "MON", "IP", "GRASS", "ZEC", "APT", "SUI", "TRUMP", "LDO", "OP", "SEI", "MEGA", "YZY"],
    "interval_minutes": 60,
    "total_snapshots": 720,
    "data_quality": 0.98
}
```

---

### **Component 3: Backtest Data Provider**

**Location:** `/Users/tdl321/quants-lab/core/backtesting/funding_rate_data_provider.py`

**Purpose:** Provide funding rate data to backtesting engine in standardized format

**Key Features:**
- Load historical funding data
- Time-based indexing
- Spread calculation on-the-fly
- Compatible with BacktestingEngine
- Data interpolation for missing values

**Methods:**
```python
class FundingRateBacktestDataProvider:
    - __init__(data_path)
    - load_data(start_timestamp, end_timestamp) -> pd.DataFrame
    - get_funding_rate(timestamp, exchange, token) -> float
    - get_spread(timestamp, exchange1, exchange2, token) -> float
    - get_best_spread(timestamp, token) -> Tuple[str, str, float]
    - get_funding_payment_times(exchange) -> List[int]
    - interpolate_missing_data(data) -> pd.DataFrame
```

---

### **Component 4: Backtesting Strategy Adapter**

**Location:** `/Users/tdl321/quants-lab/core/backtesting/funding_arb_strategy.py`

**Purpose:** Adapt v2_funding_rate_arb for backtesting with simulated execution

**Key Features:**
- Simulated position opening/closing
- Funding payment simulation
- PNL tracking (trading + funding)
- Delta neutrality validation
- Event-based execution

---

### **Component 5: Data Collection Notebook**

**Location:** `/Users/tdl321/quants-lab/research_notebooks/data_collection/download_funding_rates_coingecko.ipynb`

**Purpose:** Interactive notebook for collecting funding rate data

**Sections:**
1. Configuration (API key, exchanges, tokens)
2. Exchange Validation
3. Single Snapshot Collection
4. Historical Collection
5. Data Analysis

---

### **Component 6: Backtesting Notebook**

**Location:** `/Users/tdl321/quants-lab/research_notebooks/eda_strategies/funding_rate_arb/01_backtest_funding_rate_arb.ipynb`

**Purpose:** Run backtests and analyze results

**Sections:**
1. Data Loading
2. Strategy Configuration
3. Run Backtest
4. Analysis with Funding Metrics
5. Parameter Optimization

---

## 🔄 Implementation Workflow

### **Phase 1: Foundation (Day 1-2)**
1. ✅ Create directory structure
2. ✅ Build `CoinGeckoFundingDataSource` class
3. ✅ Test API connectivity
4. ✅ Validate exchange IDs and token availability
5. ✅ Create basic data collection script

### **Phase 2: Data Collection (Day 2-3)**
1. ✅ Build `FundingRateCollector` class
2. ✅ Create data collection notebook
3. ✅ Set up storage structure
4. ✅ Run initial 24-hour collection test
5. ✅ Validate data quality

### **Phase 3: Backtest Infrastructure (Day 3-4)**
1. ✅ Create `FundingRateBacktestDataProvider`
2. ✅ Build `FundingArbBacktestStrategy`
3. ✅ Test with sample data
4. ✅ Validate funding payment simulation
5. ✅ Verify delta neutrality

### **Phase 4: Integration & Testing (Day 4-5)**
1. ✅ Update backtesting notebook
2. ✅ Run test backtest on 7 days of data
3. ✅ Debug and fix issues
4. ✅ Add visualizations
5. ✅ Document usage

### **Phase 5: Production Collection (Ongoing)**
1. ✅ Collect 30+ days of historical data
2. ✅ Run comprehensive backtests
3. ✅ Optimize parameters
4. ✅ Generate performance reports

---

## 📊 Data Collection Strategy

### **Option 1: Real-Time Collection (Recommended)**
```python
Duration: 30 days
Interval: 60 minutes (hourly snapshots)
Snapshots: 720 total
Data size: ~5-10 MB
Cost: Minimal API calls (~720 calls total)
```

### **Option 2: Accelerated Collection**
```python
Duration: 7 days
Interval: 10 minutes
Snapshots: 1008 total
Data size: ~10-15 MB
Cost: More API calls (~1000 calls)
```

### **Option 3: Historical API (If Available)**
```python
Duration: Request last 30-90 days
Resolution: Hourly or better
Cost: Depends on API tier
```

---

## 🎯 Validation Checklist

Before starting implementation:

1. **CoinGecko API Access**
   - [ ] API key is active
   - [ ] Rate limits are sufficient
   - [ ] Can access derivatives endpoints

2. **Exchange Availability**
   - [ ] Extended is on CoinGecko
   - [ ] Lighter is on CoinGecko
   - [ ] Variational is on CoinGecko
   - [ ] Funding rates are provided

3. **Token Availability**
   - [ ] All 13 tokens exist on exchanges
   - [ ] Funding data available per token
   - [ ] Data quality is good

4. **Data Format**
   - [ ] Funding rates are in correct units
   - [ ] Timestamps are consistent
   - [ ] All required fields present

---

## 📝 Implementation Notes

- Store this plan as reference document
- Update checkboxes as components complete
- Document any deviations or issues
- Keep metadata for all collected data
- Version control all code changes

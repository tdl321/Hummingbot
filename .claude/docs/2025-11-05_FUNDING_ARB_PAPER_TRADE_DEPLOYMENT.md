# Funding Rate Arbitrage Strategy - Paper Trading Deployment Guide

## Overview

This guide covers deploying the v2 funding rate arbitrage strategy to paper trade on live markets using your custom `extended_perpetual` and `lighter_perpetual` connectors.

**Strategy**: Exploits funding rate differentials between perpetual exchanges by going long on the exchange with lower/negative rates and short on the exchange with higher rates.

**Mode**: Paper Trading (simulated execution, no real funds at risk)

---

## Configuration Summary

### Trading Parameters
- **Connectors**: extended_perpetual, lighter_perpetual (paper trade mode)
- **Tokens**: KAITO, MON, IP, GRASS, ZEC, APT, SUI, TRUMP, LDO, OP, SEI, MEGA, YZY
- **Leverage**: 5x
- **Position Size**: $500 USD per side ($1,000 total per arbitrage pair)
- **Paper Trading Balance**: $500 USD per exchange wallet

### Entry Conditions
- **Min Funding Rate Spread**: 0.3% daily (0.003)
- **Trade Profitability Check**: Disabled (will enter based on funding rates only)

### Exit Conditions
1. **Spread Flip**: Exit if spread goes negative
2. **Absolute Minimum**: Exit if spread < 0.2%
3. **Spread Compression**: Exit if spread compresses 60% from entry
4. **Max Duration**: Close after 24 hours
5. **Stop Loss**: Exit if loss exceeds 3%

---

## Files Created

### 1. Strategy Configuration
**File**: `conf/scripts/v2_funding_rate_arb.yml`

```yaml
script_file_name: v2_funding_rate_arb.py
connectors:
  - extended_perpetual_paper_trade
  - lighter_perpetual_paper_trade
tokens:
  - KAITO
  - MON
  # ... (full list in file)
leverage: 5
position_size_quote: 500
min_funding_rate_profitability: 0.003
# ... (all parameters configured)
```

---

## Setup Steps

### Step 1: Configure Paper Trading Balances

Edit `conf/__init__.py` to add paper trading balance configuration:

```python
from hummingbot.client.config.client_config_map import ClientConfigMap

# Add paper trading configuration
paper_trade_config = {
    "paper_trade_account_balance": {
        "USD": 500.0,  # $500 USD per exchange
        "USDT": 500.0,  # Backup for USDT-based exchanges
        "BTC": 0.1,    # Small BTC balance if needed
        "ETH": 1.0     # Small ETH balance if needed
    }
}
```

**Note**: With $500 per exchange and $500 position size per side, you can run **1 arbitrage pair at a time** (requiring $500 on each exchange). To run multiple pairs simultaneously, increase the USD balance accordingly (e.g., $5,000 for 10 pairs).

### Step 2: Verify Custom Connector Registration

Ensure your custom connectors are properly registered in Hummingbot:

1. **Check connector files exist**:
   ```bash
   ls hummingbot/connector/derivative/extended_perpetual/
   ls hummingbot/connector/derivative/lighter_perpetual/
   ```

2. **Verify they're in AllConnectorSettings**:
   - Should be listed in `hummingbot/client/settings.py`
   - Must have proper `ConnectorSetting` configuration

3. **Required connector features**:
   - ✓ Inherit from `PerpetualDerivativePyBase` or similar
   - ✓ Implement `get_funding_info()` method
   - ✓ Return `FundingInfo` objects with `rate` and `next_funding_utc_timestamp`
   - ✓ Support position mode setting (ONEWAY mode)
   - ✓ Support leverage setting per trading pair
   - ✓ Correctly format trading pairs as "TOKEN-USD"

### Step 3: Update Strategy for Proper Market Initialization

The strategy needs to initialize markets properly. Verify in `scripts/v2_funding_rate_arb.py`:

```python
@classmethod
def init_markets(cls, config: FundingRateArbitrageConfig):
    markets = {}
    for connector in config.connectors:
        trading_pairs = {cls.get_trading_pair_for_connector(token, connector)
                        for token in config.tokens}
        markets[connector] = trading_pairs
    cls.markets = markets
```

This method should be called before strategy initialization.

---

## How to Launch

### Option 1: Using Hummingbot CLI

1. **Start Hummingbot**:
   ```bash
   cd /Users/tdl321/hummingbot
   ./start
   ```

2. **Start the script strategy**:
   ```
   start --script scripts/v2_funding_rate_arb.py
   ```

3. **Load configuration** (if prompted):
   ```
   conf/scripts/v2_funding_rate_arb.yml
   ```

### Option 2: Using Command Line (if supported)

```bash
python bin/hummingbot.py --script scripts/v2_funding_rate_arb.py --config conf/scripts/v2_funding_rate_arb.yml
```

---

## Running the Strategy Live - Deep Dive

This section explains exactly how to run the strategy and what happens under the hood.

### Prerequisites Checklist

Before running the strategy, ensure:

- [x] **Conda environment activated**: `conda activate hummingbot`
- [x] **In project root directory**: `cd /Users/tdl321/hummingbot`
- [x] **Configuration file exists**: `conf/scripts/v2_funding_rate_arb.yml`
- [x] **Strategy script exists**: `scripts/v2_funding_rate_arb.py`
- [x] **Paper trade balances configured** (if paper trading)
- [x] **API keys configured** (if live trading) - use `connect <exchange>` command
- [x] **Custom connectors registered** in `hummingbot/client/settings.py`

### Method 1: Shell Wrapper (Quickstart)

The `./start` wrapper script provides the fastest way to launch strategies.

**Command Syntax:**
```bash
./start [-p PASSWORD] [-f FILE] [-c CONFIG]
```

**Parameters:**
- `-p`: Password for encrypted configs (optional)
- `-f`: Strategy file (.yml) or script file (.py)
- `-c`: Config file for the script (.yml)

**Examples:**

**Launch with script file and config:**
```bash
./start -f scripts/v2_funding_rate_arb.py -c conf/scripts/v2_funding_rate_arb.yml
```

**Launch with just strategy file (will prompt for config):**
```bash
./start -f scripts/v2_funding_rate_arb.py
```

**Launch with password (for encrypted configs):**
```bash
./start -p mypassword -f scripts/v2_funding_rate_arb.py -c conf/scripts/v2_funding_rate_arb.yml
```

**What Happens:**
1. Script validates conda environment is activated
2. Checks `bin/hummingbot_quickstart.py` exists
3. Validates file extensions (.py or .yml)
4. Executes `bin/hummingbot_quickstart.py` with parameters
5. Quickstart script loads strategy and starts immediately

**When to Use:**
- ✓ Automated deployments
- ✓ Running strategies in background/production
- ✓ Quick testing without interactive session
- ✓ Integration with monitoring/orchestration systems

### Method 2: Interactive CLI (Recommended for Development)

The interactive CLI provides full control and monitoring capabilities.

**Step-by-Step:**

1. **Start Hummingbot Interactive Mode:**
   ```bash
   ./bin/hummingbot.py
   ```

   **Expected Output:**
   ```
   Loading Hummingbot...

   ================================
          HUMMINGBOT v2.x.x
   ================================

   >>>
   ```

2. **Inside Hummingbot CLI, start the script:**
   ```
   start --script v2_funding_rate_arb --conf v2_funding_rate_arb
   ```

   **Note**:
   - Script name is WITHOUT `.py` extension
   - Config name is WITHOUT `.yml` extension and WITHOUT `conf/scripts/` path
   - Hummingbot automatically looks in `scripts/` and `conf/scripts/` directories

3. **Alternative: Start without config (interactive prompts):**
   ```
   start --script v2_funding_rate_arb
   ```
   You'll be prompted for each configuration parameter.

4. **Monitor the startup process:**
   ```
   Strategy v2_funding_rate_arb loading...
   Initializing markets...
   Creating connector: extended_perpetual_paper_trade
   Creating connector: lighter_perpetual_paper_trade
   Connecting to extended_perpetual...
   Connecting to lighter_perpetual...
   All markets ready
   Strategy started successfully
   ```

**When to Use:**
- ✓ Development and testing
- ✓ Real-time monitoring with status command
- ✓ Need to run other commands while strategy runs
- ✓ Debugging and log viewing
- ✓ Manual intervention during runtime

### Method 3: Python Direct Execution

For advanced users who want programmatic control.

```python
import asyncio
from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.client.config.config_helpers import load_client_config_map_from_file

async def main():
    # Load client config
    client_config = load_client_config_map_from_file()

    # Create application
    app = HummingbotApplication(client_config)

    # Start strategy
    await app.start_check(
        script="v2_funding_rate_arb",
        conf="v2_funding_rate_arb"
    )

    # Run clock
    await app._run_clock()

if __name__ == "__main__":
    asyncio.run(main())
```

### What Happens When You Start: Internal Flow

Here's what occurs behind the scenes when you run `start --script v2_funding_rate_arb`:

```
1. COMMAND PARSING
   ├─ CLI parses: script="v2_funding_rate_arb", conf="v2_funding_rate_arb"
   └─ Calls: HummingbotApplication.start_check()

2. VALIDATION CHECKS
   ├─ Check if strategy already running → abort if yes
   ├─ Check oracle rates if required
   ├─ Check gateway if using DEX connectors
   └─ Validate all prerequisites

3. SCRIPT LOADING (TradingCore.load_script_class)
   ├─ Import: scripts/v2_funding_rate_arb.py
   ├─ Extract: FundingRateArbitrage class (strategy)
   ├─ Extract: FundingRateArbitrageConfig class (config)
   └─ Load config: conf/scripts/v2_funding_rate_arb.yml → config object

4. MARKET INITIALIZATION (FundingRateArbitrage.init_markets)
   ├─ Parse config.connectors: ["extended_perpetual_paper_trade", "lighter_perpetual_paper_trade"]
   ├─ Parse config.tokens: ["KAITO", "MON", "IP", ...]
   ├─ Build markets dict:
   │   ├─ extended_perpetual_paper_trade: ["KAITO-USD", "MON-USD", ...]
   │   └─ lighter_perpetual_paper_trade: ["KAITO-USD", "MON-USD", ...]
   └─ Set: FundingRateArbitrage.markets = {...}

5. CONNECTOR CREATION (ConnectorManager.create_connector)
   For each connector in markets:
   ├─ Check if paper trade (ends with "_paper_trade")
   ├─ If paper trade:
   │   ├─ Create: PaperTradeExchange instance
   │   ├─ Set balances: from paper_trade_config
   │   └─ Use real order book data but simulate execution
   ├─ If live:
   │   ├─ Retrieve: API keys from Security.api_keys()
   │   ├─ Create: Real connector instance (e.g., ExtendedPerpetualDerivative)
   │   └─ Initialize: WebSocket connections, REST clients
   └─ Add to: ConnectorManager.connectors dict

6. STRATEGY INSTANTIATION
   ├─ Call: FundingRateArbitrage.__init__(connectors, config)
   ├─ Initialize: active_funding_arbitrages = {}
   ├─ Initialize: stopped_funding_arbitrages = {}
   ├─ Set up: Market data provider
   └─ Register: Event listeners (funding payment, order events)

7. CLOCK INITIALIZATION
   ├─ Create: Clock instance (manages tick cycle)
   ├─ Add iterators:
   │   ├─ All connectors (tick → update order books, balances)
   │   └─ Strategy (tick → on_tick() method called)
   └─ Start: Markets recorder (trade tracking)

8. POSITION MODE & LEVERAGE SETUP (Strategy.apply_initial_setting)
   For each connector:
   ├─ Set position mode: ONEWAY for extended/lighter
   └─ Set leverage: 5x for all trading pairs

9. STRATEGY START (Strategy.start)
   ├─ Set: _last_timestamp
   ├─ Call: apply_initial_setting()
   └─ Ready: Strategy now active

10. CLOCK RUN LOOP (Clock.run)
    Every tick (typically 1 second):
    ├─ Update all connectors:
    │   ├─ Fetch order book updates
    │   ├─ Update account balances
    │   ├─ Process WebSocket events
    │   └─ Check funding info updates
    ├─ Call strategy.on_tick():
    │   ├─ create_actions_proposal() → check for new arbitrage opportunities
    │   ├─ stop_actions_proposal() → check exit conditions
    │   └─ Process executor actions
    └─ Repeat until stopped

11. READY STATE
    ├─ All connectors ready (order books loaded, balances fetched)
    ├─ Strategy monitoring funding rates
    ├─ Waiting for arbitrage opportunities
    └─ User can now run 'status' command
```

### Expected Console Output

**Successful startup:**
```
>>> start --script v2_funding_rate_arb --conf v2_funding_rate_arb

Loading strategy: v2_funding_rate_arb
Loading configuration: conf/scripts/v2_funding_rate_arb.yml

Initializing markets...
  • extended_perpetual_paper_trade: 13 trading pairs
  • lighter_perpetual_paper_trade: 13 trading pairs

Creating connectors...
  ✓ extended_perpetual_paper_trade created (paper trade mode)
  ✓ lighter_perpetual_paper_trade created (paper trade mode)

Setting paper trade balances...
  ✓ USD: 500.0

Connecting to exchanges...
  ⟳ Fetching order books for extended_perpetual...
  ⟳ Fetching order books for lighter_perpetual...
  ✓ All order books loaded

Applying strategy settings...
  ✓ Position mode set to ONEWAY
  ✓ Leverage set to 5x for all pairs

Starting strategy clock...
  ✓ Strategy started successfully

Strategy 'v2_funding_rate_arb' is now running.
Use 'status' to view current state.
Use 'stop' to stop the strategy.

>>>
```

### Common Startup Issues & Solutions

#### Issue 1: "Strategy already running"
```
Error: The bot is already running - please run "stop" first
```

**Solution:**
```
stop
# Wait for strategy to stop
start --script v2_funding_rate_arb --conf v2_funding_rate_arb
```

#### Issue 2: "Connector not found"
```
Error: Connector 'extended_perpetual' not found in settings
```

**Solution:**
- Verify connector is registered in `hummingbot/client/settings.py`
- Check connector module exists in `hummingbot/connector/derivative/extended_perpetual/`
- Ensure connector is imported in settings module

#### Issue 3: "API keys required"
```
Error: API keys required for live trading connector 'extended_perpetual'
```

**Solution for paper trading:**
- Ensure connector name ends with `_paper_trade` in config file

**Solution for live trading:**
```
connect extended_perpetual
# Enter API key and secret when prompted
```

#### Issue 4: "Config file not found"
```
Error: Configuration file not found: conf/scripts/v2_funding_rate_arb.yml
```

**Solution:**
- Verify file exists: `ls -la conf/scripts/v2_funding_rate_arb.yml`
- Check YAML syntax is valid
- Ensure file has proper permissions (readable)

#### Issue 5: "Markets not initializing"
```
Error: Strategy class does not have 'markets' attribute
```

**Solution:**
- Ensure `init_markets(cls, config)` classmethod exists in strategy
- Verify it sets `cls.markets = {...}` before strategy initialization
- Check it's being called by the framework

#### Issue 6: "Funding info not available"
```
Warning: Funding info not available for KAITO-USD on extended_perpetual
```

**Solution:**
- Verify connector implements `get_funding_info(trading_pair)` method
- Check exchange API is accessible
- Confirm trading pair format is correct for that exchange
- Wait a few seconds for initial data fetch

### Stopping the Strategy

**Interactive CLI:**
```
stop
```

**What happens:**
1. Strategy stops creating new positions
2. Existing positions remain open
3. Connectors disconnect gracefully
4. Clock stops ticking
5. Resources cleaned up

**Force stop (if strategy hangs):**
```
exit
# Or Ctrl+C in terminal
```

### Background Execution (Production)

To run strategy continuously in background:

**Using screen:**
```bash
screen -S hummingbot
./start -f scripts/v2_funding_rate_arb.py -c conf/scripts/v2_funding_rate_arb.yml
# Ctrl+A, D to detach
# screen -r hummingbot to reattach
```

**Using tmux:**
```bash
tmux new -s hummingbot
./start -f scripts/v2_funding_rate_arb.py -c conf/scripts/v2_funding_rate_arb.yml
# Ctrl+B, D to detach
# tmux attach -t hummingbot to reattach
```

**Using systemd service (advanced):**
Create `/etc/systemd/system/hummingbot.service`:
```ini
[Unit]
Description=Hummingbot Funding Arbitrage
After=network.target

[Service]
Type=simple
User=tdl321
WorkingDirectory=/Users/tdl321/hummingbot
ExecStart=/bin/bash -c 'conda activate hummingbot && ./start -f scripts/v2_funding_rate_arb.py -c conf/scripts/v2_funding_rate_arb.yml'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hummingbot
sudo systemctl start hummingbot
sudo systemctl status hummingbot
```

---

## Running with Docker

This section covers deploying the funding rate arbitrage strategy using Docker, which provides isolation, portability, and consistent execution environments.

### Why Use Docker?

**Benefits:**
- ✓ **Isolation**: Strategy runs in isolated container, no conflicts with system packages
- ✓ **Portability**: Same environment on local machine, server, or cloud
- ✓ **Consistency**: Reproducible builds and deployments
- ✓ **Easy Cleanup**: Remove container and volumes to completely clean up
- ✓ **Resource Limits**: Control CPU/memory usage per container

**When to Use Docker:**
- Development and testing in isolated environment
- Running multiple strategies simultaneously (separate containers)
- Deployment to servers/VPS without installing dependencies
- CI/CD pipelines and automated testing
- Easier upgrades and rollbacks

**When Native Installation is Better:**
- Active development with frequent code changes (faster iteration)
- Need direct access to debugger
- Limited disk space (Docker images are large)
- Windows/Mac performance concerns (Docker uses VM)

### Prerequisites

1. **Install Docker**:
   ```bash
   # Mac
   brew install --cask docker

   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Verify installation
   docker --version
   docker compose version
   ```

2. **Verify Docker is Running**:
   ```bash
   docker ps
   # Should show empty list or running containers, not an error
   ```

### Docker Setup Overview

The Hummingbot repository includes Docker configuration files:

```
hummingbot/
├── Dockerfile              # Multi-stage build definition
├── docker-compose.yml      # Service configuration
├── .dockerignore          # Files excluded from build
├── conf/                  # Mounted to container (configs)
├── scripts/               # Mounted to container (strategies)
├── logs/                  # Mounted to container (log output)
└── data/                  # Mounted to container (state/data)
```

**Key Mount Points:**
- `./conf` → `/home/hummingbot/conf` (strategy configurations)
- `./scripts` → `/home/hummingbot/scripts` (strategy code)
- `./logs` → `/home/hummingbot/logs` (execution logs)
- `./data` → `/home/hummingbot/data` (persistent data)

### Method 1: Custom Build (Recommended for Custom Connectors)

Since you have custom `extended_perpetual` and `lighter_perpetual` connectors, build a custom Docker image with them baked in.

#### Step 1: Build the Docker Image

From the Hummingbot project root:

```bash
cd /Users/tdl321/hummingbot

# Build the image
docker build -t hummingbot-funding-arb:latest .
```

**Build arguments** (optional):
```bash
docker build \
  --build-arg BRANCH=$(git branch --show-current) \
  --build-arg COMMIT=$(git rev-parse --short HEAD) \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t hummingbot-funding-arb:latest .
```

**Expected build time**: 5-15 minutes (depending on system)

**What happens during build:**
1. Base image: `continuumio/miniconda3:latest`
2. System dependencies installed (gcc, g++, libusb)
3. Conda environment created from `setup/environment.yml`
4. Python packages installed from `setup/pip_packages.txt`
5. Hummingbot source compiled (`setup.py build_ext`)
6. Your custom connectors included in `/home/hummingbot/hummingbot/connector/derivative/`
7. Mount points created for conf/, scripts/, logs/, data/

#### Step 2: Verify Custom Connectors in Image

```bash
docker run --rm hummingbot-funding-arb:latest \
  ls -la /home/hummingbot/hummingbot/connector/derivative/ | grep -E "extended|lighter"
```

**Expected output:**
```
drwxr-xr-x  extended_perpetual
drwxr-xr-x  lighter_perpetual
```

#### Step 3: Update docker-compose.yml

Edit `docker-compose.yml` to use your custom image:

```yaml
services:
  hummingbot:
    container_name: hummingbot-funding-arb
    # Use custom built image instead of official
    image: hummingbot-funding-arb:latest
    # build:  # Uncomment to rebuild on every docker compose up
    #   context: .
    #   dockerfile: Dockerfile
    volumes:
      - ./conf:/home/hummingbot/conf
      - ./conf/connectors:/home/hummingbot/conf/connectors
      - ./conf/strategies:/home/hummingbot/conf/strategies
      - ./conf/controllers:/home/hummingbot/conf/controllers
      - ./conf/scripts:/home/hummingbot/conf/scripts
      - ./logs:/home/hummingbot/logs
      - ./data:/home/hummingbot/data
      - ./certs:/home/hummingbot/certs
      - ./scripts:/home/hummingbot/scripts
      - ./controllers:/home/hummingbot/controllers
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
    tty: true
    stdin_open: true
    network_mode: host
    # Uncomment for automated strategy startup
    # environment:
    #   - CONFIG_FILE_NAME=v2_funding_rate_arb.py
    #   - SCRIPT_CONFIG=v2_funding_rate_arb.yml
    #   - CONFIG_PASSWORD=  # Leave empty if no password
```

### Running the Strategy: Interactive Mode

**Step 1: Start the Container**

```bash
docker compose up -d
```

**What happens:**
- Container starts in detached mode (`-d`)
- Volumes mounted from host to container
- Conda environment activated
- Quickstart script waits for commands

**Step 2: Attach to Container**

```bash
docker attach hummingbot-funding-arb
```

**You'll see:**
```
Loading Hummingbot...

================================
       HUMMINGBOT v2.x.x
================================

>>>
```

**Step 3: Start Strategy**

Inside the container CLI:
```
start --script v2_funding_rate_arb --conf v2_funding_rate_arb
```

**Step 4: Monitor and Interact**

Use all standard Hummingbot commands:
```
status          # View strategy status
history         # View trade history
balance         # View balances
stop            # Stop strategy
exit            # Exit (Ctrl+P, Ctrl+Q to detach without exiting)
```

**To detach without stopping:**
Press `Ctrl+P` then `Ctrl+Q` (container keeps running)

**To reattach:**
```bash
docker attach hummingbot-funding-arb
```

### Running the Strategy: Automated Startup

For automated deployment without manual CLI interaction.

**Step 1: Configure Environment Variables**

Edit `docker-compose.yml`:

```yaml
services:
  hummingbot:
    # ... other config ...
    environment:
      - CONFIG_FILE_NAME=v2_funding_rate_arb.py
      - SCRIPT_CONFIG=v2_funding_rate_arb.yml
      # - CONFIG_PASSWORD=mypassword  # Only if configs are encrypted
```

**Step 2: Start Container**

```bash
docker compose up -d
```

**What happens:**
1. Container starts
2. Quickstart script reads environment variables
3. Loads strategy config automatically
4. Starts strategy without user interaction
5. Strategy runs in background

**Step 3: View Logs**

```bash
# Follow logs in real-time
docker logs -f hummingbot-funding-arb

# View last 100 lines
docker logs --tail 100 hummingbot-funding-arb

# Or access mounted log files
tail -f logs/hummingbot_logs.log
```

**Step 4: Monitor Strategy**

Attach to view status:
```bash
docker attach hummingbot-funding-arb
# Press Enter to see prompt
status
```

### Container Management

**Start container:**
```bash
docker compose up -d
```

**Stop container (graceful shutdown):**
```bash
docker compose down
```

**Stop without removing container:**
```bash
docker compose stop
```

**Restart container:**
```bash
docker compose restart
```

**View running containers:**
```bash
docker ps
```

**View all containers (including stopped):**
```bash
docker ps -a
```

**Remove container and volumes:**
```bash
docker compose down -v  # -v removes volumes (data/logs lost!)
```

**View container resource usage:**
```bash
docker stats hummingbot-funding-arb
```

### Volume Management & Persistence

All important data is persisted on the host via volume mounts:

**Configuration files** (`./conf/`):
```bash
# View strategy config
cat conf/scripts/v2_funding_rate_arb.yml

# Edit config (container will use updated file on restart)
nano conf/scripts/v2_funding_rate_arb.yml

# Restart to apply changes
docker compose restart
```

**Strategy scripts** (`./scripts/`):
```bash
# Edit strategy code on host
nano scripts/v2_funding_rate_arb.py

# Restart container to load changes
docker compose restart
```

**Note**: For code changes in `hummingbot/` directory (not `scripts/`), you must rebuild the image:
```bash
docker build -t hummingbot-funding-arb:latest .
docker compose down
docker compose up -d
```

**Logs** (`./logs/`):
```bash
# View logs from host
tail -f logs/hummingbot_logs.log
cat logs/errors.log
```

**Data and state** (`./data/`):
```bash
# SQLite databases, state files, etc.
ls -la data/
```

**Backup everything:**
```bash
tar -czf hummingbot-backup-$(date +%Y%m%d).tar.gz conf/ logs/ data/ scripts/
```

**Restore from backup:**
```bash
tar -xzf hummingbot-backup-20250105.tar.gz
```

### Paper Trading Configuration in Docker

Paper trading balances are configured in the host's `conf/` directory.

**Method 1: Edit conf/__init__.py (before first run)**

On the host machine:
```bash
nano conf/__init__.py
```

Add paper trading configuration:
```python
from hummingbot.client.config.client_config_map import ClientConfigMap

paper_trade_config = {
    "paper_trade_account_balance": {
        "USD": 500.0,
        "USDT": 500.0,
        "BTC": 0.1,
        "ETH": 1.0
    }
}
```

**Method 2: Use hummingbot config command**

Inside running container:
```
config paper_trade_account_balance
# Enter: {"USD": 500.0, "USDT": 500.0}
```

Configuration is saved to mounted volume and persists across container restarts.

### Development Workflow

**Quick iteration cycle:**

1. **Edit strategy on host:**
   ```bash
   nano scripts/v2_funding_rate_arb.py
   ```

2. **Restart container:**
   ```bash
   docker compose restart
   ```

3. **Attach and test:**
   ```bash
   docker attach hummingbot-funding-arb
   start --script v2_funding_rate_arb --conf v2_funding_rate_arb
   ```

**For connector changes:**

1. **Edit connector code:**
   ```bash
   nano hummingbot/connector/derivative/extended_perpetual/extended_perpetual_derivative.py
   ```

2. **Rebuild image:**
   ```bash
   docker build -t hummingbot-funding-arb:latest .
   ```

3. **Recreate container:**
   ```bash
   docker compose down
   docker compose up -d
   ```

### Docker-Specific Troubleshooting

#### Issue 1: Permission Denied on Mounted Volumes

```
Error: Permission denied: '/home/hummingbot/conf/scripts/v2_funding_rate_arb.yml'
```

**Solution:**
```bash
# On host, ensure files are readable
chmod -R 755 conf/ scripts/
chmod 644 conf/scripts/*.yml

# Or use Docker's auto-fix (in docker-compose.yml):
# command: ["--auto-set-permissions", "1000:1000"]
```

#### Issue 2: Custom Connector Not Found

```
Error: Connector 'extended_perpetual' not found in settings
```

**Solution:**
Rebuild the Docker image to include connector changes:
```bash
# Verify connector files exist on host
ls -la hummingbot/connector/derivative/extended_perpetual/

# Rebuild image
docker build --no-cache -t hummingbot-funding-arb:latest .

# Verify connector in image
docker run --rm hummingbot-funding-arb:latest \
  python -c "from hummingbot.client.settings import AllConnectorSettings; print([c for c in AllConnectorSettings.get_connector_settings().keys() if 'extended' in c or 'lighter' in c])"
```

#### Issue 3: Container Exits Immediately

```bash
docker ps  # Container not running
docker ps -a  # Shows container exited
```

**Check logs:**
```bash
docker logs hummingbot-funding-arb
```

**Common causes:**
- Invalid environment variables (CONFIG_FILE_NAME pointing to non-existent file)
- Syntax error in strategy script
- Missing configuration file

**Solution:**
```bash
# Start without auto-start to debug
docker compose up -d
# Remove environment variables from docker-compose.yml temporarily
docker compose restart
docker attach hummingbot-funding-arb
# Now manually start and see error messages
```

#### Issue 4: Cannot Connect to Exchanges

```
Error: Connection refused / Timeout connecting to exchange
```

**Solution:**
Check network mode in docker-compose.yml:
```yaml
network_mode: host  # Required for most exchange connections
```

If using custom network:
```yaml
network_mode: bridge
# Ensure outbound connections are allowed
```

#### Issue 5: Config Changes Not Taking Effect

**Problem:** Modified config file but strategy still uses old settings.

**Solution:**
```bash
# Stop strategy inside container
stop

# Restart container to reload configs
docker compose restart

# Attach and start with new config
docker attach hummingbot-funding-arb
start --script v2_funding_rate_arb --conf v2_funding_rate_arb
```

### Running Multiple Strategies

Run multiple strategies simultaneously in separate containers:

**Create docker-compose-multi.yml:**
```yaml
version: '3'
services:
  funding-arb-1:
    container_name: funding-arb-1
    image: hummingbot-funding-arb:latest
    volumes:
      - ./conf:/home/hummingbot/conf
      - ./logs/arb1:/home/hummingbot/logs
      - ./data/arb1:/home/hummingbot/data
      - ./scripts:/home/hummingbot/scripts
    environment:
      - CONFIG_FILE_NAME=v2_funding_rate_arb.py
      - SCRIPT_CONFIG=v2_funding_rate_arb.yml
    tty: true
    stdin_open: true
    network_mode: host

  funding-arb-2:
    container_name: funding-arb-2
    image: hummingbot-funding-arb:latest
    volumes:
      - ./conf:/home/hummingbot/conf
      - ./logs/arb2:/home/hummingbot/logs
      - ./data/arb2:/home/hummingbot/data
      - ./scripts:/home/hummingbot/scripts
    environment:
      - CONFIG_FILE_NAME=v2_funding_rate_arb.py
      - SCRIPT_CONFIG=v2_funding_rate_arb_alt.yml
    tty: true
    stdin_open: true
    network_mode: host
```

**Launch:**
```bash
docker compose -f docker-compose-multi.yml up -d
```

**Attach to specific container:**
```bash
docker attach funding-arb-1
# Ctrl+P, Ctrl+Q to detach
docker attach funding-arb-2
```

### Production Deployment with Docker

**Best practices for production:**

1. **Use specific image tags (not :latest):**
   ```bash
   docker build -t hummingbot-funding-arb:v1.0.0 .
   ```

2. **Set resource limits:**
   ```yaml
   services:
     hummingbot:
       # ... other config ...
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 4G
           reservations:
             cpus: '1.0'
             memory: 2G
   ```

3. **Configure restart policy:**
   ```yaml
   services:
     hummingbot:
       # ... other config ...
       restart: unless-stopped  # Auto-restart on failure
   ```

4. **Set up log rotation:**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "5"
   ```

5. **Use secrets for API keys:**
   Never hardcode API keys in docker-compose.yml. Use Docker secrets or environment files:
   ```bash
   # Create .env file (add to .gitignore!)
   echo "CONFIG_PASSWORD=mysecretpass" > .env
   ```

   ```yaml
   services:
     hummingbot:
       env_file:
         - .env
   ```

6. **Monitor container health:**
   ```bash
   # Add healthcheck to docker-compose.yml
   healthcheck:
     test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

7. **Set up monitoring/alerting:**
   ```bash
   # Watch for container crashes
   while true; do
     docker ps | grep funding-arb || echo "ALERT: Container stopped!"
     sleep 60
   done
   ```

### Docker Command Cheat Sheet

```bash
# Build
docker build -t hummingbot-funding-arb:latest .
docker build --no-cache -t hummingbot-funding-arb:latest .  # Force rebuild

# Run
docker compose up -d                    # Start detached
docker compose up                       # Start with logs
docker attach hummingbot-funding-arb    # Attach to running
docker compose down                     # Stop and remove

# Logs
docker logs hummingbot-funding-arb                 # View all logs
docker logs -f hummingbot-funding-arb              # Follow logs
docker logs --tail 50 hummingbot-funding-arb       # Last 50 lines

# Execute commands in running container
docker exec hummingbot-funding-arb ls -la conf/scripts/
docker exec -it hummingbot-funding-arb /bin/bash   # Open shell

# Inspect
docker inspect hummingbot-funding-arb    # Container details
docker stats hummingbot-funding-arb      # Resource usage
docker compose ps                        # Service status

# Cleanup
docker compose down -v                   # Remove volumes too
docker system prune -a                   # Clean up all unused images
docker volume prune                      # Remove unused volumes
```

---

## Monitoring & Commands

### Status Command
```
status
```

**Displays**:
- Current funding rates for all tokens across both exchanges
- Best arbitrage paths (highest funding rate differentials)
- Trade profitability estimates after fees
- Days to recover entry costs
- Time to next funding payment
- Active arbitrage positions
- Funding payments collected

### Other Useful Commands
```
history         # View trade history
config          # View/modify configuration
stop            # Stop the strategy
exit            # Exit Hummingbot
```

---

## Strategy Behavior

### Scanning Phase
- Continuously monitors funding rates across both exchanges for all configured tokens
- Calculates funding rate differentials
- Identifies best arbitrage opportunities

### Entry Phase
When a token pair meets entry conditions:
1. Funding rate spread ≥ 0.3% daily
2. Creates two position executors:
   - **Long position** on exchange with lower funding rate
   - **Short position** on exchange with higher funding rate
3. Opens both positions at market price simultaneously
4. Tracks entry spread and timestamp

### Active Position Management
For each active arbitrage:
- Collects funding payments every interval (8h for extended, 1h for lighter)
- Monitors current funding rate spread
- Calculates PnL (trading + funding payments)
- Evaluates exit conditions on every tick

### Exit Phase
Closes both positions when any condition triggers:
- Spread becomes negative
- Spread below 0.2% absolute minimum
- Spread compressed 60%+ from entry
- Position open for 24+ hours
- Total loss exceeds 3%

---

## Wallet Architecture

### Paper Trading (Current Setup)
- **No real wallets needed** - all balances are simulated
- Each connector has independent simulated balance
- Balances tracked in memory by paper trade engine

### Live Trading (Future)
When moving to live trading:
- **Separate wallets required** for each exchange
- Each exchange account is independent
- Fund each account separately:
  - Extended Perpetual account: Deposit USD/USDT
  - Lighter Perpetual account: Deposit USD/USDT
- **API keys needed** for each exchange
- Remove `_paper_trade` suffix from connector names in config

---

## Risk Considerations (Even in Paper Trade)

### Testing Objectives
1. ✓ Verify funding rate data fetching works correctly
2. ✓ Confirm arbitrage opportunity detection logic
3. ✓ Test position opening on both exchanges simultaneously
4. ✓ Validate funding payment collection
5. ✓ Confirm exit conditions trigger properly
6. ✓ Check PnL calculations are accurate

### Known Limitations of Paper Trading
- **No real slippage** - executes at exact prices
- **No order book depth simulation** - assumes infinite liquidity
- **5-second execution delay** - simulated market order fill time
- **Perfect execution** - no failed orders or API errors
- **Ideal funding payments** - no exchange downtime simulation

### Before Going Live
- [ ] Run paper trading for at least 1 week
- [ ] Observe at least 5-10 complete arbitrage cycles (entry → funding payments → exit)
- [ ] Verify all exit conditions have triggered successfully
- [ ] Confirm PnL calculations match expectations
- [ ] Test with small real capital first (e.g., $100 per side)
- [ ] Set up proper alerting/monitoring for live trading

---

## Troubleshooting

### Strategy Won't Start
- Check connector names in config match registered connectors
- Verify `_paper_trade` suffix is added for paper trading mode
- Ensure conf/scripts/v2_funding_rate_arb.yml exists and is valid YAML

### No Funding Rate Data
- Verify custom connectors implement `get_funding_info()` method
- Check connectors are properly connected (even in paper trade, they need live data)
- Confirm trading pairs are formatted correctly: "TOKEN-USD"

### No Arbitrage Opportunities Created
- **This is normal!** Strategy requires 0.3% daily spread minimum
- Funding rates may not have sufficient differential
- Check status output to see current spreads
- Lower `min_funding_rate_profitability` in config if needed for testing

### Positions Not Closing
- Check if exit conditions are actually met (view status for current spreads)
- Verify funding rate data is still updating
- Check logs for any executor errors

### Paper Trade Balance Issues
- Ensure USD balance is sufficient: $500 minimum per exchange
- Check balance hasn't been depleted by simulated losses
- Restart strategy to reset paper trade balances

---

## Next Steps

### Immediate (Paper Trading Phase)
1. ✅ Launch strategy in paper trade mode
2. ✅ Monitor first 24 hours for any errors
3. ✅ Observe funding rate scanning behavior
4. ⏳ Wait for first arbitrage opportunity to trigger
5. ⏳ Track complete position lifecycle
6. ⏳ Collect performance data

### Short-term (1-2 Weeks)
1. Analyze paper trading results
2. Tune parameters based on observations:
   - Adjust `min_funding_rate_profitability` if needed
   - Optimize exit thresholds (`compression_exit_threshold`, etc.)
   - Test different position sizes
3. Document any edge cases or issues found

### Medium-term (Before Live)
1. Implement additional safety features:
   - Max open positions limit
   - Daily loss limits
   - Exchange balance checks
2. Set up monitoring/alerting infrastructure
3. Create runbook for common issues
4. Test failover/recovery scenarios

### Live Trading Transition
1. Obtain API keys for both exchanges
2. Fund exchange accounts with test capital
3. Update config to remove `_paper_trade` suffixes
4. Start with minimal position sizes ($50-100)
5. Gradually increase position sizes as confidence grows
6. Implement proper risk management and monitoring

---

## Configuration Reference

### Adjustable Parameters

| Parameter | Current | Description | Adjustment Considerations |
|-----------|---------|-------------|--------------------------|
| `leverage` | 5 | Position leverage multiplier | Higher = more risk/reward |
| `position_size_quote` | 500 | USD per side | Match to your capital available |
| `min_funding_rate_profitability` | 0.003 | 0.3% daily entry threshold | Lower = more opportunities, less selective |
| `absolute_min_spread_exit` | 0.002 | 0.2% minimum spread to hold | Safety floor for exits |
| `compression_exit_threshold` | 0.4 | Exit at 60% compression | Lower = exit sooner on compression |
| `max_position_duration_hours` | 24 | Max time to hold position | Limit exposure duration |
| `max_loss_per_position_pct` | 0.03 | 3% stop loss | Protect against large losses |

### Funding Rate Intervals
- **extended_perpetual**: 8 hours (every 00:00, 08:00, 16:00 UTC)
- **lighter_perpetual**: 1 hour (every hour)

The strategy normalizes these to calculate daily profitability.

---

## Support & Resources

### Key Files
- Strategy code: `scripts/v2_funding_rate_arb.py`
- Configuration: `conf/scripts/v2_funding_rate_arb.yml`
- This guide: `FUNDING_ARB_PAPER_TRADE_DEPLOYMENT.md`

### Hummingbot Documentation
- V2 Strategies: https://docs.hummingbot.org/strategies/v2-strategies/
- Paper Trading: https://docs.hummingbot.org/global-configs/paper-trade/
- Script Strategies: https://docs.hummingbot.org/scripts/

### Getting Help
- Hummingbot Discord: https://discord.gg/hummingbot
- GitHub Issues: https://github.com/hummingbot/hummingbot/issues
- Strategy debugging: Enable debug logging with `config log_level` → `DEBUG`

---

## Changelog

**2025-01-05**: Initial deployment guide created
- Paper trading configuration
- Strategy behavior documentation
- Launch procedures
- Troubleshooting guide

---

*Good luck with your funding rate arbitrage testing!* 🚀

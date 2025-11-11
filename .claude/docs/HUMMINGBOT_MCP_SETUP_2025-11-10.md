# Hummingbot MCP Server Setup Guide

This document explains the current Hummingbot Model Context Protocol (MCP) server setup for use with Claude CLI.

## Overview

The Hummingbot MCP Server enables Claude CLI to interact with Hummingbot for automated cryptocurrency trading across multiple exchanges. This setup uses Docker to run the MCP server, which connects to your Hummingbot API instance.

## Architecture

```
Claude CLI (You)
    ↓ stdio transport
Hummingbot MCP Server (Docker Container)
    ↓ HTTP API
Hummingbot API Server (localhost:8000)
    ↓
Exchange Connectors & Trading Bots
```

## Current Installation

### Components Installed

1. **uv Package Manager**
   - Location: `/Users/tdl321/.local/bin/uv`
   - Version: 0.9.8
   - Purpose: Python package management for local development

2. **Hummingbot MCP Repository**
   - Location: `/Users/tdl321/mcp`
   - Source: `https://github.com/hummingbot/mcp`
   - Purpose: Source code and configuration

3. **Docker Image**
   - Image: `hummingbot/hummingbot-mcp:latest`
   - Digest: `sha256:986de78beeaa508d0bcf175a8e26bb2df6a73c012140718b1c88d253ddeda78e`
   - Purpose: Production runtime environment

4. **Claude CLI Integration**
   - Server Name: `hummingbot-mcp`
   - Scope: Local (project-specific)
   - Transport: stdio
   - Status: ✓ Connected

### Configuration Files

#### Environment Configuration
**File**: `/Users/tdl321/mcp/.env`

```env
# Hummingbot API Configuration
# Use host.docker.internal on Mac/Windows when MCP runs in Docker
# Use localhost when running MCP locally with uv
HUMMINGBOT_API_URL=http://host.docker.internal:8000
HUMMINGBOT_USERNAME=admin
HUMMINGBOT_PASSWORD=admin
```

**Current Configuration:**
- Using `host.docker.internal:8000` because MCP runs in Docker on Mac
- This allows the Docker container to access the Hummingbot API running on the host machine
- The API is still accessible locally at `http://localhost:8000` from your Mac

**Important Notes:**
- These are default credentials - update before production use
- **For Mac/Windows + Docker**: Use `http://host.docker.internal:8000` (current setup)
- **For Linux + Docker**: Use `--network host` flag instead and keep `http://localhost:8000`
- **For local uv execution**: Use `http://localhost:8000`
- Environment variables are only used for initial setup; subsequent configuration is managed via the `configure_api_servers` tool

**Understanding Docker Networking:**
When the MCP server runs in a Docker container:
- `localhost` inside the container refers to the container itself, NOT your Mac
- `host.docker.internal` is a special DNS name that Docker provides on Mac/Windows to access the host machine
- This allows the containerized MCP server to reach services running on your Mac (like the Hummingbot API)
- From your Mac, you can still access the API at `http://localhost:8000` - nothing changes on the host side

#### MCP Server Configuration
**File**: `/Users/tdl321/.claude.json` (auto-generated)

```json
{
  "mcpServers": {
    "hummingbot-mcp": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file",
        "/Users/tdl321/mcp/.env",
        "-v",
        "/Users/tdl321/.hummingbot_mcp:/root/.hummingbot_mcp",
        "hummingbot/hummingbot-mcp:latest"
      ]
    }
  }
}
```

#### Persistent Storage
**Directory**: `/Users/tdl321/.hummingbot_mcp/`

This directory stores:
- `servers.yml`: Multiple Hummingbot API server configurations
- Session data and credentials
- Configuration persists across Docker container restarts

## Available MCP Tools

Once connected, Claude CLI can access the following Hummingbot tools:

### Server Management
- **configure_api_servers**: Manage multiple Hummingbot API connections
  - List all configured servers
  - Add new servers with credentials
  - Set default server (automatically reconnects)
  - Remove servers

### Account Management
- Connect to exchange accounts
- Configure API credentials
- Manage connector settings

### Portfolio Operations
- Monitor balances across exchanges
- Track performance and P&L
- Analyze portfolio allocation
- View asset distribution

### Trading Operations
- Place orders (market, limit, etc.)
- Cancel orders
- Monitor order status
- Manage positions (for derivatives)
- View unrealized P&L

### Market Data
- Get real-time prices
- Access order book data
- Retrieve historical candles
- Monitor funding rates (perpetual contracts)

### Bot Management
- Deploy trading bots
- Configure strategies
- Start/stop bots
- Monitor bot performance

### DEX Trading (with Gateway)
- Manage Gateway container
- Execute token swaps
- Interact with AMM protocols

## Usage Examples

### Managing Multiple API Servers

```
# List all configured servers
configure_api_servers()

# Add a production server
configure_api_servers(
    action="add",
    name="production",
    url="http://prod-server:8000",
    username="admin",
    password="secure_password"
)

# Add a local server on different port
configure_api_servers(
    action="add",
    name="local_8001",
    port=8001,
    username="admin",
    password="password"
)

# Switch to production server
configure_api_servers(action="set_default", name="production")

# Remove old server
configure_api_servers(action="remove", name="old_server")
```

### Checking Portfolio
Ask Claude: "Show me my current portfolio balances across all exchanges"

### Placing Orders
Ask Claude: "Place a limit buy order for 0.1 BTC at $50,000 on Binance"

### Monitoring Bots
Ask Claude: "List all my active trading bots and their performance"

## Environment Variables

Available configuration options in `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `HUMMINGBOT_API_URL` | `http://localhost:8000` | Initial API server URL (first run only) |
| `HUMMINGBOT_USERNAME` | `admin` | Initial username (first run only) |
| `HUMMINGBOT_PASSWORD` | `admin` | Initial password (first run only) |
| `HUMMINGBOT_TIMEOUT` | `30.0` | Connection timeout in seconds |
| `HUMMINGBOT_MAX_RETRIES` | `3` | Maximum retry attempts |
| `HUMMINGBOT_RETRY_DELAY` | `2.0` | Delay between retries in seconds |
| `HUMMINGBOT_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

## Troubleshooting

### Common Issues

#### 1. MCP Server Not Connecting

**Error**: `❌ Cannot reach Hummingbot API at <url>`

**Solutions**:
- Verify Hummingbot API is running: `curl http://localhost:8000/health`
- Check Docker containers: `docker ps`
- Verify URL in `.env` file
- For Docker on Mac/Windows: use `http://host.docker.internal:8000`

#### 2. Authentication Failed

**Error**: `❌ Authentication failed when connecting to Hummingbot API`

**Solutions**:
- Verify credentials in `.env` file
- Use `configure_api_servers` tool to update credentials
- Check Hummingbot API server logs

#### 3. Docker Network Issues

**On Linux**:
- Add `--network host` flag to Docker args in `.claude.json`

**On Mac/Windows**:
- Change `HUMMINGBOT_API_URL` to `http://host.docker.internal:8000`

#### 4. Permission Denied on Volume Mount

**Error**: Permission issues with `/Users/tdl321/.hummingbot_mcp`

**Solutions**:
- Create directory manually: `mkdir -p ~/.hummingbot_mcp`
- Set proper permissions: `chmod 755 ~/.hummingbot_mcp`

### Checking MCP Server Status

```bash
# List all MCP servers
claude mcp list

# Get details about Hummingbot MCP
claude mcp get hummingbot-mcp

# Test Docker image directly
docker run --rm -i --env-file /Users/tdl321/mcp/.env \
  -v $HOME/.hummingbot_mcp:/root/.hummingbot_mcp \
  hummingbot/hummingbot-mcp:latest
```

### Viewing Logs

To see what's happening inside the MCP server:

```bash
# Check Docker logs (if container is still running)
docker logs <container_id>

# Run in foreground for debugging
docker run --rm -it --env-file /Users/tdl321/mcp/.env \
  -v $HOME/.hummingbot_mcp:/root/.hummingbot_mcp \
  hummingbot/hummingbot-mcp:latest
```

## Updating the MCP Server

### Update Docker Image

```bash
# Pull latest version
docker pull hummingbot/hummingbot-mcp:latest

# Restart Claude CLI to use new image
# (MCP servers are started fresh each time)
```

### Update Local Repository

```bash
cd /Users/tdl321/mcp
git pull origin main
uv sync
```

## Managing the Installation

### Viewing Configuration

```bash
# View current MCP servers
claude mcp list

# View specific server details
claude mcp get hummingbot-mcp

# View environment configuration
cat /Users/tdl321/mcp/.env

# View persistent configuration
cat ~/.hummingbot_mcp/servers.yml
```

### Modifying Configuration

```bash
# Edit environment variables
nano /Users/tdl321/mcp/.env

# Edit persistent server configuration
nano ~/.hummingbot_mcp/servers.yml
```

### Removing the MCP Server

```bash
# Remove from Claude CLI
claude mcp remove hummingbot-mcp -s local

# Remove Docker image
docker rmi hummingbot/hummingbot-mcp:latest

# Remove local repository
rm -rf /Users/tdl321/mcp

# Remove persistent data
rm -rf ~/.hummingbot_mcp
```

## Alternative Setup Options

### Option 1: Using Local uv (Development)

For development and debugging:

```bash
# Add to Claude CLI
claude mcp add --transport stdio hummingbot-mcp-dev -- \
  uv --directory /Users/tdl321/mcp run main.py
```

**Advantages**:
- Direct access to source code
- Easier debugging
- Can modify code on the fly

**Disadvantages**:
- Requires Python 3.11+ installed
- More dependencies to manage

### Option 2: Using Docker Exec (Cloud Deployment)

For cloud servers where both API and MCP run together:

```bash
# Start services with docker-compose
cd /Users/tdl321/mcp
docker compose up -d

# Add to Claude CLI
claude mcp add --transport stdio hummingbot-mcp-cloud -- \
  docker exec -i hummingbot-mcp uv run main.py
```

**Advantages**:
- Full stack deployment
- Production-ready setup
- Includes database and message broker

**Disadvantages**:
- More complex setup
- Requires more resources

## Security Considerations

### Credentials Management

1. **Never commit `.env` files** to version control
2. **Use strong passwords** for production API servers
3. **Rotate credentials regularly**
4. **Limit API permissions** to necessary operations only

### Network Security

1. **Run Hummingbot API on localhost** when possible
2. **Use HTTPS** for remote API connections
3. **Implement IP whitelisting** for production deployments
4. **Monitor API access logs** regularly

### Trading Safeguards

1. **Set trading limits** on exchange accounts
2. **Use test/paper trading** for strategy validation
3. **Monitor AI-generated trades** before execution
4. **Implement kill switches** for emergency stops
5. **Review all bot configurations** before deployment

## Prerequisites for Usage

Before using the Hummingbot MCP server, ensure:

1. ✅ Hummingbot API server is running
2. ✅ Exchange API keys are configured in Hummingbot
3. ✅ Proper authentication credentials are set
4. ✅ Network connectivity between MCP server and API
5. ✅ Sufficient permissions on exchange accounts

## Next Steps

1. **Start Hummingbot API Server**
   - Follow Hummingbot API installation guide
   - Verify server is accessible at `http://localhost:8000`

2. **Configure Exchange Connectors**
   - Add exchange API keys via Hummingbot API
   - Test connectivity to exchanges

3. **Test MCP Connection**
   - Ask Claude to list available tools
   - Verify portfolio access
   - Test basic commands

4. **Deploy Trading Strategies**
   - Create or import trading strategies
   - Configure bot parameters
   - Start automated trading

## Resources

- **Hummingbot MCP GitHub**: https://github.com/hummingbot/mcp
- **Hummingbot MCP Docs**: https://hummingbot.org/mcp/
- **Hummingbot API Docs**: https://hummingbot.org/hummingbot-api/
- **Hummingbot Main Docs**: https://hummingbot.org/
- **MCP Protocol Spec**: https://modelcontextprotocol.io/
- **Claude Code Docs**: https://code.claude.com/docs/

## Support

If you encounter issues:

1. Check this documentation first
2. Review Hummingbot logs
3. Join Hummingbot Discord: https://discord.gg/hummingbot
4. Submit GitHub issues: https://github.com/hummingbot/mcp/issues

---

**Last Updated**: 2025-11-10
**Setup Location**: `/Users/tdl321/hummingbot/`
**MCP Repository**: `/Users/tdl321/mcp/`
**Configuration**: `/Users/tdl321/.claude.json` (local scope)

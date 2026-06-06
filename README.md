# Sleeper MCP Server

A Model Context Protocol (MCP) server that provides Claude Desktop with access to Sleeper Fantasy Football API data. This server enables users to query league information, player data, matchups, draft results, and perform trade analysis through natural language interactions with Claude.

## Features

- **League Management**: Query leagues, rosters, users, and league settings
- **Draft Analysis**: Complete draft results with pick positions, keeper status, and team attribution
  - Full draft history with all rounds and picks
  - Player draft metadata showing original draft position and team
  - Keeper identification with 🔒 indicators
  - Free agent tracking for undrafted players
- **Player Information**: Search players, get statistics, and trending data
- **Matchup Analysis**: View current and historical matchups with real-time scoring
- **Trade Analysis**: Analyze potential trade targets and evaluate roster needs
- **Intelligent Caching**: Optimized API usage with TTL-based caching
- **Rate Limiting**: Respects Sleeper API limits with exponential backoff
- **Multiple Deployment Options**: Run locally with Claude Desktop (stdio) or as a containerized service (SSE/HTTP) in Docker/Portainer
- **Health Checks**: Built-in health and readiness endpoints for container orchestration

## Installation

### Prerequisites

- Python 3.8 or higher
- Claude Desktop application

### Install from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd sleeper-mcp-server
```

2. Install the package:
```bash
pip install -e .
```

3. For development with testing and linting tools:
```bash
pip install -e ".[dev]"
```

### Docker Installation

For containerized deployment (ideal for Portainer or orchestrated environments):

```bash
# Build the Docker image
docker build -t sleeper-mcp:latest .

# Run the container with SSE transport
docker run -it -e TRANSPORT=sse -e SSE_PORT=8000 -p 8000:8000 sleeper-mcp:latest
```

Or use docker-compose for easier management (see [Docker & Portainer Setup](#docker--portainer-setup) below).

## Configuration & Deployment

### Transport Types

The sleeper-mcp-server supports two transport modes for different deployment scenarios:

**Stdio Transport (Default)** - For local development and Claude Desktop integration
- Spawned on-demand by Claude Desktop
- Best for: Personal use, development environments
- Configuration: No special setup needed; works with standard Claude Desktop config

**SSE/HTTP Transport** - For containerized deployment in Docker/Portainer
- Runs as a persistent background service
- Exposes REST endpoints for health checks and monitoring
- Best for: Production deployments, container orchestration, Portainer management
- Configuration: Set `TRANSPORT=sse` environment variable

### Claude Desktop MCP Configuration

Add the following configuration to your Claude Desktop MCP settings file:

**Location of config file:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Basic Configuration:**
```json
{
  "mcpServers": {
    "sleeper": {
      "command": "python",
      "args": ["-m", "sleeper_mcp_server"],
      "env": {
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": [
        "get_user_leagues",
        "get_league_info",
        "search_players",
        "get_trending_players"
      ]
    }
  }
}
```

**Advanced Configuration with Custom Settings:**
```json
{
  "mcpServers": {
    "sleeper": {
      "command": "python",
      "args": ["-m", "sleeper_mcp_server"],
      "env": {
        "SLEEPER_API_BASE_URL": "https://api.sleeper.app/v1",
        "CACHE_TTL_SECONDS": "3600",
        "LOG_LEVEL": "INFO",
        "MAX_RETRIES": "3"
      },
      "disabled": false,
      "autoApprove": [
        "get_user_leagues",
        "get_league_info",
        "get_league_rosters",
        "get_league_rosters_with_draft_info",
        "get_league_users",
        "get_roster_user_mapping",
        "get_league_draft",
        "search_players",
        "get_trending_players",
        "get_player_stats",
        "get_matchups",
        "get_matchup_scores"
      ]
    }
  }
}
```

### Environment Variables

**Transport Configuration:**
| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | Transport type (`stdio` for Claude Desktop, `sse` for containers) | `stdio` |
| `SSE_PORT` | Port for SSE/HTTP server (when TRANSPORT=sse) | `8000` |
| `SSE_HOST` | Host to bind SSE/HTTP server (when TRANSPORT=sse) | `0.0.0.0` |

**API Configuration:**
| Variable | Description | Default |
|----------|-------------|---------|
| `SLEEPER_API_BASE_URL` | Sleeper API endpoint | `https://api.sleeper.app/v1` |
| `CACHE_TTL_SECONDS` | Default cache TTL in seconds | `3600` |
| `MAX_RETRIES` | Maximum API retry attempts | `3` |

**Logging:**
| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |

### Docker & Portainer Setup

#### Dockerfile

Create a `Dockerfile` in the repository root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy repository files
COPY . .

# Install the package
RUN pip install -e .

# Configure for SSE transport
ENV TRANSPORT=sse
ENV SSE_PORT=8000
ENV SSE_HOST=0.0.0.0

# Expose the port
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the server
CMD ["python", "-m", "sleeper_mcp_server"]
```

#### Docker Compose

Create a `docker-compose.yml` file for easy local testing:

```yaml
version: '3.8'

services:
  sleeper-mcp:
    build: .
    container_name: sleeper-mcp-server
    environment:
      TRANSPORT: sse
      SSE_PORT: 8000
      SSE_HOST: 0.0.0.0
      LOG_LEVEL: INFO
      SLEEPER_API_BASE_URL: https://api.sleeper.app/v1
      CACHE_TTL_SECONDS: 3600
      MAX_RETRIES: 3
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

#### Portainer Deployment

To deploy in Portainer:

1. **Create Stack via UI:**
   - Go to Stacks → Add Stack
   - Paste the docker-compose.yml content above
   - Or upload the docker-compose.yml file

2. **Configure Environment Variables:**
   - In the stack editor, set environment variables before deploying:
     - `TRANSPORT`: `sse`
     - `SSE_PORT`: `8000`
     - `LOG_LEVEL`: `INFO`
     - `SLEEPER_API_BASE_URL`: `https://api.sleeper.app/v1`

3. **Deploy:**
   - Click Deploy Stack
   - Monitor the container in Portainer dashboard

4. **Verify:**
   - Check container status (should be Running)
   - Access health endpoint: `http://<host>:8000/health`
   - Access readiness endpoint: `http://<host>:8000/readiness`

#### Using Environment Files (.env)

For Portainer deployments, use `.env` files to manage environment variables:

Create a `.env` file:
```env
TRANSPORT=sse
SSE_PORT=8000
SSE_HOST=0.0.0.0
LOG_LEVEL=INFO
SLEEPER_API_BASE_URL=https://api.sleeper.app/v1
CACHE_TTL_SECONDS=3600
MAX_RETRIES=3
```

**Important:** Never commit `.env` files to version control. Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

## Available MCP Tools

### League Tools

#### `get_user_leagues`
Get all leagues for a username in a specific season.

**Parameters:**
- `username` (required): Sleeper username to look up
- `season` (optional): Season year (default: "2024")

**Example Usage:**
```
Show me all leagues for username "john_doe" in 2024
```

#### `get_league_info`
Get detailed information about a specific league.

**Parameters:**
- `league_id` (required): League ID to retrieve information for

**Example Usage:**
```
Get information for league ID "123456789"
```

#### `get_league_rosters`
Get all team rosters in a league.

**Parameters:**
- `league_id` (required): League ID to retrieve rosters for

**Example Usage:**
```
Show me all rosters in league "123456789"
```

#### `get_league_users`
Get all users/participants in a league.

**Parameters:**
- `league_id` (required): League ID to retrieve users for

**Example Usage:**
```
Who are the users in league "123456789"?
```

#### `get_league_rosters_with_draft_info`
Get all team rosters in a league with complete draft position metadata for each player.

**Parameters:**
- `league_id` (required): League ID to retrieve rosters for

**Example Usage:**
```
Show me all rosters with draft information for league "123456789"
```

#### `get_roster_user_mapping`
Get a clear mapping of roster IDs to user names for a league.

**Parameters:**
- `league_id` (required): League ID to get roster-user mapping for

**Example Usage:**
```
Show me the roster to user mapping for league "123456789"
```

#### `get_league_draft`
Get complete draft results and pick information for a league.

**Parameters:**
- `league_id` (required): League ID to get draft information for

**Example Usage:**
```
Show me the draft results for league "123456789"
```

### Player Tools

#### `search_players`
Search for players by name with optional position filtering.

**Parameters:**
- `query` (required): Player name or partial name to search for
- `position` (optional): Position filter (QB, RB, WR, TE, K, DEF)

**Example Usage:**
```
Search for players named "Josh Allen"
Find all quarterbacks with "Josh" in their name
```

#### `get_trending_players`
Get trending players (most added/dropped).

**Parameters:**
- `sport` (optional): Sport type (default: "nfl")
- `add_drop` (optional): Type of trend - "add" or "drop" (default: "add")

**Example Usage:**
```
Show me the most added players this week
What players are being dropped the most?
```

#### `get_player_stats`
Get player statistics for a specific season.

**Parameters:**
- `player_id` (required): Player ID to get stats for
- `season` (optional): Season year (default: "2024")

**Example Usage:**
```
Get stats for player ID "4046" in 2024
```

### Matchup Tools

#### `get_matchups`
Get matchups for a specific week in a league.

**Parameters:**
- `league_id` (required): League ID to retrieve matchups for
- `week` (required): Week number (1-22)

**Example Usage:**
```
Show me week 5 matchups for league "123456789"
```

#### `get_matchup_scores`
Get real-time scoring information for matchups in a specific week.

**Parameters:**
- `league_id` (required): League ID to retrieve scores for
- `week` (required): Week number (1-22)

**Example Usage:**
```
What are the current scores for week 8 in league "123456789"?
```

### Trade Tools

#### `analyze_trade_targets`
Analyze potential trade targets for a roster based on positional needs.

**Parameters:**
- `league_id` (required): League ID to analyze
- `roster_id` (required): Roster ID requesting trade analysis
- `position` (optional): Position to focus analysis on (QB, RB, WR, TE, K, DEF)

**Example Usage:**
```
Analyze trade targets for roster 3 in league "123456789"
Find running back trade targets for my roster
```

#### `evaluate_roster_needs`
Evaluate roster strengths and weaknesses across all positions.

**Parameters:**
- `league_id` (required): League ID to analyze
- `roster_id` (required): Roster ID to evaluate

**Example Usage:**
```
Evaluate the strengths and weaknesses of roster 1 in league "123456789"
```

## API Rate Limiting and Caching

### Rate Limiting

The server implements intelligent rate limiting to respect Sleeper API guidelines:

- **Rate Limit**: Follows Sleeper's documented rate limits
- **Retry Logic**: Exponential backoff (1s, 2s, 4s, 8s) for rate-limited requests
- **Queue Management**: Requests are queued during rate limit periods
- **User Feedback**: Clear messages when rate limits are encountered

### Caching Strategy

Different data types have optimized cache TTL values:

| Data Type | Cache TTL | Reason |
|-----------|-----------|---------|
| Player Data | 1 hour | Relatively static during season |
| League Settings | 24 hours | Rarely change mid-season |
| Draft Data | 24 hours | Historical data, doesn't change |
| Matchup Data (active) | 5 minutes | Real-time scoring updates |
| Matchup Data (completed) | 1 hour | Historical data is stable |
| Trending Players | 30 minutes | Updated frequently |
| Roster Data | 15 minutes | Changes with transactions |
| Roster Data (with draft) | 15 minutes | Changes with transactions |

**Cache Features:**
- In-memory caching for optimal performance
- TTL-based expiration
- Automatic cache invalidation
- Cache hit/miss logging for monitoring

## Usage Examples

### Basic League Queries

```
# Get your leagues
"Show me all leagues for username 'myusername'"

# Get league details
"What are the settings for league ID '123456789'?"

# View rosters
"Show me all the rosters in my main league"

# View rosters with draft information
"Show me all rosters with draft info - I want to see where each player was drafted and by whom"
```

### Player Research

```
# Search for players
"Find all players named 'Cooper'"

# Get trending players
"What players are being added the most this week?"

# Player statistics
"Show me Josh Allen's stats for 2024"
```

### Matchup Analysis

```
# Current week matchups
"What are this week's matchups in my league?"

# Live scoring
"What are the current scores for week 8?"

# Historical data
"Show me the results from week 3"
```

### Draft Analysis

```
# Complete draft results
"Show me the draft results for my league"

# Roster with draft info
"Show me all rosters with draft information - I want to see where each player was drafted"

# Keeper analysis
"Which players were kept from last year and what was their original draft cost?"

# Draft value analysis
"Show me players who are outperforming their draft position"
```

### Trade Analysis

```
# Find trade partners
"Who should I target for a trade in my league? I need a running back"

# Roster evaluation
"Analyze my roster strengths and weaknesses"

# Specific position analysis
"Find quarterback trade targets for my team"
```

## Health Checks & Monitoring

When running in SSE/HTTP mode, the server provides endpoints for health monitoring:

### GET /health

Simple health check endpoint. Returns 200 OK if the server is running.

```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### GET /readiness

Readiness probe that checks if the server has completed initialization. Returns 503 if still initializing.

```bash
curl http://localhost:8000/readiness
# Response (ready): {"status": "ready"}
# Response (initializing): {"status": "initializing"} [HTTP 503]
```

### Docker Health Checks

The provided Dockerfile includes a health check configuration:

```dockerfile
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

This allows Docker and container orchestration systems to:
- Automatically restart unhealthy containers
- Prevent traffic to unhealthy instances
- Monitor service health in dashboards

### Portainer Monitoring

In Portainer:
1. View container status and health in the dashboard
2. Check logs for errors: Container → Logs
3. Monitor resource usage: Container → Stats
4. Test endpoints manually via Console

## Security & Credentials

### Handling API Keys and Passwords

**Development Environment:**
- Store credentials in a `.env` file (never commit to git)
- Load from `.env` using environment variables
- Example `.env`:
  ```env
  SLEEPER_API_BASE_URL=https://api.sleeper.app/v1
  ```

**Production Environment (Portainer/Docker):**
- Use Docker secrets (recommended for production)
- Or use environment variables passed at deployment time
- Never hardcode credentials in Dockerfile

**Docker Secrets Example:**
```yaml
version: '3.8'

secrets:
  sleeper_api_url:
    file: ./secrets/sleeper_api_url.txt

services:
  sleeper-mcp:
    image: sleeper-mcp:latest
    secrets:
      - sleeper_api_url
    environment:
      SLEEPER_API_BASE_URL_FILE: /run/secrets/sleeper_api_url
```

### Masking Sensitive Information in Logs

**Important:** Be cautious with sensitive data in logs:

- ⚠️ **DEBUG mode logs verbose information** - Avoid DEBUG in production
- Log Level defaults to `INFO` - recommended for most environments
- Sensitive API responses are NOT logged by default
- User data from the Sleeper API is only logged with DEBUG level

**Production Recommendation:**
```bash
# Ensure LOG_LEVEL is set to INFO or higher
LOG_LEVEL=INFO python -m sleeper_mcp_server
```

### Container Security Best Practices

1. **Run as non-root user (optional enhancement):**
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

2. **Use minimal base images:**
   - Use `python:3.11-slim` (recommended) instead of full Python image
   - Reduces attack surface and image size

3. **Network isolation:**
   - Bind to specific interface instead of all interfaces
   - Set `SSE_HOST=127.0.0.1` for localhost-only access
   - Use firewalls to restrict access

4. **Environment variable security:**
   - Use Docker secrets instead of plain environment variables
   - Rotate credentials regularly
   - Limit secret access to necessary containers

5. **Monitoring and logging:**
   - Aggregate logs from containers
   - Monitor for suspicious activity
   - Use container scanning tools to check for vulnerabilities

### Credential Rotation

For long-running containers:
- Rotate API credentials periodically
- Restart containers to pick up new credentials
- Use container orchestration to manage rolling updates

## Troubleshooting

### Common Issues

#### 1. Server Won't Start

**Symptoms:**
- Claude Desktop shows "Server unavailable" error
- No response from MCP tools

**Solutions:**
- Verify Python installation: `python --version` (should be 3.8+)
- Check package installation: `pip show sleeper-mcp-server`
- Verify Claude Desktop configuration syntax
- Check logs for specific error messages

#### 2. Authentication/API Errors

**Symptoms:**
- "API request failed" errors
- "Invalid league ID" messages

**Solutions:**
- Verify league IDs are correct (18-character strings)
- Check username spelling and case sensitivity
- Ensure Sleeper API is accessible from your network
- Try again after a few minutes (may be temporary API issues)

#### 3. Rate Limiting Issues

**Symptoms:**
- "Rate limit exceeded" messages
- Slow response times
- "Please wait" messages

**Solutions:**
- Wait for the specified retry period
- Reduce frequency of requests
- Use cached data when possible
- Check if multiple instances are running

#### 4. Cache Issues

**Symptoms:**
- Stale data being returned
- Inconsistent results

**Solutions:**
- Restart the MCP server to clear cache
- Adjust `CACHE_TTL_SECONDS` environment variable
- Check system memory availability

#### 5. Configuration Problems

**Symptoms:**
- Tools not appearing in Claude Desktop
- Environment variables not working

**Solutions:**
- Validate JSON syntax in Claude Desktop config
- Restart Claude Desktop after configuration changes
- Check file permissions on config file
- Verify environment variable names and values

### Debug Mode

Enable debug logging for detailed troubleshooting:

```json
{
  "mcpServers": {
    "sleeper": {
      "command": "python",
      "args": ["-m", "sleeper_mcp_server"],
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Getting Help

1. **Check Logs**: Enable DEBUG logging to see detailed error information
2. **Verify Configuration**: Ensure Claude Desktop MCP configuration is correct
3. **Test API Access**: Verify you can access Sleeper API directly
4. **Update Dependencies**: Ensure all packages are up to date
5. **Restart Services**: Try restarting both the MCP server and Claude Desktop

### Performance Optimization

#### For Large Leagues
- Use position filtering in player searches
- Cache frequently accessed league data
- Limit historical matchup queries

#### For Multiple Leagues
- Batch similar requests when possible
- Use appropriate cache TTL settings
- Monitor rate limit usage

## Development

### Running with Different Transports

**Stdio Transport (default - for Claude Desktop):**
```bash
python -m sleeper_mcp_server
```

**SSE Transport (for Docker/Portainer testing):**
```bash
TRANSPORT=sse python -m sleeper_mcp_server
# Server will listen on http://localhost:8000
```

### Running Tests

The project uses pytest with async support and coverage reporting. Configuration is in `pyproject.toml`.

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=sleeper_mcp_server

# Run specific test file
pytest tests/test_server.py

# Run with verbose output
pytest -v

# Run specific test marker
pytest -m "not slow"
```

Note: No tests currently exist, but the infrastructure is configured and ready. Tests for the SSE transport implementation are welcome contributions.

### Code Quality

```bash
# Format code
black sleeper_mcp_server/

# Sort imports
isort sleeper_mcp_server/

# Lint code
flake8 sleeper_mcp_server/

# Type checking
mypy sleeper_mcp_server/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Sleeper API](https://docs.sleeper.app/) for providing comprehensive fantasy football data including detailed draft information
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP framework
- [Claude Desktop](https://claude.ai/desktop) for MCP integration

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information about your problem

---

**Note**: This MCP server is not officially affiliated with Sleeper. It's a third-party integration that uses Sleeper's public API.
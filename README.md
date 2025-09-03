# Claude Code API Gateway

A simple, focused OpenAI-compatible API gateway for Claude Code with streaming support.
Leverage the Claude Code SDK use mode. Don't hack the token credentials.

## Getting Started

Use the Makefile to install the project or pip/uv.

![API Started](assets/api.png)

![Cline use](assets/cline.png)

![Cursor](assets/cursor.png)

![OpenWebUI](assets/openwebui.png)

![Roo Code config](assets/roocode.png)

![Roo Code chat](assets/roo_code.png) 

### Python Implementation
```bash
# Clone and setup
git clone https://github.com/codingworkflow/claude-code-api
cd claude-code-api

# Install dependencies & module
make install 

# Start the API server
make start
```

## Limitations

- There might be a limit on maximum input below normal "Sonnet 4" input as Claude Code usually doesn't ingest more than 25k tokens (despite the context being 100k).
- Claude Code auto-compacts context beyond 100k.
- Currently runs with bypass mode to avoid tool errors.
- Claude Code tools may need to be disabled to avoid overlap and background usage.
- Runs only on Linux/Mac as Claude Code doesn't run on Windows (you can use WSL).
- Note that Claude Code will default to accessing the current workspace environment/folder and is set to use bypass mode.


## Features

- **Claude-Only Models**: Supports exactly the 4 Claude models that Claude Code CLI offers
- **OpenAI Compatible**: Drop-in replacement for OpenAI API endpoints
- **Streaming Support**: Real-time streaming responses 
- **Simple & Clean**: No over-engineering, focused implementation
- **Claude Code Integration**: Leverages Claude Code CLI with streaming output

## Supported Models

- `claude-opus-4-1-20250805` - Claude Opus 4.1 (Latest, most powerful)
- `claude-opus-4-20250514` - Claude Opus 4
- `claude-sonnet-4-20250514` - Claude Sonnet 4
- `claude-3-7-sonnet-20250219` - Claude Sonnet 3.7
- `claude-3-5-sonnet-20241022` - Claude Sonnet 3.5 (Latest Sonnet)
- `claude-3-5-haiku-20241022` - Claude Haiku 3.5 (Fast & cost-effective)

## Quick Start

### Prerequisites
- Python 3.10+
- Claude Code CLI installed and accessible
- Valid Anthropic API key configured in Claude Code (ensure it works in current directory src/)

### Installation & Setup

```bash
# Clone and setup
git clone https://github.com/codingworkflow/claude-code-api
cd claude-code-api

# Copy environment example and configure
cp .env.example .env
# Edit .env to configure your settings (especially API keys for production)

# Install dependencies
make install

# Run tests to verify setup
make test

# Start the API server (development with auto-reload)
make start

# Start the API server (production, foreground)
make start-prod

# Start the API server (production, background - survives SSH disconnect)
make start-prod-bg

# Stop background server
make stop

# Restart background server  
make restart

# Check server status and recent logs
make status

# Follow server logs in real-time
make logs
```

The API will be available at:
- **API**: http://localhost:8010
- **Docs**: http://localhost:8010/docs  
- **Health**: http://localhost:8010/health

## Production Deployment

For production use, especially on remote servers:

```bash
# Start in background (survives SSH disconnect)
make start-prod-bg

# Check status
make status

# View logs
make logs

# Restart if needed
make restart

# Stop when needed
make stop

## Makefile Commands

### 🔧 使用方式

1. **开发环境**：`make start` （自动重载，适合开发）
2. **生产前台**：`make start-prod` （稳定，但SSH断开会停止）  
3. **生产后台**：`make start-prod-bg` （最稳定，SSH断开仍运行）

### Core Commands
```bash
# Development
make install        # Install dependencies
make start          # Start server (development with auto-reload)

# Production
make start-prod     # Start server (production, foreground)
make start-prod-bg  # Start server (production, background)

# Process Management
make stop           # Stop background server
make restart        # Restart background server  
make status         # Show status and recent logs
make logs           # Follow logs in real-time

# Testing & Cleanup
make test           # Run tests
make clean          # Clean cache files
make kill PORT=X    # Kill process on specific port
```

### Testing
```bash
make test           # Run all tests
make test-fast      # Run tests (skip slow ones)
make test-hello     # Test hello world with Haiku
make test-health    # Test health check only
make test-models    # Test models API only
make test-chat      # Test chat completions only
make quick-test     # Quick validation of core functionality
```

### Development
```bash
make dev-setup      # Complete development setup
make lint           # Run linting checks
make format         # Format code with black/isort
make type-check     # Run type checking
make clean          # Clean up cache files
```

### Information
```bash
make help           # Show all available commands
make models         # Show supported Claude models
make info           # Show project information
make check-claude   # Check if Claude Code CLI is available
```

## API Usage

### Authentication

By default, the API runs without authentication for development. **For production use, enable API key authentication:**

1. **Configure API Keys in `.env`:**
```bash
# Enable authentication
REQUIRE_AUTH=true

# Add your API keys (comma-separated)
API_KEYS=your-secure-api-key-1,your-secure-api-key-2

# Generate secure keys using provided script:
python3 scripts/generate_api_keys.py -n 2 --env

# Or manually with openssl:
# openssl rand -hex 32
```

2. **Use API Key in Requests:**

**Option A: Authorization Header (Recommended)**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-secure-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**Option B: X-API-Key Header**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "x-api-key: your-secure-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

3. **Rate Limiting:**
- Default: 100 requests per minute per API key
- Configurable via `RATE_LIMIT_REQUESTS_PER_MINUTE` in `.env`

### Chat Completions

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-haiku-20241022",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### List Models

```bash
curl http://localhost:8000/v1/models
```

### Streaming Chat

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-haiku-20241022", 
    "messages": [
      {"role": "user", "content": "Tell me a joke"}
    ],
    "stream": true
  }'
```

## Project Structure

```
claude-code-api/
├── claude_code_api/
│   ├── main.py              # FastAPI application
│   ├── api/                 # API endpoints
│   │   ├── chat.py          # Chat completions
│   │   ├── models.py        # Models API
│   │   ├── projects.py      # Project management
│   │   └── sessions.py      # Session management
│   ├── core/                # Core functionality
│   │   ├── auth.py          # Authentication
│   │   ├── claude_manager.py # Claude Code integration
│   │   ├── session_manager.py # Session management
│   │   ├── config.py        # Configuration
│   │   └── database.py      # Database layer
│   ├── models/              # Data models
│   │   ├── claude.py        # Claude-specific models
│   │   └── openai.py        # OpenAI-compatible models
│   ├── utils/               # Utilities
│   │   ├── streaming.py     # Streaming support
│   │   └── parser.py        # Output parsing
│   └── tests/               # Test suite
├── Makefile                 # Development commands
├── pyproject.toml          # Project configuration
├── setup.py                # Package setup
└── README.md               # This file
```

## Testing

The test suite validates:
- Health check endpoints
- Models API (Claude models only)
- Chat completions with Haiku model
- Hello world functionality
- OpenAI compatibility (structure)
- Error handling

Run specific test suites:
```bash
make test-hello    # Test hello world with Haiku
make test-models   # Test models API
make test-chat     # Test chat completions
```

## Development

### Setup Development Environment
```bash
make dev-setup
```

### Code Quality
```bash
make format        # Format code
make lint          # Check linting
make type-check    # Type checking
```

### Quick Validation
```bash
make quick-test    # Test core functionality
```

## Deployment

### Check Deployment Readiness
```bash
make deploy-check
```

### Production Server
```bash
make start-prod    # Start with multiple workers
```
Use http://127.0.0.1:8000/v1 as OpenAPI endpoint

## Configuration

Key settings in `claude_code_api/core/config.py`:
- `claude_binary_path`: Path to Claude Code CLI
- `project_root`: Root directory for projects
- `database_url`: Database connection string
- `require_auth`: Enable/disable authentication

## Design Principles

1. **Simple & Focused**: No over-engineering
2. **Claude-Only**: Pure Claude gateway, no OpenAI models
3. **Streaming First**: Built for real-time streaming
4. **OpenAI Compatible**: Drop-in API compatibility
5. **Test-Driven**: Comprehensive test coverage

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0", 
  "claude_version": "1.x.x",
  "active_sessions": 0
}
```

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

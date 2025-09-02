# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code API Gateway - An OpenAI-compatible API gateway for Claude Code CLI with streaming support. This project creates a bridge between OpenAI-style API calls and the Claude Code CLI tool, enabling integration with tools that expect OpenAI API compatibility.

## Essential Commands

### Development
```bash
# Install dependencies and project
make install

# Start development server with auto-reload
make start

# Run tests
make test

# Run real API tests (requires running server)
make test-real
```

### Production
```bash
# Start production server
make start-prod

# Kill process on specific port
make kill PORT=8000
```

### Code Quality
```bash
# Format code with black/isort
black claude_code_api/ --line-length 88
isort claude_code_api/ --profile black

# Type checking
mypy claude_code_api/

# Clean cache files
make clean
```

## Architecture Overview

### Core Components

1. **API Layer** (`claude_code_api/api/`)
   - `chat.py`: Handles OpenAI-compatible chat completions endpoint
   - `models.py`: Lists available Claude models
   - `projects.py`: Manages project contexts
   - `sessions.py`: Handles Claude Code session management

2. **Core Services** (`claude_code_api/core/`)
   - `claude_manager.py`: Manages Claude Code CLI subprocess execution - critical for streaming responses
   - `session_manager.py`: Maintains active Claude sessions
   - `config.py`: Centralized configuration using pydantic-settings
   - `database.py`: SQLAlchemy database layer for session persistence
   - `auth.py`: Optional authentication middleware

3. **Models** (`claude_code_api/models/`)
   - `openai.py`: OpenAI-compatible request/response models
   - `claude.py`: Claude-specific model definitions

4. **Utilities** (`claude_code_api/utils/`)
   - `streaming.py`: SSE streaming implementation for real-time responses
   - `parser.py`: Parses Claude Code CLI JSON output

### Key Implementation Details

- **Claude Code Integration**: The system spawns Claude Code CLI processes with `--output-format stream-json` flag and captures the output for streaming
- **Working Directory**: Claude Code processes are started from the `claude_code_api/` directory to ensure API key access
- **Streaming**: Uses Server-Sent Events (SSE) to stream responses in OpenAI-compatible format
- **Model Mapping**: Maps OpenAI model names to Claude Code CLI model identifiers

### Supported Models
- `claude-opus-4-1-20250805` - Claude Opus 4.1 (Latest)
- `claude-opus-4-20250514` - Claude Opus 4
- `claude-sonnet-4-20250514` - Claude Sonnet 4
- `claude-3-7-sonnet-20250219` - Claude Sonnet 3.7
- `claude-3-5-sonnet-20241022` - Claude Sonnet 3.5 (Latest)
- `claude-3-5-haiku-20241022` - Claude Haiku 3.5

## Important Notes

- Claude Code CLI must be installed and accessible at the path specified in `config.py`
- The API runs on port 8000 by default
- Database uses SQLite by default (configurable in settings)
- Authentication is optional and disabled by default
- The project includes both Python and TypeScript implementations (Python is primary)
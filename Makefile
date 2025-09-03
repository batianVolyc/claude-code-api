# Claude Code API - Simple & Working

# Python targets
install:
	pip install -e .
	pip install requests

test:
	python3 -m pytest tests/ -v

test-real:
	python3 tests/test_real_api.py

start:
	uvicorn claude_code_api.main:app --host 127.0.0.1 --port 8010 --reload --reload-exclude="*.db*" --reload-exclude="*.log"

start-prod:
	uvicorn claude_code_api.main:app --host 127.0.0.1 --port 8010

# Production background commands
start-prod-bg:
	@echo "Starting Claude Code API in background..."
	@nohup uvicorn claude_code_api.main:app --host 127.0.0.1 --port 8010 > claude_api.log 2>&1 & echo $$! > claude_api.pid
	@echo "API server started in background with PID: $$(cat claude_api.pid)"
	@echo "Log file: claude_api.log"
	@echo "PID file: claude_api.pid"

stop:
	@if [ -f claude_api.pid ]; then \
		PID=$$(cat claude_api.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			kill $$PID && echo "Stopped Claude API server (PID: $$PID)"; \
			rm claude_api.pid; \
		else \
			echo "Process with PID $$PID not found, removing stale PID file."; \
			rm claude_api.pid; \
		fi; \
	else \
		echo "No PID file found. Use 'make kill PORT=8010' if server is still running."; \
	fi

restart:
	@echo "Restarting Claude Code API..."
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start-prod-bg

status:
	@if [ -f claude_api.pid ]; then \
		PID=$$(cat claude_api.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "Claude API server is running (PID: $$PID)"; \
			echo "Port: 8010"; \
			echo "Log: claude_api.log"; \
			if [ -f claude_api.log ]; then \
				echo "Last 5 log lines:"; \
				tail -5 claude_api.log; \
			fi; \
		else \
			echo "PID file exists but process not running. Cleaning up..."; \
			rm claude_api.pid; \
		fi; \
	else \
		echo "Claude API server is not running (no PID file found)"; \
	fi

logs:
	@if [ -f claude_api.log ]; then \
		tail -f claude_api.log; \
	else \
		echo "Log file not found. Make sure to start the server with 'make start-prod-bg'"; \
	fi

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

kill:
	@if [ -z "$(PORT)" ]; then \
		echo "Error: PORT parameter is required. Usage: make kill PORT=8001"; \
	else \
		echo "Looking for processes on port $(PORT)..."; \
		if [ "$$(uname)" = "Darwin" ] || [ "$$(uname)" = "Linux" ]; then \
			PID=$$(lsof -iTCP:$(PORT) -sTCP:LISTEN -t); \
			if [ -n "$$PID" ]; then \
				echo "Found process(es) with PID(s): $$PID"; \
				kill -9 $$PID && echo "Process(es) killed successfully."; \
			else \
				echo "No process found listening on port $(PORT)."; \
			fi; \
		else \
			echo "This command is only supported on Unix-like systems (Linux/macOS)."; \
		fi; \
	fi

help:
	@echo "Claude Code API Commands:"
	@echo ""
	@echo "Python API:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make test           - Run Python unit tests with real Claude integration"
	@echo "  make test-real      - Run REAL end-to-end tests (curls actual API)"
	@echo "  make start          - Start Python API server (development with reload)"
	@echo "  make start-prod     - Start Python API server (production, foreground)"
	@echo "  make start-prod-bg  - Start Python API server (production, background)"
	@echo "  make stop           - Stop background API server"
	@echo "  make restart        - Restart background API server"
	@echo "  make status         - Show API server status and recent logs"
	@echo "  make logs           - Follow API server logs (tail -f)"
	@echo ""
	@echo "TypeScript API:"
	@echo "  make install-js     - Install TypeScript dependencies" 
	@echo "  make test-js        - Run TypeScript unit tests"
	@echo "  make test-js-real   - Run Python test suite against TypeScript API"
	@echo "  make start-js       - Start TypeScript API server (production)"
	@echo "  make start-js-dev   - Start TypeScript API server (development with reload)"
	@echo "  make start-js-prod  - Build and start TypeScript API server (production)"
	@echo "  make build-js       - Build TypeScript project"
	@echo ""
	@echo "General:"
	@echo "  make clean       - Clean up Python cache files"
	@echo "  make kill PORT=X - Kill process on specific port"
	@echo ""
	@echo "IMPORTANT: Both implementations are functionally equivalent!"
	@echo "Use Python or TypeScript - both provide the same OpenAI-compatible API."

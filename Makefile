# Makefile for Assistant Service
.PHONY: default help clean-project environment-create environment-sync environment-delete environment-list sync-env format lint type-check unit-test functional-test integration-test all-test validate-branch validate-branch-strict test-validate-branch all-test-validate-branch api-run api-kill api-docs chat-ws chat-http service-build service-start service-stop service-quick-start service-validate auth-gcloud

# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================
# First time setup:     make environment-create
# Start development:    make api-run
# Chat with assistant:  make chat-ws (in another terminal)
# Run quality checks:   make validate-branch
# Run all tests:        make all-test-validate-branch
# Deploy locally:       make service-quick-start
# Clean everything:     make clean-project
#
# With OpenAI key:      OPENAI_API_KEY=sk-... make api-run
# Custom assistant:     ASSISTANT_ID=asst_... make api-run
# ==============================================================================

GREEN_LINE=@echo "\033[0;32m--------------------------------------------------\033[0m"
YELLOW_LINE=@echo "\033[0;33m--------------------------------------------------\033[0m"
RED_LINE=@echo "\033[0;31m--------------------------------------------------\033[0m"

SOURCE_DIR = assistant_service/ assistant_factory/
TEST_DIR = tests/
SCRIPTS_DIR = scripts/
PROJECT_VERSION := $(shell awk '/^\[project\]/ {flag=1; next} /^\[/{flag=0} flag && /^version/ {gsub(/"/, "", $$2); print $$2}' pyproject.toml)
PYTHON_VERSION := 3.10
CLIENT_ID = leogv

# Default API settings
API_HOST ?= 0.0.0.0
API_PORT ?= 8000
API_BASE_URL ?= http://localhost:$(API_PORT)
WS_BASE_URL ?= ws://localhost:$(API_PORT)

default: help

help: ## Display this help message
	@echo "\033[1;36mAssistant Service - Available Commands\033[0m"
	$(GREEN_LINE)
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}'
	$(GREEN_LINE)
	@echo "\033[1;33mExamples:\033[0m"
	@echo "  make environment-create                    # First time setup"
	@echo "  make api-run                              # Start API server"
	@echo "  make chat-ws                              # Chat via WebSocket (in new terminal)"
	@echo "  OPENAI_API_KEY=sk-... make api-run       # Run with API key"
	@echo "  make api-run ARGS='--port 8001'          # Custom port"

# ----------------------------
# Environment Management
# ----------------------------

clean-project: ## Clean Python caches and tooling artifacts
	@echo "🧹 Cleaning project caches..."
	find . -type d \( -name '.pytest_cache' -o -name '.ruff_cache' -o -name '.mypy_cache' -o -name '__pycache__' \) -exec rm -rf {} +
	@echo "✅ Project cleaned!"
	$(GREEN_LINE)

environment-create: ## Set up Python version, venv, and install dependencies
	@echo "🔧 Installing uv if missing..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "📦 Installing uv..."; \
		python3 -m pip install --user --upgrade uv; \
	else \
		echo "✅ uv is already installed"; \
	fi
	@echo "🐍 Setting up Python $(PYTHON_VERSION) environment..."
	uv python install $(PYTHON_VERSION)
	uv venv --python $(PYTHON_VERSION)
	@echo "📦 Installing project dependencies..."
	uv sync --extra dev
	uv pip install -e '.[dev]'
	@echo "🪝 Setting up pre-commit hooks..."
	uv run pre-commit install
	@echo "🎉 Environment setup complete!"
	$(GREEN_LINE)

environment-sync: ## Re-sync project dependencies using uv
	@echo "🔄 Syncing project dependencies..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make environment-create' first."; \
		exit 1; \
	fi
	uv sync --extra dev
	uv pip install -e '.[dev]'
	@echo "✅ Dependencies synced successfully!"
	$(GREEN_LINE)

sync-env: environment-sync ## Alias for environment-sync

environment-delete: ## Remove the virtual environment folder
	@echo "🗑️  Deleting virtual environment..."
	rm -rf .venv
	@echo "✅ Virtual environment removed!"
	$(GREEN_LINE)

environment-list: ## List installed packages
	@echo "📦 Installed packages:"
	$(YELLOW_LINE)
	uv pip list
	$(GREEN_LINE)

# ----------------------------
# Code Quality
# ----------------------------

format: ## Format codebase using ruff
	@echo "🎨 Formatting code with ruff..."
	uv run ruff format
	@echo "✅ Code formatted!"
	$(GREEN_LINE)

lint: ## Lint code using ruff and autofix issues
	@echo "🔍 Running lint checks with ruff..."
	uv run ruff check . --fix
	@echo "✅ Linting complete!"
	$(GREEN_LINE)

type-check: ## Perform static type checks using mypy
	@echo "🔎 Running type checks with mypy..."
	uv run --extra dev mypy $(SOURCE_DIR)
	@echo "✅ Type checking complete!"
	$(GREEN_LINE)

# ----------------------------
# Tests
# ----------------------------

unit-test: ## Run unit tests with pytest
	@echo "🧪 Running UNIT tests..."
	uv run python -m pytest -vv --verbose -s $(TEST_DIR)
	$(GREEN_LINE)

functional-test: ## Run functional tests with pytest
	@echo "🧪 Running FUNCTIONAL tests..."
	uv run python -m pytest -m functional -vv --verbose -s $(TEST_DIR)
	$(GREEN_LINE)

integration-test: ## Run integration tests with pytest
	@echo "🧪 Running INTEGRATION tests..."
	uv run python -m pytest -m integration -vv --verbose -s $(TEST_DIR)
	$(GREEN_LINE)

all-test: ## Run all tests with coverage report
	@echo "🧪 Running ALL tests with coverage..."
	uv run python -m pytest -m "not integration" -vv -s $(TEST_DIR) \
		--cov=assistant_service \
		--cov=assistant_factory \
		--cov-config=pyproject.toml \
		--cov-fail-under=75 \
		--cov-report=term-missing
	$(GREEN_LINE)

# ----------------------------
# Branch Validation
# ----------------------------

validate-branch: ## Run formatting, linting, and type checks
	@echo "🔍 Running validation checks..."
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) type-check
	@echo "🎉 Branch validation successful - ready for PR!"
	$(GREEN_LINE)

validate-branch-strict: ## Run full validation with environment sync
	$(MAKE) sync-env
	$(MAKE) validate-branch

test-validate-branch: ## Validate branch and run unit tests
	$(MAKE) validate-branch
	$(MAKE) unit-test
	$(MAKE) clean-project

all-test-validate-branch: ## Validate branch and run all tests
	$(MAKE) validate-branch
	$(MAKE) all-test
	$(MAKE) clean-project

# ----------------------------
# Local Development - API
# ----------------------------

api-run: environment-sync ## Start API server in dev mode. Example: OPENAI_API_KEY=sk-... make api-run
	@echo "🚀 Starting Assistant Service API..."
	@echo "🤖 OpenAI Key: $(if $(OPENAI_API_KEY),✅ Set,❌ Not Set)"
	@echo "🆔 Assistant ID: $(if $(ASSISTANT_ID),$(ASSISTANT_ID),Not specified)"
	@echo ""
	@echo "📝 Configuration examples:"
	@echo "   OPENAI_API_KEY=sk-... make api-run                    # With API key"
	@echo "   ASSISTANT_ID=asst_... make api-run                    # With specific assistant"
	@echo "   CLIENT_ID=my-client make api-run                      # With custom client"
	@echo ""
	@echo "🔧 Advanced options using ARGS:"
	@echo "   make api-run ARGS='--port 8001 --host localhost'      # Custom host/port"
	@echo "   make api-run ARGS='--log-level debug'                 # Debug logging"
	@echo "   make api-run ARGS='--help'                            # Show all options"
	@echo ""
	uv run python $(SCRIPTS_DIR)/isolation/api_layer.py --host $(API_HOST) --port $(API_PORT) --reload $(ARGS)
	$(GREEN_LINE)

api-kill: ## Kill running API development server
	@echo "🛑 Stopping API development server..."
	@pkill -f "scripts/isolation/api_layer.py" && echo "✅ API server stopped successfully" || echo "ℹ️  No API server process found"
	$(GREEN_LINE)

api-docs: environment-sync ## Open Swagger UI documentation (starts API if not running)
	@echo "🚀 Starting Assistant Service API with documentation..."
	@echo "📖 Swagger UI will be available at: http://localhost:$(API_PORT)/docs"
	@echo "📋 ReDoc will be available at: http://localhost:$(API_PORT)/redoc"
	@echo "📄 OpenAPI JSON at: http://localhost:$(API_PORT)/openapi.json"
	@echo ""
	@echo "🌐 Opening Swagger UI in browser..."
	@(sleep 2 && open http://localhost:$(API_PORT)/docs 2>/dev/null || xdg-open http://localhost:$(API_PORT)/docs 2>/dev/null || echo "Please open http://localhost:$(API_PORT)/docs manually") &
	uv run python $(SCRIPTS_DIR)/isolation/api_layer.py --host $(API_HOST) --port $(API_PORT) --reload
	$(GREEN_LINE)

# ----------------------------
# Local Development - Chat
# ----------------------------

chat-ws: ## Start WebSocket chat client (requires running API server)
	@echo "💬 Starting WebSocket chat client..."
	@echo "🔌 Connecting to: $(WS_BASE_URL)"
	@echo ""
	@if ! curl -s -f $(API_BASE_URL)/ > /dev/null 2>&1; then \
		echo "❌ API server not running. Start it first with: make api-run"; \
		exit 1; \
	fi
	uv run python $(SCRIPTS_DIR)/conversation/websocket_client.py --base-url $(WS_BASE_URL)
	$(GREEN_LINE)

chat-http: ## Start HTTP chat client (requires running API server)
	@echo "💬 Starting HTTP chat client..."
	@echo "🔌 Connecting to: $(API_BASE_URL)"
	@echo ""
	@if ! curl -s -f $(API_BASE_URL)/ > /dev/null 2>&1; then \
		echo "❌ API server not running. Start it first with: make api-run"; \
		exit 1; \
	fi
	uv run python $(SCRIPTS_DIR)/conversation/http_client.py --base-url $(API_BASE_URL)
	$(GREEN_LINE)

chat-test: ## Test chat with a sample message (requires running API server)
	@echo "🧪 Testing chat functionality..."
	@if ! curl -s -f $(API_BASE_URL)/ > /dev/null 2>&1; then \
		echo "❌ API server not running. Start it first with: make api-run"; \
		exit 1; \
	fi
	@echo "1. Starting new conversation..."
	@THREAD_ID=$$(curl -s -X GET "$(API_BASE_URL)/start" | python3 -c "import sys, json; print(json.load(sys.stdin)['thread_id'])"); \
	echo "   Thread ID: $$THREAD_ID"; \
	echo ""; \
	echo "2. Sending test message..."; \
	curl -s -X POST "$(API_BASE_URL)/chat" \
		-H "Content-Type: application/json" \
		-d "{\"thread_id\": \"$$THREAD_ID\", \"message\": \"Hello! What can you help me with?\"}" | \
		python3 -m json.tool
	$(GREEN_LINE)

# ----------------------------
# Build and Deployment
# ----------------------------

service-build: environment-sync ## Build Docker image for assistant service
	@echo "🏗️  Building Assistant Service Docker image..."
	@echo "📦 Version: $(PROJECT_VERSION)"
	@echo "👤 Client: $(CLIENT_ID)"
	cp assistant_factory/client_spec/$(CLIENT_ID)/functions.py assistant_service/functions.py
	DOCKER_BUILDKIT=1 docker build --target=runtime . -t assistant-service:latest -t assistant-service:$(PROJECT_VERSION)
	@echo "✅ Docker image built successfully!"
	$(GREEN_LINE)


auth-gcloud: ## Authenticate with Google Cloud
	@echo "🔐 Authenticating with Google Cloud..."
	gcloud auth application-default login
	@echo "✅ Authentication complete!"
	$(GREEN_LINE)
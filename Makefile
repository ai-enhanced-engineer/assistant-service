# Makefile for Assistant Service

.PHONY: default help clean-project environment-create environment-sync environment-delete environment-list sync-env format lint type-check unit-test functional-test integration-test all-test validate-branch validate-branch-strict test-validate-branch all-test-validate-branch local-run build-engine auth-gcloud

GREEN_LINE=@echo "\033[0;32m--------------------------------------------------\033[0m"

SOURCE_DIR = assistant_engine/ assistant_factory/
TEST_DIR = tests/assistant_engine/ assistant_factory/tests/
PROJECT_VERSION := $(shell awk '/^\[project\]/ {flag=1; next} /^\[/{flag=0} flag && /^version/ {gsub(/"/, "", $$2); print $$2}' pyproject.toml)
PYTHON_VERSION := 3.10
CLIENT_ID = leogv

default: help

help: ## Display this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}'

# ----------------------------
# Environment Management
# ----------------------------

clean-project: ## Clean Python caches and tooling artifacts
	@echo "Cleaning project caches..."
	find . -type d \( -name '.pytest_cache' -o -name '.ruff_cache' -o -name '.mypy_cache' -o -name '__pycache__' \) -exec rm -rf {} +
	$(GREEN_LINE)

environment-create: ## Set up Python version, venv, and install dependencies
	@echo "Installing uv and pre-commit if missing..."
	@if ! command -v uv >/dev/null 2>&1; then \
		python3 -m pip install --user --upgrade uv; \
	fi
	@echo "Setting up Python $(PYTHON_VERSION) environment..."
	uv python install $(PYTHON_VERSION)
	uv venv --python $(PYTHON_VERSION)
	uv sync --extra dev
	uv pip install -e '.[dev]'
	uv pip install pre-commit
	uv run pre-commit install
	$(GREEN_LINE)

environment-sync: ## Re-sync project dependencies using uv
	@echo "Syncing up environment..."
	uv sync --extra dev
	uv pip install -e '.[dev]'
	$(GREEN_LINE)

sync-env: environment-sync ## Alias for environment-sync

environment-delete: ## Remove the virtual environment folder
	@echo "Deleting virtual environment..."
	rm -rf .venv
	$(GREEN_LINE)

environment-list: ## List installed packages
	@echo "Listing packages in environment..."
	uv pip list

# ----------------------------
# Code Quality
# ----------------------------

format: ## Format codebase using ruff
	@echo "Formatting code with ruff..."
	uv run ruff format
	$(GREEN_LINE)

lint: ## Lint code using ruff and autofix issues
	@echo "Running lint checks with ruff..."
	uv run ruff check . --fix
	$(GREEN_LINE)

type-check: ## Perform static type checks using mypy
	@echo "Running type checks with mypy..."
	uv run --extra dev mypy $(SOURCE_DIR)
	$(GREEN_LINE)

# ----------------------------
# Tests
# ----------------------------

unit-test: ## Run unit tests with pytest
	@echo "Running UNIT tests with pytest..."
	uv run python -m pytest -vv --verbose -s $(TEST_DIR)

functional-test: ## Run functional tests with pytest
	@echo "Running FUNCTIONAL tests with pytest..."
	uv run python -m pytest -m functional -vv --verbose -s $(TEST_DIR)

integration-test: ## Run integration tests with pytest
	@echo "Running INTEGRATION tests with pytest..."
	uv run python -m pytest -m integration -vv --verbose -s $(TEST_DIR)

all-test: ## Run all tests with coverage report
	@echo "Running ALL tests with pytest..."
	uv run python -m pytest -m "not integration" -vv -s $(TEST_DIR) \
		--cov=assistant_engine \
		--cov=assistant_factory \
		--cov-config=pyproject.toml \
		--cov-fail-under=80 \
		--cov-report=term-missing

# ----------------------------
# Branch Validation
# ----------------------------

validate-branch: ## Run linting and basic tests
	@echo "🔍 Running validation checks..."
	@echo "📝 Running linting..."
	uv run ruff check .
	@echo "✅ Linting passed!"
	@echo "🧪 Running tests..."
	uv run python -m pytest
	@echo "✅ All tests passed!"
	@echo "🎉 Branch validation successful - ready for PR!"

validate-branch-strict: ## Run formatting, linting, type checks, and tests
	$(MAKE) sync-env
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) type-check

test-validate-branch: ## Run linting and detailed unit tests
	@echo "🔍 Running validation checks..."
	$(MAKE) lint
	@echo "🧪 Running detailed unit tests..."
	$(MAKE) unit-test
	$(MAKE) clean-project

all-test-validate-branch: ## Validate branch and run all tests
	$(MAKE) validate-branch
	$(MAKE) all-test
	$(MAKE) clean-project

# ----------------------------
# Local Development
# ----------------------------

local-run: ## Run the assistant service locally with auto-reload
	@echo "Starting assistant service locally..."
	uv run uvicorn assistant_engine.main:app --reload --host 0.0.0.0 --port 8000
	$(GREEN_LINE)

# ----------------------------
# Build and Deployment
# ----------------------------

build-engine: ## Build Docker image for the assistant engine
	@echo "Building docker for client: $(CLIENT_ID)"
	cp assistant_factory/client_spec/$(CLIENT_ID)/functions.py assistant_engine/functions.py
	DOCKER_BUILDKIT=1 docker build --target=runtime . -t assistant-engine:latest
	$(GREEN_LINE)

auth-gcloud: ## Authenticate with Google Cloud
	@echo "Authenticating with Google Cloud..."
	gcloud auth application-default login
	$(GREEN_LINE)
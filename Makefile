# Makefile

# Define the default target
.DEFAULT_GOAL := help

# Define phony targets
.PHONY: install help environment-create environment-sync environment-delete environment-list lint lint-fix format test local-run

VENV := .venv
PYTHON := $(VENV)/bin/python
UV := $(VENV)/bin/uv

help: ## Display this help message
	@echo "Usage: make [target]"
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

######################
### Project set-up ###
######################

environment-create: ## Set up venv and install dependencies using uv
	@echo "Setting up environment..."
	uv venv $(VENV) --seed
	$(VENV)/bin/pip install uv
	$(VENV)/bin/uv sync --all-extras
	$(VENV)/bin/uv run pre-commit install
	@echo "Environment ready"
install: environment-create ## Create environment and install deps

environment-sync: ## Re-sync project dependencies
	$(UV) sync --all-extras

environment-delete: ## Remove the virtual environment folder
	rm -rf $(VENV)

environment-list: ## List installed packages
	$(UV) pip list

update: ## Update dependencies
	$(UV) pip install -e .[dev] --upgrade

show-dependencies:
	$(UV) pip list

clean:
	rm -r .pytest_cache .ruff_cache .files

############################
######### Tests ############
############################

test:
	$(UV) run python -m pytest

############################
### Linter and formatter ###
############################

lint:  ## Check for code issues.
	$(UV) run ruff check .

lint-fix:  ## Check and fix code issues.
	$(UV) run ruff check --fix .

format:  ## Format code
	$(UV) run ruff format .

############################
######## Local runs ########
############################

local-run:
	$(UV) run uvicorn nowisthetime_legacy.main:app --reload

############################
##### Build and deploy #####
############################
CLIENT_ID = leogv

build-engine:
	@echo "Building docker for client: ${CLIENT_ID}"
	cp assistant_factory/client_spec/$(CLIENT_ID)/functions.py assistant_engine/functions.py
	DOCKER_BUILDKIT=1 docker build --target=runtime . -t assistant-engine:latest
	
auth-gcloud:
	 gcloud auth application-default login



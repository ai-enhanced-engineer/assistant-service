# Makefile

# Define the default target
.DEFAULT_GOAL := help

# Define phony targets
.PHONY: install help

install: ## Make sure you are using a local version of python >= 3.10 and < 3.11
	poetry install

update: ## Update .lock file with new dependencies.
	poetry install

lint:
	poetry run ruff check .

lint-fix:
	poetry run ruff check --fix .


help: ## Display this help message
	@echo "Usage: make [target]"
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
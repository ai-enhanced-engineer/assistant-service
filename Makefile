# Makefile

# Define the default target
.DEFAULT_GOAL := help

# Define variables
PYTHON := python
FLOW := flow.py
CONFIG_FILE := experiment_config.yaml

# Define phony targets
.PHONY: install help

install: ## Make sure you are using a local version of python >= 3.10 and < 3.11
	poetry install

run-local-flow: ## Run the flow.py script with the specified config file
	python lora/flow.py run
	# python flow.py run --config-file $(CONFIG_FILE)


help: ## Display this help message
	@echo "Usage: make [target]"
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
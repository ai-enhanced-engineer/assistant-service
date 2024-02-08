# Makefile

# Define the default target
.DEFAULT_GOAL := help

# Define phony targets
.PHONY: install help

help: ## Display this help message
	@echo "Usage: make [target]"
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

######################
### Project set-up ###
######################

set-up-project: ## Set up tools and dependencies
	poetry run pip install --upgrade pip
	poetry run pip install pre-commit
	chmod +x .git/hooks/pre-commit

install: ## Make sure you are using a local version of python >= 3.10 and < 3.11
	poetry install

update: ## Update .lock file with new dependencies.
	poetry update

show-dependencies:
	poetry show --tree

clean:
	rm -r .chainlit .pytest_cache .ruff_cache chainlit.md

############################
######### Tests ############
############################

test:
	poetry run python -m pytest

############################
### Linter and formatter ###
############################

lint:  ## Check for code issues.
	poetry run ruff check .

lint-fix:  ## Check and fix code issues.
	poetry run ruff check --fix .

format:  ## Format code
	poetry run ruff format .

############################
######## Local runs ########
############################

local-run:
	poetry run chainlit run assistant_engine/main.py

############################
##### Build and deploy #####
############################

build-engine:
	DOCKER_BUILDKIT=1 docker build --target=runtime . -t assistant-engine:latest

auth-gcloud:
	 gcloud auth application-default login

# auth-docker: /Users/lkronecker/.config/gcloud/application_default_credentials.json
# 	gcloud auth configure-docker


# Repository Guidelines for Automated Agents

Welcome, automated contributors! This file describes how to interact with this
repository.

## Coding Standards
- Format code with `make format` (uses `ruff`).
- Lint with `make lint` and address all issues.

## Running Tests
- Execute `make test` before submitting changes. This uses `pytest` and expects
  the development dependencies from `pyproject.toml` to be installed.

## Environment Setup
- Use `make environment-create` to create the local virtual environment. It
  installs dependencies via `uv` and sets up pre-commit hooks.

## Pull Requests
- Provide a concise summary of your changes.
- Include the results of `make lint`, `make format`, and `make test` in the PR
  description.


# SPDX-License-Identifier: MIT
# Makefile — common development tasks for Pinocchio Models

PYTHON ?= python3

.PHONY: help lint format docs-check test typecheck coverage clean install-dev

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-dev: ## Install package with dev dependencies
	$(PYTHON) -m pip install -e ".[dev]"

lint: ## Run ruff linter
	ruff check src tests scripts

format: ## Run ruff formatter (check only)
	ruff format --check src tests scripts

format-fix: ## Run ruff formatter (apply changes)
	ruff format src tests scripts

docs-check: ## Validate local Markdown links in documentation
	$(PYTHON) scripts/check_docs_links.py

test: ## Run pytest test suite
	$(PYTHON) -m pytest -n auto --timeout=60 --tb=short -q

typecheck: ## Run mypy type checker
	mypy src --config-file pyproject.toml

coverage: ## Run tests with coverage report
	$(PYTHON) -m pytest \
		-n auto \
		--timeout=60 \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-fail-under=80 \
		--tb=short \
		-q

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

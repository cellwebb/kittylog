# kittylog Development Makefile

.PHONY: help install install-dev test test-coverage lint format check clean build publish docs

# Default target
help: ## Show this help message
	@echo "kittylog Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install the package
	uv pip install -e .

install-dev: ## Install development dependencies
	uv pip install -e ".[dev,test]"
	pre-commit install

# Testing
test: ## Run tests (excluding actual API calls)
	uv run pytest --ignore=tests/test_actual_provider_integration.py

test-all: ## Run all tests including actual API calls
	uv run pytest

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=kittylog --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	uv run pytest-watch

test-integration: ## Run integration tests only
	pytest tests/test_integration.py -v

# Code Quality
lint: ## Run linting
	ruff check .
	mypy src/kittylog

format: ## Format code
	ruff format .
	ruff check --fix .

type-check: ## Run static type checks
	mypy src/kittylog

check: lint test ## Run all checks (lint + test)

# Cleaning
clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Building
build: clean ## Build distribution packages
	python -m build

# Publishing
publish-test: build ## Publish to test PyPI
	twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	twine upload dist/*

# Documentation
docs: ## Generate documentation
	@echo "Documentation generation not yet implemented"

# Development utilities
setup-dev: ## Complete development setup
	@echo "Setting up development environment..."
	uv pip install -e ".[dev,test]"
	pre-commit install
	@echo "Development environment ready!"

run-example: ## Run example usage
	@echo "Running example changelog update..."
	python -m kittylog.cli --no-interactive --dry-run --from-tag v0.1.0 --to-tag v0.2.0

# Git hooks
pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

# Version management
bump:
	@# Check for uncommitted changes before starting
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Git working directory is not clean"; \
		echo "Please commit or stash your changes first"; \
		git status --short; \
		exit 1; \
	fi
	@echo "Bumping $(VERSION) version..."
	@OLD_VERSION=$$(python -c "import re; content=open('.bumpversion.toml').read(); print(re.search(r'current_version = \"([^\"]+)\"', content).group(1))") && \
	bump-my-version bump $(VERSION) --no-commit --no-tag && \
	NEW_VERSION=$$(python -c "import re; content=open('.bumpversion.toml').read(); print(re.search(r'current_version = \"([^\"]+)\"', content).group(1))") && \
	echo "Version bumped from $$OLD_VERSION to $$NEW_VERSION" && \
	git add -A && \
	git commit -m "chore: bump version to $$NEW_VERSION" && \
	git tag -a "v$$NEW_VERSION" -m "Release version $$NEW_VERSION" && \
	echo "✅ Created tag v$$NEW_VERSION" && \
	echo "📦 To publish: git push && git push --tags"

bump-patch: VERSION=patch
bump-patch: bump

bump-minor: VERSION=minor
bump-minor: bump

bump-major: VERSION=major
bump-major: bump

# Security
security-check: ## Run security checks
	safety check
	bandit -r src/kittylog/

# Dependencies
update-deps: ## Update dependencies
	uv pip compile pyproject.toml --upgrade

# Environment info
info: ## Show environment info
	@echo "Python version: $(shell python --version)"
	@echo "UV version: $(shell uv --version)"
	@echo "Project root: $(shell pwd)"
	@echo "Virtual environment: $(VIRTUAL_ENV)"

# Quick start for new contributors
quickstart: ## Quick setup for new contributors
	@echo " Setting up kittylog for development..."
	@echo ""
	@echo "1. Installing development dependencies..."
	uv pip install -e ".[dev,test]"
	@echo ""
	@echo "2. Setting up pre-commit hooks..."
	pre-commit install
	@echo ""
	@echo "3. Running initial tests..."
	pytest --tb=short
	@echo ""
	@echo "[OK] Setup complete! Try 'make help' to see available commands."

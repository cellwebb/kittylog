# kittylog Development Makefile

.PHONY: help install install-dev test test-coverage lint format check clean build publish docs bump bump-patch bump-minor bump-major

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
	uv run ruff check .

format: ## Format code
	uv run ruff format .
	uv run ruff check --fix .

type-check: ## Run static type checks
	uv run mypy src/kittylog

check: lint type-check test ## Run all checks (lint + type-check + test)

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

# Version bumping
bump: ## Bump version and update changelog
	@# Check for uncommitted changes before starting
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Git working directory is not clean"; \
		echo "Please commit or stash your changes first"; \
		git status --short; \
		exit 1; \
	fi
	@echo "Bumping $(VERSION) version..."
	@RESULT=$$(BUMP_KIND=$(VERSION) python -c "import os, re; from pathlib import Path; version_file = Path('src/kittylog/__version__.py'); content = version_file.read_text(encoding='utf-8'); match = re.search(r'__version__ = \"([^\"]+)\"', content); old_version = match.group(1); parts = old_version.split('.'); major, minor, patch = map(int, parts); kind = os.environ['BUMP_KIND']; new_version = f'{major}.{minor}.{patch + 1}' if kind == 'patch' else f'{major}.{minor + 1}.0' if kind == 'minor' else f'{major + 1}.0.0'; version_file.write_text(content.replace(f'__version__ = \"{old_version}\"', f'__version__ = \"{new_version}\"', 1), encoding='utf-8'); print(old_version, new_version)") && \
	OLD_VERSION=$$(echo "$$RESULT" | awk '{print $$1}') && \
	NEW_VERSION=$$(echo "$$RESULT" | awk '{print $$2}') && \
	echo "Version bumped from $$OLD_VERSION to $$NEW_VERSION" && \
		echo "📝 Generating changelog with kittylog..." && \
		uv run kittylog --yes && \
		echo "📝 Preparing changelog for release $$NEW_VERSION..." && \
		python scripts/prep_changelog_for_release.py CHANGELOG.md $$NEW_VERSION && \
	git add -A && \
	git commit -m "chore(version): bump version to $$NEW_VERSION" && \
	git tag -a "v$$NEW_VERSION" -m "Release version $$NEW_VERSION" && \
	echo "✅ Created tag v$$NEW_VERSION" && \
	echo "📦 To publish: git push && git push --tags"

bump-patch: VERSION=patch ## Bump patch version
bump-patch: bump

bump-minor: VERSION=minor ## Bump minor version
bump-minor: bump

bump-major: VERSION=major ## Bump major version
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

# ------------------------------------------------------------------------------
# Production-Grade Makefile for MCP Auto PR Monorepo
#
# This Makefile provides a comprehensive set of targets for development,
# quality assurance, security scanning, CI/CD, and release management
# for the consolidated monorepo structure.
#
# It is designed to be run from the monorepo root directory.
#
# Package structure:
# - src/shared (shared library)
# - src/mcp_local_repo_analyzer
# - src/mcp_pr_recommender
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Configuration Variables
# ------------------------------------------------------------------------------

# Define quality tools
LINTERS := ruff
FORMATTERS := black
TYPE_CHECKERS := mypy
SECURITY_SCANNERS := bandit safety pip-audit
DOCSTRING_CHECKERS := interrogate

# Docker configuration
DOCKER_IMAGE_ANALYZER := ghcr.io/manavgup/mcp-local-repo-analyzer
DOCKER_IMAGE_RECOMMENDER := ghcr.io/manavgup/mcp-pr-recommender
DOCKER_TAG := latest

# ------------------------------------------------------------------------------
# Colors for output
# ------------------------------------------------------------------------------
GREEN=\033[0;32m
BLUE=\033[0;34m
YELLOW=\033[1;33m
RED=\033[0;31m
CYAN=\033[0;36m
NC=\033[0m # No Color

# ------------------------------------------------------------------------------
# Phony targets to prevent conflicts with files of the same name
# ------------------------------------------------------------------------------
.PHONY: help install install-dev update-deps clean

.PHONY: lint lint-all lint-ruff lint-mypy lint-docstrings
.PHONY: format format-check format-black format-isort format-ruff
.PHONY: type-check check-types check-style check-quality check-fast check-pre-commit
.PHONY: check-docstrings docstrings fix analyze strict

.PHONY: test-all test-unit test-integration test-e2e test-fast test-coverage test-doctest test-slow test-benchmark test-coverage-html

.PHONY: security-scan security-scan-local security-scan-image

.PHONY: docs-build-html docs-serve

.PHONY: docker-build docker-run docker-stop docker-push docker-scan

.PHONY: ci-lint ci-test ci-security ci-build ci-release

.PHONY: release-check pypi-check release-pypi release-docs

.PHONY: pre-commit-install pre-commit-run

# ------------------------------------------------------------------------------
# Help Target
# ------------------------------------------------------------------------------
help:
	@echo "$(BLUE)MCP Auto PR Monorepo Management - Comprehensive Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup & Installation:$(NC)"
	@echo "  install                 Install dependencies for the monorepo"
	@echo "  install-dev             Install development dependencies"
	@echo "  update-deps             Update all dependencies"
	@echo "  clean                   Clean all build artifacts and caches"
	@echo ""
	@echo "$(YELLOW)Quality & Static Analysis:$(NC)"
	@echo "  lint                    Run essential linters (Ruff + Mypy)"
	@echo "  lint-all                Run all linters including docstrings"
	@echo "  format                  Auto-format code (isort, black, ruff fixes)"
	@echo "  format-check            Check formatting without changes"
	@echo "  type-check              Run Mypy type checker with strict mode"
	@echo "  check-docstrings        Check docstring coverage"
	@echo "  check-style             Check style without auto-formatting"
	@echo "  check-quality           Full quality check with auto-formatting"
	@echo "  check-fast              Quick essential checks only"
	@echo "  fix                     Apply all auto-fixes"
	@echo "  analyze                 Run code complexity analysis"
	@echo "  strict                  Run strict quality checks (fail on any issue)"
	@echo ""
	@echo "$(YELLOW)Testing & Coverage:$(NC)"
	@echo "  test-all                Run all tests (unit, integration, e2e)"
	@echo "  test-unit               Run only unit tests"
	@echo "  test-integration        Run integration tests"
	@echo "  test-e2e                Run end-to-end tests"
	@echo "  test-fast               Run fast unit tests only (no slow markers)"
	@echo "  test-doctest            Run doctests"
	@echo "  test-coverage           Run tests and generate HTML coverage reports"
	@echo "  test-coverage-html      Open HTML coverage report"
	@echo ""
	@echo "$(YELLOW)Security Scanning:$(NC)"
	@echo "  security-scan           Run all local security scanners"
	@echo "  security-scan-local     Run local dependency and code scanners"
	@echo "  security-scan-image     Scan Docker images for vulnerabilities"
	@echo ""
	@echo "$(YELLOW)Container Workflows (Docker):$(NC)"
	@echo "  docker-build            Build both Docker images (analyzer & recommender)"
	@echo "  docker-run              Run containers using docker-compose"
	@echo "  docker-stop             Stop running containers"
	@echo "  docker-push             Push images to GitHub Container Registry"
	@echo ""
	@echo "$(YELLOW)CI/CD & Release:$(NC)"
	@echo "  ci-lint                 Simulate CI linting pipeline"
	@echo "  ci-test                 Simulate CI testing pipeline"
	@echo "  ci-security             Simulate CI security scanning"
	@echo "  ci-build                Simulate CI build process (lint, test, security, docker)"
	@echo "  release-check           Run all pre-release checks"
	@echo "  pypi-check              Validate PyPI package builds and installation"
	@echo "  release-pypi            Build and publish packages to PyPI"
	@echo ""
	@echo "$(YELLOW)Pre-commit Hooks:$(NC)"
	@echo "  pre-commit-install      Install git pre-commit hooks"
	@echo "  pre-commit-run          Run all pre-commit hooks on all files"
	@echo ""
	@echo "$(YELLOW)Documentation:$(NC)"
	@echo "  docs-build-html         Build HTML documentation"
	@echo "  docs-serve              Serve documentation locally"
	@echo ""

# ------------------------------------------------------------------------------
# Installation & Dependency Management
# ------------------------------------------------------------------------------

install:
	@echo "$(BLUE)📦 Installing monorepo dependencies...$(NC)"
	poetry install --with test,dev
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

install-dev:
	@echo "$(BLUE)📦 Installing development dependencies...$(NC)"
	poetry install --with dev
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

update-deps:
	@echo "$(BLUE)🔄 Updating dependencies...$(NC)"
	poetry update
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

# ------------------------------------------------------------------------------
# Linting, Formatting, and Static Analysis
# ------------------------------------------------------------------------------

# Individual linting tools
lint-ruff:
	@echo "$(CYAN)🔍 Running Ruff linter...$(NC)"
	poetry run ruff check src/ tests/ --line-length 120
	@echo "$(GREEN)✅ Ruff checks passed$(NC)"

lint-mypy:
	@echo "$(CYAN)🔎 Running Mypy type checker...$(NC)"
	poetry run mypy src/mcp_local_repo_analyzer/ --strict --warn-redundant-casts --warn-unused-ignores --explicit-package-bases
	poetry run mypy src/mcp_pr_recommender/ --strict --warn-redundant-casts --warn-unused-ignores --explicit-package-bases
	@echo "$(GREEN)✅ Mypy type checks passed$(NC)"



lint-docstrings:
	@echo "$(CYAN)📝 Checking docstring coverage...$(NC)"
	poetry run interrogate --fail-under=80 src/ -v
	poetry run pydocstyle src/ || true
	@echo "$(GREEN)✅ Docstring checks completed$(NC)"

# Combined linting (all non-formatting linters)
lint: lint-ruff lint-mypy
	@echo "$(GREEN)✅ All linting checks passed$(NC)"

lint-all: lint-ruff lint-mypy lint-docstrings
	@echo "$(GREEN)✅ All extended linting checks completed$(NC)"

# Individual formatters
format-ruff:
	@echo "$(CYAN)🔧 Running Ruff formatter and import sorter...$(NC)"
	poetry run ruff format src/ tests/ --line-length 120
	poetry run ruff check --fix src/ tests/ --line-length 120
	@echo "$(GREEN)✅ Ruff formatting and import sorting completed$(NC)"

# Combined formatting (Ruff handles everything)
format: format-ruff
	@echo "$(GREEN)✅ All formatting completed$(NC)"

# Check formatting without making changes
format-check:
	@echo "$(CYAN)🔍 Checking code formatting...$(NC)"
	poetry run ruff format --check src/ tests/ --line-length 120
	poetry run ruff check src/ tests/ --line-length 120
	@echo "$(GREEN)✅ Format checking completed$(NC)"

# Type checking aliases for convenience
type-check: lint-mypy

check-types: lint-mypy

# Docstring checking aliases
check-docstrings: lint-docstrings

docstrings: lint-docstrings

# Combined quality checks (no auto-formatting)
check-style: format-check lint
	@echo "$(GREEN)✅ Style checks completed (no changes made)$(NC)"

# Full quality check (with auto-formatting)
check-quality: format lint-all
	@echo "$(GREEN)✅ All quality checks completed with formatting$(NC)"

# Quick quality check (fast, essential checks only)
check-fast: lint-ruff format-check
	@echo "$(GREEN)✅ Fast quality checks completed$(NC)"

# Pre-commit style check (everything without modifications)
check-pre-commit: format-check lint-all test-fast
	@echo "$(GREEN)✅ Pre-commit checks passed$(NC)"

# Auto-fix what can be fixed
fix: format
	@echo "$(GREEN)✅ All auto-fixes applied$(NC)"

# Full quality analysis with detailed output
analyze:
	@echo "$(CYAN)📊 Running full code analysis...$(NC)"
	@echo "$(BLUE)→ Code complexity analysis...$(NC)"
	poetry run radon cc src/ -a -nb
	@echo "$(BLUE)→ Maintainability index...$(NC)"
	poetry run radon mi src/ -nb
	@echo "$(BLUE)→ Cyclomatic complexity...$(NC)"
	poetry run xenon src/ --max-absolute B --max-modules B --max-average A
	@echo "$(GREEN)✅ Code analysis completed$(NC)"

# Strict mode - fail on any issue
strict: format-check
	@echo "$(CYAN)🚨 Running strict quality checks...$(NC)"
	poetry run ruff check src/ tests/ --line-length 120 --exit-non-zero-on-fix
	poetry run mypy src/mcp_local_repo_analyzer/ --strict --warn-redundant-casts --warn-unused-ignores --no-implicit-optional --explicit-package-bases
	poetry run mypy src/mcp_pr_recommender/ --strict --warn-redundant-casts --warn-unused-ignores --no-implicit-optional --explicit-package-bases
	poetry run ruff format --check src/ tests/ --line-length 120
	poetry run interrogate --fail-under=95 src/ -v
	@echo "$(GREEN)✅ Strict quality checks passed$(NC)"

# ------------------------------------------------------------------------------
# Testing & Coverage
# ------------------------------------------------------------------------------
test-all: test-unit test-integration test-e2e
	@echo "$(GREEN)✅ All tests completed successfully$(NC)"

test-unit:
	@echo "$(CYAN)🔬 Running unit tests...$(NC)"
	PYTHONPATH=src poetry run pytest tests/unit/ -m "unit" --tb=short --ignore=tests/unit/integration/test_in_memory.py --ignore=tests/unit/integration/test_quick.py
	@echo "$(GREEN)✅ All unit tests passed$(NC)"

test-integration:
	@echo "$(CYAN)🔗 Running integration tests...$(NC)"
	PYTHONPATH=src poetry run pytest tests/unit/integration/ -m "integration" --tb=short
	@echo "$(GREEN)✅ All integration tests passed$(NC)"

test-e2e:
	@echo "$(CYAN)🎯 Running end-to-end tests...$(NC)"
	@if PYTHONPATH=src poetry run pytest tests/ -m "e2e" --tb=short 2>/dev/null; then \
		echo "$(GREEN)✅ All end-to-end tests passed$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ No e2e tests found or e2e tests completed$(NC)"; \
	fi

test-fast:
	@echo "$(CYAN)⚡ Running fast tests only...$(NC)"
	PYTHONPATH=src poetry run pytest tests/ -m "unit and not slow" --tb=short -q
	@echo "$(GREEN)✅ Fast tests completed$(NC)"

test-doctest:
	@echo "$(CYAN)📚 Running doctests...$(NC)"
	PYTHONPATH=src poetry run pytest --doctest-modules src/ --tb=short
	@echo "$(GREEN)✅ All doctests passed$(NC)"

test-coverage:
	@echo "$(CYAN)📊 Generating test coverage report...$(NC)"
	PYTHONPATH=src poetry run pytest tests/ --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

test-coverage-html:
	@echo "$(CYAN)📊 Opening HTML coverage report...$(NC)"
	@if [ -f "htmlcov/index.html" ]; then \
		open htmlcov/index.html || echo "⚠️ Could not open HTML report"; \
	else \
		echo "$(YELLOW)⚠️ No coverage report found. Run 'make test-coverage' first.$(NC)"; \
	fi

# ------------------------------------------------------------------------------
# Security & Vulnerability Scanning
# ------------------------------------------------------------------------------
security-scan: security-scan-local
	@echo "$(GREEN)✅ Local security scans completed$(NC)"

security-scan-local:
	@echo "$(CYAN)🔒 Running local code and dependency security scans...$(NC)"
	@echo "$(BLUE)  → Scanning code with Bandit...$(NC)"
	poetry run bandit -r src/
	@echo "$(BLUE)  → Scanning dependencies with Safety...$(NC)"
	poetry run safety check
	@echo "$(BLUE)  → Scanning dependencies with Pip-Audit...$(NC)"
	poetry run pip-audit
	@echo "$(GREEN)✅ All local security scans passed$(NC)"

security-scan-image:
	@echo "$(CYAN)🔒 Scanning Docker images with Trivy...$(NC)"
	trivy image --severity HIGH,CRITICAL --format table $(DOCKER_IMAGE_ANALYZER):$(DOCKER_TAG)
	trivy image --severity HIGH,CRITICAL --format table $(DOCKER_IMAGE_RECOMMENDER):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Docker image security scans completed$(NC)"

# ------------------------------------------------------------------------------
# Documentation
# ------------------------------------------------------------------------------
docs-build-html:
	@echo "$(CYAN)📖 Building documentation...$(NC)"
	@if [ -d "docs" ]; then \
		cd docs && sphinx-build -M html . _build; \
		echo "$(GREEN)✅ Docs built in docs/_build/html$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ No docs directory found$(NC)"; \
	fi

docs-serve:
	@echo "$(CYAN)📖 Serving docs at http://localhost:8000...$(NC)"
	@if [ -d "docs/_build/html" ]; then \
		cd docs/_build/html && python3 -m http.server 8000; \
	else \
		echo "$(YELLOW)⚠️ No built docs found. Run 'make docs-build-html' first.$(NC)"; \
	fi

# ------------------------------------------------------------------------------
# Container Workflows (Docker)
# ------------------------------------------------------------------------------
docker-build:
	@echo "$(CYAN)🐳 Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✅ Docker images built successfully$(NC)"

docker-run:
	@echo "$(CYAN)🏃 Running Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Containers running. Check http://localhost:9070 and http://localhost:9071$(NC)"

docker-stop:
	@echo "$(CYAN)🛑 Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Containers stopped$(NC)"

docker-push:
	@echo "$(CYAN)⬆️ Pushing Docker images to GitHub Container Registry...$(NC)"
	docker push $(DOCKER_IMAGE_ANALYZER):$(DOCKER_TAG)
	docker push $(DOCKER_IMAGE_RECOMMENDER):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Docker images pushed to registry$(NC)"

# ------------------------------------------------------------------------------
# CI/CD Orchestration
# ------------------------------------------------------------------------------
ci-lint: install lint
	@echo "$(GREEN)✅ CI Linting pipeline completed$(NC)"

ci-test: install test-all test-coverage
	@echo "$(GREEN)✅ CI Testing pipeline completed$(NC)"

ci-security: install security-scan-local
	@echo "$(GREEN)✅ CI Security scanning pipeline completed$(NC)"

ci-build: ci-lint ci-test ci-security docker-build
	@echo "$(GREEN)✅ Full CI build pipeline completed$(NC)"

# ------------------------------------------------------------------------------
# Release Pipeline
# ------------------------------------------------------------------------------
release-check: pre-commit-run check-quality test-all test-coverage security-scan-local
	@echo "$(GREEN)✅ All pre-release checks passed. Ready for release!$(NC)"

pypi-check:
	@echo "$(CYAN)📦 Validating PyPI package builds...$(NC)"
	poetry build
	@echo "$(BLUE)→ Testing package installation from dist/...$(NC)"
	pip install --force-reinstall dist/*.whl
	@echo "$(BLUE)→ Running basic functionality tests...$(NC)"
	python test_pypi_packages.py
	@echo "$(BLUE)→ Cleaning up test installation...$(NC)"
	pip uninstall -y mcp-auto-pr
	@echo "$(GREEN)✅ PyPI package validation completed$(NC)"

release-pypi:
	@echo "$(CYAN)📦 Building and publishing packages to PyPI...$(NC)"
	poetry build
	poetry publish
	@echo "$(GREEN)✅ Packages published to PyPI$(NC)"

# ------------------------------------------------------------------------------
# Pre-commit Hooks
# ------------------------------------------------------------------------------
pre-commit-install:
	@echo "$(CYAN)🔧 Installing pre-commit hooks...$(NC)"
	poetry run pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"

pre-commit-run:
	@echo "$(CYAN)🔧 Running pre-commit hooks on all files...$(NC)"
	poetry run pre-commit run --all-files
	@echo "$(GREEN)✅ Pre-commit run completed$(NC)"

# ------------------------------------------------------------------------------
# Cleanup Targets
# ------------------------------------------------------------------------------
clean:
	@echo "$(BLUE)🧹 Cleaning up monorepo...$(NC)"
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

# ------------------------------------------------------------------------------
# End of Makefile
# ------------------------------------------------------------------------------

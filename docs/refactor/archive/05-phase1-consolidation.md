# Phase 1: Repository Consolidation (Days 1-2)

## Objectives
- Merge four repositories into single monorepo
- Create unified directory structure
- Consolidate configuration files
- Preserve git history where possible

## Day 1: Structure Creation

### Task 1.1: Create Directory Structure
```bash
# Create all necessary directories
make init-monorepo-structure

# Or manually:
mkdir -p src/{shared,mcp_local_repo_analyzer,mcp_pr_recommender}
mkdir -p src/shared/{models,git,mcp,common,testing}
mkdir -p tests/{unit,integration,performance,fixtures}
mkdir -p tests/unit/{test_shared,test_local_repo_analyzer,test_pr_recommender}
mkdir -p tests/integration/{test_mcp_servers,test_cross_package,test_end_to_end}
mkdir -p docker/{analyzer,recommender,dev}
mkdir -p docs/{api,architecture,guides,development}
mkdir -p docs/architecture/decisions
mkdir -p scripts/{setup,ci,utils}
mkdir -p config examples .devcontainer
```

### Task 1.2: Move Source Code
```bash
# Use migration script
./scripts/migrate-to-monorepo.sh

# Or manually for each package
rsync -av --exclude='__pycache__' --exclude='*.pyc' \
  ../mcp_shared_lib/src/mcp_shared_lib/ src/shared/
```

### Task 1.3: Consolidate Tests
- Move unit tests to `tests/unit/test_<package>/`
- Move integration tests to `tests/integration/`
- Merge fixtures into `tests/fixtures/`
- Create unified `tests/conftest.py`

## Day 2: Configuration Unification

### Task 2.1: Create Unified pyproject.toml
```toml
[tool.poetry]
name = "mcp-auto-pr"
version = "0.2.0"
description = "Monorepo for MCP PR automation tools"
authors = ["Manav Gupta <manavg@gmail.com>"]
readme = "README.md"
license = "MIT"
packages = [
    {include = "shared", from = "src"},
    {include = "mcp_local_repo_analyzer", from = "src"},
    {include = "mcp_pr_recommender", from = "src"}
]

[tool.poetry.dependencies]
python = ">=3.10,<4.0"
fastmcp = "^2.10.6"
gitpython = "^3.1.40"
pydantic = "^2.11.7"
openai = "^1.0.0"
# ... other dependencies

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

### Task 2.2: Merge Pre-commit Configurations
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Task 2.3: Update Makefile
```makefile
# Makefile
.PHONY: help install test lint format build

help:
	@echo "Available commands:"
	@echo "  install    - Install all dependencies"
	@echo "  test       - Run all tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  build      - Build packages"

install:
	poetry install --with dev,test

test:
	poetry run pytest tests/ --cov=src

test-unit:
	poetry run pytest tests/unit/

test-integration:
	poetry run pytest tests/integration/

lint:
	poetry run ruff check src/ tests/
	poetry run mypy src/

format:
	poetry run black src/ tests/
	poetry run ruff check --fix src/ tests/

build:
	poetry build
```

## Checklist

### Directory Structure
- [x] Created src/ directory with all packages
- [x] Created tests/ directory with proper organization
- [x] Created docker/ directory for containers
- [x] Created docs/ directory structure
- [x] Created scripts/ directory for utilities
- [x] Created config/ and examples/ directories

### Source Code Migration
- [x] Moved mcp_shared_lib source code (now in src/shared/)
- [x] Moved mcp_local_repo_analyzer source code
- [x] Moved mcp_pr_recommender source code
- [x] Removed duplicated code
- [x] Updated import statements

### Test Migration
- [x] Moved all unit tests
- [x] Moved all integration tests
- [x] Consolidated fixtures
- [ ] Created unified conftest.py
- [ ] Verified test discovery

### Configuration
- [x] Created unified pyproject.toml
- [ ] Merged pre-commit configurations (partial)
- [ ] Updated Makefile (needs path fixes)
- [x] Consolidated Docker configurations
- [ ] Merged GitHub workflows (only basic CI exists)

## Verification Steps

### 1. Check Package Imports
```python
# verify_imports.py
import sys
sys.path.insert(0, 'src')

try:
    import shared
    import mcp_local_repo_analyzer
    import mcp_pr_recommender
    print("✅ All packages import successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
```

### 2. Run Basic Tests
```bash
# Install and run tests
poetry install
poetry run pytest tests/unit/ -v
```

### 3. Check CLI Commands
```bash
# Test CLI interfaces
poetry run python -m mcp_local_repo_analyzer.main --help
poetry run python -m mcp_pr_recommender.main --help
```

## Troubleshooting

### Import Errors
**Issue**: ModuleNotFoundError
**Solution**:
- Check PYTHONPATH includes src/
- Verify __init__.py files exist
- Update import statements

### Test Discovery Issues
**Issue**: Tests not found
**Solution**:
- Ensure test files start with test_
- Add __init__.py to test directories
- Check pytest configuration

### Configuration Conflicts
**Issue**: Dependency conflicts
**Solution**:
- Resolve version conflicts in pyproject.toml
- Use poetry lock --no-update
- Clear poetry cache if needed

### Server Inheritance Issues
**Issue**: MCP servers can't inherit from shared base class
**Solution**:
- Ensure proper import paths
- Verify abstract method implementations
- Check FastMCP compatibility

## Next Steps
- Proceed to [Phase 2: CI/CD Setup](./06-phase2-cicd.md)
- Verify all tests pass
- Commit changes to new structure

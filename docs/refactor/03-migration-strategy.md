# Migration Strategy

## Overview
Step-by-step guide to migrate from multi-repository to monorepo structure.

## Prerequisites
- [ ] Backup all repositories
- [ ] Ensure all changes are committed or stashed
- [ ] Document current repository URLs
- [ ] Verify PyPI credentials

## Migration Steps

### Step 1: Prepare Current Repositories
```bash
# Stash uncommitted changes
cd ../mcp_local_repo_analyzer && git stash
cd ../mcp_pr_recommender && git stash
cd ../mcp_shared_lib && git stash

# Create backup branches
git checkout -b pre-monorepo-backup
git push origin pre-monorepo-backup
```

### Step 2: Create Directory Structure
```bash
# In mcp_auto_pr directory
mkdir -p src/{mcp_shared_lib,mcp_local_repo_analyzer,mcp_pr_recommender}
mkdir -p tests/{unit,integration,performance,fixtures}
mkdir -p tests/unit/{test_shared_lib,test_local_repo_analyzer,test_pr_recommender}
mkdir -p tests/integration/{test_mcp_servers,test_cross_package,test_end_to_end}
mkdir -p docker/{analyzer,recommender,dev}
mkdir -p docs/{api,architecture,guides,development}
mkdir -p docs/architecture/decisions
mkdir -p scripts/{setup,ci,utils}
mkdir -p config examples .devcontainer
```

### Step 3: Move Source Code
```bash
# Copy shared library (clean copy, no __pycache__)
rsync -av --exclude='__pycache__' --exclude='*.pyc' \
  ../mcp_shared_lib/src/mcp_shared_lib/ src/mcp_shared_lib/

# Copy analyzer (excluding duplicated shared lib)
rsync -av --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='mcp_shared_lib' \
  ../mcp_local_repo_analyzer/src/mcp_local_repo_analyzer/ \
  src/mcp_local_repo_analyzer/

# Copy recommender (excluding duplicated shared lib)
rsync -av --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='mcp_shared_lib' \
  ../mcp_pr_recommender/src/mcp_pr_recommender/ \
  src/mcp_pr_recommender/
```

### Step 4: Consolidate Tests
```bash
# Move test files preserving structure
cp -r ../mcp_shared_lib/tests/* tests/unit/test_shared_lib/
cp -r ../mcp_local_repo_analyzer/tests/* tests/unit/test_local_repo_analyzer/
cp -r ../mcp_pr_recommender/tests/* tests/unit/test_pr_recommender/

# Move fixtures to shared location
mkdir -p tests/fixtures
cp -r ../mcp_*/tests/fixtures/* tests/fixtures/ 2>/dev/null || true
```

### Step 5: Create Unified conftest.py
```python
# tests/conftest.py
"""Unified pytest configuration for all packages."""
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import and merge fixtures from all packages
# ... (merge content from all conftest.py files)
```

### Step 6: Update Import Paths
```bash
# Update imports in all Python files
find src -name "*.py" -type f -exec sed -i \
  's/from mcp_shared_lib/from mcp_shared_lib/g' {} \;

# Update test imports
find tests -name "*.py" -type f -exec sed -i \
  's/from mcp_/from mcp_/g' {} \;
```

### Step 7: Create Unified pyproject.toml
See [PyPI Publishing](./11-pypi-publishing.md) for detailed configuration.

### Step 8: Move Configuration Files
```bash
# Copy Docker files
cp ../mcp_local_repo_analyzer/Dockerfile docker/analyzer/
cp ../mcp_pr_recommender/Dockerfile docker/recommender/

# Copy GitHub workflows (will merge later)
cp -r ../mcp_auto_pr/.github/workflows/* .github/workflows/

# Copy example configurations
cp -r ../mcp_*/examples/* examples/ 2>/dev/null || true
```

### Step 9: Update Documentation
```bash
# Consolidate README files
cat ../mcp_*/README.md > docs/legacy-readmes.md

# Copy other documentation
cp -r ../mcp_*/docs/* docs/ 2>/dev/null || true
```

### Step 10: Verify Migration
```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest tests/

# Check imports
poetry run python -c "import mcp_shared_lib"
poetry run python -c "import mcp_local_repo_analyzer"
poetry run python -c "import mcp_pr_recommender"

# Test CLI commands
poetry run python -m mcp_local_repo_analyzer.main --help
poetry run python -m mcp_pr_recommender.main --help
```

## Rollback Plan

### If Migration Fails
1. Delete modified directories in mcp_auto_pr
2. Restore from backup branches
3. Document issues encountered
4. Adjust migration plan

### Backup Commands
```bash
# Create full backup
tar -czf monorepo-backup-$(date +%Y%m%d).tar.gz \
  ../mcp_local_repo_analyzer \
  ../mcp_pr_recommender \
  ../mcp_shared_lib \
  ../mcp_auto_pr

# Restore from backup
tar -xzf monorepo-backup-YYYYMMDD.tar.gz
```

## Post-Migration Tasks

### Clean Up
- [ ] Remove old __pycache__ directories
- [ ] Delete .pyc files
- [ ] Remove duplicate test fixtures
- [ ] Clean up unused imports

### Verification
- [ ] All tests pass
- [ ] Documentation builds
- [ ] Docker images build
- [ ] PyPI packages build

### Repository Management
- [ ] Archive old repositories
- [ ] Update repository descriptions
- [ ] Add deprecation notices
- [ ] Update links and references

## Common Issues and Solutions

### Import Errors
**Problem**: Module not found errors
**Solution**: Update PYTHONPATH or fix import statements

### Test Discovery
**Problem**: Tests not found by pytest
**Solution**: Ensure __init__.py files in test directories

### Configuration Conflicts
**Problem**: Multiple configuration files
**Solution**: Merge configurations carefully, test thoroughly

### Git History
**Problem**: Lost git history
**Solution**: Use git subtree or git filter-branch to preserve history
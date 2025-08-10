# Implementation Plan: Issue #6 - Fix GitHub Actions with Pre-commit Alignment

## 📋 Overview
**Issue**: https://github.com/manavgup/mcp_auto_pr/issues/6
**Goal**: Fix GitHub Actions workflows and align them with local pre-commit hooks for consistent results
**Timeline**: 1 day (8 hours)
**Priority**: P0 Critical

## 🎯 Success Criteria
- All GitHub Actions workflows pass without exit code 127 errors
- GitHub Actions uses identical tools/versions as .pre-commit-config.yaml
- Local `pre-commit run --all-files` matches CI results exactly
- No "works on my machine" issues

## 📊 Current State Analysis

### Step 1: Audit Current Workflows (30 minutes)
```bash
# Commands to run for analysis
cd mcp_auto_pr
find .github/workflows -name "*.yml" -o -name "*.yaml"
gh workflow list
gh run list --limit 10
```

**Expected findings**:
- Multiple workflow files with different configurations
- Failed runs with exit code 127
- Inconsistent tool versions across workflows
- Missing dependencies

### Step 2: Audit Pre-commit Configurations (30 minutes)
```bash
# Check pre-commit configs across all repos
find ../mcp_* -name ".pre-commit-config.yaml" -exec echo "=== {} ===" \; -exec cat {} \;
```

**Expected findings**:
- Different pre-commit configurations across repos
- Different tool versions
- Missing or incomplete configurations

## 🔧 Implementation Plan

### Phase 1: Create Master Pre-commit Configuration (1 hour)

#### Task 1.1: Design Unified Pre-commit Config
Create a master `.pre-commit-config.yaml` that will be used across all repositories:

```yaml
# .pre-commit-config.yaml (master template)
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length=88']

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports, --disallow-untyped-defs]
```

#### Task 1.2: Define Tool Configuration Standards
Create unified tool configurations in pyproject.toml:

```toml
# pyproject.toml sections (to be consistent across all repos)
[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  | .venv
  | build
  | dist
)/
'''

[tool.ruff]
target-version = "py310"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
]

[tool.ruff.isort]
known-first-party = ["mcp_shared_lib", "mcp_local_repo_analyzer", "mcp_pr_recommender"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true
```

### Phase 2: Fix Current GitHub Actions (2 hours)

#### Task 2.1: Investigate Current Failures
```bash
# Debug current workflow failures
gh run list --workflow="ci" --limit 5
gh run view [FAILED_RUN_ID] --log
```

**Common issues to fix**:
- Missing shellcheck: `sudo apt-get install -y shellcheck`
- Missing yamllint: `pip install yamllint`
- Permission errors: Update GITHUB_TOKEN permissions
- Missing dependencies: Add to workflow requirements

#### Task 2.2: Create New GitHub Actions Workflow
Create unified `.github/workflows/ci.yml`:

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

env:
  PYTHON_VERSION: '3.11'

jobs:
  pre-commit:
    name: Pre-commit Checks
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install pre-commit
        run: pip install pre-commit

      - name: Cache pre-commit
        uses: actions/cache@v3
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

      - name: Run pre-commit
        run: pre-commit run --all-files --show-diff-on-failure

  test:
    name: Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: '1.7.1'
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v3
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --no-interaction --no-root --with test

      - name: Install project
        run: poetry install --no-interaction

      - name: Run tests
        run: |
          poetry run pytest tests/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=pytest.xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

### Phase 3: Apply Configuration to All Repositories (2 hours)

#### Task 3.1: Update mcp_auto_pr Repository
```bash
cd mcp_auto_pr

# Copy master configurations
cp /path/to/master/.pre-commit-config.yaml .
cp /path/to/master/.github/workflows/ci.yml .github/workflows/

# Update pyproject.toml with tool configurations
# (merge the [tool.black], [tool.ruff], [tool.mypy] sections)

# Install and test
pre-commit install
pre-commit run --all-files
```

#### Task 3.2: Update mcp_local_repo_analyzer Repository
```bash
cd ../mcp_local_repo_analyzer

# Same process as above
cp /path/to/master/.pre-commit-config.yaml .
mkdir -p .github/workflows
cp /path/to/master/.github/workflows/ci.yml .github/workflows/

# Test configuration
pre-commit install
pre-commit run --all-files
poetry run pytest  # Ensure tests still pass
```

#### Task 3.3: Update mcp_pr_recommender Repository
```bash
cd ../mcp_pr_recommender

# Same process
cp /path/to/master/.pre-commit-config.yaml .
mkdir -p .github/workflows
cp /path/to/master/.github/workflows/ci.yml .github/workflows/

# Test configuration
pre-commit install
pre-commit run --all-files
OPENAI_API_KEY=test poetry run pytest  # With mock API key
```

#### Task 3.4: Update mcp_shared_lib Repository
```bash
cd ../mcp_shared_lib

# Same process
cp /path/to/master/.pre-commit-config.yaml .
mkdir -p .github/workflows
cp /path/to/master/.github/workflows/ci.yml .github/workflows/

# Test configuration
pre-commit install
pre-commit run --all-files
poetry run pytest
```

### Phase 4: Testing and Validation (2 hours)

#### Task 4.1: Local Validation
For each repository:
```bash
# Test pre-commit hooks
pre-commit run --all-files

# Test formatting consistency
poetry run black --check src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/

# Test full pipeline
poetry run pytest --cov=src
```

#### Task 4.2: GitHub Actions Validation
```bash
# Push changes and monitor workflows
git add .
git commit -m "feat: align GitHub Actions with pre-commit configuration"
git push origin main

# Monitor workflow runs
gh workflow run ci
gh run watch
```

#### Task 4.3: Cross-Repository Consistency Test
Create a validation script:
```bash
#!/bin/bash
# validate-consistency.sh

repos=("mcp_auto_pr" "mcp_local_repo_analyzer" "mcp_pr_recommender" "mcp_shared_lib")

for repo in "${repos[@]}"; do
    echo "=== Validating $repo ==="
    cd "../$repo"

    # Check pre-commit config exists
    if [[ ! -f .pre-commit-config.yaml ]]; then
        echo "❌ Missing .pre-commit-config.yaml"
        continue
    fi

    # Check GitHub workflow exists
    if [[ ! -f .github/workflows/ci.yml ]]; then
        echo "❌ Missing .github/workflows/ci.yml"
        continue
    fi

    # Run pre-commit
    echo "Running pre-commit..."
    if pre-commit run --all-files; then
        echo "✅ Pre-commit passed"
    else
        echo "❌ Pre-commit failed"
    fi

    # Check tool versions match
    echo "Checking tool versions..."
    black_version=$(grep "rev:" .pre-commit-config.yaml | grep black -A1 | tail -1 | sed 's/.*rev: //')
    ruff_version=$(grep "rev:" .pre-commit-config.yaml | grep ruff -A1 | tail -1 | sed 's/.*rev: //')

    echo "Black version: $black_version"
    echo "Ruff version: $ruff_version"

    cd -
done
```

### Phase 5: Documentation and Monitoring (30 minutes)

#### Task 5.1: Update Documentation
Create/update README sections in each repo:
```markdown
## Development Setup

### Prerequisites
- Python 3.10+
- Poetry 1.7+
- Git

### Quick Setup
```bash
# Install dependencies
poetry install --with dev,test

# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files

# Run tests
poetry run pytest
```

### Code Quality
This project uses:
- **Black** (23.12.1) for code formatting
- **Ruff** (v0.1.11) for linting
- **mypy** (v1.8.0) for type checking

Local pre-commit hooks run the same checks as CI to ensure consistency.
```

#### Task 5.2: Set Up Monitoring
```bash
# Create monitoring script for ongoing validation
cat > scripts/monitor-ci.sh << 'EOF'
#!/bin/bash
# Monitor CI health across all repos

repos=("mcp_auto_pr" "mcp_local_repo_analyzer" "mcp_pr_recommender" "mcp_shared_lib")

for repo in "${repos[@]}"; do
    echo "=== $repo CI Status ==="
    gh repo set-default "manavgup/$repo"
    gh run list --limit 3 --json status,conclusion,headBranch
done
EOF

chmod +x scripts/monitor-ci.sh
```

## 🧪 Testing Checklist

### Pre-deployment Testing
- [ ] All pre-commit configs are identical across repos
- [ ] Tool versions match between pre-commit and CI
- [ ] Local pre-commit runs produce same results as CI
- [ ] All workflows run successfully on test branch
- [ ] No exit code 127 errors in any workflow

### Post-deployment Validation
- [ ] All repositories have green CI status
- [ ] No "works on my machine" issues reported
- [ ] Coverage reporting works correctly
- [ ] Security scans complete successfully

## 🚧 Rollback Plan

If issues arise:
1. **Immediate rollback**: Revert workflow changes
   ```bash
   git revert [COMMIT_HASH]
   git push origin main
   ```

2. **Partial rollback**: Disable problematic jobs
   ```yaml
   # In workflow file
   jobs:
     problematic-job:
       if: false  # Temporarily disable
   ```

3. **Full reset**: Return to original configurations
   ```bash
   git checkout HEAD~1 -- .github/workflows/
   git checkout HEAD~1 -- .pre-commit-config.yaml
   ```

## 📊 Success Metrics

### Immediate (End of Day)
- [ ] 0 failed GitHub Actions workflows
- [ ] All repos have consistent pre-commit config
- [ ] Local and CI results match exactly

### Ongoing (Weekly)
- [ ] CI success rate >95%
- [ ] No pre-commit vs CI discrepancies reported
- [ ] Build time remains <10 minutes

## 📝 Implementation Timeline

| Time | Task | Duration |
|------|------|----------|
| 0:00-0:30 | Audit current workflows and pre-commit configs | 30 min |
| 0:30-1:30 | Create master pre-commit configuration | 1 hour |
| 1:30-3:30 | Fix current GitHub Actions workflows | 2 hours |
| 3:30-5:30 | Apply configuration to all repositories | 2 hours |
| 5:30-7:30 | Testing and validation | 2 hours |
| 7:30-8:00 | Documentation and monitoring setup | 30 min |

**Total**: 8 hours (1 day)

## 🔗 Related Issues
- **Issue #12**: Standardize pre-commit configuration (dependency)
- **Epic #2**: CI/CD Pipeline Stability (parent)

This implementation plan ensures complete alignment between local pre-commit hooks and GitHub Actions while fixing all current CI failures.

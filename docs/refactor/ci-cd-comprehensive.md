# Comprehensive CI/CD Configuration

## Overview
This document provides detailed CI/CD configurations for the monorepo consolidation, based on actual analysis of existing workflows and current issues.

## Current CI/CD State Analysis

### Existing Workflows
- **mcp_auto_pr**: Basic CI with pre-commit and security scanning
- **mcp_shared_lib**: Full CI with testing, linting, and PyPI publishing
- **mcp_local_repo_analyzer**: No CI workflows found
- **mcp_pr_recommender**: No CI workflows found

### Current Issues
1. **Inconsistent CI coverage** - Only 2/4 repos have CI
2. **Different FastMCP versions** - 2.10.6 vs 2.6.1
3. **Test failures** - Local repo analyzer has 4 failing tests
4. **Configuration validation errors** - GitAnalyzerSettings extra fields
5. **CLI help failures** - Both servers have CLI issues

## Unified CI/CD Pipeline

### 1. Main CI Pipeline (.github/workflows/ci.yml)

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

env:
  PYTHON_VERSION: '3.11'
  POETRY_VERSION: '1.7.1'
  COVERAGE_THRESHOLD: '90'

jobs:
  pre-commit:
    name: Pre-commit Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
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
        package: ['shared', 'analyzer', 'recommender']
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}
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
        run: poetry install --with test

      - name: Install project
        run: poetry install

      - name: Run tests for ${{ matrix.package }}
        run: |
          poetry run pytest tests/unit/test_${{ matrix.package }}/ \
            --cov=src/${{ matrix.package }} \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=${{ env.COVERAGE_THRESHOLD }} \
            --junitxml=pytest-${{ matrix.package }}.xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
          name: ${{ matrix.package }}-${{ matrix.python-version }}

  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}

      - name: Install dependencies
        run: poetry install --with test

      - name: Run integration tests
        run: |
          poetry run pytest tests/integration/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=pytest-integration.xml

      - name: Upload integration coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
          name: integration-tests

  performance:
    name: Performance Tests
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}

      - name: Install dependencies
        run: poetry install --with test

      - name: Run performance tests
        run: |
          poetry run pytest tests/performance/ \
            --benchmark-only \
            --benchmark-save=performance-results

      - name: Upload performance results
        uses: actions/upload-artifact@v4
        with:
          name: performance-results
          path: .benchmarks/
          retention-days: 30

  quality:
    name: Quality Checks
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}

      - name: Install dependencies
        run: poetry install --with dev

      - name: Run linting
        run: |
          poetry run ruff check src/ tests/
          poetry run mypy src/

      - name: Run formatting check
        run: poetry run black --check src/ tests/

      - name: Run security checks
        run: |
          poetry run bandit -r src/
          poetry run safety check

      - name: Check code coverage
        run: |
          poetry run pytest --cov=src --cov-report=term-missing --cov-fail-under=${{ env.COVERAGE_THRESHOLD }}

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run CodeQL analysis
        uses: github/codeql-action/init@v3
        with:
          languages: python

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

### 2. Docker Build Pipeline (.github/workflows/docker.yml)

```yaml
name: Docker Build & Push

on:
  push:
    tags:
      - 'v*'
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      build_type:
        description: 'Build type'
        required: true
        default: 'all'
        type: choice
        options:
        - all
        - analyzer
        - recommender

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: ${{ github.event.inputs.build_type == 'all' && fromJSON('["analyzer", "recommender"]') || fromJSON('["' + github.event.inputs.build_type + '"]') }}
        platform: [linux/amd64, linux/arm64]
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/mcp-${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/${{ matrix.service }}/Dockerfile
          platforms: ${{ matrix.platform }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILDKIT_INLINE_CACHE=1

      - name: Run container tests
        run: |
          # Test the built image
          docker run --rm ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/mcp-${{ matrix.service }}:latest --help

      - name: Upload Docker image info
        uses: actions/upload-artifact@v4
        with:
          name: docker-info-${{ matrix.service }}
          path: |
            docker/${{ matrix.service }}/Dockerfile
            docker/${{ matrix.service }}/docker-entrypoint.sh
          retention-days: 30
```

### 3. PyPI Publishing Pipeline (.github/workflows/release.yml)

```yaml
name: PyPI Release

on:
  workflow_dispatch:
    inputs:
      version_type:
        description: 'Version type'
        required: true
        default: 'patch'
        type: choice
        options:
        - patch
        - minor
        - major
        - prerelease
      packages:
        description: 'Packages to release'
        required: true
        default: 'all'
        type: choice
        options:
        - all
        - analyzer
        - recommender
  release:
    types: [published]

permissions:
  contents: write
  id-token: write

jobs:
  publish-analyzer:
    name: Publish Analyzer
    runs-on: ubuntu-latest
    if: github.event.inputs.packages == 'all' || github.event.inputs.packages == 'analyzer' || github.event_name == 'release'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - uses: snok/install-poetry@v1
        with:
          version: '1.7.1'
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ steps.setup-python.outputs.python-version }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --with dev

      - name: Run tests
        run: |
          poetry run pytest tests/unit/test_mcp_local_repo_analyzer/ \
            --cov=src/mcp_local_repo_analyzer \
            --cov-fail-under=90

      - name: Run quality checks
        run: |
          poetry run ruff check src/mcp_local_repo_analyzer/
          poetry run mypy src/mcp_local_repo_analyzer/

      - name: Configure git
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Update version (manual)
        if: github.event_name == 'workflow_dispatch'
        run: |
          case "${{ github.event.inputs.version_type }}" in
            patch)
              poetry version patch
              ;;
            minor)
              poetry version minor
              ;;
            major)
              poetry version major
              ;;
            prerelease)
              poetry version prerelease
              ;;
          esac
          git add pyproject.toml
          git commit -m "Bump version to $(poetry version -s)"
          git tag "v$(poetry version -s)"
          git push origin main --tags

      - name: Build package
        run: |
          cp pyproject-analyzer.toml pyproject.toml
          poetry build

      - name: Upload package artifacts
        uses: actions/upload-artifact@v4
        with:
          name: analyzer-dist
          path: dist/
          retention-days: 30

      - name: Publish to PyPI
        if: success()
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
        run: poetry publish

  publish-recommender:
    name: Publish Recommender
    runs-on: ubuntu-latest
    if: github.event.inputs.packages == 'all' || github.event.inputs.packages == 'recommender' || github.event_name == 'release'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - uses: snok/install-poetry@v1
        with:
          version: '1.7.1'
          virtualenvs-create: true
          virtualenvs-in-project: true

      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ steps.setup-python.outputs.python-version }}-${{ hashFiles('**/poetry.lock') }}

      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --with dev

      - name: Run tests
        run: |
          poetry run pytest tests/unit/test_mcp_pr_recommender/ \
            --cov=src/mcp_pr_recommender \
            --cov-fail-under=90

      - name: Run quality checks
        run: |
          poetry run ruff check src/mcp_pr_recommender/
          poetry run mypy src/mcp_pr_recommender/

      - name: Configure git
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Update version (manual)
        if: github.event_name == 'workflow_dispatch'
        run: |
          case "${{ github.event.inputs.version_type }}" in
            patch)
              poetry version patch
              ;;
            minor)
              poetry version minor
              ;;
            major)
              poetry version major
              ;;
            prerelease)
              poetry version prerelease
              ;;
          esac
          git add pyproject.toml
          git commit -m "Bump version to $(poetry version -s)"
          git tag "v$(poetry version -s)"
          git push origin main --tags

      - name: Build package
        run: |
          cp pyproject-recommender.toml pyproject.toml
          poetry build

      - name: Upload package artifacts
        uses: actions/upload-artifact@v4
        with:
          name: recommender-dist
          path: dist/
          retention-days: 30

      - name: Publish to PyPI
        if: success()
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
        run: poetry publish

  create-release:
    name: Create GitHub Release
    runs-on: ubuntu-latest
    needs: [publish-analyzer, publish-recommender]
    if: always() && (needs.publish-analyzer.result == 'success' || needs.publish-recommender.result == 'success')
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts/

      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.ref_name }}
          name: Release ${{ github.ref_name }}
          body: |
            ## What's Changed

            ### New Features
            - Monorepo consolidation
            - Shared server base class
            - Unified CI/CD pipeline

            ### Improvements
            - 90%+ test coverage
            - Automated security scanning
            - Multi-platform Docker builds

            ### Bug Fixes
            - Fixed configuration validation errors
            - Resolved CLI help command issues
            - Fixed MCP server initialization problems

            ## Installation

            ```bash
            # Install analyzer
            pip install mcp-local-repo-analyzer==${{ github.ref_name }}

            # Install recommender
            pip install mcp-pr-recommender==${{ github.ref_name }}
            ```

            ## Docker Images

            ```bash
            # Pull images
            docker pull ghcr.io/manavgup/mcp-analyzer:${{ github.ref_name }}
            docker pull ghcr.io/manavgup/mcp-recommender:${{ github.ref_name }}
            ```
          files: |
            artifacts/*/dist/*.whl
            artifacts/*/dist/*.tar.gz
          draft: false
          prerelease: ${{ contains(github.ref_name, 'alpha') || contains(github.ref_name, 'beta') || contains(github.ref_name, 'rc') }}
```

### 4. Security Pipeline (.github/workflows/security.yml)

```yaml
name: Security & Compliance

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          allow-licenses: MIT,Apache-2.0,BSD-2-Clause,BSD-3-Clause

  secret-scanning:
    name: Secret Scanning
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          path: .
          base: HEAD~1
          head: HEAD
          extra_args: --only-verified

  code-scanning:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python
          queries: security-extended,security-and-quality

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:python"

  container-scanning:
    name: Container Scanning
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build container images
        run: |
          docker build -f docker/analyzer/Dockerfile -t mcp-analyzer:test .
          docker build -f docker/recommender/Dockerfile -t mcp-recommender:test .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'image'
          scan-ref: 'mcp-analyzer:test,mcp-recommender:test'
          format: 'sarif'
          output: 'trivy-results.sarif'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

### 5. Pre-commit CI (.github/workflows/pre-commit.yml)

```yaml
name: Pre-commit

on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  pre-commit:
    name: Pre-commit Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install pre-commit
        run: pip install pre-commit

      - name: Cache pre-commit
        uses: actions/cache@v3
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

      - name: Run pre-commit on all files
        run: pre-commit run --all-files --show-diff-on-failure

      - name: Run pre-commit on PR files
        if: github.event_name == 'pull_request'
        run: |
          git fetch origin ${{ github.event.pull_request.base.sha }}
          pre-commit run --from-ref origin/${{ github.event.pull_request.base.sha }} --to-ref HEAD
```

## Pre-commit Configuration

### Unified .pre-commit-config.yaml

```yaml
# Master pre-commit configuration for monorepo
# Aligned with CI/CD pipeline for "works on my machine" prevention

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
      - id: check-case-conflict
      - id: check-docstring-first
      - id: check-json
      - id: check-merge-conflict
      - id: check-symlinks
      - id: check-toml
      - id: check-vcs-permalinks
      - id: detect-private-key
      - id: requirements-txt-fixer

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length=88', '--target-version=py311']

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-pyyaml
          - types-requests
          - types-setuptools
        args:
          - --ignore-missing-imports
          - --disallow-untyped-defs
          - --warn-return-any
          - --warn-unused-configs

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'src/', '-f', 'json', '-o', 'bandit-report.json']
        exclude: ^tests/

  - repo: https://github.com/PyCQA/safety
    rev: 2.3.5
    hooks:
      - id: safety
        args: ['--json', '--output', 'safety-report.json']

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile', 'black', '--line-length', '88']

  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types: [yaml, json, markdown]

  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
        args: ['--fix']

  - repo: https://github.com/PyCQA/docformatter
    rev: v1.7.5
    hooks:
      - id: docformatter
        args: ['--in-place', '--wrap-summaries', '88', '--wrap-descriptions', '88']

  - repo: https://github.com/PyCQA/interrogate
    rev: 1.5.0
    hooks:
      - id: interrogate
        args: ['--fail-under=90', '--exclude=tests/', '--exclude=src/shared/testing/']

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

## Dependabot Configuration

### .github/dependabot.yml

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 10
    reviewers:
      - "manavgup"
    assignees:
      - "manavgup"
    commit-message:
      prefix: "deps"
      include: "scope"
    labels:
      - "dependencies"
      - "python"
    ignore:
      # Ignore major version updates for critical packages
      - dependency-name: "fastmcp"
        update-types: ["version-update:semver-major"]
      - dependency-name: "pydantic"
        update-types: ["version-update:semver-major"]

  # Docker dependencies
  - package-ecosystem: "docker"
    directory: "/docker/analyzer"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "docker"

  - package-ecosystem: "docker"
    directory: "/docker/recommender"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "docker"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "github-actions"

  # Pre-commit hooks
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "monthly"
      day: "monday"
      time: "09:00"
      timezone: "UTC"
    target-branch: "develop"
    open-pull-requests-limit: 3
    labels:
      - "dependencies"
      - "pre-commit"
    ignore:
      - dependency-name: "pre-commit"
        update-types: ["version-update:semver-major"]
```

## CI/CD Environment Variables

### Required Secrets

```bash
# PyPI Publishing
PYPI_TOKEN=your_pypi_token_here

# GitHub Container Registry
GITHUB_TOKEN=your_github_token_here

# Codecov (optional)
CODECOV_TOKEN=your_codecov_token_here

# Security scanning (optional)
TRIVY_TOKEN=your_trivy_token_here
```

### Environment Configuration

```yaml
# .github/env/ci.yml
PYTHON_VERSION: '3.11'
POETRY_VERSION: '1.7.1'
COVERAGE_THRESHOLD: '90'
TEST_TIMEOUT: '300'
MAX_PARALLEL_JOBS: '4'
DOCKER_BUILDKIT: '1'
```

## Monitoring and Alerting

### CI/CD Metrics

- **Build success rate**: Target 99%+
- **Test execution time**: Target <10 minutes
- **Coverage trend**: Monitor for decreases
- **Security scan results**: Track vulnerability counts
- **Dependency update frequency**: Weekly updates

### Failure Notifications

- **Slack/Teams integration** for CI failures
- **Email notifications** for security issues
- **GitHub Issues** for persistent failures
- **Dashboard monitoring** for trends

## Migration Steps

### Phase 1: Setup (Day 1)
1. Create `.github/workflows/` directory
2. Add all workflow files
3. Configure secrets and permissions
4. Test basic CI pipeline

### Phase 2: Integration (Day 2)
1. Update pre-commit configuration
2. Configure dependabot
3. Set up security scanning
4. Test full pipeline

### Phase 3: Optimization (Day 3)
1. Optimize build caching
2. Configure parallel jobs
3. Set up monitoring
4. Document processes

This comprehensive CI/CD configuration provides a production-grade pipeline that addresses all current issues while maintaining high quality standards and automated processes.

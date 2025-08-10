# PyPI Publishing from Monorepo

## Overview
Strategy for publishing multiple PyPI packages from a single monorepo.

## Package Configuration

### Unified pyproject.toml Structure
```toml
[tool.poetry]
name = "mcp-auto-pr"
version = "0.2.0"
description = "Monorepo for MCP PR automation tools"
authors = ["Manav Gupta <manavg@gmail.com>"]
readme = "README.md"
license = "MIT"
repository = "https://github.com/manavgup/mcp_auto_pr"
packages = [
    {include = "mcp_shared_lib", from = "src"},
    {include = "mcp_local_repo_analyzer", from = "src"},
    {include = "mcp_pr_recommender", from = "src"}
]

[tool.poetry.dependencies]
python = ">=3.10,<4.0"
# Shared dependencies
fastmcp = "^2.10.6"
pydantic = "^2.11.7"
# Analyzer-specific
gitpython = "^3.1.40"
# Recommender-specific
openai = "^1.0.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

## Multi-Package Publishing Strategy

### Option 1: Separate Build Configs (Recommended)
Create separate build configurations for each package:

#### pyproject-analyzer.toml
```toml
[tool.poetry]
name = "mcp-local-repo-analyzer"
version = "0.2.0"
description = "MCP server for analyzing git changes"
packages = [
    {include = "mcp_local_repo_analyzer", from = "src"},
    {include = "mcp_shared_lib", from = "src"}
]
# Package-specific metadata
```

#### pyproject-recommender.toml
```toml
[tool.poetry]
name = "mcp-pr-recommender"
version = "0.2.0"
description = "AI-powered PR recommendation MCP server"
packages = [
    {include = "mcp_pr_recommender", from = "src"},
    {include = "mcp_shared_lib", from = "src"}
]
# Package-specific metadata
```

### Option 2: Build Script Approach
Use a custom build script to create distributions:

```python
# scripts/build_packages.py
import shutil
import subprocess
from pathlib import Path

def build_package(name, includes):
    """Build a specific package."""
    # Create temporary pyproject.toml
    # Copy required source files
    # Run poetry build
    # Move artifacts to dist/
    pass

# Build each package
build_package("mcp-local-repo-analyzer",
              ["mcp_local_repo_analyzer", "mcp_shared_lib"])
build_package("mcp-pr-recommender",
              ["mcp_pr_recommender", "mcp_shared_lib"])
```

## Publishing Workflow

### Manual Publishing
```bash
# Build all packages
make build-all

# Or individually
poetry build -f wheel
poetry build -f sdist

# Publish to TestPyPI first
poetry publish -r testpypi

# Publish to PyPI
poetry publish
```

### Automated Publishing (GitHub Actions)
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish-analyzer:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: snok/install-poetry@v1

      - name: Build analyzer package
        run: |
          cp pyproject-analyzer.toml pyproject.toml
          poetry build

      - name: Publish analyzer
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
        run: poetry publish

  publish-recommender:
    runs-on: ubuntu-latest
    steps:
      # Similar steps for recommender
```

## Package Metadata

### mcp-local-repo-analyzer
```toml
[tool.poetry]
name = "mcp-local-repo-analyzer"
version = "0.2.0"
description = "MCP server for analyzing outstanding git changes"
keywords = ["mcp", "git", "repository-analysis", "mcp-server"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Version Control :: Git",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[tool.poetry.scripts]
mcp-analyzer = "mcp_local_repo_analyzer.cli:main"
```

### mcp-pr-recommender
```toml
[tool.poetry]
name = "mcp-pr-recommender"
version = "0.2.0"
description = "AI-powered MCP server for PR recommendations"
keywords = ["mcp", "ai", "pull-requests", "mcp-server", "openai"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Version Control",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "License :: OSI Approved :: MIT License",
]

[tool.poetry.scripts]
mcp-recommender = "mcp_pr_recommender.cli:main"
```

## Version Management

### Synchronized Versioning
Keep all packages at the same version:

```python
# scripts/update_version.py
import toml
from pathlib import Path

def update_all_versions(new_version):
    """Update version in all configuration files."""
    configs = [
        "pyproject.toml",
        "pyproject-analyzer.toml",
        "pyproject-recommender.toml"
    ]

    for config_file in configs:
        with open(config_file, 'r') as f:
            data = toml.load(f)
        data['tool']['poetry']['version'] = new_version
        with open(config_file, 'w') as f:
            toml.dump(data, f)
```

### Version Bumping
```bash
# Bump version using poetry
poetry version patch  # 0.2.0 -> 0.2.1
poetry version minor  # 0.2.0 -> 0.3.0
poetry version major  # 0.2.0 -> 1.0.0

# Or use custom script
python scripts/update_version.py 0.2.1
```

## Testing Package Installation

### Local Testing
```bash
# Build packages
make build-all

# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install from local dist
pip install dist/mcp_local_repo_analyzer-0.2.0-py3-none-any.whl
pip install dist/mcp_pr_recommender-0.2.0-py3-none-any.whl

# Test imports
python -c "import mcp_local_repo_analyzer"
python -c "import mcp_pr_recommender"

# Test CLI
mcp-analyzer --help
mcp-recommender --help
```

### TestPyPI Testing
```bash
# Publish to TestPyPI
poetry publish -r testpypi

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    mcp-local-repo-analyzer==0.2.0
```

## Distribution Checklist

### Pre-Publishing
- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run all tests
- [ ] Check coverage (90%+)
- [ ] Update documentation
- [ ] Create git tag

### Publishing
- [ ] Build distributions
- [ ] Check package contents
- [ ] Publish to TestPyPI
- [ ] Test installation from TestPyPI
- [ ] Publish to PyPI
- [ ] Verify on PyPI

### Post-Publishing
- [ ] Create GitHub release
- [ ] Update documentation links
- [ ] Announce release
- [ ] Monitor for issues

## Troubleshooting

### Common Issues

#### Package Not Found
**Problem**: Import errors after installation
**Solution**: Ensure packages are correctly specified in pyproject.toml

#### Missing Dependencies
**Problem**: Runtime errors due to missing packages
**Solution**: Verify all dependencies are listed

#### Version Conflicts
**Problem**: Dependency version conflicts
**Solution**: Use compatible version ranges

#### Build Failures
**Problem**: Poetry build fails
**Solution**: Clear build cache, verify pyproject.toml syntax

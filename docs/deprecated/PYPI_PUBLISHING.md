# PyPI Publishing Instructions

This document provides instructions for publishing two independent MCP servers to PyPI.

## Publishing Strategy

We publish **two independent MCP servers**:
1. **mcp-local-repo-analyzer** - Git change analysis MCP server
2. **mcp-pr-recommender** - AI-powered PR recommendation MCP server

The `mcp-shared-lib` remains as a GitHub dependency (not published to PyPI) to keep implementation details internal.

## Prerequisites

1. **PyPI Account**: Create accounts on both PyPI (production) and TestPyPI (testing)
   - PyPI: https://pypi.org/account/register/
   - TestPyPI: https://test.pypi.org/account/register/

2. **API Tokens**: Generate API tokens for secure publishing
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

## Configuration

### 1. Configure Poetry with PyPI credentials

```bash
# Configure production PyPI token
poetry config pypi-token.pypi your_pypi_token_here

# Configure TestPyPI for testing (optional)
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi your_testpypi_token_here
```

### 2. Verify configuration

```bash
poetry config --list | grep pypi
```

## Publishing Process

### Step 1: Test on TestPyPI (Recommended)

```bash
# Publish to TestPyPI first for testing
cd mcp_local_repo_analyzer
poetry build
poetry publish -r testpypi

cd ../mcp_pr_recommender
poetry build
poetry publish -r testpypi
```

### Step 2: Verify TestPyPI packages

```bash
# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-local-repo-analyzer
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-pr-recommender
```

### Step 3: Publish to production PyPI

Once testing is successful, publish to production PyPI:

```bash
# Publish to production PyPI
cd mcp_local_repo_analyzer
poetry build
poetry publish

cd ../mcp_pr_recommender
poetry build
poetry publish
```

## Package Information

### mcp-local-repo-analyzer
- **Version**: 0.2.0
- **Description**: MCP server for analyzing outstanding git changes in repositories
- **PyPI URL**: https://pypi.org/project/mcp-local-repo-analyzer/
- **Key Features**:
  - Analyze uncommitted changes with risk assessment
  - Detect staged changes ready for commit
  - Track unpushed commits
  - Provide comprehensive change summaries

### mcp-pr-recommender
- **Version**: 0.2.0
- **Description**: AI-powered MCP server for intelligent PR grouping recommendations
- **PyPI URL**: https://pypi.org/project/mcp-pr-recommender/
- **Key Features**:
  - Generate intelligent PR groupings using GPT-4
  - Analyze PR feasibility and conflicts
  - Multiple grouping strategies (semantic, size-based, directory-based)
  - Validate and refine recommendations
- **Requirements**: OPENAI_API_KEY environment variable

## User Installation

Users can install each MCP server independently based on their needs:

```bash
# For git repository analysis only
pip install mcp-local-repo-analyzer

# For AI-powered PR recommendations only
pip install mcp-pr-recommender

# For complete PR workflow (install both)
pip install mcp-local-repo-analyzer mcp-pr-recommender
```

## Quick Start for Users

### MCP Local Repository Analyzer

```bash
# Install and run
pip install mcp-local-repo-analyzer
python -m mcp_local_repo_analyzer.main --transport stdio
```

### MCP PR Recommender

```bash
# Install and configure
pip install mcp-pr-recommender
export OPENAI_API_KEY=your_openai_api_key

# Run the server
python -m mcp_pr_recommender.main --transport stdio
```

## Verification

After publishing, verify the packages are available:

1. Check package pages:
   - https://pypi.org/project/mcp-shared-lib/
   - https://pypi.org/project/mcp-local-repo-analyzer/
   - https://pypi.org/project/mcp-pr-recommender/

2. Test installation in a fresh environment:
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install mcp-shared-lib mcp-local-repo-analyzer mcp-pr-recommender
   ```

## Notes

- All packages built successfully and are ready for publishing
- Authentication credentials need to be configured before publishing
- Consider using GitHub Actions for automated publishing on releases
- The packages follow semantic versioning and include comprehensive metadata

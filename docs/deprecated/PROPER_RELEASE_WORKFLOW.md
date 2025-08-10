# Proper Release Workflow

## The Right Way to Release MCP Packages

### Current Issue
- We published v0.3.1 when this should be v0.1.0 (first real release)
- We published to PyPI without thorough local testing first
- Version numbers got inflated due to iterative fixes

### Correct Release Process

#### Step 1: Reset to Proper Version Numbers
```bash
# Update to proper v0.1.0 for first real release
cd mcp_local_repo_analyzer
# Edit pyproject.toml: version = "0.1.0"

cd ../mcp_pr_recommender
# Edit pyproject.toml: version = "0.1.0"

cd ../mcp_shared_lib
# Edit pyproject.toml: version = "0.1.0"
```

#### Step 2: Build Locally
```bash
cd mcp_local_repo_analyzer
poetry build

cd ../mcp_pr_recommender
poetry build

cd ../mcp_shared_lib
poetry build
```

#### Step 3: Test Locally First
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install LOCAL builds (not from PyPI)
pip install ./mcp_local_repo_analyzer/dist/mcp_local_repo_analyzer-0.1.0-py3-none-any.whl
pip install ./mcp_pr_recommender/dist/mcp_pr_recommender-0.1.0-py3-none-any.whl

# Run comprehensive tests
python test_script.py

# Test actual MCP functionality
export OPENAI_API_KEY=your_key
python -m mcp_local_repo_analyzer.main --transport stdio
python -m mcp_pr_recommender.main --transport stdio
```

#### Step 4: Only After Local Tests Pass
```bash
# Then and only then, publish to PyPI
poetry publish
```

### Recommended: Yanking Current Versions

Since v0.2.0 and v0.3.x are inflated, we should:

1. **Yank the problematic versions** on PyPI (mark as unavailable)
2. **Release proper v0.1.0** as the canonical first release
3. **Document this as the official first release**

### Command to Yank Versions
```bash
# Yank inflated versions (requires PyPI permissions)
pip install twine
twine yank mcp-local-repo-analyzer 0.2.0 0.3.0 0.3.1
twine yank mcp-pr-recommender 0.2.0 0.3.0 0.3.1
```

### Proper Version Strategy Going Forward

- **v0.1.0** - First proper release (bundled packages)
- **v0.1.x** - Bug fixes and patches
- **v0.2.0** - New features or breaking changes
- **v1.0.0** - Stable API, production ready

### Lesson Learned

Always follow this sequence:
1. **Local build** → 2. **Local test** → 3. **Publish**

Never publish directly to PyPI without thorough local validation first.

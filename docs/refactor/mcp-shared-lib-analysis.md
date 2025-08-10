# MCP Shared Lib Analysis & Production-Grade Restructure

## Current Structure Analysis

### Files Actually Used by Other Packages

#### ✅ **Heavily Used - Core Shared Code**
1. **Models** (models/*)
   - `git/repository.py` - LocalRepository (used in 8+ places)
   - `git/changes.py` - FileStatus, WorkingDirectoryChanges
   - `analysis/results.py` - OutstandingChangesAnalysis
   - `analysis/repository.py` - RepositoryStatus
   - `base/common.py` - BranchStatus

2. **Services** (services/git/*)
   - `git_client.py` - GitClient (core git operations, used everywhere)

3. **Configuration** (config/*)
   - `git_analyzer.py` - GitAnalyzerSettings (used by analyzer services)
   - `base.py` - Base configuration classes

4. **Utils** (utils/*)
   - `git_utils.py` - find_git_root, is_git_repository (used in all tools)
   - `logging_utils.py` - logging_service (used in main.py, cli.py)
   - `file_utils.py` - File system utilities

5. **Transports** (transports/*)
   - All transport files (config, factory, implementations)
   - Used by both CLI modules for server startup

6. **Server** (server/*)
   - `runner.py` - run_server function (used by both CLIs)

#### ❌ **Unused/Underused - Should Be Removed or Reorganized**
1. **tools/base.py** - BaseMCPTool abstract class (0 usages)
2. **test_utils/** - Only used in 1 conftest.py file (minimal usage)

#### 🤔 **Config Organization Issue**
- `config/git_analyzer.py` - Only used by mcp_local_repo_analyzer
- Should move to analyzer-specific config

## Current Issues with Structure

### 1. **Poor Naming**
- "mcp_shared_lib" is scaffolding naming, not descriptive
- Doesn't indicate what functionality is actually shared

### 2. **Mixed Concerns**
- Git-specific config mixed with general config
- Package-specific settings in "shared" library
- Test utilities that aren't actually shared

### 3. **Unused Abstractions**
- BaseMCPTool isn't used anywhere
- Over-engineered for current needs

### 4. **Inconsistent Organization**
- git_analyzer.py and git_client.py in different folders but related
- Some models truly shared, others package-specific

## Proposed Production-Grade Structure

```
mcp_auto_pr/
├── src/
│   ├── shared/                          # Renamed from mcp_shared_lib
│   │   ├── __init__.py
│   │   ├── models/                      # Truly shared data models
│   │   │   ├── __init__.py
│   │   │   ├── git.py                   # Git-related models (consolidated)
│   │   │   └── analysis.py              # Analysis result models
│   │   ├── git/                         # Git operations and utilities
│   │   │   ├── __init__.py
│   │   │   ├── client.py                # GitClient (renamed from git_client.py)
│   │   │   ├── config.py                # Git-specific config (moved from config/)
│   │   │   └── utils.py                 # Git utilities (find_git_root, etc.)
│   │   ├── mcp/                         # MCP protocol shared code
│   │   │   ├── __init__.py
│   │   │   ├── server.py                # Server runner (renamed from server/runner.py)
│   │   │   └── transports/              # All transport implementations
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── config.py
│   │   │       ├── factory.py
│   │   │       ├── http.py
│   │   │       ├── stdio.py
│   │   │       ├── websocket.py
│   │   │       └── sse.py
│   │   ├── common/                      # Common utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # Base configuration classes
│   │   │   ├── logging.py               # Logging utilities (renamed)
│   │   │   └── files.py                 # File system utilities
│   │   └── testing/                     # Test utilities (if needed)
│   │       ├── __init__.py
│   │       └── factories.py             # Consolidated test factories
│   ├── mcp_local_repo_analyzer/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── cli.py
│   │   ├── main.py
│   │   ├── config.py                    # Package-specific config
│   │   ├── services/
│   │   │   └── git/
│   │   │       ├── change_detector.py
│   │   │       ├── diff_analyzer.py
│   │   │       └── status_tracker.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── staging_area.py
│   │       ├── summary.py
│   │       ├── unpushed_commits.py
│   │       └── working_directory.py
│   └── mcp_pr_recommender/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── main.py
│       ├── config.py
│       ├── prompts.py
│       ├── services/
│       │   ├── atomicity_validator.py
│       │   ├── grouping_engine.py
│       │   └── semantic_analyzer.py
│       └── tools/
│           ├── __init__.py
│           ├── pr_recommender_tool.py
│           ├── feasibility_analyzer_tool.py
│           ├── strategy_manager_tool.py
│           └── validator_tool.py
```

## Key Changes Explained

### 1. **Better Naming**
- `mcp_shared_lib` → `shared` (clearer, less scaffolding)
- `git_client.py` → `git/client.py` (better organization)
- `logging_utils.py` → `common/logging.py` (clearer naming)

### 2. **Logical Grouping**
- **Git-related code** all under `shared/git/`
- **MCP protocol code** under `shared/mcp/`
- **Common utilities** under `shared/common/`
- **Models** grouped by domain (git vs analysis)

### 3. **Consolidated Models**
Instead of scattered model files:
```python
# shared/models/git.py
"""All git-related models in one place."""
class LocalRepository:
    # ...

class FileStatus:
    # ...

class WorkingDirectoryChanges:
    # ...

# shared/models/analysis.py
"""All analysis result models."""
class OutstandingChangesAnalysis:
    # ...

class RepositoryStatus:
    # ...
```

### 4. **Configuration Rationalization**
- Move `GitAnalyzerSettings` to `mcp_local_repo_analyzer/config.py`
- Keep only truly shared config in `shared/common/config.py`

### 5. **Removed Dead Code**
- `tools/base.py` (BaseMCPTool - unused)
- Minimal `test_utils` (barely used, can be recreated if needed)

## Migration Benefits

### 1. **Clarity**
- Clear separation between truly shared vs package-specific
- Logical grouping of related functionality
- No more "shared_lib" scaffolding names

### 2. **Maintainability**
- Related code lives together (git client + git config + git utils)
- Easier to find and modify related functionality
- Clear ownership boundaries

### 3. **Extensibility**
- Easy to add new shared models/utilities
- Clear patterns for where new code should live
- Modular structure supports growth

## Import Changes

### Before (Current)
```python
from mcp_shared_lib.models.git.repository import LocalRepository
from mcp_shared_lib.services.git.git_client import GitClient
from mcp_shared_lib.utils.git_utils import find_git_root
from mcp_shared_lib.config.git_analyzer import GitAnalyzerSettings
from mcp_shared_lib.server.runner import run_server
```

### After (Proposed)
```python
from shared.models.git import LocalRepository
from shared.git.client import GitClient
from shared.git.utils import find_git_root
from mcp_local_repo_analyzer.config import GitAnalyzerSettings  # Moved to package
from shared.mcp.server import run_server
```

## PyPI Publishing Impact

### Packages Structure
```toml
# pyproject.toml packages for mcp-local-repo-analyzer
packages = [
    {include = "mcp_local_repo_analyzer", from = "src"},
    {include = "shared", from = "src"}  # Include shared code
]

# pyproject.toml packages for mcp-pr-recommender
packages = [
    {include = "mcp_pr_recommender", from = "src"},
    {include = "shared", from = "src"}  # Include shared code
]
```

This maintains the bundling approach but with cleaner naming and organization.

## Recommended Implementation Order

1. **Phase 1**: Rename `mcp_shared_lib` → `shared`
2. **Phase 2**: Reorganize into logical folders (git/, mcp/, common/)
3. **Phase 3**: Consolidate models files
4. **Phase 4**: Move package-specific config out of shared
5. **Phase 5**: Remove unused code (BaseMCPTool, test_utils)
6. **Phase 6**: Update all import statements

This structure represents a production-grade organization that's both maintainable and extensible while eliminating the scaffolding feel of the current "mcp_shared_lib" approach.
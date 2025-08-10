# Epic 4: Shared Library Improvements

## 📋 Epic Overview
**Epic ID**: E4
**Priority**: P1 (High)
**Estimated Effort**: 3 days
**Sprint**: 2
**Dependencies**: Epic 2 (Test Coverage) - need good tests before refactoring

## 🎯 Epic Goal
Improve the structure, naming, and organization of shared code to create a production-grade foundation that's maintainable and extensible.

## 🚫 Current Problems
- "mcp_shared_lib" feels like scaffolding naming
- Mixed concerns: git-specific config in general shared lib
- Unused abstractions (BaseMCPTool with 0 usages)
- Related code scattered across different folders
- Package-specific code in "shared" library

## 🎯 Epic Outcome
A clean, well-organized shared codebase with:
- Clear naming that reflects actual purpose
- Logical grouping of related functionality
- Removal of unused/dead code
- Better separation of truly shared vs package-specific code
- Production-grade structure suitable for long-term maintenance

## 📋 User Stories

### Story 4.1: Rename and Restructure Shared Library
**As a** developer
**I want** the shared library to have clear, professional naming
**So that** the codebase feels production-ready and is easy to navigate

#### Acceptance Criteria
- [ ] mcp_shared_lib renamed to "shared"
- [ ] Clear folder structure with logical grouping
- [ ] Related functionality co-located
- [ ] Import statements updated throughout codebase
- [ ] No broken imports or missing modules
- [ ] PyPI packaging still works correctly

#### Tasks
- [ ] **Rename package**: mcp_shared_lib → shared
- [ ] **Reorganize structure**:
  - [ ] Create `shared/git/` for git-related code
  - [ ] Create `shared/mcp/` for MCP protocol code
  - [ ] Create `shared/common/` for general utilities
  - [ ] Create `shared/models/` for consolidated data models
- [ ] **Update all import statements** in analyzer and recommender
- [ ] **Update pyproject.toml** packaging configuration
- [ ] **Test imports work correctly**

### Story 4.2: Consolidate and Cleanup Models
**As a** developer
**I want** data models organized logically in fewer files
**So that** I can find and use models efficiently without hunting through many small files

#### Acceptance Criteria
- [ ] Related models consolidated into single files
- [ ] Clear separation between git models and analysis models
- [ ] All existing model functionality preserved
- [ ] Import paths simplified and logical
- [ ] Models properly documented with examples

#### Tasks
- [ ] **Consolidate git models** into `shared/models/git.py`:
  - [ ] LocalRepository (from git/repository.py)
  - [ ] FileStatus, WorkingDirectoryChanges (from git/changes.py)
  - [ ] Commit models (from git/commits.py)
  - [ ] File models (from git/files.py)
- [ ] **Consolidate analysis models** into `shared/models/analysis.py`:
  - [ ] OutstandingChangesAnalysis (from analysis/results.py)
  - [ ] RepositoryStatus (from analysis/repository.py)
  - [ ] Risk and categorization models
- [ ] **Update imports** throughout codebase
- [ ] **Add model documentation** and usage examples

### Story 4.3: Reorganize Git-Related Code
**As a** developer
**I want** all git-related functionality grouped together
**So that** I can easily find and maintain git operations, config, and utilities

#### Acceptance Criteria
- [ ] All git code under `shared/git/` directory
- [ ] Git client, config, and utilities co-located
- [ ] Clear separation of concerns within git module
- [ ] Git-specific configuration moved from general config
- [ ] Consistent API across git operations

#### Tasks
- [ ] **Move git_client.py** → `shared/git/client.py`
- [ ] **Move git_analyzer.py** → `shared/git/config.py` (package-specific config)
- [ ] **Move git_utils.py** → `shared/git/utils.py`
- [ ] **Update imports** for new git module structure
- [ ] **Review git module API** for consistency
- [ ] **Add git module documentation**

### Story 4.4: Remove Dead Code and Unused Abstractions
**As a** developer
**I want** unused code removed from the shared library
**So that** the codebase stays lean and doesn't confuse future developers

#### Acceptance Criteria
- [ ] BaseMCPTool removed (0 usages confirmed)
- [ ] Minimally-used test_utils reviewed and cleaned
- [ ] Dead imports removed
- [ ] Unused utility functions removed
- [ ] Code complexity reduced without losing functionality

#### Tasks
- [ ] **Remove tools/base.py** (BaseMCPTool - confirmed 0 usage)
- [ ] **Review test_utils/factories/**:
  - [ ] Keep only factories actually used in tests
  - [ ] Remove or consolidate rarely-used factories
  - [ ] Move to `shared/testing/` if kept
- [ ] **Clean up imports**:
  - [ ] Remove unused imports throughout shared code
  - [ ] Update __init__.py files for new structure
  - [ ] Remove circular import risks
- [ ] **Remove unused utility functions**
- [ ] **Clean up configuration**:
  - [ ] Move package-specific config out of shared
  - [ ] Keep only truly shared configuration classes

### Story 4.5: Update Package-Specific Code
**As a** developer
**I want** package-specific configuration moved to the appropriate packages
**So that** shared code only contains truly shared functionality

#### Acceptance Criteria
- [ ] GitAnalyzerSettings moved to mcp_local_repo_analyzer
- [ ] Package-specific config no longer in shared lib
- [ ] Clear boundaries between shared and package-specific code
- [ ] Imports updated to reflect new organization
- [ ] Configuration precedence still works correctly

#### Tasks
- [ ] **Move GitAnalyzerSettings**:
  - [ ] From `shared/config/git_analyzer.py`
  - [ ] To `mcp_local_repo_analyzer/config.py`
  - [ ] Update imports in analyzer package
- [ ] **Review other package-specific code** in shared lib
- [ ] **Clean up shared config**:
  - [ ] Keep only base configuration classes
  - [ ] Remove package-specific settings
  - [ ] Consolidate into `shared/common/config.py`

## ✅ Definition of Done

### Story-Level DoD
- [ ] All acceptance criteria met
- [ ] Tests pass with new structure
- [ ] Imports work correctly throughout codebase
- [ ] No functionality lost in refactoring
- [ ] Code review completed (if team)

### Epic-Level DoD
- [ ] Shared library has professional structure and naming
- [ ] All related code logically grouped
- [ ] Dead code removed, codebase is lean
- [ ] Package-specific code moved to appropriate packages
- [ ] All tests pass with new structure
- [ ] PyPI packaging works with new structure
- [ ] Documentation reflects new organization
- [ ] Import paths are intuitive and consistent
- [ ] Code complexity reduced while maintaining functionality

## 🧪 Testing Strategy

### Refactoring Safety
- [ ] **Comprehensive test coverage** before refactoring (Epic 2)
- [ ] **Import validation tests** to ensure no broken imports
- [ ] **Functionality tests** to ensure no behavior changes
- [ ] **Integration tests** to verify packages still work together

### Validation Approach
- [ ] **Step-by-step refactoring** with tests at each step
- [ ] **Import path validation** after each change
- [ ] **PyPI build testing** to ensure packaging works
- [ ] **End-to-end testing** of both MCP servers

### Rollback Strategy
- [ ] **Git branch** for each major refactoring step
- [ ] **Tagged commit** before starting refactoring
- [ ] **Rollback procedure** documented and tested

## 📊 Success Metrics

### Code Quality Metrics
- **Code Organization Score**: Subjective improvement in navigability
- **Import Complexity**: Reduced number of import paths
- **Dead Code**: 0% unused functions/classes
- **Documentation Coverage**: All modules documented

### Functional Metrics
- **Test Pass Rate**: 100% after refactoring
- **Build Success**: PyPI packages build successfully
- **Import Performance**: No significant slowdown
- **Backward Compatibility**: Existing functionality preserved

## 🚧 Risks & Dependencies

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|---------|------------|
| Breaking imports during refactor | Medium | High | Step-by-step approach, comprehensive testing |
| PyPI packaging breaks | Low | High | Test packaging at each step |
| Performance regression | Low | Medium | Monitor import times, profile if needed |
| Team confusion during transition | Medium | Low | Clear documentation, communication |

### Dependencies
- **Epic 2 (Test Coverage)**: Need good tests before refactoring
- **Clean git state**: No conflicts during refactoring
- **Stable CI**: To validate changes don't break anything

## 📋 Implementation Checklist

### Day 8: Structure and Naming
- [ ] **Morning (4h)**: Rename and reorganize
  - [ ] Rename mcp_shared_lib → shared
  - [ ] Create new directory structure
  - [ ] Move files to logical locations
  - [ ] Update basic imports

- [ ] **Afternoon (4h)**: Model consolidation
  - [ ] Consolidate git models into single file
  - [ ] Consolidate analysis models into single file
  - [ ] Update imports throughout codebase
  - [ ] Test imports and basic functionality

### Day 9: Git Module and Cleanup
- [ ] **Morning (4h)**: Git module organization
  - [ ] Organize git-related code under shared/git/
  - [ ] Move git config from general config
  - [ ] Update all git-related imports
  - [ ] Test git functionality

- [ ] **Afternoon (4h)**: Remove dead code
  - [ ] Remove BaseMCPTool and unused abstractions
  - [ ] Clean up test_utils
  - [ ] Remove unused imports and functions
  - [ ] Test for any broken dependencies

### Day 10: Package-Specific and Final Polish
- [ ] **Morning (4h)**: Move package-specific code
  - [ ] Move GitAnalyzerSettings to analyzer package
  - [ ] Clean up shared configuration
  - [ ] Update package-specific imports
  - [ ] Test configuration loading

- [ ] **Afternoon (4h)**: Final validation
  - [ ] Comprehensive testing of refactored code
  - [ ] PyPI packaging validation
  - [ ] End-to-end testing of both servers
  - [ ] Documentation updates

### Quality Gates
- **End of Day 8**: Basic structure works, imports resolve
- **End of Day 9**: Git module organized, dead code removed
- **End of Day 10**: All functionality preserved, packaging works

## 📝 Before/After Examples

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
from mcp_local_repo_analyzer.config import GitAnalyzerSettings  # Moved
from shared.mcp.server import run_server
```

## 📝 Notes
- **Safety first**: Comprehensive tests before any refactoring
- **Step by step**: Make changes incrementally, test at each step
- **Clear communication**: Document changes and rationale
- **Future-focused**: Structure should support future growth
- **Pragmatic approach**: Don't over-engineer, focus on real improvements

---

**Next Epic**: [Epic 5: Security Enhancements](./epic-5-security.md)

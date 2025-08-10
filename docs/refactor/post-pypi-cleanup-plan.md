# Post-PyPI Publishing Cleanup Plan - v0.2.0 Consolidation

## Executive Summary
After successfully publishing `mcp-local-repo-analyzer` and `mcp-pr-recommender` to PyPI as v0.1.0, we're consolidating the multi-repository structure into a single `mcp_auto_pr` repository for improved maintainability and simplified publishing workflow.

## Current State Analysis

### ✅ **Good News:**
- Both packages successfully published on PyPI as v0.1.0
- No duplicated mcp_shared_lib code in current codebase
- Proper dependency management via GitHub dependencies
- Consistent versioning across all components

### ⚠️ **Issues to Address:**
1. **Multiple repository complexity** - 4 separate repos to maintain
2. **Conflicting pre-commit configurations** - 4 different `.pre-commit-config.yaml` files
3. **Uncommitted changes** across all repositories
4. **CI/CD pipeline failures** in mcp_auto_pr
5. **Complex cross-repository dependencies**
6. **Critical test coverage gaps** - Current coverage is very low

## Test Coverage Analysis

### **Current Coverage Status:**
- **mcp_local_repo_analyzer**: 15.65% coverage (1243/1497 lines uncovered)
- **mcp_pr_recommender**: 0.00% coverage (1194/1194 lines uncovered)
- **mcp_shared_lib**: 13.22% coverage (1985/2361 lines uncovered)

### **Critical Coverage Gaps:**
1. **CLI modules** - 0% coverage across all packages
2. **Main server modules** - 0-25% coverage
3. **Tool implementations** - 0% coverage
4. **Service layer** - 0-30% coverage
5. **Transport layer** - 0% coverage

### **90% Coverage Targets:**
- **Core functionality**: 90%+ coverage for all major modules
- **CLI interfaces**: 90%+ coverage for user-facing commands
- **Service layer**: 90%+ coverage for business logic
- **Tool implementations**: 90%+ coverage for MCP tools
- **Model validation**: 90%+ coverage for data models

## Consolidation Strategy

### **Decision: Single Repository Approach**
**Rationale:**
- Single owner (no need for granular access control)
- Natural integration between MCP servers
- Simplified maintenance and CI/CD
- Easier dependency management
- Better development experience

### **New Monorepo Structure (Recommended):**
```
mcp_auto_pr/
├── src/                              # All source code in single src directory
│   ├── mcp_shared_lib/               # Shared library (internal use only)
│   │   ├── __init__.py
│   │   ├── config/                   # Configuration management
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── git_analyzer.py
│   │   ├── models/                   # Shared data models
│   │   │   ├── __init__.py
│   │   │   ├── analysis/
│   │   │   ├── base/
│   │   │   └── git/
│   │   ├── services/                 # Shared services
│   │   │   ├── __init__.py
│   │   │   └── git/
│   │   ├── transports/               # MCP transport implementations
│   │   │   ├── __init__.py
│   │   │   ├── stdio.py
│   │   │   ├── http.py
│   │   │   ├── websocket.py
│   │   │   └── sse.py
│   │   ├── utils/                    # Shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── file_utils.py
│   │   │   ├── git_utils.py
│   │   │   └── logging_utils.py
│   │   └── test_utils/               # Test factories and utilities
│   │       └── factories/
│   ├── mcp_local_repo_analyzer/      # Git analysis MCP server
│   │   ├── __init__.py
│   │   ├── __main__.py              # Entry point for python -m
│   │   ├── cli.py                   # CLI interface
│   │   ├── main.py                  # Server initialization
│   │   ├── services/                # Package-specific services
│   │   │   └── git/
│   │   │       ├── change_detector.py
│   │   │       ├── diff_analyzer.py
│   │   │       └── status_tracker.py
│   │   └── tools/                   # MCP tool implementations
│   │       ├── __init__.py
│   │       ├── staging_area.py
│   │       ├── summary.py
│   │       ├── unpushed_commits.py
│   │       └── working_directory.py
│   └── mcp_pr_recommender/          # AI-powered PR recommender
│       ├── __init__.py
│       ├── __main__.py              # Entry point for python -m
│       ├── cli.py                   # CLI interface
│       ├── main.py                  # Server initialization
│       ├── config.py                # Package-specific config
│       ├── prompts.py               # LLM prompts
│       ├── models/                  # Package-specific models
│       │   └── pr/
│       │       └── recommendations.py
│       ├── services/                # Package-specific services
│       │   ├── atomicity_validator.py
│       │   ├── grouping_engine.py
│       │   └── semantic_analyzer.py
│       └── tools/                   # MCP tool implementations
│           ├── __init__.py
│           ├── pr_recommender_tool.py
│           ├── feasibility_analyzer_tool.py
│           ├── strategy_manager_tool.py
│           └── validator_tool.py
├── tests/                           # Unified test structure
│   ├── __init__.py
│   ├── conftest.py                  # Shared pytest configuration
│   ├── fixtures/                    # Shared test fixtures
│   │   ├── sample_repos/
│   │   ├── mock_configs/
│   │   └── expected_results/
│   ├── unit/                        # Unit tests organized by package
│   │   ├── test_shared_lib/
│   │   │   ├── test_models/
│   │   │   ├── test_services/
│   │   │   ├── test_transports/
│   │   │   └── test_utils/
│   │   ├── test_local_repo_analyzer/
│   │   │   ├── test_cli.py
│   │   │   ├── test_services/
│   │   │   └── test_tools/
│   │   └── test_pr_recommender/
│   │       ├── test_cli.py
│   │       ├── test_services/
│   │       └── test_tools/
│   ├── integration/                 # Integration tests
│   │   ├── test_mcp_servers/       # Server integration tests
│   │   │   ├── test_analyzer_server.py
│   │   │   └── test_recommender_server.py
│   │   ├── test_cross_package/     # Cross-package tests
│   │   │   └── test_analyzer_to_recommender.py
│   │   └── test_end_to_end/        # Complete workflow tests
│   │       ├── test_full_pr_workflow.py
│   │       └── test_docker_deployment.py
│   └── performance/                # Performance benchmarks
│       ├── test_large_repos.py
│       └── test_concurrent_operations.py
├── docker/                          # Docker configurations
│   ├── analyzer/
│   │   └── Dockerfile
│   ├── recommender/
│   │   └── Dockerfile
│   └── dev/
│       └── Dockerfile.dev          # Development container
├── docs/                           # Documentation
│   ├── api/                        # API documentation
│   │   ├── analyzer.md
│   │   └── recommender.md
│   ├── architecture/               # Architecture docs
│   │   ├── overview.md
│   │   └── decisions/             # ADRs
│   ├── guides/                     # User guides
│   │   ├── quickstart.md
│   │   ├── installation.md
│   │   └── troubleshooting.md
│   └── development/                # Developer docs
│       ├── contributing.md
│       ├── testing.md
│       └── releasing.md
├── scripts/                        # Utility scripts
│   ├── setup/                      # Setup scripts
│   │   ├── install.sh
│   │   └── dev-setup.sh
│   ├── ci/                         # CI/CD scripts
│   │   ├── test.sh
│   │   └── publish.sh
│   └── utils/                      # Utility scripts
│       ├── health-check.sh
│       └── cleanup.sh
├── .github/                        # GitHub configuration
│   ├── workflows/                  # GitHub Actions
│   │   ├── ci.yml                 # Main CI pipeline
│   │   ├── release.yml            # Release workflow
│   │   ├── docker.yml             # Docker build & publish
│   │   └── security.yml           # Security scanning
│   ├── ISSUE_TEMPLATE/            # Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml             # Dependency updates
├── config/                         # Configuration files
│   ├── default.yaml               # Default configuration
│   ├── development.yaml           # Development config
│   └── production.yaml            # Production config
├── examples/                       # Usage examples
│   ├── basic_usage/
│   ├── advanced_workflows/
│   └── integration_examples/
├── .devcontainer/                  # VS Code dev containers
│   ├── devcontainer.json
│   └── Dockerfile
├── pyproject.toml                  # Single unified pyproject.toml
├── poetry.lock                     # Dependency lock file
├── Makefile                        # Build automation
├── docker-compose.yml              # Production deployment
├── docker-compose.dev.yml          # Development deployment
├── .pre-commit-config.yaml         # Pre-commit hooks
├── .gitignore                      # Git ignore rules
├── .dockerignore                   # Docker ignore rules
├── LICENSE                         # MIT License
├── README.md                       # Main documentation
├── CHANGELOG.md                    # Version history
├── CONTRIBUTING.md                 # Contribution guidelines
└── SECURITY.md                     # Security policy
```

### **Benefits of This Monorepo Structure:**

#### **Development Benefits:**
- **Single source of truth** - All code in one place
- **Atomic changes** - Changes across packages in single commit
- **Shared tooling** - One set of linters, formatters, CI/CD
- **Consistent standards** - Same coding standards across all packages
- **Simplified imports** - Direct imports between packages during development

#### **Testing Benefits:**
- **Unified test suite** - Run all tests with single command
- **Cross-package testing** - Easy to test interactions
- **Shared fixtures** - Reuse test data and mocks
- **Better coverage** - See coverage across entire codebase

#### **Publishing Benefits:**
- **Synchronized releases** - Version all packages together
- **Single build process** - One command builds all packages
- **Consistent metadata** - Same author, license, etc.
- **Selective publishing** - Can still publish packages independently

#### **Maintenance Benefits:**
- **Single dependency update** - Update dependencies once
- **One CI/CD pipeline** - Maintain single workflow
- **Unified documentation** - All docs in one place
- **Easier refactoring** - Move code between packages easily

### **Migration Strategy from Current Structure:**

#### **Step 1: Prepare Current Repos**
```bash
# Clean up uncommitted changes in each repo
cd mcp_local_repo_analyzer && git stash
cd mcp_pr_recommender && git stash
cd mcp_shared_lib && git stash
```

#### **Step 2: Create New Structure**
```bash
# In mcp_auto_pr directory
mkdir -p src/{mcp_shared_lib,mcp_local_repo_analyzer,mcp_pr_recommender}
mkdir -p tests/{unit,integration,performance,fixtures}
mkdir -p docker/{analyzer,recommender,dev}
mkdir -p docs/{api,architecture,guides,development}
mkdir -p scripts/{setup,ci,utils}
mkdir -p config examples .devcontainer
```

#### **Step 3: Move Source Code**
```bash
# Move shared library
cp -r ../mcp_shared_lib/src/mcp_shared_lib/* src/mcp_shared_lib/

# Move analyzer (excluding duplicated shared lib)
cp -r ../mcp_local_repo_analyzer/src/mcp_local_repo_analyzer/* src/mcp_local_repo_analyzer/

# Move recommender (excluding duplicated shared lib)
cp -r ../mcp_pr_recommender/src/mcp_pr_recommender/* src/mcp_pr_recommender/
```

#### **Step 4: Consolidate Tests**
```bash
# Move and organize tests
cp -r ../mcp_shared_lib/tests/* tests/unit/test_shared_lib/
cp -r ../mcp_local_repo_analyzer/tests/* tests/unit/test_local_repo_analyzer/
cp -r ../mcp_pr_recommender/tests/* tests/unit/test_pr_recommender/

# Merge conftest.py files
cat ../mcp_*/tests/conftest.py > tests/conftest.py
```

#### **Step 5: Create Unified pyproject.toml**
The unified `pyproject.toml` will define all packages:

```toml
[tool.poetry]
name = "mcp-auto-pr"
version = "0.2.0"
description = "Monorepo for MCP-based PR automation tools"
authors = ["Manav Gupta <manavg@gmail.com>"]
packages = [
    {include = "mcp_shared_lib", from = "src"},
    {include = "mcp_local_repo_analyzer", from = "src"},
    {include = "mcp_pr_recommender", from = "src"}
]

# Publishing configuration for individual packages
[[tool.poetry.packages]]
name = "mcp-local-repo-analyzer"
include = ["mcp_local_repo_analyzer", "mcp_shared_lib"]
from = "src"

[[tool.poetry.packages]]
name = "mcp-pr-recommender"
include = ["mcp_pr_recommender", "mcp_shared_lib"]
from = "src"
```

### **Publishing Strategy:**
- **Single pyproject.toml** with multiple packages defined
- **Keep separate PyPI packages** for backward compatibility
- **Single GitHub workflow** publishes both packages
- **Synchronized versioning** - Both packages version together
- **Common practice** - Many projects publish multiple packages from one repo

### **Single pyproject.toml Approach:**
The consolidated repository will use a single `pyproject.toml` file that defines all three packages:
- **mcp-local-repo-analyzer** - Git repository analysis server
- **mcp-pr-recommender** - PR recommendation server  
- **mcp-shared-lib** - Shared library for both servers

This approach:
- **Simplifies dependency management** - All dependencies in one place
- **Ensures version consistency** - All packages version together
- **Reduces configuration complexity** - Single build configuration
- **Maintains separate PyPI packages** - Each package publishes independently
- **Enables unified development** - Single development environment

### **Unified Testing Approach:**
The consolidated repository will use a single `tests/` directory with organized test structure:
- **tests/conftest.py** - Consolidated test configuration and fixtures
- **tests/unit/** - Unit tests organized by package
  - `test_local_repo_analyzer/` - Local repo analyzer unit tests
  - `test_pr_recommender/` - PR recommender unit tests  
  - `test_shared_lib/` - Shared library unit tests
- **tests/integration/** - Integration and end-to-end tests
  - `test_mcp_servers/` - MCP server integration tests
  - `test_cross_package/` - Cross-package dependency tests
  - `test_end_to_end/` - Complete workflow tests

This approach:
- **Consolidates test configuration** - Single conftest.py for all fixtures
- **Organizes tests logically** - Unit vs integration separation
- **Enables cross-package testing** - Easy testing of package interactions
- **Simplifies test discovery** - Clear test organization
- **Reduces duplication** - Shared fixtures and utilities

## v0.2.0 Release Plan

### **Version Strategy:**
- **Current:** v0.1.0 (published on PyPI)
- **Target:** v0.2.0 (consolidated structure)
- **Breaking Changes:** None (maintains backward compatibility)

### **Release Highlights:**
- Repository consolidation for improved maintainability
- Unified CI/CD pipeline
- Simplified development workflow
- Enhanced testing and linting
- Updated documentation
- **90% test coverage** for all major modules

## Comprehensive Checklist

### Phase 1: Repository Consolidation (Day 1-2)

#### Task 1: Create New Repository Structure
- [ ] **1.1** Create new directory structure in mcp_auto_pr
  - [ ] Move mcp_local_repo_analyzer to `mcp_auto_pr/mcp_local_repo_analyzer/`
  - [ ] Move mcp_pr_recommender to `mcp_auto_pr/mcp_pr_recommender/`
  - [ ] Move mcp_shared_lib to `mcp_auto_pr/mcp_shared_lib/`
  - [ ] Remove individual pyproject.toml files from each package
  - [ ] Create single pyproject.toml in root with all packages defined
- [ ] **1.2** Create unified tests structure
  - [ ] Create `tests/` directory in root
  - [ ] Move all test files from individual packages to `tests/unit/`
  - [ ] Create `tests/integration/` for cross-package tests
  - [ ] Consolidate all conftest.py files into single `tests/conftest.py`
  - [ ] Organize tests by package: `test_local_repo_analyzer/`, `test_pr_recommender/`, `test_shared_lib/`

#### Task 2: Update Package Configurations
- [ ] **2.1** Create unified pyproject.toml
  - [ ] Define all three packages in single pyproject.toml
  - [ ] Configure package discovery for all src/ directories
  - [ ] Set up dependencies between packages
  - [ ] Configure build system for multiple packages
- [ ] **2.2** Update package imports and references
  - [ ] Update import paths for new structure
  - [ ] Update relative imports between packages
  - [ ] Verify all imports work correctly

#### Task 3: Consolidate Development Tools
- [ ] **3.1** Create unified pre-commit configuration
  - [ ] Merge all 4 .pre-commit-config.yaml files
  - [ ] Standardize linting rules across all packages
  - [ ] Update pre-commit hooks for new structure
- [ ] **3.2** Update Makefile for new structure
  - [ ] Update paths in Makefile
  - [ ] Add new targets for consolidated workflow
  - [ ] Test all make targets

#### Task 4: Update VSCode Workspace
- [ ] **4.1** Update workspace configuration
  - [ ] Modify mcp_workspace.code-workspace
  - [ ] Update folder paths
  - [ ] Update Python analysis paths
  - [ ] Test workspace functionality

### Phase 2: CI/CD and Testing (Day 3-4)

#### Task 5: Consolidate GitHub Workflows
- [ ] **5.1** Create unified CI workflow
  - [ ] Merge workflows from all repos
  - [ ] Update paths for new structure
  - [ ] Add multi-package testing
  - [ ] Add publishing workflow for both packages
  - [ ] **Add Docker image publishing workflow**
    - [ ] Build Docker images for both MCP servers
    - [ ] Push to GitHub Container Registry (ghcr.io)
    - [ ] Tag images with version numbers
    - [ ] Add Docker image security scanning
- [ ] **5.2** Update Docker configurations
  - [ ] Update docker-compose.yml for new paths
  - [ ] Update Dockerfile paths
  - [ ] Test Docker builds
  - [ ] **Add Docker image publishing configuration**
    - [ ] Configure GitHub Container Registry authentication
    - [ ] Set up Docker image tagging strategy
    - [ ] Add multi-platform Docker builds (linux/amd64, linux/arm64)
    - [ ] Configure Docker image labels and metadata

#### Task 6: Comprehensive Testing
- [ ] **6.1** Run all test suites
  - [ ] `make test-all` - Test all packages
  - [ ] `make test-shared` - Test shared library
  - [ ] `make test-analyzer` - Test local repo analyzer
  - [ ] `make test-recommender` - Test PR recommender
  - [ ] `make test-integration` - Test integration scenarios
- [ ] **6.2** Test linting and formatting
  - [ ] `make lint-all` - Lint all packages
  - [ ] `make format-all` - Format all code
  - [ ] Run pre-commit hooks on all files

#### Task 7: Test Publishing Workflow
- [ ] **7.1** Test package building
  - [ ] `make build-all` - Build all packages
  - [ ] Verify dist/ directories contain correct packages
  - [ ] Test package installation in clean environment
- [ ] **7.2** Test PyPI publishing (dry run)
  - [ ] Test publishing workflow without uploading
  - [ ] Verify package metadata
  - [ ] Test package installation from test PyPI

### Phase 3: Test Coverage Implementation (Day 5-7)

#### Task 8: Implement 90% Test Coverage
- [ ] **8.1** Unit Tests (Target: 90%+)
  - [ ] **test_local_repo_analyzer/** - All local repo analyzer unit tests
    - [ ] Test CLI modules (0% → 90%+)
    - [ ] Test main server modules (25% → 90%+)
    - [ ] Test service layer (30-69% → 90%+)
    - [ ] Test tool implementations (0% → 90%+)
  - [ ] **test_pr_recommender/** - All PR recommender unit tests
    - [ ] Test CLI modules (0% → 90%+)
    - [ ] Test main server modules (0% → 90%+)
    - [ ] Test service layer (0% → 90%+)
    - [ ] Test tool implementations (0% → 90%+)
  - [ ] **test_shared_lib/** - All shared library unit tests
    - [ ] Test git utilities (4-15% → 90%+)
    - [ ] Test transport modules (0% → 90%+)
    - [ ] Test model validation (50-85% → 90%+)
    - [ ] Test utility functions (50-79% → 90%+)

- [ ] **8.2** Integration Tests (Target: 90%+)
  - [ ] **test_mcp_servers/** - MCP server integration tests
    - [ ] Test server startup and shutdown
    - [ ] Test tool registration and execution
    - [ ] Test error handling and recovery
  - [ ] **test_cross_package/** - Cross-package dependency tests
    - [ ] Test shared library usage across packages
    - [ ] Test import and dependency resolution
    - [ ] Test configuration sharing
  - [ ] **test_end_to_end/** - End-to-end workflow tests
    - [ ] Test complete MCP workflows
    - [ ] Test Docker deployment scenarios
    - [ ] Test PyPI package installation

#### Task 9: Integration Testing
- [ ] **9.1** End-to-End Testing
  - [ ] Test complete MCP server startup
  - [ ] Test tool registration and execution
  - [ ] Test cross-package dependencies
  - [ ] Test error propagation between layers
- [ ] **9.2** Performance Testing
  - [ ] Test with large repositories
  - [ ] Test concurrent operations
  - [ ] Test memory usage under load
  - [ ] Test response times for all tools

#### Task 10: Test Infrastructure
- [ ] **10.1** Test Utilities and Factories
  - [ ] Complete test_utils/factories coverage (0% → 90%+)
  - [ ] Add comprehensive test fixtures
  - [ ] Add property-based testing with Hypothesis
  - [ ] Add performance benchmarks
- [ ] **10.2** Test Configuration
  - [ ] Test all configuration loading scenarios
  - [ ] Test environment variable handling
  - [ ] Test validation and error cases
  - [ ] Test configuration merging

### Phase 4: Documentation and Cleanup (Day 8)

#### Task 11: Update Documentation
- [ ] **11.1** Update main README
  - [ ] Document new repository structure
  - [ ] Update installation instructions
  - [ ] Update development setup
  - [ ] Add troubleshooting section
- [ ] **11.2** Update package documentation
  - [ ] Update individual package READMEs
  - [ ] Update API documentation
  - [ ] Update examples and tutorials

#### Task 12: Create v0.2.0 CHANGELOG
- [ ] **12.1** Create comprehensive CHANGELOG
  - [ ] Document repository consolidation
  - [ ] List all improvements and fixes
  - [ ] Document breaking changes (if any)
  - [ ] Add upgrade instructions
- [ ] **12.2** Update version numbers
  - [ ] Update all pyproject.toml files to v0.2.0
  - [ ] Update CHANGELOG.md files
  - [ ] Create git tags for v0.2.0

#### Task 13: Final Verification
- [ ] **13.1** Complete system test
  - [ ] Test workspace setup from scratch
  - [ ] Test all MCP servers start correctly
  - [ ] Test Docker deployment
  - [ ] Test PyPI package installation
- [ ] **13.2** Clean up old repositories
  - [ ] Archive old repositories (don't delete yet)
  - [ ] Update GitHub repository descriptions
  - [ ] Add deprecation notices to old repos

### Phase 5: Release and Deployment (Day 9)

#### Task 14: Publish v0.2.0
- [ ] **14.1** Publish to PyPI
  - [ ] Publish mcp-local-repo-analyzer v0.2.0
  - [ ] Publish mcp-pr-recommender v0.2.0
  - [ ] Verify packages are available on PyPI
- [ ] **14.2** Publish Docker Images
  - [ ] Build and push mcp-local-repo-analyzer:v0.2.0 to ghcr.io
  - [ ] Build and push mcp-pr-recommender:v0.2.0 to ghcr.io
  - [ ] Update latest tags for both images
  - [ ] Verify Docker images are available and functional
- [ ] **14.3** Create GitHub release
  - [ ] Create release notes
  - [ ] Tag release in git
  - [ ] Update GitHub repository

#### Task 15: Post-Release Tasks
- [ ] **15.1** Update documentation
  - [ ] Update PyPI package descriptions
  - [ ] Update GitHub repository README
  - [ ] Update any external references
- [ ] **15.2** Monitor and support
  - [ ] Monitor for any issues
  - [ ] Respond to user feedback
  - [ ] Plan next release

## Testing and Linting Commands

### **Testing Commands (from Makefile):**
```bash
# Test all packages
make test-all

# Test by type
make test-unit
make test-integration

# Test individual packages
make test-local-repo-analyzer
make test-pr-recommender
make test-shared-lib

# Test integration scenarios
make test-mcp-servers
make test-cross-package
make test-end-to-end

# Test workspace setup
make test-setup

# Build all packages
make build-all

# Install all packages in development mode
make install-dev
```

### **Coverage Commands:**
```bash
# Generate coverage reports
poetry run pytest --cov=src --cov-report=term-missing --cov-report=html

# Check coverage thresholds
poetry run pytest --cov=src --cov-fail-under=90

# Generate coverage badges
poetry run coverage-badge -o coverage.svg
```

### **Linting Commands (from Makefile):**
```bash
# Lint all packages
make lint-all

# Format all code
make format-all

# Run pre-commit hooks
pre-commit run --all-files
```

### **Service Testing:**
```bash
# Check server entry points
make check-servers

# Start individual servers
make serve-analyzer
make serve-recommender

# Start all servers
make serve-all

# Stop servers
make stop-servers
```

## Docker Publishing Workflow

### **Docker Image Publishing Strategy:**
- **GitHub Container Registry (ghcr.io)** for Docker image hosting
- **Multi-platform builds** (linux/amd64, linux/arm64) for compatibility
- **Versioned tags** matching PyPI package versions
- **Latest tags** for development and testing
- **Security scanning** with Trivy vulnerability scanner

### **Docker Images to Publish:**
1. **mcp-local-repo-analyzer** - Git repository analysis server
2. **mcp-pr-recommender** - PR recommendation server
3. **mcp-auto-pr** - Combined development image (optional)

### **Docker Publishing Commands:**
```bash
# Build and publish Docker images
make docker-build-all
make docker-push-all

# Build individual images
make docker-build-analyzer
make docker-build-recommender

# Push to GitHub Container Registry
make docker-push-analyzer
make docker-push-recommender

# Test Docker images locally
make docker-test-analyzer
make docker-test-recommender
```

### **Docker Image Tags:**
- **Versioned**: `ghcr.io/manavgup/mcp-local-repo-analyzer:v0.2.0`
- **Latest**: `ghcr.io/manavgup/mcp-local-repo-analyzer:latest`
- **Development**: `ghcr.io/manavgup/mcp-local-repo-analyzer:dev`

### **Docker Security:**
- [ ] **Vulnerability scanning** with Trivy
- [ ] **SBOM generation** for compliance
- [ ] **Image signing** with cosign (optional)
- [ ] **Multi-stage builds** for smaller images
- [ ] **Non-root user** for security

## Test Coverage Requirements

### **Module-Specific Coverage Targets:**

#### **mcp_local_repo_analyzer (Current: 15.65% → Target: 90%+)**
- [ ] **cli.py** (0% → 90%+): CLI argument parsing, error handling
- [ ] **main.py** (25% → 90%+): Server initialization, service registration
- [ ] **change_detector.py** (30% → 90%+): Git change detection logic
- [ ] **diff_analyzer.py** (51% → 90%+): Diff analysis and categorization
- [ ] **status_tracker.py** (69% → 90%+): Git status tracking
- [ ] **staging_area.py** (0% → 90%+): Staging area tool implementation
- [ ] **summary.py** (0% → 90%+): Summary generation tool
- [ ] **unpushed_commits.py** (0% → 90%+): Unpushed commits tool
- [ ] **working_directory.py** (0% → 90%+): Working directory tool

#### **mcp_pr_recommender (Current: 0% → Target: 90%+)**
- [ ] **cli.py** (0% → 90%+): CLI interface and argument handling
- [ ] **main.py** (0% → 90%+): Server setup and tool registration
- [ ] **config.py** (0% → 90%+): Configuration management
- [ ] **atomicity_validator.py** (0% → 90%+): PR atomicity validation
- [ ] **grouping_engine.py** (0% → 90%+): File grouping algorithms
- [ ] **semantic_analyzer.py** (0% → 90%+): Semantic analysis logic
- [ ] **pr_recommender_tool.py** (0% → 90%+): Main PR recommendation tool
- [ ] **feasibility_analyzer_tool.py** (0% → 90%+): Feasibility analysis
- [ ] **validator_tool.py** (0% → 90%+): Validation tool implementation

#### **mcp_shared_lib (Current: 13.22% → Target: 90%+)**
- [ ] **git_client.py** (4% → 90%+): Git command execution and parsing
- [ ] **git_utils.py** (15% → 90%+): Git utility functions
- [ ] **file_utils.py** (50% → 90%+): File system utilities
- [ ] **logging_utils.py** (79% → 90%+): Logging configuration
- [ ] **All transport modules** (0% → 90%+): HTTP, SSE, WebSocket, stdio
- [ ] **All model validation** (50-85% → 90%+): Pydantic models
- [ ] **All test utilities** (0% → 90%+): Test factories and fixtures

### **Test Categories Required:**

#### **Unit Tests (90%+ coverage)**
- [ ] **Function-level testing** for all public APIs
- [ ] **Edge case testing** for error conditions
- [ ] **Mock testing** for external dependencies
- [ ] **Property-based testing** with Hypothesis

#### **Integration Tests (90%+ coverage)**
- [ ] **Service integration** testing
- [ ] **Tool registration** and execution
- [ ] **Cross-package dependency** testing
- [ ] **Error propagation** testing

#### **End-to-End Tests (90%+ coverage)**
- [ ] **Complete server startup** and shutdown
- [ ] **Tool execution** workflows
- [ ] **Configuration loading** scenarios
- [ ] **Error handling** and recovery

#### **Performance Tests**
- [ ] **Load testing** with large repositories
- [ ] **Memory usage** monitoring
- [ ] **Response time** benchmarking
- [ ] **Concurrent operation** testing

## Risk Mitigation

### **Backup Strategy:**
- [ ] Create git branches for each old repository
- [ ] Archive old repositories before deletion
- [ ] Keep old repository URLs for reference

### **Rollback Plan:**
- [ ] Maintain ability to revert to multi-repo structure
- [ ] Keep old CI/CD configurations as backup
- [ ] Document rollback procedures

### **Testing Strategy:**
- [ ] Test each change in isolation
- [ ] Use feature branches for major changes
- [ ] Test in clean environment before release
- [ ] **Continuous coverage monitoring** in CI/CD

## Success Criteria

### **Technical Success:**
- [ ] All tests pass in consolidated repository
- [ ] **90%+ test coverage** for all major modules
- [ ] Both packages publish successfully to PyPI
- [ ] **Docker images publish successfully to GitHub Container Registry**
- [ ] Docker builds work with new structure
- [ ] VSCode workspace functions correctly
- [ ] All linting and formatting passes

### **User Experience Success:**
- [ ] Installation instructions work for new structure
- [ ] No breaking changes for existing users
- [ ] Documentation is clear and complete
- [ ] Development workflow is simplified

### **Maintenance Success:**
- [ ] Single CI/CD pipeline works correctly
- [ ] Pre-commit hooks work across all packages
- [ ] Version management is simplified
- [ ] Dependency management is streamlined
- [ ] **Test coverage is maintained** at 90%+

## Timeline

- **Day 1-2:** Repository consolidation and configuration updates
- **Day 3-4:** CI/CD consolidation and comprehensive testing
- **Day 5-7:** **Test coverage implementation (90% target)**
- **Day 8:** Documentation updates and final verification
- **Day 9:** Release and deployment

## Command Reference

### **Consolidation Commands:**
```bash
# Create new structure
mv ../mcp_local_repo_analyzer ./
mv ../mcp_pr_recommender ./
mv ../mcp_shared_lib ./

# Remove individual pyproject.toml files
rm mcp_local_repo_analyzer/pyproject.toml
rm mcp_pr_recommender/pyproject.toml
rm mcp_shared_lib/pyproject.toml

# Create unified tests structure
mkdir -p tests/unit tests/integration
mkdir -p tests/unit/test_local_repo_analyzer
mkdir -p tests/unit/test_pr_recommender
mkdir -p tests/unit/test_shared_lib
mkdir -p tests/integration/test_mcp_servers
mkdir -p tests/integration/test_cross_package
mkdir -p tests/integration/test_end_to_end

# Move test files to unified structure
mv mcp_local_repo_analyzer/tests/* tests/unit/test_local_repo_analyzer/
mv mcp_pr_recommender/tests/* tests/unit/test_pr_recommender/
mv mcp_shared_lib/tests/* tests/unit/test_shared_lib/

# Consolidate conftest.py files
# (Will merge all conftest.py files into tests/conftest.py)

# Create unified pyproject.toml in root
# (Will be created with all packages defined)
```

### **Testing Commands:**
```bash
# Test new structure
make test-all
make lint-all
make format-all

# Test publishing
make build-all
poetry publish --dry-run

# Coverage testing
poetry run pytest --cov=src --cov-report=term-missing --cov-fail-under=90
```

### **Docker Publishing Commands:**
```bash
# Build and publish Docker images
make docker-build-all
make docker-push-all

# Test Docker images
make docker-test-analyzer
make docker-test-recommender

# Security scan Docker images
make docker-scan-analyzer
make docker-scan-recommender
```

### **Git Commands:**
```bash
# Create v0.2.0 tags
git tag -a v0.2.0 -m "Release v0.2.0 - Repository consolidation with 90% test coverage"
git push origin v0.2.0

# Update all packages to v0.2.0
find . -name "pyproject.toml" -exec sed -i 's/version = "0.1.0"/version = "0.2.0"/g' {} \;
```

## Contact & Support
- Primary: Manav Gupta <manavg@gmail.com>
- GitHub Issues: https://github.com/manavgup/mcp_auto_pr/issues
- Documentation: https://github.com/manavgup/mcp_auto_pr/docs

## Additional Improvements for Well-Designed System

### **Phase 6: User Experience & Quick Start (Day 10)**

#### Task 16: Docker Compose Quick Start
- [ ] **16.1** Create comprehensive docker-compose.yml
  - [ ] Add both MCP servers with proper networking
  - [ ] Add health check endpoints for both servers
  - [ ] Add volume mounts for persistent data
  - [ ] Add environment variable configuration
- [ ] **16.2** Create quick start scripts
  - [ ] `quick-start.sh` - One-command setup
  - [ ] `dev-setup.sh` - Development environment setup
  - [ ] `production-setup.sh` - Production deployment

#### Task 17: Usage Examples & Documentation
- [ ] **17.1** Create comprehensive examples
  - [ ] Sample MCP client configurations
  - [ ] Example workflows for each tool
  - [ ] Integration examples with popular IDEs
  - [ ] Troubleshooting guide
- [ ] **17.2** Add API documentation
  - [ ] OpenAPI/Swagger documentation
  - [ ] Tool parameter documentation
  - [ ] Response format examples

### **Phase 7: Security & Compliance (Day 11)**

#### Task 18: Security Enhancements
- [ ] **18.1** Add dependency vulnerability scanning
  - [ ] Integrate Trivy for dependency scanning
  - [ ] Add Snyk for runtime vulnerability detection
  - [ ] Configure automated security alerts
- [ ] **18.2** Add secrets scanning
  - [ ] Configure pre-commit hooks for secrets detection
  - [ ] Add gitleaks for repository scanning
  - [ ] Add environment variable validation
- [ ] **18.3** Add license compliance
  - [ ] Add license checking with `licensecheck`
  - [ ] Generate license attribution files
  - [ ] Verify all dependencies are properly licensed

#### Task 19: Production Security
- [ ] **19.1** Add authentication/authorization
  - [ ] Add API key validation
  - [ ] Add rate limiting per client
  - [ ] Add request logging and audit trails
- [ ] **19.2** Add secure defaults
  - [ ] Non-root Docker containers
  - [ ] Read-only filesystem where possible
  - [ ] Minimal attack surface configuration

### **Phase 8: Monitoring & Observability (Day 12)**

#### Task 20: Structured Logging
- [ ] **20.1** Implement structured logging
  - [ ] JSON log format for all components
  - [ ] Consistent log levels across all packages
  - [ ] Add correlation IDs for request tracing
- [ ] **20.2** Add log aggregation
  - [ ] Configure log shipping to centralized system
  - [ ] Add log rotation and retention policies
  - [ ] Add log level configuration via environment

#### Task 21: Metrics & Monitoring
- [ ] **21.1** Add Prometheus metrics
  - [ ] Request count and duration metrics
  - [ ] Error rate and type metrics
  - [ ] Resource usage metrics (CPU, memory)
- [ ] **21.2** Add health check endpoints
  - [ ] `/health` endpoint for each server
  - [ ] `/ready` endpoint for readiness checks
  - [ ] `/metrics` endpoint for Prometheus scraping

#### Task 22: Distributed Tracing
- [ ] **22.1** Add OpenTelemetry integration
  - [ ] Add trace context propagation
  - [ ] Add span creation for major operations
  - [ ] Configure trace sampling and export
- [ ] **22.2** Add performance monitoring
  - [ ] Add performance benchmarks
  - [ ] Add memory usage monitoring
  - [ ] Add response time tracking

### **Phase 9: Developer Experience (Day 13)**

#### Task 23: Development Containers
- [ ] **23.1** Create VS Code dev containers
  - [ ] `.devcontainer/devcontainer.json` configuration
  - [ ] Pre-configured development environment
  - [ ] All dependencies pre-installed
- [ ] **23.2** Add development tools
  - [ ] Add debugging configuration
  - [ ] Add hot reload for development
  - [ ] Add development-specific logging

#### Task 24: Automated Maintenance
- [ ] **24.1** Configure Dependabot
  - [ ] Automated dependency updates
  - [ ] Security vulnerability alerts
  - [ ] Automated PR creation for updates
- [ ] **24.2** Add contribution guidelines
  - [ ] Create CONTRIBUTING.md
  - [ ] Add code review guidelines
  - [ ] Add testing requirements

### **Phase 10: Production Readiness (Day 14)**

#### Task 25: Graceful Shutdown
- [ ] **25.1** Implement proper signal handling
  - [ ] Handle SIGTERM gracefully
  - [ ] Complete in-flight requests
  - [ ] Clean up resources properly
- [ ] **25.2** Add startup validation
  - [ ] Validate configuration at startup
  - [ ] Check required dependencies
  - [ ] Verify file permissions and access

#### Task 26: Performance & Scalability
- [ ] **26.1** Add connection pooling
  - [ ] Database connection pooling (if applicable)
  - [ ] HTTP client connection pooling
  - [ ] Resource cleanup and reuse
- [ ] **26.2** Add caching
  - [ ] Add result caching for expensive operations
  - [ ] Add configuration caching
  - [ ] Add dependency caching

### **Updated Success Criteria:**

#### **Production Readiness Success:**
- [ ] **Docker Compose quick start** works seamlessly
- [ ] **Health check endpoints** respond correctly
- [ ] **Structured logging** provides useful debugging info
- [ ] **Metrics collection** works for monitoring
- [ ] **Security scanning** passes all checks
- [ ] **Graceful shutdown** handles all scenarios
- [ ] **Rate limiting** prevents abuse
- [ ] **Authentication** works for production use

#### **Developer Experience Success:**
- [ ] **Dev containers** provide consistent environment
- [ ] **Automated dependency updates** work correctly
- [ ] **Contribution guidelines** are clear and followed
- [ ] **Debugging tools** work effectively
- [ ] **Hot reload** speeds up development

### **Updated Timeline:**
- **Day 1-2:** Repository consolidation and configuration updates
- **Day 3-4:** CI/CD consolidation and comprehensive testing
- **Day 5-7:** Test coverage implementation (90% target)
- **Day 8:** Documentation updates and final verification
- **Day 9:** Release and deployment
- **Day 10:** User experience and quick start improvements
- **Day 11:** Security and compliance enhancements
- **Day 12:** Monitoring and observability implementation
- **Day 13:** Developer experience improvements
- **Day 14:** Production readiness and performance optimization

---

**Note:** This plan maintains backward compatibility while significantly improving the development and maintenance experience. The consolidation reduces complexity while preserving the functionality that users depend on. **The 90% test coverage requirement ensures code quality and maintainability for the v0.2.0 release.** The additional phases (10-14) create a production-ready, well-designed system with excellent user and developer experience.
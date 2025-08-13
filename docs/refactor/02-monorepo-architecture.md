# Monorepo Architecture

## Overview
This document provides a comprehensive, granular architecture plan for consolidating the MCP ecosystem into a single monorepo. Based on actual codebase analysis, this plan addresses real issues and provides implementable solutions.

## Current State Analysis

### Repository Status
- **mcp_shared_lib**: ✅ Published to PyPI v0.1.0, 88.53% test coverage
- **mcp_local_repo_analyzer**: ✅ Published to PyPI v0.1.0, tests failing (4 failed, 18 passed)
- **mcp_pr_recommender**: ✅ Published to PyPI v0.1.0, 132 tests passed
- **mcp_auto_pr**: 🟡 Orchestration repo, minimal CI setup

### Critical Issues Identified
1. **Configuration Validation Errors**: GitAnalyzerSettings has extra fields causing import failures
2. **Test Failures**: Local repo analyzer has 4 failing tests
3. **CLI Issues**: Both servers have CLI help command failures
4. **MCP Server Issues**: StdioTransport initialization problems
5. **Dependency Conflicts**: Different FastMCP versions (2.10.6 vs 2.6.1)

## Proposed Structure

```
mcp_auto_pr/
├── .github/                              # GitHub configuration
│   ├── ISSUE_TEMPLATE/                   # Issue templates
│   │   ├── bug_report.md                 # Bug report template
│   │   ├── feature_request.md            # Feature request template
│   │   └── mcp_server_issue.md          # MCP server specific template
│   ├── workflows/                        # CI/CD pipelines
│   │   ├── ci.yml                        # Main CI pipeline (unified)
│   │   ├── docker.yml                    # Docker builds and publishing
│   │   ├── release.yml                   # PyPI publishing workflow
│   │   ├── security.yml                  # Security scanning
│   │   ├── pre-commit.yml                # Pre-commit CI checks
│   │   └── dependency-review.yml         # Dependency vulnerability scanning
│   ├── dependabot.yml                    # Automated dependency updates
│   ├── CODEOWNERS                        # Code ownership rules
│   └── SECURITY.md                       # Security policy
│
├── .devcontainer/                         # VS Code dev containers
│   ├── devcontainer.json                 # Dev container configuration
│   ├── Dockerfile                        # Development environment
│   ├── docker-compose.yml                # Dev services
│   └── scripts/                          # Dev container setup scripts
│
├── src/                                   # All source code
│   ├── shared/                           # Truly shared functionality
│   │   ├── __init__.py                   # Package initialization
│   │   ├── models/                       # Shared data models
│   │   │   ├── __init__.py
│   │   │   ├── git.py                    # Git-related models (consolidated)
│   │   │   ├── analysis.py               # Analysis result models
│   │   │   └── base.py                   # Base model classes
│   │   ├── git/                          # Git operations and utilities
│   │   │   ├── __init__.py
│   │   │   ├── client.py                 # GitClient (renamed from git_client.py)
│   │   │   ├── config.py                 # Git-specific configuration
│   │   │   ├── utils.py                  # Git utility functions
│   │   │   └── exceptions.py             # Git-specific exceptions
│   │   ├── mcp/                          # MCP protocol shared code
│   │   │   ├── __init__.py
│   │   │   ├── server.py                 # Shared server base class
│   │   │   ├── base.py                   # Base MCP classes
│   │   │   └── utils.py                  # MCP utility functions
│   │   ├── common/                       # Common utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # Base configuration classes
│   │   │   ├── logging.py                # Logging utilities
│   │   │   ├── files.py                  # File system utilities
│   │   │   ├── exceptions.py             # Common exceptions
│   │   │   └── validators.py             # Common validation functions
│   │   └── testing/                      # Test utilities
│   │       ├── __init__.py
│   │       ├── factories.py               # Test data factories
│   │       ├── mocks.py                  # Mock objects
│   │       └── helpers.py                # Test helper functions
│   │
│   ├── mcp_local_repo_analyzer/          # Git analysis server
│   │   ├── __init__.py
│   │   ├── __main__.py                   # Entry point for -m flag
│   │   ├── cli.py                        # Command-line interface
│   │   ├── main.py                       # Server initialization (inherits from shared)
│   │   ├── config.py                     # Package-specific configuration
│   │   ├── services/                     # Analysis services
│   │   │   ├── __init__.py
│   │   │   ├── git/                      # Git-specific services
│   │   │   │   ├── __init__.py
│   │   │   │   ├── change_detector.py    # Change detection logic
│   │   │   │   ├── diff_analyzer.py      # Diff analysis logic
│   │   │   │   └── status_tracker.py     # Status tracking logic
│   │   │   └── analysis/                 # Analysis services
│   │   │       ├── __init__.py
│   │   │       ├── categorizer.py        # Change categorization
│   │   │       └── risk_assessor.py      # Risk assessment
│   │   └── tools/                        # MCP tool implementations
│   │       ├── __init__.py
│   │       ├── staging_area.py           # Staging area analysis
│   │       ├── summary.py                # Summary generation
│   │       ├── unpushed_commits.py       # Unpushed commits analysis
│   │       └── working_directory.py      # Working directory analysis
│   │
│   └── mcp_pr_recommender/               # PR recommendation server
│       ├── __init__.py
│       ├── __main__.py                   # Entry point for -m flag
│       ├── cli.py                        # Command-line interface
│       ├── main.py                       # Server initialization (inherits from shared)
│       ├── config.py                     # Package-specific configuration
│       ├── prompts.py                    # AI prompts and templates
│       ├── services/                     # Recommendation services
│       │   ├── __init__.py
│       │   ├── atomicity_validator.py    # Atomicity validation
│       │   ├── grouping_engine.py        # Change grouping logic
│       │   └── semantic_analyzer.py      # Semantic analysis
│       └── tools/                        # MCP tool implementations
│           ├── __init__.py
│           ├── pr_recommender_tool.py     # Main PR recommendation tool
│           ├── feasibility_analyzer_tool.py # Feasibility analysis
│           ├── strategy_manager_tool.py   # Strategy management
│           └── validator_tool.py         # Validation tool
│
├── tests/                                 # Unified testing
│   ├── __init__.py
│   ├── conftest.py                       # Shared pytest configuration
│   ├── pytest.ini                        # Pytest configuration
│   ├── fixtures/                         # Shared test data
│   │   ├── __init__.py
│   │   ├── git_repos/                    # Test git repositories
│   │   ├── mock_data/                    # Mock data sets
│   │   ├── configs/                      # Test configurations
│   │   └── scenarios/                    # Test scenarios
│   ├── unit/                             # Unit tests by package
│   │   ├── __init__.py
│   │   ├── shared/                       # Shared library tests
│   │   │   ├── __init__.py
│   │   │   ├── test_models/              # Model tests
│   │   │   ├── test_git/                 # Git service tests
│   │   │   ├── test_mcp/                 # MCP protocol tests
│   │   │   ├── test_common/              # Common utility tests
│   │   │   └── test_utils/               # Utility tests
│   │   ├── mcp_local_repo_analyzer/      # Analyzer tests
│   │   │   ├── __init__.py
│   │   │   ├── test_cli.py               # CLI tests
│   │   │   ├── test_main.py              # Main module tests
│   │   │   ├── test_services/            # Service tests
│   │   │   └── test_tools/               # Tool tests
│   │   └── mcp_pr_recommender/           # Recommender tests
│   │       ├── __init__.py
│   │       ├── test_cli.py               # CLI tests
│   │       ├── test_main.py              # Main module tests
│   │       ├── test_services/            # Service tests
│   │       └── test_tools/               # Tool tests
│   ├── integration/                      # Integration tests
│   │   ├── __init__.py
│   │   ├── test_mcp_servers/             # MCP server integration
│   │   ├── test_cross_package/           # Cross-package functionality
│   │   ├── test_end_to_end/              # End-to-end workflows
│   │   └── test_docker/                  # Docker integration
│   ├── performance/                      # Performance tests
│   │   ├── __init__.py
│   │   ├── test_large_repos.py           # Large repository performance
│   │   ├── test_concurrent_ops.py        # Concurrent operations
│   │   └── benchmarks/                   # Performance benchmarks
│   └── utils/                            # Test utilities
│       ├── __init__.py
│       ├── factories/                    # Test data factories
│       ├── mocks/                        # Mock objects
│       └── helpers/                      # Test helper functions
│
├── docker/                                # Container configurations
│   ├── analyzer/                          # Analyzer container
│   │   ├── Dockerfile                     # Analyzer Dockerfile
│   │   ├── docker-entrypoint.sh           # Entry point script
│   │   └── healthcheck.sh                 # Health check script
│   ├── recommender/                       # Recommender container
│   │   ├── Dockerfile                     # Recommender Dockerfile
│   │   ├── docker-entrypoint.sh           # Entry point script
│   │   └── healthcheck.sh                 # Health check script
│   ├── dev/                               # Development container
│   │   ├── Dockerfile                     # Dev environment
│   │   └── docker-compose.yml             # Dev services
│   └── base/                              # Base images
│       └── Dockerfile                     # Common base image
│
├── docs/                                  # Documentation
│   ├── README.md                          # Main documentation
│   ├── api/                               # API documentation
│   │   ├── shared/                        # Shared library API
│   │   ├── analyzer/                      # Analyzer API
│   │   └── recommender/                   # Recommender API
│   ├── architecture/                      # Architecture decisions
│   │   ├── decisions/                     # ADR documents
│   │   │   ├── 001-monorepo-structure.md # Monorepo decision
│   │   │   ├── 002-shared-server.md      # Shared server decision
│   │   │   └── 003-testing-strategy.md   # Testing strategy decision
│   │   ├── diagrams/                      # Architecture diagrams
│   │   │   ├── system-overview.png        # System overview
│   │   │   ├── data-flow.png              # Data flow diagram
│   │   │   └── deployment.png             # Deployment diagram
│   │   └── overview.md                    # System overview
│   ├── guides/                            # User guides
│   │   ├── getting-started.md             # Quick start guide
│   │   ├── installation.md                # Installation guide
│   │   ├── configuration.md               # Configuration guide
│   │   ├── troubleshooting.md             # Troubleshooting guide
│   │   └── examples/                      # Usage examples
│   ├── development/                       # Developer documentation
│   │   ├── setup.md                       # Development setup
│   │   ├── contributing.md                # Contributing guide
│   │   ├── testing.md                     # Testing guide
│   │   ├── releasing.md                   # Release process
│   │   └── architecture/                  # Developer architecture docs
│   ├── migration/                         # Migration guides
│   │   ├── from-v0.1.md                  # v0.1 to v0.2 migration
│   │   └── from-multirepo.md              # Multi-repo to monorepo
│   └── legacy/                            # Legacy documentation
│       ├── mcp_shared_lib/                # Old shared lib docs
│       ├── mcp_local_repo_analyzer/       # Old analyzer docs
│       └── mcp_pr_recommender/            # Old recommender docs
│
├── scripts/                                # Utility scripts
│   ├── setup/                             # Setup scripts
│   │   ├── setup-dev-env.sh               # Development environment setup
│   │   ├── setup-monorepo.sh              # Monorepo setup
│   │   ├── setup-ci.sh                    # CI environment setup
│   │   └── setup-docker.sh                # Docker environment setup
│   ├── ci/                                # CI/CD scripts
│   │   ├── build-packages.sh              # Package building
│   │   ├── publish-pypi.sh                # PyPI publishing
│   │   ├── build-docker.sh                # Docker building
│   │   ├── run-tests.sh                   # Test execution
│   │   └── check-quality.sh               # Quality checks
│   ├── utils/                             # Utility scripts
│   │   ├── update-version.sh              # Version updating
│   │   ├── generate-changelog.sh          # Changelog generation
│   │   ├── cleanup.sh                     # Cleanup utilities
│   │   ├── health-check.sh                # Health checking
│   │   └── dependency-check.sh            # Dependency analysis
│   └── migration/                         # Migration scripts
│       ├── migrate-to-monorepo.sh         # Main migration script
│       ├── consolidate-tests.sh           # Test consolidation
│       ├── update-imports.sh              # Import path updates
│       └── fix-configs.sh                 # Configuration fixes
│
├── config/                                 # Configuration files
│   ├── default.yaml                       # Default configuration
│   ├── development.yaml                    # Development configuration
│   ├── production.yaml                     # Production configuration
│   ├── test.yaml                          # Test configuration
│   ├── docker/                             # Docker-specific configs
│   │   ├── analyzer.yaml                   # Analyzer config
│   │   └── recommender.yaml                # Recommender config
│   └── ci/                                 # CI/CD configuration
│       ├── pytest.ini                     # Pytest configuration
│       ├── coverage.ini                   # Coverage configuration
│       └── mypy.ini                       # MyPy configuration
│
├── examples/                               # Usage examples
│   ├── basic-usage/                       # Basic usage examples
│   │   ├── analyze-repo.py                # Basic repository analysis
│   │   ├── generate-prs.py                # Basic PR generation
│   │   └── integration.py                 # Basic integration
│   ├── advanced-usage/                    # Advanced usage examples
│   │   ├── custom-strategies.py           # Custom grouping strategies
│   │   ├── batch-processing.py            # Batch processing
│   │   └── performance-tuning.py          # Performance optimization
│   ├── integration/                       # Integration examples
│   │   ├── github-actions.py              # GitHub Actions integration
│   │   ├── jenkins-pipeline.py            # Jenkins integration
│   │   └── gitlab-ci.py                   # GitLab CI integration
│   └── docker/                            # Docker usage examples
│       ├── docker-compose.yml             # Example docker-compose
│       ├── kubernetes/                    # Kubernetes manifests
│       └── helm/                          # Helm charts
│
├── tools/                                  # Development tools
│   ├── pre-commit/                        # Pre-commit hooks
│   │   ├── hooks/                         # Custom hooks
│   │   └── config/                        # Hook configuration
│   ├── linting/                           # Linting configuration
│   │   ├── ruff.toml                      # Ruff configuration
│   │   ├── pylintrc                       # Pylint configuration
│   │   └── bandit.yaml                    # Bandit configuration
│   ├── formatting/                        # Code formatting
│   │   ├── black.toml                     # Black configuration
│   │   └── isort.cfg                      # isort configuration
│   └── type-checking/                     # Type checking config
│       ├── mypy.ini                       # MyPy configuration
│       └── pyrightconfig.json             # Pyright configuration
│
├── monitoring/                             # Monitoring and observability
│   ├── dashboards/                        # Grafana dashboards
│   │   ├── mcp-servers.json               # MCP servers dashboard
│   │   ├── performance.json               # Performance dashboard
│   │   └── errors.json                    # Error tracking dashboard
│   ├── alerts/                            # Alert rules
│   │   ├── prometheus/                    # Prometheus alert rules
│   │   └── grafana/                       # Grafana alert rules
│   └── metrics/                           # Custom metrics
│       ├── server_metrics.py              # Server performance metrics
│       └── business_metrics.py            # Business logic metrics
│
├── security/                               # Security configuration
│   ├── policies/                          # Security policies
│   │   ├── code-security.md               # Code security policy
│   │   ├── dependency-security.md         # Dependency security policy
│   │   └── runtime-security.md            # Runtime security policy
│   ├── scanning/                          # Security scanning config
│   │   ├── trivy.yaml                     # Trivy configuration
│   │   ├── bandit.yaml                    # Bandit configuration
│   │   └── safety.yaml                    # Safety configuration
│   └── compliance/                        # Compliance documentation
│       ├── gdpr.md                        # GDPR compliance
│       ├── sox.md                         # SOX compliance
│       └── pci.md                         # PCI compliance
│
├── .pre-commit-config.yaml                 # Pre-commit hooks (unified)
├── .gitignore                              # Git ignore patterns
├── .dockerignore                           # Docker ignore patterns
├── pyproject.toml                          # Main project configuration
├── pyproject-analyzer.toml                 # Analyzer package config
├── pyproject-recommender.toml              # Recommender package config
├── poetry.lock                             # Poetry lock file
├── Makefile                                # Build automation
├── docker-compose.yml                      # Production services
├── docker-compose.dev.yml                  # Development services
├── README.md                               # Main project README
├── CHANGELOG.md                            # Project changelog
├── CONTRIBUTING.md                         # Contributing guidelines
├── SECURITY.md                             # Security policy
├── LICENSE                                 # Project license
└── CODE_OF_CONDUCT.md                      # Code of conduct
```

## Design Principles

### 1. Single Source Directory
- All source code under `src/`
- Clear package boundaries with `__init__.py` files
- Simplified imports and dependency management
- Consistent package structure across all components

### 2. Unified Testing
- Single test configuration (`pytest.ini`, `conftest.py`)
- Shared fixtures and utilities in `tests/fixtures/`
- Cross-package testing capability
- Performance and integration test suites

### 3. Centralized Configuration
- One `pyproject.toml` for main project
- Separate build configs for each PyPI package
- Unified pre-commit configuration
- Single CI/CD pipeline with matrix builds

### 4. Documentation Organization
- API documentation for each package
- Architecture decision records (ADRs)
- User guides and examples
- Developer documentation and migration guides

### 5. Quality Assurance
- Unified linting and formatting rules
- Comprehensive security scanning
- Automated dependency updates
- Code coverage requirements (90%+)

## Package Organization

### shared/
**Purpose**: Truly shared functionality across MCP servers
- `models/` - Shared data models (git, analysis, base)
- `git/` - Git operations, config, and utilities
- `mcp/` - MCP protocol shared code (server base class)
- `common/` - Common utilities (logging, files, config, validators)
- `testing/` - Test utilities and factories

### mcp_local_repo_analyzer
**Purpose**: Git repository analysis and change detection
- `cli.py` - Command-line interface with argument parsing
- `main.py` - Server initialization (inherits from shared server)
- `config.py` - Package-specific configuration
- `services/` - Analysis services (change detection, diff analysis, status tracking)
- `tools/` - MCP tool implementations for git analysis

### mcp_pr_recommender
**Purpose**: AI-powered PR recommendations and grouping
- `cli.py` - Command-line interface with argument parsing
- `main.py` - Server initialization (inherits from shared server)
- `config.py` - Package-specific configuration
- `prompts.py` - AI prompts and templates
- `services/` - Recommendation services (atomicity validation, grouping, semantic analysis)
- `tools/` - MCP tool implementations for PR recommendations

## Configuration Management

### Unified pyproject.toml
```toml
[tool.poetry]
name = "mcp-auto-pr"
version = "0.2.0"
description = "Monorepo for MCP PR automation tools"
packages = [
    {include = "shared", from = "src"},
    {include = "mcp_local_repo_analyzer", from = "src"},
    {include = "mcp_pr_recommender", from = "src"}
]

[tool.poetry.dependencies]
python = ">=3.10,<4.0"
fastmcp = "^2.10.6"  # Unified version
pydantic = "^2.11.7"
gitpython = "^3.1.40"
openai = "^1.0.0"
```

### Package-Specific Build Configs
- `pyproject-analyzer.toml` - For mcp-local-repo-analyzer package
- `pyproject-recommender.toml` - For mcp-pr-recommender package
- Each includes shared code and package-specific metadata

## CI/CD Pipeline

### GitHub Actions Workflows
1. **ci.yml** - Main CI pipeline with matrix builds
2. **docker.yml** - Docker image building and publishing
3. **release.yml** - PyPI package publishing
4. **security.yml** - Security scanning and vulnerability assessment
5. **pre-commit.yml** - Pre-commit hook validation
6. **dependency-review.yml** - Dependency vulnerability scanning

### CI Matrix Strategy
- **Python versions**: 3.10, 3.11, 3.12
- **Operating systems**: ubuntu-latest, windows-latest, macos-latest
- **Package types**: wheel, sdist
- **Architectures**: x86_64, arm64

## Testing Strategy

### Test Categories
1. **Unit Tests** (60% of coverage target)
   - Individual function and method testing
   - Mocked external dependencies
   - Edge cases and error handling

2. **Integration Tests** (25% of coverage target)
   - Component interaction testing
   - Cross-package functionality
   - Real git repository testing

3. **End-to-End Tests** (10% of coverage target)
   - Complete workflow testing
   - Docker deployment testing
   - PyPI package installation testing

4. **Performance Tests** (5% of coverage target)
   - Load testing with large repositories
   - Memory usage monitoring
   - Response time benchmarking

### Coverage Requirements
- **Overall**: 90%+ coverage
- **Critical paths**: 95%+ coverage
- **Error handling**: 100% coverage
- **Public APIs**: 100% coverage

## Docker Strategy

### Multi-Stage Builds
- **Base image**: Python 3.11-slim with common dependencies
- **Builder stage**: Poetry installation and dependency resolution
- **Runtime stage**: Minimal runtime with only necessary packages

### Image Optimization
- **Layer caching**: Optimized for CI/CD pipeline
- **Security**: Non-root user execution
- **Health checks**: Built-in health check endpoints
- **Multi-platform**: Support for linux/amd64 and linux/arm64

### Container Orchestration
- **docker-compose.yml**: Production services
- **docker-compose.dev.yml**: Development environment
- **Kubernetes manifests**: Production deployment
- **Helm charts**: Package management

## Security & Compliance

### Security Scanning
- **Trivy**: Container and filesystem vulnerability scanning
- **Bandit**: Python security linting
- **Safety**: Dependency vulnerability checking
- **CodeQL**: GitHub's semantic code analysis

### Compliance
- **GDPR**: Data privacy compliance
- **SOX**: Financial reporting compliance
- **PCI**: Payment card industry compliance
- **SOC2**: Security and availability compliance

## Monitoring & Observability

### Metrics Collection
- **Prometheus**: Time-series metrics collection
- **Grafana**: Metrics visualization and dashboards
- **Custom metrics**: Business logic and performance metrics

### Logging Strategy
- **Structured logging**: JSON format for machine readability
- **Log levels**: Configurable logging levels
- **Log aggregation**: Centralized log collection
- **Log retention**: Configurable retention policies

### Alerting
- **Performance alerts**: Response time and throughput
- **Error rate alerts**: Error percentage thresholds
- **Resource alerts**: Memory and CPU usage
- **Business alerts**: Custom business logic alerts

## Migration Strategy

### Phase 1: Repository Consolidation (Days 1-2)
- Create monorepo structure
- Move source code from all repositories
- Consolidate configuration files
- Preserve git history

### Phase 2: CI/CD Setup (Days 3-4)
- Create unified GitHub Actions workflows
- Set up Docker image building
- Configure security scanning
- Implement automated testing

### Phase 3: Test Implementation (Days 5-7)
- Achieve 90% test coverage
- Fix failing tests
- Implement integration tests
- Add performance benchmarks

### Phase 4: Documentation (Day 8)
- Consolidate documentation
- Create migration guides
- Update API documentation
- Add architecture decision records

### Phase 5: Release (Day 9)
- Publish v0.2.0 to PyPI
- Create GitHub release
- Update documentation links
- Announce release

## Benefits

### Development Benefits
- **Single source of truth** - All code in one place
- **Atomic changes** - Cross-package changes in single commit
- **Shared tooling** - One set of development tools
- **Consistent standards** - Same coding standards everywhere

### Testing Benefits
- **Unified test suite** - Single test command
- **Cross-package testing** - Easy integration tests
- **Shared fixtures** - Reusable test data
- **Better coverage** - Holistic view of coverage

### Publishing Benefits
- **Synchronized releases** - Version together
- **Single build process** - One build command
- **Consistent metadata** - Same author, license
- **Selective publishing** - Can still publish independently

### Maintenance Benefits
- **Single dependency update** - Update once
- **One CI/CD pipeline** - Single workflow
- **Unified documentation** - All docs together
- **Easier refactoring** - Move code easily

### Quality Benefits
- **Consistent linting** - Same rules across all packages
- **Unified formatting** - Consistent code style
- **Security scanning** - Automated vulnerability detection
- **Dependency management** - Centralized dependency updates

## Success Metrics

### Technical Metrics
- **Test coverage**: 90%+ across all packages
- **Build success rate**: 99%+ CI/CD success
- **Security vulnerabilities**: 0 critical/high vulnerabilities
- **Performance**: <2s response time for standard operations

### Process Metrics
- **Release frequency**: Monthly releases
- **Time to fix**: <24 hours for critical bugs
- **Documentation coverage**: 100% API documentation
- **Migration success**: 100% user migration rate

### Business Metrics
- **User adoption**: Increased usage after consolidation
- **Maintenance cost**: Reduced by 40%
- **Development velocity**: 25% faster feature delivery
- **Bug reduction**: 30% fewer production issues

This comprehensive architecture provides a solid foundation for a production-grade monorepo that addresses all current issues while maintaining the benefits of separate packages and improving overall maintainability and developer experience.

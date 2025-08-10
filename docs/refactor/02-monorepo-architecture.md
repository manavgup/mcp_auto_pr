# Monorepo Architecture

## Proposed Structure

```
mcp_auto_pr/
├── src/                              # All source code
│   ├── shared/                       # Truly shared functionality (renamed from mcp_shared_lib)
│   │   ├── models/                   # Shared data models
│   │   │   ├── git.py               # Git-related models (consolidated)
│   │   │   └── analysis.py          # Analysis result models
│   │   ├── git/                     # Git operations and utilities
│   │   │   ├── client.py            # Git client operations
│   │   │   ├── config.py            # Git-specific configuration
│   │   │   └── utils.py             # Git utility functions
│   │   ├── mcp/                     # MCP protocol shared code
│   │   │   ├── server.py            # Server runner
│   │   │   └── transports/          # Transport implementations
│   │   │       ├── base.py
│   │   │       ├── config.py
│   │   │       ├── factory.py
│   │   │       ├── http.py
│   │   │       ├── stdio.py
│   │   │       ├── websocket.py
│   │   │       └── sse.py
│   │   ├── common/                  # Common utilities
│   │   │   ├── config.py            # Base configuration
│   │   │   ├── logging.py           # Logging utilities
│   │   │   └── files.py             # File system utilities
│   │   └── testing/                 # Test utilities (if needed)
│   │       └── factories.py         # Test data factories
│   ├── mcp_local_repo_analyzer/      # Git analysis server
│   └── mcp_pr_recommender/           # PR recommendation server
├── tests/                            # Unified testing
│   ├── conftest.py                   # Shared configuration
│   ├── fixtures/                     # Test data
│   ├── unit/                         # Unit tests by package
│   ├── integration/                  # Integration tests
│   └── performance/                  # Performance tests
├── docker/                           # Container configurations
├── docs/                             # Documentation
├── scripts/                          # Utility scripts
├── config/                           # Configuration files
├── examples/                         # Usage examples
├── .github/                          # GitHub configuration
├── .devcontainer/                    # VS Code dev containers
├── pyproject.toml                    # Single configuration
├── Makefile                          # Build automation
└── docker-compose.yml                # Container orchestration
```

## Design Principles

### 1. Single Source Directory
- All source code under `src/`
- Clear package boundaries
- Simplified imports

### 2. Unified Testing
- Single test configuration
- Shared fixtures and utilities
- Cross-package testing capability

### 3. Centralized Configuration
- One pyproject.toml
- Single pre-commit config
- Unified CI/CD pipeline

### 4. Documentation Organization
- API documentation
- Architecture decisions
- User guides
- Developer documentation

## Package Organization

### shared/
**Purpose**: Truly shared functionality across MCP servers
- `models/` - Shared data models (git, analysis)
- `git/` - Git operations, config, and utilities
- `mcp/` - MCP protocol and transport implementations
- `common/` - Common utilities (logging, files, base config)
- `testing/` - Test utilities and factories (minimal)

### mcp_local_repo_analyzer
**Purpose**: Git repository analysis
- `cli.py` - Command-line interface
- `main.py` - Server initialization
- `services/` - Analysis services
- `tools/` - MCP tool implementations

### mcp_pr_recommender
**Purpose**: AI-powered recommendations
- `cli.py` - Command-line interface
- `main.py` - Server initialization
- `config.py` - Configuration
- `services/` - Recommendation services
- `tools/` - MCP tool implementations

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

## Key Directories

### /src
Contains all production code organized by package.

### /tests
- `unit/` - Package-specific unit tests
- `integration/` - Cross-package integration
- `performance/` - Performance benchmarks
- `fixtures/` - Shared test data

### /docker
- `analyzer/` - Analyzer container
- `recommender/` - Recommender container
- `dev/` - Development container

### /docs
- `api/` - API documentation
- `architecture/` - Design decisions
- `guides/` - User guides
- `development/` - Developer docs

### /scripts
- `setup/` - Installation scripts
- `ci/` - CI/CD scripts
- `utils/` - Utility scripts

### /.github
- `workflows/` - GitHub Actions
- `ISSUE_TEMPLATE/` - Issue templates
- `dependabot.yml` - Dependency updates

## Configuration Files

### pyproject.toml
Single file defining all packages:
```toml
[tool.poetry]
packages = [
    {include = "shared", from = "src"},
    {include = "mcp_local_repo_analyzer", from = "src"},
    {include = "mcp_pr_recommender", from = "src"}
]
```

### .pre-commit-config.yaml
Unified pre-commit hooks for all packages.

### Makefile
Common commands for development and deployment.

## Publishing Strategy

### PyPI Packages
- `mcp-local-repo-analyzer` - Published independently (includes shared code)
- `mcp-pr-recommender` - Published independently (includes shared code)
- `shared` - Not published independently (bundled with each package)

### Docker Images
- `ghcr.io/manavgup/mcp-local-repo-analyzer`
- `ghcr.io/manavgup/mcp-pr-recommender`

### Versioning
- Synchronized version numbers
- Single CHANGELOG.md
- Coordinated releases
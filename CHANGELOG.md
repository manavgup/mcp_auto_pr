# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-08-07

### Added
- Initial release of MCP Auto PR system
- Two production-ready MCP servers published to PyPI:
  - `mcp-local-repo-analyzer` - Repository change analysis
  - `mcp-pr-recommender` - AI-powered PR recommendations
- Multi-repository workspace architecture with coordinated build system
- Docker deployment with docker-compose configuration
- Comprehensive IDE integration support (VS Code, Cursor, Cline)
- Multi-transport protocol support (STDIO, HTTP, WebSocket, SSE)
- Intelligent git change detection and categorization
- AI-powered semantic grouping using OpenAI GPT-4
- Risk assessment and conflict detection
- Dependency-aware PR ordering
- Review time estimation and optimization
- One-command installation script (`./install.sh`)
- Health monitoring and comprehensive testing framework
- PyPI installation guide and test script (`test_pypi_packages.py`)
- Workspace-level build commands and automation
- Production-ready Docker images with health checks
- Bundled shared library for transparent installation
- Self-contained packages requiring no external dependencies

### Technical Details
- **Architecture**: 4-repository workspace with coordinated releases
- **Dependencies**: Python ≥3.10, Poetry, FastMCP 2.10.6+, OpenAI API
- **Packaging**: Self-contained PyPI packages with bundled dependencies
- **Testing**: Comprehensive test suites with coverage reporting
- **Documentation**: Complete setup guides, API docs, and architecture overview
- **Build System**: Makefile-based multi-repository coordination
- **CI/CD**: Automated testing and quality checks
- **Transport Layer**: Pluggable MCP transports with configuration management

### Repository Structure
```
mcp_pr_workspace/
├── mcp_auto_pr/                 # 🚀 Orchestration & deployment (this repo)
├── mcp_shared_lib/              # 📚 Foundation library (bundled)
├── mcp_local_repo_analyzer/     # 🔍 Git analysis engine (PyPI package)
└── mcp_pr_recommender/          # 🧠 AI recommendations (PyPI package)
```

### MCP Tools Introduced
#### Repository Analyzer
- `analyze_working_directory` - Uncommitted changes analysis with risk assessment
- `analyze_staged_changes` - Staged changes analysis ready for commit
- `get_outstanding_summary` - Comprehensive summary across repository state
- `compare_with_remote` - Local vs remote branch comparison
- `analyze_repository_health` - Overall repository health metrics

#### PR Recommender
- `generate_pr_recommendations` - Intelligent PR groupings with dependency ordering
- `analyze_pr_feasibility` - PR feasibility analysis and conflict detection
- `get_strategy_options` - Available grouping strategies (semantic, size-based, etc.)
- `validate_pr_recommendations` - Recommendation validation and refinement

### Configuration Management
- Environment variable-based configuration
- YAML configuration file support
- Transport-specific configuration options
- OpenAI API key validation and management
- Flexible deployment options (local, Docker, cloud)

### Quality Assurance
- 100% test coverage across core functionality
- Integration tests for all MCP tools
- Docker deployment testing
- Multi-platform compatibility (Linux, macOS, Windows)
- Security scanning and vulnerability assessment
- Performance benchmarking and optimization

### Breaking Changes
- None (initial release)

### Security
- No known vulnerabilities
- Secure API key handling
- Docker security best practices
- Input validation and sanitization
- No secrets in logs or error messages

### Performance
- Async-first architecture for non-blocking operations
- Optimized git operations with caching
- Efficient LLM API usage with token management
- Minimal memory footprint
- Fast startup times (<2 seconds)

[Unreleased]: https://github.com/manavgup/mcp_auto_pr/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/manavgup/mcp_auto_pr/releases/tag/v0.1.0

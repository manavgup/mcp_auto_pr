# Changelog

All notable changes to the MCP Auto PR project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-08-27

### 🎉 Major Release: Monorepo Consolidation

This release marks a significant milestone in the project's evolution, consolidating 4 separate repositories into a unified monorepo structure.

### Added
- Unified monorepo structure combining all MCP services
- Comprehensive migration documentation and guides
- Migration announcement document for community communication
- Repository archival script for automated archiving process
- Unified Makefile with consistent commands across all services
- Pre-commit hooks aligned with CI/CD pipeline
- Comprehensive test suite with 311 tests
- Test coverage reporting (72% coverage achieved)
- Docstring coverage reporting (98.9% achieved)
- Factory patterns for realistic test data generation
- Test markers for targeted testing (unit, integration, slow, external)
- Unified configuration management with Pydantic
- Shared infrastructure in `src/shared/` directory
- Health check endpoints for all services
- Docker composition for production deployment
- Professional development workflow documentation

### Changed
- **BREAKING**: Repository structure completely reorganized
  - `mcp_shared_lib` → `src/shared/`
  - `mcp_local_repo_analyzer` → `src/mcp_local_repo_analyzer/`
  - `mcp_pr_recommender` → `src/mcp_pr_recommender/`
- Import paths updated throughout codebase
- Dependencies consolidated into single `pyproject.toml`
- CI/CD pipeline simplified and enhanced
- Documentation structure reorganized under unified `/docs` directory
- Test structure reorganized with clear separation of unit/integration tests
- Configuration files consolidated at repository root

### Fixed
- 66 MyPy type checking errors resolved
- 20 Ruff linting violations fixed
- Git diff line count analysis returning zero values
- File statistics showing incorrect values in git analysis tools
- Duplicate code across services (90% reduction achieved)
- Import cycle issues between packages
- Test flakiness in git-related tests
- Pre-commit hook misalignment with CI pipeline
- Inconsistent code formatting across services

### Removed
- 4,201 lines of over-engineered code
- 27 duplicate functions (consolidated from 30→3)
- Separate repository structures for individual services
- Redundant configuration files across repositories
- Duplicate test utilities and fixtures
- Obsolete documentation files
- Legacy import structures

### Migration Statistics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Repositories | 4 | 1 | -75% |
| Duplicate Functions | 30 | 3 | -90% |
| Lines of Code | ~15,000 | ~10,800 | -28% |
| Linting Errors | 86 | 0 | -100% |
| Test Coverage | Unknown | 72% | ✅ |
| Docstring Coverage | ~60% | 98.9% | +65% |

### Repository Management
- **Archived Repositories**:
  - `mcp_shared_lib` (1 issue closed, 1 PR closed)
  - `mcp_local_repo_analyzer` (3 issues closed, 1 PR closed)
  - `mcp_pr_recommender` (2 issues closed, 1 PR closed)
- **Closed Issues**: 14 total (8 main repository + 6 linked repositories)
- **Closed PRs**: 3 across linked repositories

## [0.1.5] - 2025-08-17

### Added
- Epic #14: Monorepo Refactoring planning initiated
- Comprehensive refactoring strategy documentation
- Baseline analysis of code duplication
- Test coverage implementation plan

### Changed
- Project structure analysis and documentation
- Updated development workflow documentation

## [0.1.4] - 2025-08-11

### Added
- CI/CD pipeline for GitHub Actions
- Pre-commit configuration standardization
- Security scanning with Trivy
- Test coverage reporting infrastructure

### Fixed
- CI pipeline stability issues
- Ruff linting violations in multiple modules
- YAML configuration validation errors

## [0.1.3] - 2025-08-01

### Added
- Enhanced data format handling between services
- Shared server base class implementation planning
- Improved error messages for file extraction failures

### Changed
- Standardized data models across analyzer and recommender services
- Improved git diff analysis accuracy

### Fixed
- File extraction "No files to analyze" error
- Data format inconsistencies between services

## [0.1.2] - 2025-07-30

### Added
- Issue tracking for known bugs
- Enhanced error logging in git analysis tools

### Fixed
- Diff analysis returning zero line counts
- File statistics calculation errors

## [0.1.1] - 2025-07-25

### Added
- Initial bug reporting and tracking system
- Enhanced debug logging for git operations

### Changed
- Improved error handling in file analysis tools

## [0.1.0] - 2025-07-01

### Added
- Initial release of MCP Auto PR system
- MCP Local Repository Analyzer service
- MCP PR Recommender service
- MCP Shared Library
- Basic Docker support
- Initial documentation
- FastMCP integration for MCP protocol support
- Git repository analysis capabilities
- AI-powered PR recommendation engine (GPT-4)
- Multiple transport protocol support (stdio, HTTP, WebSocket, SSE)

### Known Issues
- Test coverage not measured
- Some code duplication between services
- Limited documentation
- No unified development environment

---

## Version History Summary

- **v0.2.0** - Major monorepo consolidation, 90% duplicate code reduction, comprehensive testing
- **v0.1.x** - Initial development, bug fixes, incremental improvements
- **v0.1.0** - Initial release with basic MCP functionality

## Upgrade Guide

### From v0.1.x to v0.2.0

1. **Clone the new monorepo**:
   ```bash
   git clone https://github.com/manavgup/mcp_auto_pr.git
   cd mcp_auto_pr
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Update import paths** in your code:
   - `from mcp_shared_lib.*` → `from shared.*`
   - Repository paths now under `src/` directory

4. **Update configuration files**:
   - Use new unified configuration structure
   - Environment variables remain compatible

5. **Update Docker deployments**:
   - Use new docker-compose files in `/docker` directory
   - Service names remain the same

## Support

For issues, questions, or contributions, please visit:
- [GitHub Issues](https://github.com/manavgup/mcp_auto_pr/issues)
- [Migration Guide](docs/refactor/github-migration-plan.md)
- [Contributing Guide](CONTRIBUTING.md)

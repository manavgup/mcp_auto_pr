# MCP Auto PR v0.2.0 Monorepo Consolidation

## Overview
This documentation outlines the consolidation of four separate repositories into a single monorepo structure for improved maintainability, testing, and deployment.

## Quick Navigation

### 📋 Planning Documents
- [Current State Analysis](./01-current-state.md) - Analysis of existing issues and repository state
- [Monorepo Architecture](./02-monorepo-architecture.md) - Proposed folder structure and organization
- [Migration Strategy](./03-migration-strategy.md) - Step-by-step migration plan
- [Test Coverage Plan](./04-test-coverage-plan.md) - 90% coverage target implementation

### 🚀 Implementation Guides
- [Phase 1: Repository Consolidation](./05-phase1-consolidation.md) - Days 1-2
- [Phase 2: CI/CD Setup](./06-phase2-cicd.md) - Days 3-4
- [Phase 3: Test Implementation](./07-phase3-testing.md) - Days 5-7
- [Phase 4: Documentation](./08-phase4-documentation.md) - Day 8
- [Phase 5: Release](./09-phase5-release.md) - Day 9

### 🔧 Technical References
- [Docker Strategy](./10-docker-strategy.md) - Container build and publishing
- [PyPI Publishing](./11-pypi-publishing.md) - Multi-package publishing from monorepo
- [Development Workflow](./12-development-workflow.md) - Local development setup
- [Command Reference](./13-command-reference.md) - Useful commands and scripts

### 📊 Additional Improvements
- [User Experience](./14-user-experience.md) - Quick start and usability
- [Security & Compliance](./15-security-compliance.md) - Security enhancements
- [Monitoring & Observability](./16-monitoring.md) - Logging and metrics
- [Developer Experience](./17-developer-experience.md) - Dev containers and tooling

## Executive Summary

After successfully publishing `mcp-local-repo-analyzer` and `mcp-pr-recommender` to PyPI as v0.1.0, we're consolidating the multi-repository structure into a single `mcp_auto_pr` repository for improved maintainability.

### Key Changes
- **Single Repository**: Consolidate 4 repos into 1 monorepo
- **Unified Testing**: Achieve 90% test coverage across all packages
- **Simplified CI/CD**: Single pipeline for all packages
- **Docker Publishing**: Automated container builds to GitHub Container Registry
- **Backward Compatible**: Maintain separate PyPI packages

### Current Issues Being Addressed
1. ✅ Duplicated mcp_shared_lib code (removed)
2. 🔴 GitHub Actions CI failures
3. 🟡 Uncommitted changes across repositories
4. 🟡 Conflicting pre-commit configurations
5. 🔴 Low test coverage (15% → 90% target)

## Timeline
- **Day 1-2**: Repository consolidation
- **Day 3-4**: CI/CD and infrastructure
- **Day 5-7**: Test implementation (90% coverage)
- **Day 8**: Documentation
- **Day 9**: v0.2.0 Release

## Success Criteria
- [ ] All tests pass with 90%+ coverage
- [ ] Both PyPI packages publish successfully
- [ ] Docker images available on ghcr.io
- [ ] CI/CD pipeline fully functional
- [ ] No breaking changes for users

## Quick Start

For immediate action items, see:
1. [Migration Strategy](./03-migration-strategy.md) - Start here
2. [Phase 1 Consolidation](./05-phase1-consolidation.md) - First implementation steps
3. [Command Reference](./13-command-reference.md) - Useful commands

## Contact & Support
- **Primary**: Manav Gupta <manavg@gmail.com>
- **GitHub Issues**: https://github.com/manavgup/mcp_auto_pr/issues
- **Documentation**: This directory
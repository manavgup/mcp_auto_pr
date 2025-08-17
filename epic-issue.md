# Epic: Monorepo Refactoring - Consolidate Multi-Repository Structure

## 🎯 Overview
Consolidate four separate repositories (mcp_auto_pr, mcp_local_repo_analyzer, mcp_pr_recommender, mcp_shared_lib) into a single monorepo while maintaining separate PyPI packages and Docker containers. This refactoring will improve maintainability, testing, and deployment while preserving backward compatibility.

## ✅ Success Criteria
- [ ] All repositories successfully consolidated into single monorepo structure
- [ ] Both PyPI packages (`mcp-local-repo-analyzer`, `mcp-pr-recommender`) publish successfully from monorepo
- [ ] Both Docker containers build and publish to GitHub Container Registry from monorepo
- [ ] 90% test coverage achieved across all packages (currently at 0-15%)
- [ ] Unified CI/CD pipeline fully functional with automated testing and deployment
- [ ] No breaking changes for existing users or integrations
- [ ] All existing functionality preserved and working

## 📅 Timeline
**Total Duration**: 9 days
- **Phase 1**: Repository consolidation (Days 1-2)
- **Phase 2**: CI/CD setup (Days 3-4)
- **Phase 3**: Test implementation (Days 5-7)
- **Phase 4**: Documentation (Day 8)
- **Phase 5**: Release (Day 9)

## 🏗️ Architecture Changes

### Current State
- 4 separate repositories with duplicated code
- Multiple CI/CD pipelines
- Inconsistent test coverage (0-15%)
- Complex cross-repository dependencies
- Multiple pre-commit configurations

### Target State
- Single monorepo with clear package boundaries
- Unified CI/CD pipeline
- 90% test coverage target
- Shared code properly organized under `src/shared/`
- Single development workflow and tooling

## 📋 Implementation Phases

### Phase 1: Repository Consolidation (Days 1-2)
- [ ] Create monorepo directory structure
- [ ] Move source code from all repositories
- [ ] Consolidate tests and fixtures
- [ ] Create unified configuration files
- [ ] Update import statements and dependencies

### Phase 2: CI/CD Setup (Days 3-4)
- [ ] Set up unified GitHub Actions workflows
- [ ] Configure Docker build and publish pipelines
- [ ] Implement security scanning and quality gates
- [ ] Set up automated testing and coverage reporting

### Phase 3: Test Implementation (Days 5-7)
- [ ] Implement comprehensive unit tests for all modules
- [ ] Add integration tests for cross-package functionality
- [ ] Create end-to-end tests for complete workflows
- [ ] Achieve 90% test coverage target

### Phase 4: Documentation (Day 8)
- [ ] Update all documentation for monorepo structure
- [ ] Create developer onboarding guides
- [ ] Update API documentation
- [ ] Consolidate README files

### Phase 5: Release (Day 9)
- [ ] Final testing and validation
- [ ] Create v0.2.0 release
- [ ] Publish to PyPI and Docker Hub
- [ ] Update repository descriptions and links

## 🔗 Related Issues
- #3 Epic 2: Test Coverage Implementation
- #5 Epic 4: Shared Library Improvements
- #7 Implement CLI module testing for both packages
- #8 Clean up uncommitted changes across all repositories
- #9 Test MCP tool implementations with realistic scenarios
- #10 Rename mcp_shared_lib to 'shared' and reorganize structure
- #11 Set up test coverage reporting and enforcement
- #12 Standardize pre-commit configuration across all repositories

## 🚨 Risks and Mitigation

### High Risk
- **Breaking changes during migration**
  - Mitigation: Comprehensive testing, incremental migration, rollback plan
- **Loss of git history**
  - Mitigation: Use git subtree/filter-branch, create backup branches

### Medium Risk
- **CI/CD pipeline failures**
  - Mitigation: Test workflows locally, implement health checks
- **Dependency conflicts**
  - Mitigation: Careful dependency analysis, use poetry lock files

### Low Risk
- **Documentation gaps**
  - Mitigation: Comprehensive documentation plan, peer review

## 🧪 Testing Strategy
- **Unit Tests**: 60% of coverage target
- **Integration Tests**: 25% of coverage target
- **End-to-End Tests**: 10% of coverage target
- **Performance Tests**: 5% of coverage target

## 📦 Publishing Strategy
- **PyPI Packages**: Maintain separate packages with shared code bundled
- **Docker Images**: Build from monorepo with service-specific Dockerfiles
- **Versioning**: Synchronized version numbers across all packages
- **Releases**: Coordinated releases with single CHANGELOG.md

## 🔄 Rollback Plan
If migration fails:
1. Restore from backup branches
2. Document issues encountered
3. Adjust migration plan based on learnings
4. Retry with modified approach

## 🔗 Dependencies
- All existing issues in Sprint 1 and Sprint 2
- GitHub Actions CI/CD setup
- Docker build configurations
- PyPI publishing workflows
- Test infrastructure setup

## 📚 Documentation
- [Monorepo Architecture](./docs/refactor/02-monorepo-architecture.md)
- [Migration Strategy](./docs/refactor/03-migration-strategy.md)
- [Phase 1 Implementation](./docs/refactor/05-phase1-consolidation.md)
- [CI/CD Setup](./docs/refactor/06-phase2-cicd.md)
- [PyPI Publishing](./docs/refactor/11-pypi-publishing.md)

## 🏷️ Labels
- `epic`
- `priority/critical`
- `sprint-1`
- `v0.2.0`
- `refactoring`
- `monorepo`

## 📝 Notes
- This refactoring is based on comprehensive documentation in `docs/refactor/`
- All phases have detailed implementation guides
- Migration can be done incrementally to reduce risk
- Success will significantly improve maintainability and development velocity

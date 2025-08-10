# Epic 2: Test Coverage

## 📋 Epic Overview
**Epic ID**: E2
**Priority**: P0 (Critical)
**Estimated Effort**: 5 days
**Sprint**: 1
**Dependencies**: Epic 1 (CI/CD Stability)

## 🎯 Epic Goal
Achieve 70%+ test coverage on critical code paths to ensure reliability and enable confident refactoring and feature development.

## 🚫 Current State
- **mcp_local_repo_analyzer**: 15.65% coverage (1243/1497 lines uncovered)
- **mcp_pr_recommender**: 0.00% coverage (1194/1194 lines uncovered)
- **mcp_shared_lib**: 13.22% coverage (1985/2361 lines uncovered)

## 🎯 Target State
- **All packages**: 70%+ coverage on critical paths
- **CLI modules**: 80%+ coverage (user-facing)
- **Core services**: 75%+ coverage (business logic)
- **Models/utilities**: 60%+ coverage (lower risk)

## 📋 User Stories

### Story 2.1: CLI Module Testing
**As a** developer
**I want** comprehensive CLI testing
**So that** user-facing commands work reliably and provide good error messages

#### Acceptance Criteria
- [ ] CLI argument parsing tested for all commands
- [ ] Error handling tested for invalid inputs
- [ ] Help text generation tested
- [ ] Transport selection logic tested
- [ ] Configuration loading tested
- [ ] 80%+ coverage on CLI modules

#### Tasks
- **mcp_local_repo_analyzer/cli.py**:
  - [ ] Test --transport argument parsing
  - [ ] Test --port, --host argument handling
  - [ ] Test --config file loading
  - [ ] Test invalid argument combinations
  - [ ] Test help text generation

- **mcp_pr_recommender/cli.py**:
  - [ ] Test OpenAI API key validation
  - [ ] Test transport configuration
  - [ ] Test error handling for missing dependencies
  - [ ] Test configuration precedence (CLI > env > file)

### Story 2.2: MCP Tool Testing
**As a** developer
**I want** all MCP tools thoroughly tested
**So that** the core functionality works correctly for users

#### Acceptance Criteria
- [ ] Each tool's main functionality tested with real git repositories
- [ ] Error conditions tested (invalid repos, permissions, etc.)
- [ ] Edge cases covered (empty repos, large repos, binary files)
- [ ] Integration with shared models tested
- [ ] 85%+ coverage on tool implementations

#### Tasks
- **Analyzer Tools**:
  - [ ] `working_directory.py` - Test with various git states
  - [ ] `staging_area.py` - Test staged vs unstaged changes
  - [ ] `unpushed_commits.py` - Test branch tracking scenarios
  - [ ] `summary.py` - Test analysis aggregation

- **Recommender Tools**:
  - [ ] `pr_recommender_tool.py` - Test with sample change sets
  - [ ] `feasibility_analyzer_tool.py` - Test conflict detection
  - [ ] `strategy_manager_tool.py` - Test different grouping strategies
  - [ ] `validator_tool.py` - Test validation logic

### Story 2.3: Service Layer Testing
**As a** developer
**I want** core business logic thoroughly tested
**So that** the application behaves correctly under various conditions

#### Acceptance Criteria
- [ ] Git operations tested with mock and real repositories
- [ ] Analysis logic tested with comprehensive scenarios
- [ ] Error handling tested for git failures
- [ ] Performance acceptable for large repositories
- [ ] 75%+ coverage on service modules

#### Tasks
- **Analyzer Services**:
  - [ ] `change_detector.py` - Test change detection algorithms
  - [ ] `diff_analyzer.py` - Test diff parsing and categorization
  - [ ] `status_tracker.py` - Test git status interpretation

- **Recommender Services**:
  - [ ] `semantic_analyzer.py` - Test with OpenAI mocking
  - [ ] `grouping_engine.py` - Test file grouping logic
  - [ ] `atomicity_validator.py` - Test PR atomicity rules

- **Shared Services**:
  - [ ] `git_client.py` - Test all git operations with mocks
  - [ ] Test configuration loading and validation

### Story 2.4: Model and Utility Testing
**As a** developer
**I want** data models and utilities well-tested
**So that** data integrity is maintained and utilities work correctly

#### Acceptance Criteria
- [ ] All Pydantic models tested for validation
- [ ] Serialization/deserialization tested
- [ ] Utility functions tested with edge cases
- [ ] File operations tested with various scenarios
- [ ] 60%+ coverage on models and utils

#### Tasks
- **Models Testing**:
  - [ ] Git models - test validation rules
  - [ ] Analysis models - test data transformation
  - [ ] Base models - test inheritance and composition

- **Utilities Testing**:
  - [ ] `git_utils.py` - Test repository detection, path handling
  - [ ] `file_utils.py` - Test file operations, permissions
  - [ ] `logging_utils.py` - Test logging configuration

### Story 2.5: Integration Testing Setup
**As a** developer
**I want** integration tests between components
**So that** the system works correctly as a whole

#### Acceptance Criteria
- [ ] End-to-end workflow tests (analyzer → recommender)
- [ ] Transport layer integration tested
- [ ] Real git repository scenarios tested
- [ ] Error propagation tested across components
- [ ] Performance benchmarks established

#### Tasks
- [ ] Set up integration test framework
- [ ] Create test git repositories with known states
- [ ] Test complete MCP server startup and tool execution
- [ ] Test cross-package data flow
- [ ] Test error handling across component boundaries

## ✅ Definition of Done

### Story-Level DoD
- [ ] All acceptance criteria met
- [ ] Tests pass both locally and in CI
- [ ] Code coverage targets achieved for the story scope
- [ ] Tests are maintainable and well-documented
- [ ] Performance impact assessed and acceptable

### Epic-Level DoD
- [ ] 70%+ overall test coverage achieved
- [ ] Critical path coverage >80%
- [ ] All 0% coverage modules now have >50% coverage
- [ ] Integration tests cover main user workflows
- [ ] Test suite runs in <5 minutes
- [ ] Flaky tests identified and fixed
- [ ] Test documentation complete
- [ ] Coverage badges updated and accurate

## 🧪 Testing Strategy

### Prioritization (80/20 Rule)
**Focus 80% effort on 20% most critical code:**
1. **CLI interfaces** - Direct user impact
2. **MCP tool implementations** - Core functionality
3. **Git operations** - Data integrity critical
4. **Error handling paths** - User experience critical

### Test Types
- **Unit Tests**: Fast, isolated, mocked dependencies
- **Integration Tests**: Real components, controlled environment
- **Contract Tests**: Interface compatibility between components
- **Property Tests**: Use Hypothesis for edge case discovery

### Test Data Strategy
- **Real git repositories** for integration tests
- **Mock objects** for isolated unit tests
- **Factory pattern** for consistent test data generation
- **Fixtures** for common test scenarios

## 📊 Success Metrics

### Coverage Metrics
- **Line Coverage**: 70%+ overall, 80%+ critical paths
- **Branch Coverage**: 65%+ (decision points tested)
- **Function Coverage**: 85%+ (most functions tested)

### Quality Metrics
- **Test Execution Time**: <5 minutes total
- **Test Reliability**: <1% flaky test rate
- **Mutation Testing Score**: >70% (if implemented)

### Process Metrics
- **Test Writing Velocity**: 2-3 tests per hour average
- **Bug Detection Rate**: Tests catch >90% of regressions
- **Maintenance Overhead**: <20% of development time

## 🚧 Risks & Dependencies

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|---------|------------|
| OpenAI API costs for testing | High | Low | Mock OpenAI calls, limit real API tests |
| Test suite becomes too slow | Medium | Medium | Optimize slow tests, use test categories |
| Complex git scenarios hard to test | Medium | Medium | Use git test fixtures, focus on common cases |
| Flaky tests with real git operations | Medium | High | Use deterministic test data, mock when possible |

### Dependencies
- **Epic 1 completion**: Need stable CI to run tests reliably
- **Git repositories**: Need controlled test environments
- **External APIs**: OpenAI mocking strategy required
- **Test data**: Realistic but lightweight test scenarios

## 📋 Implementation Checklist

### Week 1 (Days 4-6)
#### Day 4: Foundation
- [ ] Set up test infrastructure and fixtures
- [ ] Create mock strategies for external dependencies
- [ ] Implement CLI testing for both packages
- [ ] **Target**: 40% coverage

#### Day 5: Core Functionality
- [ ] Test all MCP tools with realistic scenarios
- [ ] Test service layer business logic
- [ ] Add integration tests for happy path
- [ ] **Target**: 60% coverage

#### Day 6: Edge Cases & Polish
- [ ] Test error handling and edge cases
- [ ] Add performance benchmarks
- [ ] Optimize slow tests
- [ ] **Target**: 70%+ coverage

### Quality Gates
- **End of Day 4**: CI runs tests successfully, basic coverage reporting
- **End of Day 5**: Critical paths covered, integration tests passing
- **End of Day 6**: Coverage targets met, test suite optimized

## 📝 Notes
- **Prioritize user-facing functionality** - CLI and tools first
- **Mock external dependencies** - Git operations, OpenAI API, file system
- **Focus on behavior, not implementation** - Test what the code does, not how
- **Keep tests fast and reliable** - Avoid test flakiness from the start
- **Document test patterns** - Make it easy for future developers

---

**Next Epic**: [Epic 3: Development Workflow](./epic-3-dev-workflow.md)

# Epic 3: Development Workflow

## 📋 Epic Overview
**Epic ID**: E3
**Priority**: P1 (High)
**Estimated Effort**: 2 days
**Sprint**: 1
**Dependencies**: None (can run parallel with other epics)

## 🎯 Epic Goal
Establish a clean, consistent development workflow across all repositories with standardized tooling and no uncommitted changes blocking development.

## 🚫 Current Problems
- Uncommitted changes scattered across repositories
- Inconsistent pre-commit configurations (4 different files)
- Different linting rules and formatting standards
- Missing or outdated development setup documentation
- No clear contribution guidelines

## 🎯 Epic Outcome
A streamlined development workflow where:
- All repositories have clean git status
- Consistent code quality standards enforced
- Pre-commit hooks work reliably
- New developers can get started quickly
- Clear guidelines for code contributions

## 📋 User Stories

### Story 3.1: Clean Repository State
**As a** developer
**I want** all repositories to have clean git status
**So that** I can work without conflicts and understand what changes are intentional

#### Acceptance Criteria
- [ ] All repositories show `git status` clean
- [ ] Uncommitted changes properly reviewed and committed or discarded
- [ ] No untracked files that should be in .gitignore
- [ ] Git history is clean and meaningful
- [ ] Stale branches cleaned up

#### Tasks
- **mcp_auto_pr**:
  - [ ] Review untracked files: PYPI_PUBLISHING.md, REMOVE_SHARED_LIB.md, etc.
  - [ ] Commit valuable documentation
  - [ ] Clean up .DS_Store and temp files
  - [ ] Update .gitignore if needed

- **mcp_local_repo_analyzer**:
  - [ ] Review modified: CHANGELOG.md, poetry.lock, pyproject.toml
  - [ ] Review untracked: echo_server.py, mock_auth_server.py
  - [ ] Commit necessary changes, remove temp files

- **mcp_pr_recommender**:
  - [ ] Review modified source files and configs
  - [ ] Commit intentional changes
  - [ ] Document any breaking changes

- **mcp_shared_lib**:
  - [ ] Review and commit CHANGELOG.md updates
  - [ ] Review pyproject.toml changes

### Story 3.2: Standardized Code Quality Tools
**As a** developer
**I want** consistent code quality standards across all repositories
**So that** code style is uniform and quality is maintained automatically

#### Acceptance Criteria
- [ ] Single pre-commit configuration template applied to all repos
- [ ] Consistent linting rules (Ruff configuration)
- [ ] Consistent formatting rules (Black configuration)
- [ ] Consistent import sorting (isort configuration)
- [ ] Type checking rules (mypy configuration) standardized
- [ ] All pre-commit hooks run successfully on existing code

#### Tasks
- **Create master configuration**:
  - [ ] Design unified .pre-commit-config.yaml
  - [ ] Define Ruff linting rules in pyproject.toml
  - [ ] Set Black formatting standards
  - [ ] Configure mypy for type checking
  - [ ] Set up import sorting rules

- **Apply to all repositories**:
  - [ ] Copy master config to each repo
  - [ ] Run pre-commit on all files and fix issues
  - [ ] Test hooks work correctly
  - [ ] Update CI to validate pre-commit compliance

### Story 3.3: Development Environment Setup
**As a** developer
**I want** clear, simple instructions to set up a development environment
**So that** I can start contributing quickly without friction

#### Acceptance Criteria
- [ ] Single command setup for each repository
- [ ] Clear documentation of prerequisites (Python, Poetry, etc.)
- [ ] Development environment validation script
- [ ] Troubleshooting guide for common issues
- [ ] IDE/editor configuration recommendations

#### Tasks
- [ ] Create dev-setup.sh script for automated setup
- [ ] Document prerequisites and system requirements
- [ ] Create environment validation script
- [ ] Document VS Code/IDE configuration
- [ ] Add troubleshooting section to README
- [ ] Test setup on fresh system

### Story 3.4: Contribution Guidelines
**As a** developer
**I want** clear guidelines for contributing to the project
**So that** contributions are consistent and review process is smooth

#### Acceptance Criteria
- [ ] CONTRIBUTING.md file with clear guidelines
- [ ] Code review checklist
- [ ] Commit message conventions
- [ ] Testing requirements for contributions
- [ ] Documentation requirements

#### Tasks
- [ ] Create CONTRIBUTING.md with detailed guidelines
- [ ] Define commit message format (conventional commits?)
- [ ] Create pull request template
- [ ] Document code review process
- [ ] Set up branch protection rules (if applicable)

### Story 3.5: Development Scripts and Automation
**As a** developer
**I want** convenient scripts for common development tasks
**So that** I can be productive without memorizing complex commands

#### Acceptance Criteria
- [ ] Makefile or script collection with common tasks
- [ ] Scripts for testing, linting, building
- [ ] Scripts for running services locally
- [ ] Scripts for cleaning up development artifacts
- [ ] Documentation for all available scripts

#### Tasks
- [ ] Create comprehensive Makefile for each repo
- [ ] Add scripts for: test, lint, format, build, clean
- [ ] Add scripts for: serve, debug, coverage
- [ ] Document all available commands
- [ ] Test scripts on different environments

## ✅ Definition of Done

### Story-Level DoD
- [ ] All acceptance criteria met
- [ ] Changes tested on clean environment
- [ ] Documentation updated
- [ ] No breaking changes to existing workflow
- [ ] Team feedback incorporated (if applicable)

### Epic-Level DoD
- [ ] All repositories have clean git status
- [ ] Pre-commit hooks working consistently across all repos
- [ ] New developer can set up environment in <10 minutes
- [ ] Code quality standards documented and enforced
- [ ] CONTRIBUTING.md complete and accurate
- [ ] Development scripts tested and documented
- [ ] No regression in existing functionality

## 🧪 Testing Strategy

### Manual Testing
- [ ] Test full setup process on clean machine
- [ ] Verify pre-commit hooks work correctly
- [ ] Test all development scripts
- [ ] Validate documentation accuracy

### Automated Testing
- [ ] CI validates pre-commit configuration
- [ ] Setup scripts tested in GitHub Actions
- [ ] Code quality checks integrated into CI

### User Acceptance
- [ ] Development workflow feels smooth
- [ ] Common tasks are easy to perform
- [ ] Error messages are helpful and actionable

## 📊 Success Metrics

### Process Metrics
- **Setup Time**: <10 minutes for new developer
- **Pre-commit Success Rate**: >98% after initial setup
- **Code Quality Consistency**: Same rules across all repos
- **Documentation Accuracy**: Setup works on first try

### Developer Experience
- **Onboarding Time**: Reduced by 50%
- **Code Review Speed**: Reduced by 30% (due to consistency)
- **Development Friction**: Subjective improvement

## 🚧 Risks & Dependencies

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|---------|------------|
| Pre-commit hooks too strict | Medium | Medium | Start with warnings, gradually enforce |
| Breaking existing workflows | Low | High | Test thoroughly, provide migration guide |
| Tool version conflicts | Medium | Low | Pin versions, document compatibility |

### Dependencies
- Git repositories accessible
- No dependencies on other epics
- Can run in parallel with CI/CD work

## 📋 Implementation Checklist

### Day 7: Repository Cleanup & Standards
- [ ] **Morning (4h)**: Clean up uncommitted changes
  - [ ] Review and commit valuable changes
  - [ ] Remove temporary files
  - [ ] Update .gitignore files
  - [ ] Clean git history if needed

- [ ] **Afternoon (4h)**: Standardize code quality
  - [ ] Create master pre-commit configuration
  - [ ] Apply to all repositories
  - [ ] Fix any pre-commit violations
  - [ ] Update CI to enforce standards

### Quality Gates
- **End of Morning**: All repos have clean `git status`
- **End of Day**: Pre-commit hooks working on all repos

### Follow-up Tasks (if time permits)
- [ ] Create comprehensive CONTRIBUTING.md
- [ ] Set up development scripts
- [ ] Improve setup documentation
- [ ] Add troubleshooting guides

## 📝 Configuration Templates

### Master .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Makefile Template
```makefile
.PHONY: help install test lint format clean

help:
	@echo "Available commands:"
	@echo "  install  - Install dependencies"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linting"
	@echo "  format   - Format code"
	@echo "  clean    - Clean artifacts"

install:
	poetry install --with dev,test

test:
	poetry run pytest

lint:
	poetry run ruff check src/ tests/
	poetry run mypy src/

format:
	poetry run black src/ tests/
	poetry run ruff check --fix src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf dist/ build/ *.egg-info
```

## 📝 Notes
- **Focus on consistency over perfection** - Same standards everywhere
- **Make it easy to do the right thing** - Automated tools, clear docs
- **Test on fresh environment** - Don't assume local setup
- **Keep it simple** - Avoid over-engineering the development workflow

---

**Next Epic**: [Epic 4: Shared Library Improvements](./epic-4-shared-library.md)

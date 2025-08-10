# Release Checklist

Use this checklist before creating any release to ensure quality and consistency.

## Pre-Release Checklist

### 📋 Planning & Preparation

- [ ] **Version Decision**: Determine version number using [Semantic Versioning](https://semver.org/)
  - `MAJOR.MINOR.PATCH` (e.g., 1.2.3)
  - Major: Breaking changes
  - Minor: New features, backward compatible
  - Patch: Bug fixes, backward compatible

- [ ] **Branch Strategy**: Ensure proper branch state
  - [ ] All intended changes merged to main/master
  - [ ] No pending critical PRs
  - [ ] Branch is stable and tested

- [ ] **Dependencies**: Review and update dependencies
  - [ ] Check for security updates
  - [ ] Update to compatible versions
  - [ ] Test with updated dependencies

### 🧪 Code Quality & Testing

- [ ] **Automated Tests**: All tests passing
  - [ ] Unit tests: `make test-unit`
  - [ ] Integration tests: `make test-integration`
  - [ ] End-to-end tests: `./test_pypi_packages.py`
  - [ ] Test coverage: `make test-coverage` (aim for >90%)

- [ ] **Code Quality**: Quality checks passing
  - [ ] Linting: `make lint`
  - [ ] Formatting: `make format`
  - [ ] Type checking: `make type-check`
  - [ ] Security scanning: `make security-check`

- [ ] **Manual Testing**: Critical functionality verified
  - [ ] PyPI packages install correctly
  - [ ] CLI tools work as expected
  - [ ] MCP servers start and respond
  - [ ] IDE integration functions
  - [ ] Docker deployment works

### 🔢 Version Management

- [ ] **Version Consistency**: Update version in all files
  - [ ] `mcp_local_repo_analyzer/pyproject.toml`
  - [ ] `mcp_pr_recommender/pyproject.toml`
  - [ ] `mcp_shared_lib/pyproject.toml` (if standalone)
  - [ ] Docker image tags
  - [ ] Any hardcoded version references

- [ ] **Git Tagging**: Prepare git tags
  - [ ] Delete any incorrect tags: `git tag -d v0.x.x`
  - [ ] Create new tag: `git tag v0.x.x`
  - [ ] Tag follows format: `v0.1.0` (with v prefix)

### 📦 Build & Distribution

- [ ] **Package Building**: Packages build successfully
  - [ ] Local repo analyzer: `cd mcp_local_repo_analyzer && poetry build`
  - [ ] PR recommender: `cd mcp_pr_recommender && poetry build`
  - [ ] Verify package contents and sizes
  - [ ] Test packages in clean environment

- [ ] **Docker Images**: Docker deployment ready
  - [ ] Images build: `docker-compose build`
  - [ ] Images run: `docker-compose up -d`
  - [ ] Health checks pass: `curl http://localhost:9070/health`
  - [ ] Services accessible and functional

### 📝 Documentation

- [ ] **Documentation Updates**: All docs current
  - [ ] README.md updated with new features
  - [ ] CHANGELOG.md updated with all changes
  - [ ] API documentation reflects current state
  - [ ] Installation instructions tested
  - [ ] Configuration examples work

- [ ] **Breaking Changes**: If any breaking changes
  - [ ] Migration guide created
  - [ ] Breaking changes highlighted in CHANGELOG
  - [ ] Deprecation warnings added (if applicable)
  - [ ] Timeline for removal communicated

### 🚀 Release Preparation

- [ ] **Release Assets**: Prepare all release materials
  - [ ] GitHub release notes drafted
  - [ ] CHANGELOG.md section complete
  - [ ] Test script works: `python test_pypi_packages.py`
  - [ ] Installation guide verified

- [ ] **PyPI Preparation**: Ready for PyPI publishing
  - [ ] PyPI credentials configured
  - [ ] Package descriptions updated
  - [ ] Keywords and classifiers current
  - [ ] Test on TestPyPI first (if major changes)

## Release Execution Checklist

### 🎯 Publishing

- [ ] **PyPI Publishing**: Publish packages
  - [ ] Local repo analyzer: `cd mcp_local_repo_analyzer && poetry publish`
  - [ ] PR recommender: `cd mcp_pr_recommender && poetry publish`
  - [ ] Verify packages appear on PyPI
  - [ ] Test installation from PyPI

- [ ] **Git Operations**: Tag and push
  - [ ] Push latest changes: `git push origin master`
  - [ ] Push tags: `git push origin v0.x.x`
  - [ ] Verify tag appears on GitHub

- [ ] **GitHub Release**: Create GitHub release
  - [ ] Create release from tag
  - [ ] Add comprehensive release notes
  - [ ] Attach relevant assets (if any)
  - [ ] Mark as latest release

### ✅ Post-Release Verification

- [ ] **Installation Testing**: Verify release works
  - [ ] Fresh install: `pip install mcp-local-repo-analyzer mcp-pr-recommender`
  - [ ] Run test script: `python test_pypi_packages.py`
  - [ ] Test IDE integration
  - [ ] Verify Docker deployment

- [ ] **Documentation**: Update links and references
  - [ ] PyPI badge versions
  - [ ] Download links
  - [ ] Version references in docs

## Post-Release Checklist

### 📢 Communication

- [ ] **Notifications**: Inform stakeholders
  - [ ] Team notification
  - [ ] User community (if applicable)
  - [ ] Update project status

- [ ] **Documentation**: Final documentation updates
  - [ ] Update project homepage
  - [ ] Refresh installation guides
  - [ ] Update any external documentation

### 🔍 Monitoring

- [ ] **Release Health**: Monitor release
  - [ ] Check for immediate issues
  - [ ] Monitor error reports
  - [ ] Watch PyPI download stats
  - [ ] Review user feedback

- [ ] **Next Steps**: Plan future development
  - [ ] Update project roadmap
  - [ ] Plan next release
  - [ ] Address any technical debt

## Emergency Rollback Checklist

If issues are discovered post-release:

- [ ] **Assessment**: Determine severity
  - [ ] Categorize issue (critical, major, minor)
  - [ ] Assess user impact
  - [ ] Decide on rollback vs hotfix

- [ ] **Rollback Actions** (if necessary):
  - [ ] Yank problematic PyPI version
  - [ ] Revert problematic changes
  - [ ] Create hotfix release
  - [ ] Update documentation

- [ ] **Communication**: Notify users
  - [ ] GitHub issue/announcement
  - [ ] Update release notes
  - [ ] Provide mitigation steps

## Templates

### Release Notes Template
```markdown
# v0.X.Y - Release Name

## 🚀 What's New
- Feature highlights

## 🐛 Bug Fixes
- Bug fix summaries

## 📋 Full Changelog
Link to full changelog

## 📦 Installation
\```bash
pip install mcp-local-repo-analyzer mcp-pr-recommender
\```

## 🔗 Links
- [PyPI: mcp-local-repo-analyzer](https://pypi.org/project/mcp-local-repo-analyzer/)
- [PyPI: mcp-pr-recommender](https://pypi.org/project/mcp-pr-recommender/)
```

### Git Tag Commands
```bash
# Create and push tag
git tag v0.X.Y
git push origin v0.X.Y

# Delete tag (if needed)
git tag -d v0.X.Y
git push origin --delete v0.X.Y
```

### PyPI Publishing Commands
```bash
# Build and publish analyzer
cd mcp_local_repo_analyzer
poetry build
poetry publish

# Build and publish recommender
cd mcp_pr_recommender
poetry build
poetry publish
```

---

**Note**: This checklist should be updated as the project evolves. Consider automation for repetitive tasks.

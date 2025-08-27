# GitHub Repository Migration Plan

> **Complete strategy for transitioning from multi-repository to monorepo structure**

**Created**: 2025-08-27
**Status**: Ready for Execution
**Related**: [Issue #14 - Monorepo Refactoring](https://github.com/manavgup/mcp_auto_pr/issues/14)

## 🎯 Migration Overview

### **Objective**
Safely transition from 4 separate repositories to a single monorepo while preserving history, handling dependencies, and minimizing disruption to users.

### **Current State Analysis**
```
┌─ Main Repository (manavgup/mcp_auto_pr)
│  ├─ 23 commits, master branch
│  ├─ 8 open issues (refactoring-related, now resolved)
│  ├─ 0 open PRs, 1 closed PR
│  └─ Active CI/CD with GitHub Actions
│
├─ Linked Repository (mcp_shared_lib)
│  ├─ 41 commits, v0.2.0 released
│  ├─ 1 open issue, 1 open PR
│  └─ Now consolidated into main repo
│
├─ Linked Repository (mcp_local_repo_analyzer)
│  ├─ 44 commits, v0.2.0 released
│  ├─ 3 open issues, 1 open PR
│  └─ Now consolidated into main repo
│
└─ Linked Repository (mcp_pr_recommender)
   ├─ 51 commits, v0.2.0 released
   ├─ No visible open issues/PRs
   └─ Now consolidated into main repo
```

### **Migration Scope**
- **4 repositories** to consolidate/archive
- **~12 open issues** to migrate/close/resolve
- **~3 open PRs** to resolve/migrate
- **CI/CD webhooks** to update
- **External documentation** to update
- **Community communication** required

## 📋 Pre-Migration Checklist

### ✅ **Validation Complete** (Already Done)
- [x] **All tests pass**: 311 tests passing, 72% coverage
- [x] **All linting passes**: Ruff, MyPy, pre-commit alignment
- [x] **Documentation updated**: All refactoring docs current
- [x] **Code quality verified**: 90% duplicate reduction achieved
- [x] **CI/CD working**: GitHub Actions configured and tested

### 🔍 **Pre-Migration Audit** (Execute Before Push)
```bash
# Final validation commands
make lint                    # Verify all linting passes
make test-fast              # Run full test suite
make pre-commit-run         # Check pre-commit alignment
git status --porcelain      # Review uncommitted changes
```

## 🚀 Migration Execution Plan

### **Phase 1: Repository Preparation** (30 minutes)

#### 1.1 Final Code Push to Main Repository
```bash
# Navigate to monorepo
cd /path/to/mcp_auto_pr

# Stage all changes
git add .

# Create comprehensive commit
git commit -m "feat: Complete monorepo refactoring

🎉 Major refactoring achievements:
- ✅ 90% duplicate code reduction (30→3 functions)
- ✅ 4,201 lines over-engineered code removed
- ✅ All linting issues fixed (66 MyPy + 20 Ruff)
- ✅ 311 tests passing with 72% coverage
- ✅ Pre-commit hooks aligned with CI
- ✅ Professional development workflow established

📦 Repository consolidation:
- mcp_shared_lib → src/shared/
- mcp_local_repo_analyzer → src/mcp_local_repo_analyzer/
- mcp_pr_recommender → src/mcp_pr_recommender/

🔧 Infrastructure improvements:
- Comprehensive CI/CD pipeline
- 98.9% docstring coverage
- HTML/XML coverage reporting
- Docker deployment ready

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin master
```

#### 1.2 Update Main Repository Documentation
```bash
# Update README with monorepo structure
# Add migration notices
# Update installation instructions
# Document new development workflow
```

### **Phase 2: Issue Migration** (1-2 hours)

#### 2.1 Audit and Categorize Issues

**Main Repository Issues** (8 total):
- **#14**: Epic: Monorepo Refactoring → ✅ **CLOSE** (Complete)
- **#12**: Standardize pre-commit → ✅ **CLOSE** (Complete)
- **#11**: Test coverage reporting → ✅ **CLOSE** (Complete)
- **#10**: Rename mcp_shared_lib → ✅ **CLOSE** (Complete)
- **#9**: Test MCP tools → ✅ **CLOSE** (Complete)
- **#8**: Clean uncommitted changes → ✅ **CLOSE** (Complete)
- **#7**: CLI module testing → ✅ **CLOSE** (Complete)
- **#5**: Shared Library Improvements → ✅ **CLOSE** (Complete)

**Linked Repository Issues** (~4 total):
- **mcp_shared_lib**: 1 issue → **EVALUATE** for migration/closure
- **mcp_local_repo_analyzer**: 3 issues → **EVALUATE** for migration/closure
- **mcp_pr_recommender**: 0 visible issues → **NO ACTION**

#### 2.2 Issue Resolution Strategy

**For Completed Issues** (Most of them):
```markdown
## ✅ Issue Resolved - Monorepo Migration Complete

This issue has been resolved as part of the monorepo refactoring completed on 2025-08-27.

### What Changed
- All code consolidated into single repository
- [Specific achievements for this issue]
- Full test coverage and linting implemented

### New Development Location
- **Main Repository**: https://github.com/manavgup/mcp_auto_pr
- **This Repository**: Archived (read-only)

Closing as complete. Future development continues in the monorepo.
```

**For Ongoing Issues** (If any):
```markdown
## 🔄 Issue Migrated to Monorepo

This issue has been migrated to the main monorepo:
➡️ **New Issue**: [Link to migrated issue]

### Migration Details
- Original issue preserved for reference
- Active development continues in monorepo
- This repository is now archived

Please follow the migrated issue for updates.
```

### **Phase 3: Pull Request Resolution** (30 minutes)

#### 3.1 Handle Open PRs

**Strategy for Each PR**:
1. **Evaluate relevance** to monorepo structure
2. **If relevant**: Create equivalent PR in main repo
3. **If obsolete**: Close with explanation
4. **Document decision** in PR comments

**PR Closure Template**:
```markdown
## 🔄 Repository Archived - Monorepo Migration

This repository has been consolidated into the main monorepo as part of our v0.2.0 refactoring.

### Status of This PR
- **[MERGED/OBSOLETE/MIGRATED]**: [Explanation]
- **Monorepo Location**: https://github.com/manavgup/mcp_auto_pr
- **Equivalent Change**: [Link if applicable]

### Next Steps
- Future development happens in the monorepo
- This repository is archived (read-only)
- Thank you for your contribution!

Closing due to repository consolidation.
```

### **Phase 4: Repository Archival** (45 minutes)

#### 4.1 Create Deprecation READMEs

**For Each Linked Repository**:
```bash
# Create ARCHIVE_NOTICE.md
cat > ARCHIVE_NOTICE.md << 'EOF'
# ⚠️ REPOSITORY ARCHIVED

This repository has been **consolidated** into the main monorepo and is now **read-only**.

## 🚀 New Location
**All development has moved to**: https://github.com/manavgup/mcp_auto_pr

## 📦 What Happened
As of 2025-08-27, we consolidated our multi-repository structure into a single monorepo:
- `mcp_shared_lib` → `src/shared/`
- `mcp_local_repo_analyzer` → `src/mcp_local_repo_analyzer/`
- `mcp_pr_recommender` → `src/mcp_pr_recommender/`

## ✨ Benefits of Monorepo
- **Unified development workflow**
- **Shared infrastructure and tooling**
- **90% reduction in duplicate code**
- **Improved test coverage and CI/CD**

## 🔄 Migration Guide

### For Users
```bash
# Old installation
pip install mcp-shared-lib mcp-local-repo-analyzer mcp-pr-recommender

# New installation
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr
poetry install
```

### For Developers
```bash
# Clone the monorepo
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr

# Install dependencies
make install-all

# Run tests
make test-all

# Start services
make serve-analyzer
make serve-recommender
```

## 📚 Documentation
- **Setup Guide**: [README.md](https://github.com/manavgup/mcp_auto_pr/blob/master/README.md)
- **Development Guide**: [docs/](https://github.com/manavgup/mcp_auto_pr/tree/master/docs)
- **API Reference**: [docs/api/](https://github.com/manavgup/mcp_auto_pr/tree/master/docs/api)

## 🐛 Issues and Support
- **Report Issues**: [GitHub Issues](https://github.com/manavgup/mcp_auto_pr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/manavgup/mcp_auto_pr/discussions)

---

Thank you for being part of our journey! 🙏

**The MCP Auto PR Team**
EOF

# Commit the notice
git add ARCHIVE_NOTICE.md
git commit -m "docs: Add repository archival notice

This repository has been consolidated into the main monorepo.
New development location: https://github.com/manavgup/mcp_auto_pr"
git push origin master
```

#### 4.2 Update Repository README

**Prepend to existing README**:
```markdown
# ⚠️ ARCHIVED: Development Moved to Monorepo

> **🚀 This repository is archived. Active development continues at:**
> **https://github.com/manavgup/mcp_auto_pr**

**Migration Date**: August 27, 2025
**Reason**: Consolidated into monorepo for better maintainability

[Continue with existing README content...]
```

#### 4.3 Archive Repositories on GitHub

**For Each Repository**:
1. Go to **Settings** → **General**
2. Scroll to **Danger Zone**
3. Click **Archive this repository**
4. Confirm archival

**Archive Order** (From least to most critical):
1. `mcp_shared_lib` (foundation library)
2. `mcp_pr_recommender` (ML service)
3. `mcp_local_repo_analyzer` (analysis service)

### **Phase 5: Infrastructure Updates** (30 minutes)

#### 5.1 Update CI/CD Webhooks

**Audit External Services**:
- **GitHub Actions**: ✅ Already configured in main repo
- **Docker Hub**: Update to point to main repo
- **Codecov**: Update repository configuration
- **Dependabot**: Verify configuration
- **External monitoring**: Update endpoints

#### 5.2 Update Documentation

**External Documentation to Update**:
- **PyPI package descriptions** (when publishing)
- **Docker Hub descriptions**
- **Personal/team documentation**
- **Blog posts or articles** (if any)

### **Phase 6: Community Communication** (30 minutes)

#### 6.1 GitHub Announcements

**Create GitHub Discussion** in main repository:
```markdown
# 🎉 Monorepo Migration Complete!

We've successfully consolidated our multi-repository structure into a single monorepo!

## What Changed
- **mcp_shared_lib**, **mcp_local_repo_analyzer**, and **mcp_pr_recommender** are now part of this monorepo
- **90% reduction in duplicate code**
- **Unified development workflow**
- **Improved CI/CD pipeline**
- **72% test coverage** with comprehensive reporting

## Benefits
- **Easier contribution**: One repo, one workflow
- **Faster development**: Shared infrastructure
- **Better testing**: Integrated test suite
- **Simpler installation**: Single source of truth

## Migration Guide
[Include installation and development instructions]

## Archived Repositories
The following repositories are now **read-only archives**:
- [mcp_shared_lib](https://github.com/manavgup/mcp_shared_lib)
- [mcp_local_repo_analyzer](https://github.com/manavgup/mcp_local_repo_analyzer)
- [mcp_pr_recommender](https://github.com/manavgup/mcp_pr_recommender)

Questions? Ask below! 👇
```

#### 6.2 Update Profile/Organization

**If applicable**:
- Update GitHub profile/organization description
- Pin the main repository
- Update bio or organization details

## 🔍 Post-Migration Validation

### **Immediate Verification** (Within 1 hour)

```bash
# Clone fresh copy to verify
git clone https://github.com/manavgup/mcp_auto_pr.git test-migration
cd test-migration

# Verify installation works
poetry install

# Verify tests pass
make test-fast

# Verify linting passes
make lint

# Verify services start
make serve-analyzer &
sleep 5
curl http://localhost:9070/health
kill %1

# Cleanup
cd ..
rm -rf test-migration
```

### **Monitor for Issues** (24-48 hours)

**Check for**:
- **Broken external links** pointing to archived repos
- **CI/CD failures** from webhook changes
- **User questions** about migration
- **Dependency issues** from external projects

### **Issue Response Template**

```markdown
Hi! Thanks for your question about the migration.

We've consolidated our repositories into a single monorepo for better maintainability.

**New location**: https://github.com/manavgup/mcp_auto_pr

**Quick fix**:
```bash
# Replace your old installation
pip uninstall mcp-shared-lib mcp-local-repo-analyzer mcp-pr-recommender

# Install from monorepo
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr && poetry install
```

Let me know if you need help with the migration!
```

## ⚠️ Risk Mitigation

### **Identified Risks & Solutions**

| Risk | Impact | Mitigation | Recovery |
|------|--------|------------|----------|
| **External dependencies break** | High | Archive (don't delete), provide 6-month notice | Temporarily unarchive if critical |
| **CI/CD webhooks fail** | Medium | Update before archiving, monitor alerts | Quick webhook updates |
| **Lost issue context** | Medium | Export important issues, migrate selectively | Issue history preserved in archives |
| **User confusion** | Low | Clear documentation, migration guides | Responsive support |

### **Rollback Plan** (Emergency)

**If critical issues arise**:
1. **Unarchive repositories** (GitHub Settings → Unarchive)
2. **Revert webhook changes** to point back to original repos
3. **Create emergency patches** in original repos if needed
4. **Communicate rollback** to users
5. **Analyze failure** and improve migration plan

**Recovery Time**: < 1 hour for emergency rollback

### **Monitoring Checklist**

**Week 1** (Daily checks):
- [ ] CI/CD pipelines working
- [ ] No broken external dependencies
- [ ] User questions addressed promptly
- [ ] GitHub Issues monitoring

**Week 2-4** (Weekly checks):
- [ ] Search engine indexing updated
- [ ] External documentation updated
- [ ] Community adoption of new structure
- [ ] Performance monitoring

**Month 2+** (Monthly checks):
- [ ] Archive repositories still accessible
- [ ] No critical dependencies on old structure
- [ ] User satisfaction with new structure

## 🎯 Success Metrics

### **Technical Success** ✅
- [ ] Main repository updated with monorepo code
- [ ] All tests pass in new structure
- [ ] CI/CD working without issues
- [ ] All linked repositories properly archived

### **Community Success** ✅
- [ ] All issues resolved/migrated appropriately
- [ ] Clear migration documentation available
- [ ] User questions addressed promptly
- [ ] No major disruption to existing workflows

### **Project Success** ✅
- [ ] Development velocity improved
- [ ] Code duplication eliminated (90% reduction maintained)
- [ ] Infrastructure simplified
- [ ] Long-term maintainability achieved

## 📊 Timeline Summary

| Phase | Duration | Tasks | Dependencies |
|-------|----------|-------|--------------|
| **1. Preparation** | 30 min | Code push, docs update | Code ready |
| **2. Issue Migration** | 1-2 hours | Close/migrate issues | Repository access |
| **3. PR Resolution** | 30 min | Handle open PRs | PR evaluation |
| **4. Repository Archival** | 45 min | Archive notices, README updates | Content prepared |
| **5. Infrastructure** | 30 min | Update webhooks, services | Service access |
| **6. Communication** | 30 min | Announcements, notifications | Community ready |

**Total Estimated Time**: 3-4 hours active work
**Monitoring Period**: 4 weeks post-migration

---

> **Next Steps**: Execute this plan phase by phase, validating each step before proceeding to the next.

*Related: [00-refactoring-status.md](./00-refactoring-status.md) | [Issue #14](https://github.com/manavgup/mcp_auto_pr/issues/14)*

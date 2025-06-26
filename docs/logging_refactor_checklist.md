# Logging Refactor Checklist (All MCP Repos)

Use this checklist to track the progress of standardizing logging across all MCP repos using the structured logging service from `mcp_shared_lib.utils.logging_utils`.

---

## 1. Preparation (All Repos)
- [ ] Ensure `logging_utils.py` in `mcp_shared_lib` is robust and well-documented
- [ ] Export the logging service in `__init__.py` for easy import
- [ ] Add logging policy to each repo's `CONTRIBUTING.md`

---

## 2. Refactor Steps by Repo

### A. mcp_shared_lib
- [ ] Identify all direct uses of `logging` (except in `logging_utils.py`)
- [ ] Replace with structured logger (`logging_service.get_logger(name)`)
- [ ] Remove direct `import logging` where possible
- [ ] Update tests for new logger
- [ ] Run and verify all tests

### B. mcp_local_repo_analyzer
- [ ] Identify all direct uses of `logging`
- [ ] Import and use structured logger
- [ ] Replace logger creation and log calls
- [ ] Remove direct `import logging`
- [ ] Run and verify all tests

### C. mcp_pr_recommender
- [ ] Identify all direct uses of `logging`
- [ ] Import and use structured logger
- [ ] Replace logger creation and log calls
- [ ] Remove direct `import logging`
- [ ] Run and verify all tests

### D. mcp_auto_pr
- [ ] Add logging policy to `CONTRIBUTING.md`
- [ ] Add example usage of structured logger in docs
- [ ] Review new code for compliance

---

## 3. Error Handling Standardization (All Repos)
- [ ] Use try/except blocks at logical boundaries
- [ ] Log errors with context using the structured logger
- [ ] Define and use custom exception classes
- [ ] Propagate meaningful error messages
- [ ] Test error handling and log output

---

## 4. Final Steps
- [ ] Code review for logging compliance
- [ ] Update documentation and READMEs
- [ ] Run all tests and verify logs
- [ ] Add CI check to prevent direct use of `import logging`

---

**How to use:**
- Check off each item as you complete it.
- Add notes or links to PRs/issues as needed.
- Update this file regularly to track progress. 
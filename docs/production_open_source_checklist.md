# MCP Auto PR: Production & Open Source Checklist

Use this checklist to track progress toward making `mcp_auto_pr` production-grade and open source ready. Check off each item as you complete it.

---

## 1. Project Structure
- [ ] `src/` directory for source code
- [ ] `tests/` directory for unit/integration tests
- [ ] `docs/` directory for documentation
- [ ] `README.md` with project overview, usage, and contribution guide
- [ ] `LICENSE` file (e.g., Apache-2.0)
- [ ] `.gitignore` for Python and project-specific files
- [ ] `pyproject.toml` or `setup.py` for packaging

## 2. Code Quality
- [ ] All code uses type annotations
- [ ] All public functions/classes have docstrings
- [ ] Linting with `black`, `isort`, and `flake8`/`ruff`
- [ ] Pre-commit hooks configured for formatting and linting

## 3. Logging
- [ ] All logging uses `mcp_shared_lib.utils.logging_utils`
- [ ] No direct use of the standard `logging` module

## 4. Testing
- [ ] >90% test coverage with `pytest`
- [ ] Tests for edge cases and error handling
- [ ] Test coverage measured and reported in CI

## 5. Documentation
- [ ] Complete `README.md` (overview, usage, configuration, contribution)
- [ ] API documentation generated with Sphinx or mkdocs
- [ ] All configuration options documented

## 6. Packaging
- [ ] Pip-installable (with `pyproject.toml` or `setup.py`)
- [ ] Versioned with semantic versioning
- [ ] All dependencies pinned in `requirements.txt`/`pyproject.toml`

## 7. Continuous Integration (CI/CD)
- [ ] GitHub Actions (or similar) for:
  - [ ] Linting
  - [ ] Type checking
  - [ ] Running tests
  - [ ] Building documentation
- [ ] CI status badge in `README.md`

## 8. Security
- [ ] Static analysis with `bandit`
- [ ] Dependency vulnerability checks with `safety` or `pip-audit`

## 9. Open Source Readiness
- [ ] LICENSE file present and correct
- [ ] `CODE_OF_CONDUCT.md`
- [ ] `CONTRIBUTING.md`
- [ ] `SECURITY.md`
- [ ] Issue and PR templates

## 10. Badges
- [ ] CI status badge
- [ ] Test coverage badge
- [ ] License badge
- [ ] PyPI badge (if published)

---

**How to use:**
- Check off each item as you complete it.
- Add notes or links to PRs/issues as needed.
- Update this file regularly to track progress. 
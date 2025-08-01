# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   🚀 MCP PR AUTOMATION WORKSPACE - Makefile
#   (Unified build & deployment for all MCP components)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Workspace configuration
WORKSPACE_ROOT := $(shell pwd)/..
SHARED_LIB := $(WORKSPACE_ROOT)/mcp_shared_lib
LOCAL_ANALYZER := $(WORKSPACE_ROOT)/mcp_local_repo_analyzer  
PR_RECOMMENDER := $(WORKSPACE_ROOT)/mcp_pr_recommender
AUTO_PR := $(WORKSPACE_ROOT)/mcp_auto_pr

# All repo directories
REPOS := $(SHARED_LIB) $(LOCAL_ANALYZER) $(PR_RECOMMENDER) $(AUTO_PR)

# Server ports (configurable)
ANALYZER_PORT := 8001
RECOMMENDER_PORT := 8002

# =============================================================================
# 📖 HELP
# =============================================================================
.PHONY: help
help:
	@echo "🚀 MCP PR AUTOMATION WORKSPACE"
	@echo "════════════════════════════════════════════════════"
	@echo "🏗️  SETUP & INSTALLATION"
	@echo "  setup-workspace    - Initialize entire workspace"
	@echo "  setup-auto         - Auto-clone all repos and setup"
	@echo "  test-setup         - Test if workspace is properly setup"
	@echo "  install-all        - Install all repo dependencies"
	@echo "  update-all         - Update all repo dependencies"
	@echo ""
	@echo "🧪 TESTING"
	@echo "  test-all           - Run tests across all repos"
	@echo "  test-shared        - Test shared library"
	@echo "  test-analyzer      - Test local repo analyzer"
	@echo "  test-recommender   - Test PR recommender"
	@echo "  test-integration   - Run workspace integration tests"
	@echo ""
	@echo "🔍 LINTING & QUALITY"
	@echo "  lint-all           - Run linting across all repos"
	@echo "  format-all         - Format code across all repos"
	@echo ""
	@echo "▶️  SERVICES"
	@echo "  serve-analyzer     - Start local repo analyzer (port $(ANALYZER_PORT))"
	@echo "  serve-recommender  - Start PR recommender (port $(RECOMMENDER_PORT))"
	@echo "  serve-all          - Start all MCP servers"
	@echo "  check-servers      - Check if servers can be started"
	@echo ""
	@echo "🧹 CLEANUP"
	@echo "  clean-all          - Clean all repos"
	@echo "  reset-workspace    - Reset entire workspace"

# =============================================================================
# 🏗️ SETUP & INSTALLATION
# =============================================================================
.PHONY: setup-workspace setup-auto test-setup install-all update-all check-repos

setup-auto:
	@echo "🚀 Auto-setting up MCP workspace..."
	@./scripts/setup-workspace.sh

test-setup:
	@echo "🧪 Testing workspace setup..."
	@./scripts/test-setup.sh

check-repos:
	@echo "🔍 Checking workspace structure..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "✅ Found: $$repo"; \
		else \
			echo "❌ Missing: $$repo"; \
		fi \
	done

setup-workspace: check-repos
	@echo "🏗️ Setting up MCP workspace..."
	@$(MAKE) install-all
	@echo "✅ Workspace setup complete!"

install-all:
	@echo "📦 Installing dependencies for all repos..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "Installing $$repo..."; \
			cd "$$repo" && poetry install || echo "❌ Failed to install $$repo"; \
		fi \
	done

update-all:
	@echo "⬆️ Updating dependencies for all repos..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "Updating $$repo..."; \
			cd "$$repo" && poetry update || echo "❌ Failed to update $$repo"; \
		fi \
	done

# =============================================================================
# 🧪 TESTING
# =============================================================================
.PHONY: test-all test-shared test-analyzer test-recommender test-integration

test-all:
	@echo "🧪 Running tests across all repos..."
	@$(MAKE) test-shared test-analyzer test-recommender

test-shared:
	@echo "🧪 Testing shared library..."
	@cd $(SHARED_LIB) && poetry run pytest tests/ -v || echo "❌ Shared lib tests failed"

test-analyzer:
	@echo "🧪 Testing local repo analyzer..."
	@cd $(LOCAL_ANALYZER) && poetry run pytest tests/ -v || echo "❌ Analyzer tests failed"

test-recommender:
	@echo "🧪 Testing PR recommender..."
	@cd $(PR_RECOMMENDER) && poetry run pytest tests/ -v || echo "❌ Recommender tests failed"

test-integration:
	@echo "🧪 Running workspace integration tests..."
	@# Add integration tests that span multiple repos
	@echo "🚧 Integration tests not yet implemented"

# =============================================================================
# 🔍 LINTING & QUALITY
# =============================================================================
.PHONY: lint-all format-all

lint-all:
	@echo "🔍 Running linting across all repos..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ] && [ -f "$$repo/Makefile" ]; then \
			echo "Linting $$repo..."; \
			cd "$$repo" && make lint || echo "❌ Linting failed for $$repo"; \
		fi \
	done

format-all:
	@echo "🎨 Formatting code across all repos..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "Formatting $$repo..."; \
			cd "$$repo" && poetry run black . && poetry run isort . || echo "❌ Formatting failed for $$repo"; \
		fi \
	done

# =============================================================================
# ▶️ SERVICES
# =============================================================================
.PHONY: serve-analyzer serve-recommender serve-all check-servers stop-servers

check-servers:
	@echo "🔍 Checking server entry points..."
	@echo "Analyzer:"
	@cd $(LOCAL_ANALYZER) && ls -la src/mcp_local_repo_analyzer/ | grep -E "(main\.py|__main__\.py|server\.py)" || echo "  No main files found"
	@echo "Recommender:"
	@cd $(PR_RECOMMENDER) && ls -la src/mcp_pr_recommender/ | grep -E "(main\.py|__main__\.py|server\.py)" || echo "  No main files found"
	@echo ""
	@echo "Checking for entry points in pyproject.toml:"
	@cd $(LOCAL_ANALYZER) && grep -A 5 "scripts\]" pyproject.toml 2>/dev/null || echo "  No scripts in analyzer"
	@cd $(PR_RECOMMENDER) && grep -A 5 "scripts\]" pyproject.toml 2>/dev/null || echo "  No scripts in recommender"

serve-analyzer:
	@echo "🚀 Starting local repo analyzer on port $(ANALYZER_PORT)..."
	@echo "Using CLI entry point: local-git-analyzer"
	@cd $(LOCAL_ANALYZER) && poetry run local-git-analyzer

serve-recommender:
	@echo "🚀 Starting PR recommender on port $(RECOMMENDER_PORT)..."
	@echo "Using CLI entry point: pr-recommender"
	@cd $(PR_RECOMMENDER) && poetry run pr-recommender

serve-all:
	@echo "🚀 Starting all MCP servers..."
	@echo "💡 This will start servers in background. Use 'make stop-servers' to stop them."
	@$(MAKE) serve-analyzer &
	@sleep 2
	@$(MAKE) serve-recommender &
	@echo "✅ All servers starting..."
	@echo "📋 Check status with: curl http://localhost:$(ANALYZER_PORT)/health"
	@echo "📋 Check status with: curl http://localhost:$(RECOMMENDER_PORT)/health"

stop-servers:
	@echo "🛑 Stopping MCP servers..."
	@pkill -f "mcp_local_repo_analyzer" || echo "Analyzer not running"
	@pkill -f "mcp_pr_recommender" || echo "Recommender not running"
	@echo "✅ Servers stopped"

# =============================================================================
# 🧹 CLEANUP
# =============================================================================
.PHONY: clean-all reset-workspace

clean-all:
	@echo "🧹 Cleaning all repos..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ] && [ -f "$$repo/Makefile" ]; then \
			echo "Cleaning $$repo..."; \
			cd "$$repo" && make clean || echo "❌ Clean failed for $$repo"; \
		fi \
	done

reset-workspace: clean-all
	@echo "🧹 Resetting entire workspace..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "Removing Poetry env for $$repo..."; \
			cd "$$repo" && poetry env remove --all 2>/dev/null || true; \
		fi \
	done
	@echo "✅ Workspace reset complete!"

# =============================================================================
# 🚀 DEPLOYMENT & PACKAGING
# =============================================================================
.PHONY: build-all package-all

build-all:
	@echo "🏗️ Building all packages..."
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "Building $$repo..."; \
			cd "$$repo" && poetry build || echo "❌ Build failed for $$repo"; \
		fi \
	done

package-all: build-all
	@echo "📦 Packaging complete!"
	@echo "💡 Built packages are in each repo's dist/ directory"
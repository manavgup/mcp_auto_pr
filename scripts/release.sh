#!/bin/bash
# =============================================================================
# MCP Workspace Release Script
# =============================================================================
#
# This script coordinates releases across all MCP workspace repositories:
# - mcp_shared_lib (foundation)
# - mcp_local_repo_analyzer
# - mcp_pr_recommender
#
# Usage:
#   ./scripts/release.sh [patch|minor|major|prerelease] [--dry-run]
#
# Examples:
#   ./scripts/release.sh patch           # Release patch versions
#   ./scripts/release.sh minor --dry-run # Preview minor version bumps
#   ./scripts/release.sh major           # Release major versions
#
# =============================================================================

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
readonly SHARED_LIB_DIR="$WORKSPACE_ROOT/../mcp_shared_lib"
readonly ANALYZER_DIR="$WORKSPACE_ROOT/../mcp_local_repo_analyzer"
readonly RECOMMENDER_DIR="$WORKSPACE_ROOT/../mcp_pr_recommender"

# Default values
VERSION_TYPE="patch"
DRY_RUN=false
VERBOSE=false

# Function to print colored output
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "INFO")  echo -e "${BLUE}[INFO]${NC}  [$timestamp] $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC}  [$timestamp] $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} [$timestamp] $message" >&2 ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} [$timestamp] $message" ;;
    esac
}

# Function to show usage
show_usage() {
    cat << EOF
MCP Workspace Release Script

USAGE:
    $0 [VERSION_TYPE] [OPTIONS]

VERSION_TYPE:
    patch       Patch release (x.y.Z) - bug fixes
    minor       Minor release (x.Y.z) - new features
    major       Major release (X.y.z) - breaking changes
    prerelease  Prerelease (x.y.z-alpha.N) - testing

OPTIONS:
    --dry-run   Show what would be done without making changes
    --verbose   Show detailed output
    --help      Show this help message

EXAMPLES:
    $0 patch                    # Release patch versions
    $0 minor --dry-run          # Preview minor version bumps
    $0 major --verbose          # Release major versions with detailed output

REPOSITORY ORDER:
    1. mcp_shared_lib (foundation dependency)
    2. mcp_local_repo_analyzer & mcp_pr_recommender (parallel)

EOF
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            patch|minor|major|prerelease)
                VERSION_TYPE="$1"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                log "ERROR" "Unknown argument: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to check if directory exists and is a git repository
validate_repository() {
    local repo_dir=$1
    local repo_name=$2

    if [[ ! -d "$repo_dir" ]]; then
        log "ERROR" "Repository directory not found: $repo_dir"
        return 1
    fi

    if [[ ! -d "$repo_dir/.git" ]]; then
        log "ERROR" "$repo_name is not a git repository: $repo_dir"
        return 1
    fi

    log "INFO" "✓ $repo_name repository found at $repo_dir"
    return 0
}

# Function to check if working directory is clean
check_working_directory() {
    local repo_dir=$1
    local repo_name=$2

    cd "$repo_dir"

    if [[ -n $(git status --porcelain) ]]; then
        log "WARN" "$repo_name has uncommitted changes:"
        git status --short
        echo
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "ERROR" "Aborted due to uncommitted changes"
            return 1
        fi
    else
        log "INFO" "✓ $repo_name working directory is clean"
    fi

    return 0
}

# Function to run tests for a repository
run_tests() {
    local repo_dir=$1
    local repo_name=$2

    log "INFO" "Running tests for $repo_name..."
    cd "$repo_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would run: make test"
        return 0
    fi

    if make test; then
        log "SUCCESS" "✓ $repo_name tests passed"
        return 0
    else
        log "ERROR" "✗ $repo_name tests failed"
        return 1
    fi
}

# Function to run quality checks for a repository
run_quality_checks() {
    local repo_dir=$1
    local repo_name=$2

    log "INFO" "Running quality checks for $repo_name..."
    cd "$repo_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would run: make quality-check"
        return 0
    fi

    if make quality-check; then
        log "SUCCESS" "✓ $repo_name quality checks passed"
        return 0
    else
        log "ERROR" "✗ $repo_name quality checks failed"
        return 1
    fi
}

# Function to get current version
get_current_version() {
    local repo_dir=$1

    cd "$repo_dir"
    poetry version --short
}

# Function to preview version bump
preview_version() {
    local repo_dir=$1
    local repo_name=$2

    cd "$repo_dir"
    local current_version=$(get_current_version "$repo_dir")

    if command -v poetry >/dev/null 2>&1; then
        local next_version=$(poetry run semantic-release version --print 2>/dev/null || echo "unknown")
        log "INFO" "$repo_name: $current_version → $next_version"
    else
        log "WARN" "$repo_name: Poetry not found, cannot preview version"
    fi
}

# Function to create release for a repository
create_release() {
    local repo_dir=$1
    local repo_name=$2

    log "INFO" "Creating $VERSION_TYPE release for $repo_name..."
    cd "$repo_dir"

    local current_version=$(get_current_version "$repo_dir")

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would create $VERSION_TYPE release for $repo_name"
        preview_version "$repo_dir" "$repo_name"
        return 0
    fi

    # Create the release using semantic-release
    local cmd="poetry run semantic-release version --$VERSION_TYPE --no-push"
    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbose"
    fi

    if eval "$cmd"; then
        local new_version=$(get_current_version "$repo_dir")
        log "SUCCESS" "✓ $repo_name released: $current_version → $new_version"
        return 0
    else
        log "ERROR" "✗ Failed to create release for $repo_name"
        return 1
    fi
}

# Function to push releases
push_releases() {
    local repo_dir=$1
    local repo_name=$2

    log "INFO" "Pushing release for $repo_name..."
    cd "$repo_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would push tags and commits for $repo_name"
        return 0
    fi

    if git push origin main --tags; then
        log "SUCCESS" "✓ $repo_name pushed successfully"
        return 0
    else
        log "ERROR" "✗ Failed to push $repo_name"
        return 1
    fi
}

# Function to create GitHub release
create_github_release() {
    local repo_dir=$1
    local repo_name=$2

    cd "$repo_dir"
    local version=$(get_current_version "$repo_dir")

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would create GitHub release v$version for $repo_name"
        return 0
    fi

    log "INFO" "Creating GitHub release v$version for $repo_name..."

    # Use semantic-release to create the GitHub release
    if poetry run semantic-release publish; then
        log "SUCCESS" "✓ GitHub release created for $repo_name v$version"
        return 0
    else
        log "WARN" "Could not create GitHub release for $repo_name (may need to be done manually)"
        return 0  # Don't fail the entire process
    fi
}

# Main release function
main() {
    log "INFO" "Starting MCP Workspace Release Process"
    log "INFO" "Version type: $VERSION_TYPE"
    log "INFO" "Dry run: $DRY_RUN"
    echo

    # Parse command line arguments
    parse_args "$@"

    # Validate all repositories exist
    log "INFO" "Validating repositories..."
    validate_repository "$SHARED_LIB_DIR" "mcp_shared_lib" || exit 1
    validate_repository "$ANALYZER_DIR" "mcp_local_repo_analyzer" || exit 1
    validate_repository "$RECOMMENDER_DIR" "mcp_pr_recommender" || exit 1
    echo

    # Check working directories are clean
    log "INFO" "Checking working directories..."
    check_working_directory "$SHARED_LIB_DIR" "mcp_shared_lib" || exit 1
    check_working_directory "$ANALYZER_DIR" "mcp_local_repo_analyzer" || exit 1
    check_working_directory "$RECOMMENDER_DIR" "mcp_pr_recommender" || exit 1
    echo

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN MODE - Previewing release changes..."
        echo

        log "INFO" "Version changes preview:"
        preview_version "$SHARED_LIB_DIR" "mcp_shared_lib"
        preview_version "$ANALYZER_DIR" "mcp_local_repo_analyzer"
        preview_version "$RECOMMENDER_DIR" "mcp_pr_recommender"
        echo

        log "INFO" "DRY RUN completed. Use without --dry-run to execute."
        exit 0
    fi

    # Run tests for all repositories
    log "INFO" "Running tests..."
    run_tests "$SHARED_LIB_DIR" "mcp_shared_lib" || exit 1
    run_tests "$ANALYZER_DIR" "mcp_local_repo_analyzer" || exit 1
    run_tests "$RECOMMENDER_DIR" "mcp_pr_recommender" || exit 1
    echo

    # Run quality checks for all repositories
    log "INFO" "Running quality checks..."
    run_quality_checks "$SHARED_LIB_DIR" "mcp_shared_lib" || exit 1
    run_quality_checks "$ANALYZER_DIR" "mcp_local_repo_analyzer" || exit 1
    run_quality_checks "$RECOMMENDER_DIR" "mcp_pr_recommender" || exit 1
    echo

    # Create releases in dependency order
    log "INFO" "Creating releases..."

    # Step 1: Release foundation library first
    create_release "$SHARED_LIB_DIR" "mcp_shared_lib" || exit 1

    # Step 2: Release analyzer and recommender (they can be parallel)
    create_release "$ANALYZER_DIR" "mcp_local_repo_analyzer" || exit 1
    create_release "$RECOMMENDER_DIR" "mcp_pr_recommender" || exit 1
    echo

    # Push all releases
    log "INFO" "Pushing releases..."
    push_releases "$SHARED_LIB_DIR" "mcp_shared_lib" || exit 1
    push_releases "$ANALYZER_DIR" "mcp_local_repo_analyzer" || exit 1
    push_releases "$RECOMMENDER_DIR" "mcp_pr_recommender" || exit 1
    echo

    # Create GitHub releases
    log "INFO" "Creating GitHub releases..."
    create_github_release "$SHARED_LIB_DIR" "mcp_shared_lib"
    create_github_release "$ANALYZER_DIR" "mcp_local_repo_analyzer"
    create_github_release "$RECOMMENDER_DIR" "mcp_pr_recommender"
    echo

    log "SUCCESS" "🎉 MCP Workspace release completed successfully!"
    log "INFO" "Next steps:"
    log "INFO" "  1. Check GitHub releases are created properly"
    log "INFO" "  2. Monitor CI/CD pipelines"
    log "INFO" "  3. Update documentation if needed"
    log "INFO" "  4. Consider publishing to PyPI when ready"
}

# Execute main function with all arguments
main "$@"

#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   🚀 MCP Auto PR - Workspace Configuration
#   Configuration file for workspace setup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Repository configuration
# Format: "local_name:github_owner/repo_name"
REPOS=(
    "mcp_shared_lib:manavgup/mcp_shared_lib"
    "mcp_local_repo_analyzer:manavgup/mcp_local_repo_analyzer"
    "mcp_pr_recommender:manavgup/mcp_pr_recommender"
)

# Default branch for each repository
# If a repo uses a different default branch, add it here
DEFAULT_BRANCHES=(
    "mcp_shared_lib:main"
    "mcp_local_repo_analyzer:main"
    "mcp_pr_recommender:main"
)

# Workspace settings
WORKSPACE_NAME="mcp_workspace"
WORKSPACE_FILE="mcp_workspace.code-workspace"

# Python settings
PYTHON_VERSION="3.11"
POETRY_VERSION="1.7.0"

# Git settings
GIT_REMOTE_HTTPS_PREFIX="https://github.com"
GIT_REMOTE_SSH_PREFIX="git@github.com"

# Output colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to get repository URL by name
get_repo_url() {
    local repo_name=$1
    for repo_info in "${REPOS[@]}"; do
        local name=$(echo "$repo_info" | cut -d: -f1)
        local url=$(echo "$repo_info" | cut -d: -f2)
        if [ "$name" = "$repo_name" ]; then
            echo "$url"
            return 0
        fi
    done
    return 1
}

# Function to get default branch by repository name
get_default_branch() {
    local repo_name=$1
    for branch_info in "${DEFAULT_BRANCHES[@]}"; do
        local name=$(echo "$branch_info" | cut -d: -f1)
        local branch=$(echo "$branch_info" | cut -d: -f2)
        if [ "$name" = "$repo_name" ]; then
            echo "$branch"
            return 0
        fi
    done
    echo "main"  # Default fallback
    return 0
}

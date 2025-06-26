#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   🚀 MCP Auto PR Workspace Setup Script
#   Automatically clones and sets up all required repositories
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e  # Exit on any error

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if git is available
check_git() {
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install git first."
        exit 1
    fi
}

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "This script must be run from within a git repository."
        exit 1
    fi
}

# Function to get the workspace root (parent directory of mcp_auto_pr)
get_workspace_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local repo_dir="$(dirname "$script_dir")"
    echo "$(dirname "$repo_dir")"
}

# Function to clone a repository
clone_repo() {
    local repo_name=$1
    local repo_url=$2
    local workspace_root=$3
    
    local repo_path="$workspace_root/$repo_name"
    local default_branch=$(get_default_branch "$repo_name")
    
    if [ -d "$repo_path" ]; then
        print_warning "Repository $repo_name already exists at $repo_path"
        print_status "Pulling latest changes..."
        cd "$repo_path"
        git pull origin "$default_branch" || print_warning "Failed to pull latest changes for $repo_name"
        cd - > /dev/null
    else
        print_status "Cloning $repo_name..."
        cd "$workspace_root"
        
        # Try HTTPS first, then SSH
        if git clone "$GIT_REMOTE_HTTPS_PREFIX/$repo_url.git" "$repo_name" 2>/dev/null; then
            print_success "Successfully cloned $repo_name via HTTPS"
        elif git clone "$GIT_REMOTE_SSH_PREFIX/$repo_url.git" "$repo_name" 2>/dev/null; then
            print_success "Successfully cloned $repo_name via SSH"
        else
            print_error "Failed to clone $repo_name. Please check your git configuration."
            print_status "You can manually clone it with:"
            print_status "  git clone $GIT_REMOTE_HTTPS_PREFIX/$repo_url.git $repo_name"
            print_status "  or"
            print_status "  git clone $GIT_REMOTE_SSH_PREFIX/$repo_url.git $repo_name"
            return 1
        fi
        
        cd - > /dev/null
    fi
}

# Function to setup Python environment
setup_python_env() {
    local workspace_root=$1
    
    print_status "Setting up Python environment..."
    
    # Check if poetry is available
    if ! command -v poetry &> /dev/null; then
        print_warning "Poetry is not installed. Installing dependencies manually..."
        return 0
    fi
    
    # Install dependencies for each repo
    for repo_info in "${REPOS[@]}"; do
        local repo_name=$(echo "$repo_info" | cut -d: -f1)
        local repo_path="$workspace_root/$repo_name"
        
        if [ -d "$repo_path" ] && [ -f "$repo_path/pyproject.toml" ]; then
            print_status "Installing dependencies for $repo_name..."
            cd "$repo_path"
            poetry install --no-interaction || print_warning "Failed to install dependencies for $repo_name"
            cd - > /dev/null
        fi
    done
}

# Function to create workspace file
create_workspace_file() {
    local workspace_root=$1
    
    print_status "Creating VSCode workspace file..."
    
    local workspace_file="$workspace_root/$WORKSPACE_FILE"
    
    cat > "$workspace_file" << EOF
{
    "folders": [
        {
            "name": "📁 workspace-root",
            "path": "."
        },
        {
            "name": "mcp_auto_pr",
            "path": "./mcp_auto_pr"
        },
EOF

    # Add each repository to the workspace
    for repo_info in "${REPOS[@]}"; do
        local repo_name=$(echo "$repo_info" | cut -d: -f1)
        cat >> "$workspace_file" << EOF
        {
            "name": "$repo_name",
            "path": "./$repo_name"
        },
EOF
    done

    # Remove the trailing comma from the last entry and close the folders array
    sed -i '' '$ s/,$//' "$workspace_file"
    
    cat >> "$workspace_file" << EOF
    ],
    "settings": {
        "python.defaultInterpreterPath": "./.venv/bin/python",
        "python.terminal.activateEnvironment": true,
        "python.analysis.extraPaths": [
            "./mcp_shared_lib/src",
            "./mcp_local_repo_analyzer/src",
            "./mcp_pr_recommender/src"
        ]
    },
    "extensions": {
        "recommendations": [
            "ms-python.python",
            "ms-python.pylint",
            "ms-python.black-formatter",
            "ms-python.isort"
        ]
    }
}
EOF
    
    print_success "Created workspace file at $workspace_file"
}

# Function to display next steps
show_next_steps() {
    local workspace_root=$1
    
    echo ""
    echo -e "${GREEN}🎉 Workspace setup complete!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Open the workspace in VSCode:"
    echo "   code $workspace_root/$WORKSPACE_FILE"
    echo ""
    echo "2. Or navigate to the workspace:"
    echo "   cd $workspace_root"
    echo ""
    echo "3. Run the setup command from mcp_auto_pr:"
    echo "   cd mcp_auto_pr && make setup-workspace"
    echo ""
    echo -e "${BLUE}Available repositories:${NC}"
    for repo_info in "${REPOS[@]}"; do
        local repo_name=$(echo "$repo_info" | cut -d: -f1)
        echo "  ✅ $repo_name"
    done
    echo "  ✅ mcp_auto_pr (this repository)"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo "  make help                    - Show all available commands"
    echo "  make setup-workspace         - Setup the entire workspace"
    echo "  make install-all             - Install all dependencies"
    echo "  make test-all                - Run all tests"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}🚀 MCP Auto PR Workspace Setup${NC}"
    echo "=================================="
    echo ""
    
    # Pre-flight checks
    check_git
    check_git_repo
    
    # Get workspace root
    local workspace_root=$(get_workspace_root)
    print_status "Workspace root: $workspace_root"
    
    # Clone repositories
    print_status "Cloning required repositories..."
    for repo_info in "${REPOS[@]}"; do
        local repo_name=$(echo "$repo_info" | cut -d: -f1)
        local repo_url=$(echo "$repo_info" | cut -d: -f2)
        
        clone_repo "$repo_name" "$repo_url" "$workspace_root"
    done
    
    # Setup Python environment
    setup_python_env "$workspace_root"
    
    # Create workspace file
    create_workspace_file "$workspace_root"
    
    # Show next steps
    show_next_steps "$workspace_root"
}

# Run main function
main "$@" 
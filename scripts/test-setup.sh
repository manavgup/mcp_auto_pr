#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   🚀 MCP Auto PR - Setup Test Script
#   Tests the workspace setup to ensure everything is working correctly
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

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

# Function to get the workspace root
get_workspace_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local repo_dir="$(dirname "$script_dir")"
    echo "$(dirname "$repo_dir")"
}

# Function to test repository setup
test_repositories() {
    local workspace_root=$1
    local all_good=true

    print_status "Testing repository setup..."

    # Test each repository
    for repo_info in "${REPOS[@]}"; do
        local repo_name=$(echo "$repo_info" | cut -d: -f1)
        local repo_path="$workspace_root/$repo_name"

        if [ -d "$repo_path" ]; then
            if [ -d "$repo_path/.git" ]; then
                print_success "✅ $repo_name - Found and is a git repository"
            else
                print_error "❌ $repo_name - Found but not a git repository"
                all_good=false
            fi
        else
            print_error "❌ $repo_name - Not found at $repo_path"
            all_good=false
        fi
    done

    # Test mcp_auto_pr itself
    local auto_pr_path="$workspace_root/mcp_auto_pr"
    if [ -d "$auto_pr_path" ] && [ -d "$auto_pr_path/.git" ]; then
        print_success "✅ mcp_auto_pr - Found and is a git repository"
    else
        print_error "❌ mcp_auto_pr - Not found or not a git repository"
        all_good=false
    fi

    return $([ "$all_good" = true ] && echo 0 || echo 1)
}

# Function to test workspace file
test_workspace_file() {
    local workspace_root=$1
    local workspace_file="$workspace_root/$WORKSPACE_FILE"

    print_status "Testing workspace file..."

    if [ -f "$workspace_file" ]; then
        print_success "✅ Workspace file found at $workspace_file"

        # Check if it's valid JSON
        if python3 -m json.tool "$workspace_file" > /dev/null 2>&1; then
            print_success "✅ Workspace file is valid JSON"
        else
            print_error "❌ Workspace file is not valid JSON"
            return 1
        fi
    else
        print_error "❌ Workspace file not found at $workspace_file"
        return 1
    fi

    return 0
}

# Function to test Python environments
test_python_envs() {
    local workspace_root=$1
    local all_good=true

    print_status "Testing Python environments..."

    # Check if poetry is available
    if ! command -v poetry &> /dev/null; then
        print_warning "⚠️  Poetry not found - skipping Python environment tests"
        return 0
    fi

    # Test each repository's Python setup
    for repo_info in "${REPOS[@]}"; do
        local repo_name=$(echo "$repo_info" | cut -d: -f1)
        local repo_path="$workspace_root/$repo_name"

        if [ -d "$repo_path" ] && [ -f "$repo_path/pyproject.toml" ]; then
            print_success "✅ $repo_name - Has pyproject.toml"

            # Check if virtual environment exists
            if [ -d "$repo_path/.venv" ]; then
                print_success "✅ $repo_name - Has virtual environment"
            else
                print_warning "⚠️  $repo_name - No virtual environment found (run 'poetry install')"
            fi
        else
            print_warning "⚠️  $repo_name - No pyproject.toml found"
        fi
    done

    return 0
}

# Function to test git remotes
test_git_remotes() {
    local workspace_root=$1
    local all_good=true

    print_status "Testing git remotes..."

    # Test each repository's git remote
    for repo_info in "${REPOS[@]}"; do
        local repo_name=$(echo "$repo_info" | cut -d: -f1)
        local expected_url=$(echo "$repo_info" | cut -d: -f2)
        local repo_path="$workspace_root/$repo_name"

        if [ -d "$repo_path/.git" ]; then
            cd "$repo_path"
            local remote_url=$(git remote get-url origin 2>/dev/null || echo "")
            cd - > /dev/null

            if [[ "$remote_url" == *"$expected_url"* ]]; then
                print_success "✅ $repo_name - Remote URL matches expected"
            else
                print_warning "⚠️  $repo_name - Remote URL mismatch: $remote_url"
            fi
        fi
    done

    return 0
}

# Main test function
main() {
    echo -e "${BLUE}🧪 MCP Auto PR - Setup Test${NC}"
    echo "================================"
    echo ""

    local workspace_root=$(get_workspace_root)
    print_status "Workspace root: $workspace_root"
    echo ""

    local overall_success=true

    # Run all tests
    test_repositories "$workspace_root" || overall_success=false
    echo ""

    test_workspace_file "$workspace_root" || overall_success=false
    echo ""

    test_python_envs "$workspace_root"
    echo ""

    test_git_remotes "$workspace_root"
    echo ""

    # Summary
    if [ "$overall_success" = true ]; then
        echo -e "${GREEN}🎉 All critical tests passed!${NC}"
        echo "Your workspace is ready to use."
        echo ""
        echo "Next steps:"
        echo "  code $workspace_root/$WORKSPACE_FILE"
        echo "  cd mcp_auto_pr && make help"
    else
        echo -e "${RED}❌ Some tests failed.${NC}"
        echo "Please check the errors above and run the setup script again:"
        echo "  ./scripts/setup-workspace.sh"
    fi
}

# Run main function
main "$@"

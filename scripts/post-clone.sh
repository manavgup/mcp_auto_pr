#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   🚀 MCP Auto PR - Post Clone Setup
#   Run this after cloning mcp_auto_pr to set up the complete workspace
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "🚀 MCP Auto PR - Post Clone Setup"
echo "================================="
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -f "Makefile" ]; then
    echo "❌ Error: This script must be run from the mcp_auto_pr directory"
    echo "   Please navigate to the mcp_auto_pr directory and try again"
    exit 1
fi

# Run the main setup script
echo "Setting up complete workspace..."
./scripts/setup-workspace.sh

echo ""
echo "✅ Post-clone setup complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Open the workspace: code ../mcp_workspace.code-workspace"
echo "   2. Or run: make help (from this directory)"
echo "" 
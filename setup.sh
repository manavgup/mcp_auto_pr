#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   🚀 MCP Auto PR - Quick Setup Script
#   Run this script immediately after cloning mcp_auto_pr
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "🚀 MCP Auto PR - Quick Setup"
echo "============================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the main setup script
echo "Running workspace setup..."
"$SCRIPT_DIR/scripts/setup-workspace.sh"

echo ""
echo "✅ Setup complete! Check the output above for next steps."

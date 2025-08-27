#!/bin/bash

# Archive Linked Repositories Script
# This script adds archive notices to linked repositories and archives them on GitHub

set -e

echo "🔄 Starting repository archival process..."
echo "================================================"

# Archive notice to prepend to README
ARCHIVE_NOTICE='# ⚠️ ARCHIVED: Development Moved to Monorepo

> **🚀 This repository is archived. Active development continues at:**
> **https://github.com/manavgup/mcp_auto_pr**

**Migration Date**: August 27, 2025
**Reason**: Consolidated into monorepo for better maintainability

## 🔄 Migration Guide

### For Users
```bash
# New installation method
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr
poetry install
```

### For Developers
```bash
# Development setup
git clone https://github.com/manavgup/mcp_auto_pr.git
cd mcp_auto_pr
make install-all
make test-all
```

**See full migration guide**: [Migration Documentation](https://github.com/manavgup/mcp_auto_pr/blob/master/docs/refactor/github-migration-plan.md)

---

**[ORIGINAL README BELOW]**

'

# Function to update repository
update_repo() {
    local REPO_NAME=$1
    local REPO_URL="https://github.com/manavgup/$REPO_NAME.git"

    echo ""
    echo "📦 Processing $REPO_NAME..."
    echo "--------------------------------"

    # Clone repo to temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    echo "  📥 Cloning repository..."
    git clone "$REPO_URL" "$REPO_NAME" 2>/dev/null || {
        echo "  ❌ Failed to clone $REPO_NAME"
        rm -rf "$TEMP_DIR"
        return 1
    }

    cd "$REPO_NAME"

    # Update README
    echo "  📝 Updating README.md..."
    if [ -f "README.md" ]; then
        # Create backup
        cp README.md README.md.bak

        # Prepend archive notice
        echo "$ARCHIVE_NOTICE" > README_NEW.md
        cat README.md >> README_NEW.md
        mv README_NEW.md README.md

        # Commit changes
        git add README.md
        git commit -m "Archive repository: Migration to monorepo

This repository has been archived and consolidated into the main monorepo.
Active development continues at: https://github.com/manavgup/mcp_auto_pr

Migration Date: August 27, 2025"

        # Push changes
        echo "  📤 Pushing changes..."
        git push origin main 2>/dev/null || git push origin master 2>/dev/null || {
            echo "  ⚠️  Could not push changes. You may need to manually push to $REPO_NAME"
        }

        echo "  ✅ README updated successfully"
    else
        echo "  ⚠️  No README.md found"
    fi

    # Archive repository using GitHub CLI
    echo "  🔒 Archiving repository on GitHub..."
    gh repo archive "manavgup/$REPO_NAME" --yes || {
        echo "  ⚠️  Could not archive via CLI. Please archive manually in GitHub settings."
    }

    # Clean up
    cd /
    rm -rf "$TEMP_DIR"

    echo "  ✅ $REPO_NAME processing complete"
}

# Process each repository
echo ""
echo "🚀 Processing linked repositories..."
echo ""

update_repo "mcp_shared_lib"
update_repo "mcp_local_repo_analyzer"
update_repo "mcp_pr_recommender"

echo ""
echo "================================================"
echo "✅ Repository archival process complete!"
echo ""
echo "📋 Summary:"
echo "  - Archive notices added to README files"
echo "  - Repositories marked as archived on GitHub"
echo "  - Migration guide provided in each repository"
echo ""
echo "🎯 Next Steps:"
echo "  1. Verify archive status on GitHub"
echo "  2. Update any external documentation"
echo "  3. Notify team members of migration"
echo ""

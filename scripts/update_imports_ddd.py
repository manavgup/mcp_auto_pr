#!/usr/bin/env python3
"""Update imports for DDD bounded context structure."""

import re
from pathlib import Path

# DDD Import mappings
DDD_IMPORT_MAPPINGS = [
    # Analyzer bounded context - internal imports
    (r"from core\.models\.git", "from mcp_local_repo_analyzer.models"),
    (r"from core\.models\.analysis", "from mcp_local_repo_analyzer.models"),
    (r"from core\.services\.git", "from mcp_local_repo_analyzer.services"),
    (r"from core\.config\.analyzer", "from mcp_local_repo_analyzer.config"),
    # Recommender bounded context - internal imports
    (r"from core\.models\.pr", "from mcp_pr_recommender.models"),
    (r"from core\.services\.pr", "from mcp_pr_recommender.services"),
    (r"from core\.config\.recommender", "from mcp_pr_recommender.config"),
    (r"from mcp_pr_recommender\.prompts", "from mcp_pr_recommender.prompts.semantic"),
    # Infrastructure imports (shared)
    (r"from shared\.base\.server", "from shared.base.server"),
    (r"from shared\.base\.cli", "from shared.base.cli"),
    (r"from shared\.base\.tool", "from shared.base.tool"),
    (r"from core\.config\.base", "from shared.base.config"),
    # Server imports within bounded context
    (r"from mcp_local_repo_analyzer\.server", "from mcp_local_repo_analyzer.server"),
    (r"from mcp_pr_recommender\.server", "from mcp_pr_recommender.server"),
    (r"from servers\.analyzer\.server", "from mcp_local_repo_analyzer.server"),
    (r"from servers\.recommender\.server", "from mcp_pr_recommender.server"),
    # Tool imports within bounded context
    (r"from mcp_local_repo_analyzer\.tools", "from mcp_local_repo_analyzer.tools"),
    (r"from mcp_pr_recommender\.tools", "from mcp_pr_recommender.tools"),
    (r"from servers\.analyzer\.tools", "from mcp_local_repo_analyzer.tools"),
    (r"from servers\.recommender\.tools", "from mcp_pr_recommender.tools"),
    # Clean up old core imports
    (r"from core\.models import", "# REMOVED: from core.models import"),
    (r"from core\.services import", "# REMOVED: from core.services import"),
    # Infrastructure utilities
    (r"from shared\.utils\.logging", "from shared.utils.logging"),
]


def update_file_imports(file_path: Path, mappings: list) -> bool:
    """Update imports in a single file."""
    try:
        with open(file_path) as f:
            content = f.read()

        original_content = content

        for old_pattern, new_import in mappings:
            content = re.sub(old_pattern, new_import, content)

        if content != original_content:
            with open(file_path, "w") as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def update_all_imports_ddd(src_dir: str) -> None:
    """Update all imports for DDD structure."""
    src_path = Path(src_dir)
    updated_files = []

    # Target directories for DDD
    target_dirs = ["mcp_local_repo_analyzer", "mcp_pr_recommender", "shared"]

    for target_dir in target_dirs:
        target_path = src_path / target_dir
        if not target_path.exists():
            print(f"⚠️  Skipping {target_dir} - does not exist")
            continue

        print(f"🔄 Processing {target_dir}...")

        # Find all Python files in the target directory
        for py_file in target_path.glob("**/*.py"):
            # Skip __pycache__ and test files
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue

            if update_file_imports(py_file, DDD_IMPORT_MAPPINGS):
                updated_files.append(py_file)
                print(f"  ✅ Updated: {py_file.relative_to(src_path)}")

    print(f"\n📊 Summary: Updated {len(updated_files)} files")

    if updated_files:
        print("\nUpdated files:")
        for f in sorted(updated_files):
            print(f"  - {f.relative_to(src_path)}")


def main():
    """Main entry point."""
    src_dir = "/Users/mg/mg-work/manav/work/ai-experiments/mcp_pr_workspace/mcp_auto_pr/src"

    print("🏗️  Updating imports for DDD bounded context structure...")
    print(f"📁 Base directory: {src_dir}\n")

    update_all_imports_ddd(src_dir)

    print("\n✅ DDD import update complete!")
    print("\n📋 Next steps:")
    print("  1. Remove old 'core' directory")
    print("  2. Remove old 'servers' directory")
    print("  3. Update entry points in pyproject.toml")
    print("  4. Test the new structure")


if __name__ == "__main__":
    main()

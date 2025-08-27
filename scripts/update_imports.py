#!/usr/bin/env python3
"""Script to update imports after folder restructuring."""

import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = [
    # Models
    (r"from shared\.models\.git", "from core.models.git"),
    (r"from shared\.models\.analysis", "from core.models.analysis"),
    (r"from shared\.models\.base", "from core.models.base"),
    (r"from shared\.models import", "from core.models import"),
    (r"from mcp_pr_recommender\.models\.pr", "from core.models.pr"),
    # Services
    (r"from shared\.services\.git", "from core.services.git"),
    (r"from shared\.services import GitClient", "from core.services import GitClient"),
    (r"from mcp_local_repo_analyzer\.services\.git", "from core.services.git"),
    (r"from mcp_pr_recommender\.services", "from core.services.pr"),
    # Config
    (r"from shared\.config\.base", "from core.config.base"),
    (r"from shared\.config\.git_analyzer", "from core.config.analyzer"),
    (r"from shared\.config\.pr_recommender", "from core.config.recommender"),
    (r"from mcp_pr_recommender\.config", "from core.config.recommender"),
    # Base classes
    (r"from shared\.server\.base_server", "from shared.base.server"),
    (r"from shared\.cli\.base_cli", "from shared.base.cli"),
    (r"from shared\.tools\.base", "from shared.base.tool"),
    (r"from shared\.cli import BaseMCPCLI", "from shared.base import BaseMCPCLI"),
    (r"from shared\.server import BaseMCPServer", "from shared.base import BaseMCPServer"),
    # Utils
    (r"from shared\.utils import logging_service", "from shared.utils.logging import logging_service"),
    (r"from shared\.utils\.logging_utils", "from shared.utils.logging"),
    (r"from shared\.utils\.file_utils", "from shared.utils.file"),
    (r"from shared\.utils\.git_utils", "from shared.utils.git"),
    # Server-specific
    (r"from mcp_local_repo_analyzer\.server", "from servers.analyzer.server"),
    (r"from mcp_pr_recommender\.server", "from servers.recommender.server"),
    (r"from mcp_local_repo_analyzer\.tools", "from servers.analyzer.tools"),
    (r"from mcp_pr_recommender\.tools", "from servers.recommender.tools"),
    (r"from mcp_pr_recommender\.prompts", "from servers.recommender.prompts.semantic"),
]


def update_file(file_path: Path, mappings: list[tuple[str, str]]) -> bool:
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


def update_all_imports(base_dir: str) -> None:
    """Update imports in all Python files."""
    base_path = Path(base_dir)
    updated_files = []

    # Find all Python files
    for py_file in base_path.glob("**/*.py"):
        # Skip __pycache__ and other unwanted directories
        if "__pycache__" in str(py_file):
            continue

        if update_file(py_file, IMPORT_MAPPINGS):
            updated_files.append(py_file)
            print(f"✅ Updated: {py_file.relative_to(base_path)}")

    print(f"\n📊 Summary: Updated {len(updated_files)} files")

    if updated_files:
        print("\nUpdated files:")
        for f in sorted(updated_files):
            print(f"  - {f.relative_to(base_path)}")


def main():
    """Main entry point."""
    src_dir = "/Users/mg/mg-work/manav/work/ai-experiments/mcp_pr_workspace/mcp_auto_pr/src"

    print("🔄 Updating imports after folder restructuring...")
    print(f"📁 Base directory: {src_dir}\n")

    update_all_imports(src_dir)

    print("\n✅ Import update complete!")
    print("\n⚠️  Note: Some imports may need manual review, especially:")
    print("  - Relative imports within modules")
    print("  - Circular import issues")
    print("  - Test file imports")


if __name__ == "__main__":
    main()

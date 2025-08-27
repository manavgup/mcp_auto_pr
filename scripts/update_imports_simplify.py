#!/usr/bin/env python3
"""Update import statements to remove nested .analyzer and .recommender paths."""

import re
from pathlib import Path


def update_imports_in_file(file_path: Path) -> bool:
    """Update import statements in a single file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Update mcp_local_repo_analyzer.analyzer imports
        content = re.sub(
            r"from mcp_local_repo_analyzer\.analyzer\.",
            "from mcp_local_repo_analyzer.",
            content,
        )
        content = re.sub(
            r"import mcp_local_repo_analyzer\.analyzer\.",
            "import mcp_local_repo_analyzer.",
            content,
        )

        # Update mcp_pr_recommender.recommender imports
        content = re.sub(
            r"from mcp_pr_recommender\.recommender\.",
            "from mcp_pr_recommender.",
            content,
        )
        content = re.sub(
            r"import mcp_pr_recommender\.recommender\.",
            "import mcp_pr_recommender.",
            content,
        )

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to update all Python files."""
    root_dir = Path(__file__).parent.parent
    src_dir = root_dir / "src"
    tests_dir = root_dir / "tests"

    updated_files = 0

    # Update files in src directory
    for py_file in src_dir.rglob("*.py"):
        if update_imports_in_file(py_file):
            updated_files += 1

    # Update files in tests directory
    for py_file in tests_dir.rglob("*.py"):
        if update_imports_in_file(py_file):
            updated_files += 1

    # Update scripts directory
    scripts_dir = root_dir / "scripts"
    for py_file in scripts_dir.rglob("*.py"):
        if update_imports_in_file(py_file):
            updated_files += 1

    print(f"\nTotal files updated: {updated_files}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Debug test for git line count issue that pytest can discover and run.
Save this as: mcp_local_repo_analyzer/tests/integration/test_git_line_count.py
"""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_debug_git_line_counts():
    """Debug test to isolate the line count calculation issue."""

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        print(f"\n=== Working in: {repo_path} ===")

        # Set up git repository exactly like the failing test
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
        )

        # Create and commit initial file
        test_file = repo_path / "test_file.py"
        test_file.write_text("print('Hello, world!')\n")

        subprocess.run(["git", "add", "test_file.py"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        # Modify and stage the file (exactly like the failing test)
        test_file.write_text("print('Hello, world!')\nprint('New line')\n")
        subprocess.run(["git", "add", "test_file.py"], cwd=repo_path, check=True)

        # Test git commands manually first
        print("\n=== Manual Git Commands ===")

        # Check status
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        print(f"git status --porcelain: '{result.stdout.strip()}'")

        # Check working directory diff (should be empty since file is staged)
        result = subprocess.run(["git", "diff", "--numstat"], cwd=repo_path, capture_output=True, text=True)
        print(f"git diff --numstat: '{result.stdout.strip()}'")

        # Check staged diff (should show the changes)
        result = subprocess.run(
            ["git", "diff", "--cached", "--numstat"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        print(f"git diff --cached --numstat: '{result.stdout.strip()}'")
        staged_numstat = result.stdout.strip()

        # Verify the staged diff shows the addition
        assert staged_numstat, "Staged diff should not be empty"
        assert "1\t0\ttest_file.py" in staged_numstat, f"Expected '1\\t0\\ttest_file.py' but got '{staged_numstat}'"

        # Check specific file status
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", "test_file.py"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        print(f"git status --porcelain -- test_file.py: '{result.stdout.strip()}'")
        file_status = result.stdout.strip()

        # Parse the status line
        assert file_status, "File status should not be empty"
        print(f"\nParsing status line: '{file_status}'")
        print(f"Length: {len(file_status)}")

        if len(file_status) >= 2:
            index_status = file_status[0] if file_status[0] != " " else None
            working_status = file_status[1] if file_status[1] != " " else None
            filename = file_status[3:] if len(file_status) > 3 else ""

            print(f"Index status: '{index_status}'")
            print(f"Working status: '{working_status}'")
            print(f"Filename: '{filename}'")

            # Verify parsing
            assert index_status == "M", f"Expected index status 'M' but got '{index_status}'"
            assert working_status in [
                None,
                " ",
            ], f"Expected no working status but got '{working_status}'"
            assert filename == "test_file.py", f"Expected 'test_file.py' but got '{filename}'"

            is_staged = bool(index_status) and index_status != "?"
            print(f"Is staged: {is_staged}")
            assert is_staged, "File should be detected as staged"

        # Now test our GitClient implementation
        print("\n=== Testing GitClient Implementation ===")

        try:
            from mcp_local_repo_analyzer.config import GitAnalyzerSettings
            from mcp_local_repo_analyzer.services.client import GitClient

            settings = GitAnalyzerSettings()
            git_client = GitClient(settings)

            # Test get_status
            status_result = await git_client.get_status(repo_path)
            print(f"GitClient.get_status(): {status_result}")

            files = status_result.get("files", [])
            assert len(files) == 1, f"Expected 1 file but got {len(files)}"

            file_info = files[0]
            assert file_info["filename"] == "test_file.py", f"Expected 'test_file.py' but got '{file_info['filename']}'"
            assert file_info["index_status"] == "M", f"Expected index status 'M' but got '{file_info['index_status']}'"

            # Test get_diff_stats with different parameters
            for staged_param in [True, False, None]:
                try:
                    diff_stats = await git_client.get_diff_stats(repo_path, "test_file.py", staged=staged_param)
                    print(f"GitClient.get_diff_stats(staged={staged_param}): {diff_stats}")

                    if staged_param in [True, None]:  # Should work for staged files
                        assert (
                            diff_stats["lines_added"] == 1
                        ), f"Expected 1 line added but got {diff_stats['lines_added']} with staged={staged_param}"
                        assert (
                            diff_stats["lines_deleted"] == 0
                        ), f"Expected 0 lines deleted but got {diff_stats['lines_deleted']} with staged={staged_param}"

                except Exception as e:
                    print(f"GitClient.get_diff_stats(staged={staged_param}) failed: {e}")
                    if staged_param in [True, None]:  # These should not fail
                        raise

            print("\n=== Testing ChangeDetector ===")

            from mcp_local_repo_analyzer.models.repository import LocalRepository
            from mcp_local_repo_analyzer.services.git.change_detector import ChangeDetector

            change_detector = ChangeDetector(git_client)
            repo_model = LocalRepository(
                path=repo_path,
                name="test_repo",
                current_branch="main",
                head_commit="test",
            )

            # This is the method that should populate line counts correctly
            working_changes = await change_detector.detect_working_directory_changes(repo_model)

            print(f"Working directory changes: {working_changes}")

            print("\n=== All tests passed! ===")

        except ImportError as e:
            pytest.skip(f"Could not import required modules: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_simple_git_commands():
    """Simple test to verify git commands work as expected."""

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)

        # Initialize repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True)

        # Create file
        (repo_path / "test.txt").write_text("line1\n")
        subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True)

        # Modify file
        (repo_path / "test.txt").write_text("line1\nline2\n")
        subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True)

        # Check staged diff
        result = subprocess.run(
            ["git", "diff", "--cached", "--numstat"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()

        print(f"Git diff output: '{output}'")
        assert "1\t0\ttest.txt" in output, f"Expected '1\\t0\\ttest.txt' but got '{output}'"

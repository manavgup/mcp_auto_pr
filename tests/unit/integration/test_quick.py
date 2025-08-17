import json

import pytest
from fastmcp import Client

from mcp_local_repo_analyzer.main import create_server, register_tools


# Helper function for extracting data from CallToolResult
def _extract_tool_data(raw_result):
    """Extracts the structured content from a CallToolResult object."""
    # The CallToolResult import is removed because it causes ImportError
    # We assume raw_result is already the structured content or dict
    if (
        isinstance(raw_result, list)
        and len(raw_result) > 0
        and hasattr(raw_result[0], "text")
    ):
        try:
            import json

            return json.loads(raw_result[0].text)
        except Exception:
            return raw_result[0].text
    elif hasattr(raw_result, "structured_content") and raw_result.structured_content:
        return raw_result.structured_content
    elif (
        hasattr(raw_result, "content")
        and raw_result.content
        and isinstance(raw_result.content[0].text, str)
    ):
        try:
            import json

            return json.loads(raw_result.content[0].text)
        except Exception:
            return raw_result.content[0].text
    elif hasattr(raw_result, "data"):
        return raw_result.data
    return raw_result


def print_result(result):
    """Print tool result in a readable format."""
    if isinstance(result, list) and len(result) > 0:
        content = result[0]
        if hasattr(content, "text"):
            try:
                data = json.loads(content.text)
                print_dict(data, indent=2)
            except Exception:
                print(content.text)
        else:
            print(content)
    else:
        print_dict(result, indent=2)


def print_dict(data, indent=0):
    """Pretty print dictionary data."""
    if isinstance(data, dict):
        if "error" in data:
            print(f"{'  ' * indent}❌ Error: {data['error']}")
            return

        for key, value in data.items():
            if key in [
                "summary",
                "has_outstanding_work",
                "total_outstanding_changes",
                "health_score",
                "ready_to_push",
            ]:
                if key == "summary" and isinstance(value, str):
                    print(f"{'  ' * indent}📋 {key}: {value}")
                elif key == "has_outstanding_work":
                    status = "📝 Yes" if value else "✅ No"
                    print(f"{'  ' * indent}🔄 Outstanding work: {status}")
                elif key == "total_outstanding_changes":
                    print(f"{'  ' * indent}📊 Total changes: {value}")
                elif key == "health_score":
                    print(f"{'  ' * indent}💚 Health score: {value}/100")
                elif key == "ready_to_push":
                    status = "✅ Ready" if value else "⏳ Not ready"
                    print(f"{'  ' * indent}🚀 Push status: {status}")
                else:
                    print(f"{'  ' * indent}{key}: {value}")
            elif key == "recommendations" and isinstance(value, list):
                if value:
                    print(f"{'  ' * indent}🔧 Recommendations:")
                    for rec in value[:5]:
                        if rec:
                            print(f"{'  ' * (indent+1)}• {rec}")
            elif isinstance(value, dict):
                print(f"{'  ' * indent}{key}:")
                print_dict(value, indent + 1)
            elif isinstance(value, list) and key not in [
                "recommendations",
                "files_affected",
                "potential_conflict_files",
                "high_risk_files",
                "factors",
                "large_changes",
                "warnings",
                "errors",
                "action_plan",
            ]:
                print(f"{'  ' * indent}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        print_dict(item, indent + 1)
                    else:
                        print(f"{'  ' * (indent + 1)}- {item}")
            else:
                print(f"{'  ' * indent}{key}: {value}")
    else:
        print(f"{'  ' * indent}{data}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyze_repo_with_unstaged_changes(tmp_path):
    """
    Tests the scenario where a file is modified but not staged.
    Focuses on analyze_working_directory and get_outstanding_summary.
    """
    import subprocess

    # --- Setup: Create a repository with unstaged changes ---
    repo_path = tmp_path / "repo_unstaged"
    repo_path.mkdir()

    test_file = repo_path / "test_file.py"
    test_file.write_text("print('Hello, world!')\n")

    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "test_file.py"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

    # Modify the file, but DON'T STAGE IT
    test_file.write_text("print('Hello, world!')\nprint('New line')\n")

    # --- Arrange: Create and configure FastMCP server and client ---
    server, services = create_server()
    server.git_client = services["git_client"]
    server.change_detector = services["change_detector"]
    server.diff_analyzer = services["diff_analyzer"]
    server.status_tracker = services["status_tracker"]
    register_tools(server, services)
    client = Client(server)

    async with client:
        print("\n" + "=" * 80)
        print(f"RUNNING TEST: UNSTAGED CHANGES SCENARIO ({repo_path})")
        print("=" * 80)

        # --- Act & Assert: Test Outstanding Summary ---
        print("\n📊 Outstanding Summary (Unstaged):")
        raw_summary_result = await client.call_tool(
            "get_outstanding_summary",
            {"repository_path": str(repo_path), "detailed": True},
        )
        summary_data = _extract_tool_data(raw_summary_result)
        print_result(summary_data)
        assert isinstance(summary_data, dict)
        assert summary_data.get("has_outstanding_work") is True
        assert summary_data["quick_stats"]["working_directory_changes"] == 1
        assert (
            summary_data["quick_stats"]["staged_changes"] == 0
        )  # Key assertion for unstaged
        assert "uncommitted changes" in summary_data["summary"].lower()
        print("✅ Outstanding Summary check passed.")

        # --- Act & Assert: Test Working Directory Changes ---
        print("\n📝 Working Directory Changes (Unstaged):")
        raw_wd_result = await client.call_tool(
            "analyze_working_directory",
            {"repository_path": str(repo_path), "include_diffs": False},
        )
        wd_data = _extract_tool_data(raw_wd_result)
        print_result(wd_data)
        assert isinstance(wd_data, dict)
        modified_files = wd_data["repository_status"]["working_directory"][
            "modified_files"
        ]

        assert (
            len(modified_files) == 1
        ), f"Expected 1 modified file in working directory, got {len(modified_files)}"
        assert (
            modified_files[0]["path"] == "test_file.py"
        ), f"Expected 'test_file.py', got {modified_files[0]['path']}"
        assert (
            modified_files[0].get("lines_added", 0) == 1
        ), f"Expected 1 line added in WD, got {modified_files[0].get('lines_added')}"
        assert not modified_files[0]["staged"], "Expected file to be NOT staged"
        assert (
            wd_data["repository_status"]["working_directory"]["total_files"] == 1
        ), "Expected total_files in WD to be 1"
        print("✅ Working Directory Changes check passed.")

        # --- Act & Assert: Test Staged Changes (should be empty for unstaged scenario) ---
        print("\n📋 Staged Changes (Unstaged - expecting empty):")
        raw_staged_result = await client.call_tool(
            "analyze_staged_changes", {"repository_path": str(repo_path)}
        )
        staged_data = _extract_tool_data(raw_staged_result)
        print_result(staged_data)
        assert isinstance(staged_data, dict)
        assert (
            staged_data.get("total_staged_files") == 0
        ), "Expected 0 staged files for unstaged scenario"
        assert (
            staged_data.get("ready_to_commit") is False
        ), "Expected not ready to commit for unstaged scenario"
        print("✅ Staged Changes (Unstaged) check passed.")

        # --- Act & Assert: Test Repository Health (should reflect unstaged work) ---
        print("\n💚 Repository Health (Unstaged):")
        raw_health_result = await client.call_tool(
            "analyze_repository_health", {"repository_path": str(repo_path)}
        )
        health_data = _extract_tool_data(raw_health_result)
        print_result(health_data)
        assert isinstance(health_data, dict)
        assert (
            health_data.get("health_score", 100) < 100
        ), "Expected health score less than 100 due to unstaged changes"
        assert (
            health_data.get("health_status") == "good"
            or health_data.get("health_status") == "fair"
        ), "Expected health status to reflect changes"
        assert "Uncommitted changes in working directory" in health_data.get(
            "issues", []
        ), "Expected 'Uncommitted changes' issue"
        print("✅ Repository Health (Unstaged) check passed.")

    print("\n" + "=" * 80)
    print("FINISHED TEST: UNSTAGED CHANGES SCENARIO")
    print("=" * 80 + "\n")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyze_repo_with_staged_changes(tmp_path):
    """
    Tests the scenario where a file is modified and staged.
    Focuses on analyze_staged_changes and get_outstanding_summary.
    """
    import subprocess

    # --- Setup: Create a repository with staged changes ---
    repo_path = tmp_path / "repo_staged"
    repo_path.mkdir()

    test_file = repo_path / "test_file.py"
    test_file.write_text("print('Hello, staged world!')\n")

    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "test_file.py"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit for staged test"],
        cwd=repo_path,
        check=True,
    )

    # Modify the file AND STAGE IT
    test_file.write_text("print('Hello, staged world!')\nprint('Another new line')\n")
    subprocess.run(["git", "add", "test_file.py"], cwd=repo_path, check=True)

    # --- Arrange: Create and configure FastMCP server and client ---
    server, services = create_server()
    server.git_client = services["git_client"]
    server.change_detector = services["change_detector"]
    server.diff_analyzer = services["diff_analyzer"]
    server.status_tracker = services["status_tracker"]
    register_tools(server, services)
    client = Client(server)

    async with client:
        print("\n" + "=" * 80)
        print(f"RUNNING TEST: STAGED CHANGES SCENARIO ({repo_path})")
        print("=" * 80)

        # --- Act & Assert: Test Outstanding Summary ---
        print("\n📊 Outstanding Summary (Staged):")
        raw_summary_result = await client.call_tool(
            "get_outstanding_summary",
            {"repository_path": str(repo_path), "detailed": True},
        )
        summary_data = _extract_tool_data(raw_summary_result)
        print_result(summary_data)
        assert isinstance(summary_data, dict)
        assert summary_data.get("has_outstanding_work") is True
        assert (
            summary_data["quick_stats"]["working_directory_changes"] == 0
        )  # Key assertion for staged
        assert summary_data["quick_stats"]["staged_changes"] == 1
        assert "staged for commit" in summary_data["summary"].lower()
        print("✅ Outstanding Summary check passed.")

        # --- Act & Assert: Test Working Directory Changes (should be empty for staged scenario) ---
        print("\n📝 Working Directory Changes (Staged - expecting empty):")
        raw_wd_result = await client.call_tool(
            "analyze_working_directory",
            {"repository_path": str(repo_path), "include_diffs": False},
        )
        wd_data = _extract_tool_data(raw_wd_result)
        print_result(wd_data)
        assert isinstance(wd_data, dict)
        assert (
            wd_data["repository_status"]["working_directory"]["total_files"] == 0
        ), "Expected 0 modified files in working directory for staged scenario"
        print("✅ Working Directory Changes (Staged) check passed.")

        # --- Act & Assert: Test Staged Changes ---
        print("\n📋 Staged Changes (Staged):")
        raw_staged_result = await client.call_tool(
            "analyze_staged_changes", {"repository_path": str(repo_path)}
        )
        staged_data = _extract_tool_data(raw_staged_result)
        print_result(staged_data)
        assert isinstance(staged_data, dict)
        staged_files = staged_data.get("staged_files", [])
        assert (
            len(staged_files) == 1
        ), f"Expected 1 staged file, got {len(staged_files)}"
        assert (
            staged_files[0]["path"] == "test_file.py"
        ), f"Expected 'test_file.py', got {staged_files[0]['path']}"
        assert (
            staged_files[0].get("lines_added", 0) == 1
        ), f"Expected 1 line added in staged, got {staged_files[0].get('lines_added')}"
        assert staged_data.get("ready_to_commit") is True, "Expected ready to commit"
        print("✅ Staged Changes check passed.")

        # --- Act & Assert: Test Repository Health (should reflect staged work) ---
        print("\n💚 Repository Health (Staged):")
        raw_health_result = await client.call_tool(
            "analyze_repository_health", {"repository_path": str(repo_path)}
        )
        health_data = _extract_tool_data(raw_health_result)
        print_result(health_data)
        assert isinstance(health_data, dict)
        assert (
            health_data.get("health_score", 100) < 100
        ), "Expected health score less than 100 due to staged changes"
        assert (
            health_data.get("health_status") == "good"
            or health_data.get("health_status") == "fair"
        ), "Expected health status to reflect changes"
        assert (
            health_data["metrics"]["has_staged_changes"] is True
        ), "Expected has_staged_changes to be True"
        print("✅ Repository Health (Staged) check passed.")

    print("\n" + "=" * 80)
    print("FINISHED TEST: STAGED CHANGES SCENARIO")
    print("=" * 80 + "\n")


# You could add more tests for other scenarios like:
# - test_analyze_repo_with_unpushed_commits
# - test_analyze_repo_with_stashed_changes
# - test_analyze_repo_clean_state

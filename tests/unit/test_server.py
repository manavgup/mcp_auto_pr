#!/usr/bin/env python3
"""
Enhanced test client for the MCP PR Recommender FastMCP server.
Tests full integration with mcp_local_repo_analyzer for the "messy developer" scenario.
Now includes proper untracked file handling.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client

# Mock data similar to what mcp_local_repo_analyzer would provide
MOCK_ANALYSIS = {
    "repository_path": "/path/to/repo",
    "analysis_timestamp": datetime.now().isoformat(),
    "total_outstanding_files": 5,
    "categories": {
        "critical_files": [],
        "source_code": ["src/main.py", "src/utils.py", "src/models.py"],
        "documentation": ["README.md", "docs/api.md"],
        "tests": ["tests/test_main.py", "tests/test_utils.py"],
        "configuration": ["pyproject.toml", ".env.example"],
        "other": ["Makefile"],
    },
    "risk_assessment": {
        "risk_level": "medium",
        "risk_factors": ["Multiple file types", "Large changeset"],
        "large_changes": ["src/main.py"],
        "potential_conflicts": [],
    },
    "summary": "5 files with mixed changes across source code, tests, and configuration",
    "working_directory_files": [
        {
            "path": "src/main.py",
            "status_code": "M",
            "staged": False,
            "lines_added": 45,
            "lines_deleted": 12,
            "is_binary": False,
        },
        {
            "path": "src/utils.py",
            "status_code": "M",
            "staged": False,
            "lines_added": 15,
            "lines_deleted": 3,
            "is_binary": False,
        },
        {
            "path": "src/models.py",
            "status_code": "A",
            "staged": False,
            "lines_added": 67,
            "lines_deleted": 0,
            "is_binary": False,
        },
        {
            "path": "tests/test_main.py",
            "status_code": "M",
            "staged": False,
            "lines_added": 23,
            "lines_deleted": 5,
            "is_binary": False,
        },
        {
            "path": "tests/test_utils.py",
            "status_code": "A",
            "staged": False,
            "lines_added": 18,
            "lines_deleted": 0,
            "is_binary": False,
        },
        {
            "path": "README.md",
            "status_code": "M",
            "staged": False,
            "lines_added": 8,
            "lines_deleted": 2,
            "is_binary": False,
        },
        {
            "path": "pyproject.toml",
            "status_code": "M",
            "staged": False,
            "lines_added": 3,
            "lines_deleted": 1,
            "is_binary": False,
        },
    ],
    "staged_files": [],
}


@pytest.fixture
def analysis_data():
    """Fixture providing mock analysis data for workflow tests."""
    return MOCK_ANALYSIS


async def get_mcp_local_repo_analyzer_client():
    """Create a client for the mcp_local_repo_analyzer server."""
    from fastmcp.client.transports import PythonStdioTransport

    # Path to the other MCP server
    analyzer_path = "../mcp_local_repo_analyzer/src/local_git_analyzer/main.py"

    if not Path(analyzer_path).exists():
        raise FileNotFoundError(f"mcp_local_repo_analyzer not found at {analyzer_path}")

    transport = PythonStdioTransport(
        script_path=analyzer_path,
        python_cmd="python",
        env={
            **os.environ,
            "PYTHONPATH": str(Path("../mcp_local_repo_analyzer").resolve()),
        },
    )
    return Client(transport)


async def get_pr_recommender_client():
    """Create a client for our PR recommender server."""
    from fastmcp.client.transports import PythonStdioTransport

    transport = PythonStdioTransport(
        script_path="src/mcp_pr_recommender/main.py",
        python_cmd="python",
        env={
            **os.environ,
            "PYTHONPATH": str(Path("src").resolve()),
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY") or "dummy-key-for-tests",
        },
    )
    return Client(transport)


async def estimate_untracked_file_size(repo_path: str, file_path: str) -> int:
    """Estimate the size of an untracked file in lines"""
    try:
        full_path = Path(repo_path) / file_path

        if not full_path.exists():
            return 0

        # Skip directories
        if full_path.is_dir():
            return 0

        # Skip binary files based on extension
        binary_extensions = {
            ".pyc",
            ".pyo",
            ".so",
            ".dylib",
            ".dll",
            ".exe",
            ".bin",
            ".jpg",
            ".png",
            ".gif",
            ".pdf",
        }
        if full_path.suffix.lower() in binary_extensions:
            return 0

        # Try to count lines for text files
        try:
            with open(full_path, encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for line in f if line.strip())  # Count non-empty lines
                return lines
        except (UnicodeDecodeError, PermissionError):
            # If we can't read it as text, estimate based on file size
            file_size = full_path.stat().st_size
            # Rough estimate: 50 characters per line average
            estimated_lines = max(1, file_size // 50)
            return min(estimated_lines, 1000)  # Cap at 1000 lines for estimation

    except Exception:
        return 0


async def get_comprehensive_file_analysis(analyzer_client, repo_path: str) -> dict[str, Any]:
    """Get comprehensive analysis including untracked files with size estimates"""

    # Get working directory changes (includes untracked files)
    wd_result = await analyzer_client.call_tool(
        "analyze_working_directory",
        {"repository_path": repo_path, "include_diffs": False},
    )
    wd_data = json.loads(wd_result[0].text)

    # Get staged changes
    staged_result = await analyzer_client.call_tool(
        "analyze_staged_changes", {"repository_path": repo_path, "include_diffs": False}
    )
    staged_data = json.loads(staged_result[0].text)

    # ENHANCED: Get detailed untracked file analysis
    untracked_result = await analyzer_client.call_tool("get_untracked_files", {"repository_path": repo_path})
    untracked_data = json.loads(untracked_result[0].text)

    all_files = []

    # Process tracked files (modified, added, deleted, etc.)
    for category in ["modified", "added", "deleted", "renamed"]:
        if category in wd_data.get("files", {}):
            for file_obj in wd_data["files"][category]:
                # Get real diff stats for files with changes
                real_lines_added = 0
                real_lines_deleted = 0

                if file_obj.get("status") in ["M", "A"] and not file_obj.get("is_binary", False):
                    try:
                        diff_result = await analyzer_client.call_tool(
                            "get_file_diff",
                            {
                                "file_path": file_obj.get("path"),
                                "repository_path": repo_path,
                                "staged": False,
                                "max_lines": 50,
                            },
                        )
                        diff_data = json.loads(diff_result[0].text)

                        if diff_data.get("has_changes"):
                            stats = diff_data.get("statistics", {})
                            real_lines_added = stats.get("lines_added", 0)
                            real_lines_deleted = stats.get("lines_deleted", 0)
                    except Exception as e:
                        print(f"      ⚠️  Could not get diff for {file_obj.get('path')}: {e}")

                normalized_file = {
                    "path": file_obj.get("path"),
                    "status_code": file_obj.get("status", "?"),
                    "staged": file_obj.get("staged", False),
                    "lines_added": real_lines_added,
                    "lines_deleted": real_lines_deleted,
                    "is_binary": file_obj.get("is_binary", False),
                    "old_path": file_obj.get("old_path"),
                    "file_type": "tracked",
                }
                all_files.append(normalized_file)

    # ENHANCED: Process untracked files with size estimation
    untracked_count = untracked_data.get("untracked_count", 0)
    print(f"   📁 Processing {untracked_count} untracked files...")

    untracked_files_processed = 0
    total_untracked_lines = 0

    for file_obj in untracked_data.get("files", []):
        file_path = file_obj.get("path")

        # Estimate file size for untracked files
        estimated_lines = await estimate_untracked_file_size(repo_path, file_path)

        if estimated_lines > 0:
            untracked_files_processed += 1
            total_untracked_lines += estimated_lines

        # Treat untracked files as "new additions"
        normalized_file = {
            "path": file_path,
            "status_code": "A",  # Treat as addition
            "staged": False,
            "lines_added": estimated_lines,
            "lines_deleted": 0,
            "is_binary": file_obj.get("is_binary", False),
            "old_path": None,
            "file_type": "untracked",
        }
        all_files.append(normalized_file)

    # Add staged files
    for file_obj in staged_data.get("staged_files", []):
        normalized_file = {
            "path": file_obj.get("path"),
            "status_code": file_obj.get("status", "A"),
            "staged": True,
            "lines_added": file_obj.get("lines_added", 0),
            "lines_deleted": file_obj.get("lines_deleted", 0),
            "is_binary": file_obj.get("is_binary", False),
            "old_path": file_obj.get("old_path"),
            "file_type": "staged",
        }
        all_files.append(normalized_file)

    # Summary stats
    tracked_files = [f for f in all_files if f["file_type"] == "tracked"]
    untracked_files = [f for f in all_files if f["file_type"] == "untracked"]
    staged_files = [f for f in all_files if f["file_type"] == "staged"]

    files_with_changes = [f for f in all_files if f["lines_added"] > 0 or f["lines_deleted"] > 0]
    total_new_lines = sum(f["lines_added"] for f in all_files)

    print("   📊 Comprehensive analysis:")
    print(f"      • Tracked files: {len(tracked_files)}")
    print(f"      • Untracked files: {len(untracked_files)} ({total_untracked_lines:,} estimated lines)")
    print(f"      • Staged files: {len(staged_files)}")
    print(f"      • Files with changes: {len(files_with_changes)}")
    print(f"      • Total new lines: {total_new_lines:,}")

    return {
        "all_files": all_files,
        "working_directory_files": tracked_files,
        "untracked_files": untracked_files,
        "staged_files": staged_files,
        "stats": {
            "tracked_count": len(tracked_files),
            "untracked_count": len(untracked_files),
            "staged_count": len(staged_files),
            "files_with_changes": len(files_with_changes),
            "total_new_lines": total_new_lines,
            "untracked_lines": total_untracked_lines,
        },
    }


async def discover_analyzer_capabilities():
    """Discover all available tools and their parameters from the analyzer."""
    print("🔍 Discovering mcp_local_repo_analyzer capabilities...")

    try:
        analyzer_client = await get_mcp_local_repo_analyzer_client()

        async with analyzer_client:
            print("✅ Connected to Local Repo Analyzer")

            # List available tools
            tools = await analyzer_client.list_tools()
            print(f"\n📋 Found {len(tools)} available tools:")

            tool_info = {}
            for tool in tools:
                tool_name = getattr(tool, "name", "Unknown")
                tool_desc = getattr(tool, "description", "No description")

                # Extract parameters if available
                params = {}
                if hasattr(tool, "input_schema") and tool.input_schema:
                    schema = tool.input_schema
                    if "properties" in schema:
                        for param_name, param_info in schema["properties"].items():
                            params[param_name] = {
                                "type": param_info.get("type", "unknown"),
                                "description": param_info.get("description", "No description"),
                                "default": param_info.get("default"),
                                "required": param_name in schema.get("required", []),
                            }

                tool_info[tool_name] = {"description": tool_desc, "parameters": params}

                print(f"\n  🔧 {tool_name}")
                print(f"     📝 {tool_desc}")
                if params:
                    print(f"     📊 Parameters ({len(params)}):")
                    for param_name, param_data in params.items():
                        required_str = " (required)" if param_data["required"] else ""
                        default_str = (
                            f" [default: {param_data['default']}]" if param_data["default"] is not None else ""
                        )
                        print(f"       • {param_name}: {param_data['type']}{required_str}{default_str}")
                        print(f"         {param_data['description']}")

            return tool_info

    except Exception as e:
        print(f"❌ Failed to discover analyzer capabilities: {e}")
        return {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_messy_developer_workflow(analysis_data: dict[str, Any]):
    """Test the complete workflow for a messy developer scenario."""
    print("\n🎯 Testing 'Messy Developer' Workflow...")
    print("=" * 60)

    # Extract key metrics for routing decisions
    has_outstanding_work = analysis_data.get("has_outstanding_work", False)
    total_changes = analysis_data.get("total_outstanding_changes", 0)
    risk_level = analysis_data.get("risk_assessment", {}).get("risk_level", "low")
    quick_stats = analysis_data.get("quick_stats", {})

    # Enhanced stats including untracked files
    comprehensive_stats = analysis_data.get("comprehensive_stats", {})
    untracked_count = comprehensive_stats.get("untracked_count", 0)
    untracked_lines = comprehensive_stats.get("untracked_lines", 0)

    print("📊 Analysis Overview:")
    print(f"   • Outstanding work: {has_outstanding_work}")
    print(f"   • Total changes: {total_changes:,}")
    print(f"   • Risk level: {risk_level}")
    print(f"   • Working directory changes: {quick_stats.get('working_directory_changes', 0)}")
    print(f"   • Staged changes: {quick_stats.get('staged_changes', 0)}")
    print(f"   • Unpushed commits: {quick_stats.get('unpushed_commits', 0)}")
    print(f"   • Untracked files: {untracked_count} ({untracked_lines:,} lines of new code)")

    if not has_outstanding_work and untracked_count == 0:
        print("✅ Repository is clean - no workflow needed")
        return True

    # Connect to both servers
    try:
        analyzer_client = await get_mcp_local_repo_analyzer_client()
        pr_client = await get_pr_recommender_client()

        async with analyzer_client, pr_client:
            print(f"\n🔀 Routing workflow based on risk level: {risk_level}")

            if risk_level == "high":
                await _handle_high_risk_workflow(analyzer_client, pr_client, analysis_data)
            elif quick_stats.get("working_directory_changes", 0) > 0 or untracked_count > 0:
                await _handle_working_directory_workflow(analyzer_client, pr_client, analysis_data)
            elif quick_stats.get("unpushed_commits", 0) > 0:
                await _handle_unpushed_commits_workflow(analyzer_client, pr_client, analysis_data)
            else:
                await _handle_default_workflow(analyzer_client, pr_client, analysis_data)

            # Finally, get PR recommendations with enhanced data
            await _generate_pr_recommendations(pr_client, analysis_data)

            return True

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False


async def _handle_high_risk_workflow(analyzer_client, pr_client, analysis_data):
    """Handle high-risk scenario workflow."""
    print("\n⚠️  HIGH RISK WORKFLOW")
    print("   Performing comprehensive validation...")

    repo_path = analysis_data.get("repository_path", ".")

    try:
        # Validate staged changes if any
        if analysis_data.get("quick_stats", {}).get("staged_changes", 0) > 0:
            print("   🔍 Validating staged changes...")
            validation_result = await analyzer_client.call_tool(
                "validate_staged_changes", {"repository_path": repo_path}
            )
            validation_data = json.loads(validation_result[0].text)
            print(f"   ✅ Validation result: {'VALID' if validation_data.get('valid') else 'INVALID'}")

            if not validation_data.get("valid"):
                print(f"   ⚠️  Validation errors: {validation_data.get('errors', [])}")

        # Check for potential conflicts
        print("   🔍 Detecting potential conflicts...")
        conflicts_result = await analyzer_client.call_tool(
            "detect_conflicts", {"repository_path": repo_path, "target_branch": "main"}
        )
        conflicts_data = json.loads(conflicts_result[0].text)

        if conflicts_data.get("has_potential_conflicts"):
            conflict_files = conflicts_data.get("potential_conflict_files", [])
            print(f"   ⚠️  Potential conflicts detected in {len(conflict_files)} files")
            for file_path in conflict_files[:3]:
                print(f"      • {file_path}")
        else:
            print("   ✅ No obvious conflicts detected")

    except Exception as e:
        print(f"   ❌ High-risk workflow error: {e}")


async def _handle_working_directory_workflow(analyzer_client, pr_client, analysis_data):
    """Handle working directory changes workflow."""
    print("\n📝 WORKING DIRECTORY WORKFLOW")
    print("   Analyzing uncommitted changes for PR grouping...")

    repo_path = analysis_data.get("repository_path", ".")
    comprehensive_stats = analysis_data.get("comprehensive_stats", {})

    try:
        # Get detailed working directory analysis
        wd_result = await analyzer_client.call_tool(
            "analyze_working_directory",
            {"repository_path": repo_path, "include_diffs": False},
        )
        wd_data = json.loads(wd_result[0].text)

        print("   📊 Working directory summary:")
        summary = wd_data.get("summary", {})
        for change_type, count in summary.items():
            if count > 0:
                print(f"      • {change_type}: {count} files")

        # Show untracked file summary
        untracked_count = comprehensive_stats.get("untracked_count", 0)
        untracked_lines = comprehensive_stats.get("untracked_lines", 0)
        if untracked_count > 0:
            print(f"      • untracked: {untracked_count} files ({untracked_lines:,} estimated lines)")

        # Get untracked files specifically if we have many
        if summary.get("untracked", 0) > 5:
            print("   🔍 Analyzing untracked files...")
            untracked_result = await analyzer_client.call_tool("get_untracked_files", {"repository_path": repo_path})
            untracked_data = json.loads(untracked_result[0].text)
            print(f"   📁 Found {untracked_data.get('untracked_count', 0)} untracked files")

            # Show sample of large untracked files
            untracked_files = untracked_data.get("files", [])
            if untracked_files:
                print("   📋 Sample untracked files:")
                for file_obj in untracked_files[:5]:
                    path = file_obj.get("path", "unknown")
                    if path.startswith("src/") or path.startswith("tests/"):
                        print(f"      • {path} (likely new feature code)")
                    else:
                        print(f"      • {path}")

    except Exception as e:
        print(f"   ❌ Working directory workflow error: {e}")


async def _handle_unpushed_commits_workflow(analyzer_client, pr_client, analysis_data):
    """Handle unpushed commits workflow."""
    print("\n🚀 UNPUSHED COMMITS WORKFLOW")
    print("   Checking push readiness...")

    repo_path = analysis_data.get("repository_path", ".")

    try:
        # Check push readiness
        push_result = await analyzer_client.call_tool("get_push_readiness", {"repository_path": repo_path})
        push_data = json.loads(push_result[0].text)

        ready_to_push = push_data.get("ready_to_push", False)
        print(f"   ✅ Push ready: {ready_to_push}")

        if not ready_to_push:
            blockers = push_data.get("blockers", [])
            print(f"   ⚠️  Blockers ({len(blockers)}):")
            for blocker in blockers:
                print(f"      • {blocker}")

        # Compare with remote
        print("   🔍 Comparing with remote...")
        remote_result = await analyzer_client.call_tool(
            "compare_with_remote",
            {"remote_name": "origin", "repository_path": repo_path},
        )
        remote_data = json.loads(remote_result[0].text)

        sync_status = remote_data.get("sync_status", "unknown")
        print(f"   📊 Sync status: {sync_status}")

        if remote_data.get("needs_pull"):
            print("   ⬇️  Pull needed before push")
        elif remote_data.get("needs_push"):
            print("   ⬆️  Ready to push")

    except Exception as e:
        print(f"   ❌ Unpushed commits workflow error: {e}")


async def _handle_default_workflow(analyzer_client, pr_client, analysis_data):
    """Handle default workflow for other scenarios."""
    print("\n🔄 DEFAULT WORKFLOW")
    print("   Running repository health check...")

    repo_path = analysis_data.get("repository_path", ".")

    try:
        health_result = await analyzer_client.call_tool("analyze_repository_health", {"repository_path": repo_path})
        health_data = json.loads(health_result[0].text)

        health_score = health_data.get("health_score", 0)
        health_status = health_data.get("health_status", "unknown")

        print(f"   📊 Health score: {health_score}/100 ({health_status})")

        issues = health_data.get("issues", [])
        if issues:
            print(f"   ⚠️  Issues found ({len(issues)}):")
            for issue in issues:
                print(f"      • {issue}")
        else:
            print("   ✅ No issues found")

    except Exception as e:
        print(f"   ❌ Default workflow error: {e}")


async def _generate_pr_recommendations(pr_client, analysis_data):
    """Enhanced PR generation that includes untracked files"""
    print("\n🤖 GENERATING PR RECOMMENDATIONS")
    print("   Analyzing for atomic PR groupings...")

    try:
        # Use the enhanced file data that includes untracked files
        result = await pr_client.call_tool("generate_pr_recommendations", {"analysis_data": analysis_data})

        pr_data = json.loads(result[0].text)
        print("   ✅ PR recommendations generated")

        # Enhanced display
        recommendations = pr_data.get("recommendations", [])
        if recommendations:
            print(f"\n  📋 Found {len(recommendations)} PR recommendations:\n")

            for i, rec in enumerate(recommendations, 1):
                print(f"  📝 PR #{i}:")
                print(f"    📌 Title: {rec.get('title', 'No title')}")

                # Show enhanced description with first few lines
                description = rec.get("description", "")
                if description:
                    # Extract first line or two for preview
                    desc_lines = description.split("\n")
                    preview_lines = []
                    for line in desc_lines[:4]:  # First 4 lines
                        if line.strip() and not line.startswith("#"):
                            preview_lines.append(line.strip())

                    if preview_lines:
                        print(f"    📄 Description: {preview_lines[0]}")
                        if len(preview_lines) > 1:
                            print(f"                   {preview_lines[1]}")

                files = rec.get("files", [])
                total_lines = rec.get("total_lines_changed", 0)

                # Enhanced file categorization
                untracked_in_pr = 0
                config_in_pr = 0
                source_in_pr = 0
                test_in_pr = 0

                for f in files:
                    if any(pattern in f for pattern in ["src/pr_recommender/", "tests/", "Makefile"]):
                        if "test" in f.lower():
                            test_in_pr += 1
                        elif f.endswith((".py", ".js", ".ts")):
                            source_in_pr += 1
                        untracked_in_pr += 1
                    elif any(
                        cfg in f
                        for cfg in [
                            "pyproject.toml",
                            "poetry.lock",
                            ".env",
                            ".gitignore",
                        ]
                    ):
                        config_in_pr += 1

                # Show file type breakdown
                if untracked_in_pr > 0:
                    print(f"    🆕 New files: {untracked_in_pr} ({source_in_pr} source, {test_in_pr} tests)")
                if config_in_pr > 0:
                    print(f"    ⚙️  Config files: {config_in_pr}")

                print(f"    📊 Total: {len(files)} files, {total_lines:,} lines changed")
                print(f"    ⚡ Priority: {rec.get('priority', 'unknown')}")
                print(f"    ⚠️  Risk: {rec.get('risk_level', 'unknown')}")

                reasoning = rec.get("reasoning", "")
                if reasoning:
                    # Show short reasoning
                    short_reasoning = reasoning.split(".")[0]  # First sentence
                    print(f"    💭 Reasoning: {short_reasoning}")
                print()

            # Enhanced summary
            total_files = sum(len(rec.get("files", [])) for rec in recommendations)
            total_lines = sum(rec.get("total_lines_changed", 0) for rec in recommendations)

            print(
                f"  📊 Summary: Generated {len(recommendations)} atomic PRs from {total_files} files ({total_lines:,} total lines)"
            )

    except Exception as e:
        print(f"   ❌ PR recommendation error: {e}")
        import traceback

        traceback.print_exc()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration: analyzer -> recommender with comprehensive workflow."""
    print("🔗 Testing Full Integration (Analyzer -> Recommender)")
    print("🎯 Focus: 'Messy Developer' Scenario with Untracked Files")
    print("=" * 80)

    try:
        # Step 1: Discover analyzer capabilities
        tool_info = await discover_analyzer_capabilities()

        if not tool_info:
            print("⚠️  Could not discover analyzer capabilities, proceeding with mock data...")
            return await test_pr_recommender_with_mock()

        # Step 2: Get comprehensive analysis
        print("\n📊 Step 2: Getting comprehensive repository analysis...")
        analyzer_client = await get_mcp_local_repo_analyzer_client()

        async with analyzer_client:
            print("✅ Connected to Local Repo Analyzer")

            # Get outstanding summary with detailed analysis
            analysis_result = await analyzer_client.call_tool(
                "get_outstanding_summary", {"repository_path": ".", "detailed": True}
            )

            # Extract analysis data
            analysis_data = json.loads(analysis_result[0].text)

            print("📋 Analysis completed:")
            print(f"   • Repository: {analysis_data.get('repository_name', 'Unknown')}")
            print(f"   • Branch: {analysis_data.get('current_branch', 'Unknown')}")
            print(f"   • Outstanding changes: {analysis_data.get('total_outstanding_changes', 0)}")
            print(f"   • Risk level: {analysis_data.get('risk_assessment', {}).get('risk_level', 'unknown')}")

            # Step 2.5: Get comprehensive file details including untracked files
            if analysis_data.get("has_outstanding_work"):
                print("\n📁 Step 2.5: Getting comprehensive file information (including untracked files)...")

                # Get comprehensive analysis that includes untracked files
                comprehensive_analysis = await get_comprehensive_file_analysis(analyzer_client, ".")

                # ENHANCED: Merge comprehensive analysis into the main analysis data
                analysis_data["all_files"] = comprehensive_analysis["all_files"]
                analysis_data["working_directory_files"] = comprehensive_analysis["working_directory_files"]
                analysis_data["staged_files"] = comprehensive_analysis["staged_files"]
                analysis_data["untracked_files"] = comprehensive_analysis["untracked_files"]
                analysis_data["comprehensive_stats"] = comprehensive_analysis["stats"]

                # Update total changes to include untracked files
                original_changes = analysis_data.get("total_outstanding_changes", 0)
                untracked_lines = comprehensive_analysis["stats"]["untracked_lines"]
                total_changes_including_untracked = original_changes + untracked_lines
                analysis_data["total_outstanding_changes"] = total_changes_including_untracked

                print("   ✅ Enhanced analysis complete:")
                print(f"      • Tracked files: {comprehensive_analysis['stats']['tracked_count']}")
                print(f"      • Untracked files: {comprehensive_analysis['stats']['untracked_count']}")
                print(f"      • Staged files: {comprehensive_analysis['stats']['staged_count']}")
                print(f"      • Total impact: {total_changes_including_untracked:,} lines")

        # Step 3: Execute enhanced messy developer workflow
        success = await test_messy_developer_workflow(analysis_data)

        if success:
            print("\n🎉 Full integration test completed successfully!")
            print("=" * 80)
            return True
        else:
            print("\n❌ Integration test had issues")
            return False

    except FileNotFoundError as e:
        print(f"⚠️  Local repo analyzer not found: {e}")
        print("💡 Falling back to mock data test...")
        return await test_pr_recommender_with_mock()
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires actual MCP server process - integration test only")
async def test_pr_recommender_with_mock():
    """Test PR recommender with mock data."""
    print("🧪 Testing PR Recommender with mock data...")

    client = await get_pr_recommender_client()

    async with client:
        try:
            print("✅ Connected to PR Recommender server")

            # List available tools
            tools = await client.list_tools()
            print(f"\n📋 Available tools ({len(tools)}):")
            for tool in tools:
                tool_name = getattr(tool, "name", "Unknown")
                tool_desc = getattr(tool, "description", "No description")
                print(f"  - {tool_name}: {tool_desc}")

            # Test PR recommendation with mock data
            print("\n🤖 Testing PR recommendation with mock data...")
            result = await client.call_tool("generate_pr_recommendations", {"analysis_data": MOCK_ANALYSIS})

            pr_data = json.loads(result[0].text)
            print("✅ PR Recommendation Result:")
            print_pr_recommendations(pr_data)

            return True

        except Exception as e:
            print(f"❌ Error testing PR recommender: {e}")
            import traceback

            traceback.print_exc()
            return False


def print_pr_recommendations(result):
    """Print PR recommendation results in a nice format."""
    if isinstance(result, dict):
        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            return

        # Print main recommendations
        if "recommendations" in result:
            recommendations = result["recommendations"]
            if isinstance(recommendations, list) and recommendations:
                print(f"\n  📋 Found {len(recommendations)} PR recommendations:")

                for i, rec in enumerate(recommendations, 1):
                    print(f"\n  📝 PR #{i}:")

                    if isinstance(rec, dict):
                        # Print PR details
                        if "title" in rec:
                            print(f"    📌 Title: {rec['title']}")
                        if "description" in rec:
                            # Show condensed description
                            desc = rec["description"]
                            lines = desc.split("\n")
                            # Find the first meaningful line
                            for line in lines:
                                if line.strip() and not line.startswith("#") and not line.startswith("**"):
                                    print(f"    📄 Description: {line.strip()}")
                                    break
                        if "priority" in rec:
                            print(f"    ⚡ Priority: {rec['priority']}")
                        if "risk_level" in rec:
                            print(f"    ⚠️  Risk: {rec['risk_level']}")

                        # Enhanced file information
                        if "files" in rec:
                            files = rec["files"]
                            total_lines = rec.get("total_lines_changed", 0)
                            print(f"    📊 Files: {len(files)}, Lines: {total_lines:,}")

                            # Categorize files
                            new_files = [
                                f
                                for f in files
                                if any(
                                    pattern in f
                                    for pattern in [
                                        "src/pr_recommender/",
                                        "tests/",
                                        "Makefile",
                                    ]
                                )
                            ]
                            config_files = [
                                f
                                for f in files
                                if any(
                                    pattern in f
                                    for pattern in [
                                        "pyproject.toml",
                                        "poetry.lock",
                                        ".env",
                                    ]
                                )
                            ]
                            other_files = [f for f in files if f not in new_files and f not in config_files]

                            if new_files:
                                print(f"    🆕 New feature files: {len(new_files)}")
                            if config_files:
                                print(f"    ⚙️  Config files: {len(config_files)}")
                            if other_files:
                                print(f"    📁 Other files: {len(other_files)}")

                        # Print reasoning
                        if "reasoning" in rec:
                            reasoning = rec["reasoning"]
                            # Show first sentence
                            short_reasoning = reasoning.split(".")[0] if "." in reasoning else reasoning
                            print(f"    💭 Reasoning: {short_reasoning}")
                    else:
                        print(f"    📄 {rec}")
            else:
                print("  📭 No specific recommendations provided")

        # Print summary info
        if "summary" in result:
            print(f"\n  📊 Summary: {result['summary']}")

        if "total_prs" in result:
            print(f"  🔢 Total PRs suggested: {result['total_prs']}")

    else:
        print(f"  📄 Result: {str(result)[:200]}...")


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires actual MCP server process - integration test only")
async def test_connection_only():
    """Test basic connection to PR recommender."""
    print("🔌 Testing connection to PR Recommender...")

    client = await get_pr_recommender_client()

    async with client:
        try:
            await client.ping()
            print("🏓 Server ping successful")

            tools = await client.list_tools()
            print(f"🔧 Available tools: {len(tools)}")

            for tool in tools:
                tool_name = getattr(tool, "name", "Unknown")
                print(f"   - {tool_name}")

            return True

        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False


def main():
    """Main entry point for the test client."""
    import argparse

    parser = argparse.ArgumentParser(description="Test the MCP PR Recommender server")
    parser.add_argument(
        "--mode",
        choices=["mock", "integration", "connection", "discover"],
        default="integration",  # Changed default to integration
        help="Test mode to run",
    )
    parser.add_argument("--repository-path", default=".", help="Repository path to analyze")

    args = parser.parse_args()

    if args.mode == "connection":
        success = asyncio.run(test_connection_only())
    elif args.mode == "integration":
        success = asyncio.run(test_full_integration())
    elif args.mode == "discover":
        success = asyncio.run(discover_analyzer_capabilities()) is not None
    else:  # mock
        success = asyncio.run(test_pr_recommender_with_mock())

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

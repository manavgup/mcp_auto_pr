#!/usr/bin/env python3
"""
Enhanced test client for the Local Git Changes Analyzer FastMCP server.
Tests all tools with focus on return type validation and chaining patterns.
"""

import asyncio
import json
import os
import sys
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport


class GitAnalyzerTestClient:
    """Enhanced test client for comprehensive git analyzer testing."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.client = None
        self.transport = None
        self.test_results = {}

    async def __aenter__(self):
        """Async context manager entry."""
        self.transport = PythonStdioTransport(
            script_path="local_git_analyzer/main.py",
            python_cmd="python",
            env={**os.environ, "PYTHONPATH": os.getcwd()},
        )
        self.client = Client(self.transport)
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    def _extract_result_from_mcp_response(self, mcp_response: list) -> dict[str, Any]:
        """Extract the actual result from FastMCP's TextContent wrapper.

        FastMCP client returns a list of TextContent objects, where the first
        item contains the JSON-serialized tool result.
        """
        if not mcp_response or len(mcp_response) == 0:
            return {}

        # Get the first TextContent object
        first_content = mcp_response[0]

        # Extract the text content
        if hasattr(first_content, "text"):
            text_content = first_content.text
        elif isinstance(first_content, dict) and "text" in first_content:
            text_content = first_content["text"]
        else:
            # Fallback - might be raw text
            text_content = str(first_content)

        # Parse JSON if it looks like JSON
        try:
            import json

            return json.loads(text_content)
        except (json.JSONDecodeError, TypeError):
            # If not JSON, return as-is wrapped in a dict
            return {"content": text_content}

    async def test_connection(self) -> bool:
        """Test basic connection and list available tools."""
        try:
            print("🔌 Testing basic connection...")
            await self.client.ping()
            print("✅ Server ping successful")

            tools = await self.client.list_tools()
            print(f"🔧 Available tools: {len(tools)}")

            expected_tools = {
                "analyze_working_directory",
                "get_file_diff",
                "get_untracked_files",
                "analyze_staged_changes",
                "preview_commit",
                "validate_staged_changes",
                "analyze_unpushed_commits",
                "compare_with_remote",
                "analyze_commit_history",
                "get_outstanding_summary",
                "analyze_repository_health",
                "get_push_readiness",
                "analyze_stashed_changes",
                "detect_conflicts",
            }

            available_tools = set()
            for tool in tools:
                tool_name = (
                    tool.name if hasattr(tool, "name") else tool.get("name", "Unknown")
                )
                available_tools.add(tool_name)
                print(f"   - {tool_name}")

            missing_tools = expected_tools - available_tools
            if missing_tools:
                print(f"❌ Missing expected tools: {missing_tools}")
                return False

            print("✅ All expected tools available")
            return True

        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    async def test_working_directory_tools(self) -> dict[str, Any]:
        """Test working directory analysis tools and return type validation."""
        print("\n📁 Testing Working Directory Tools...")
        results = {}

        # Test 1: analyze_working_directory
        try:
            print("  🔍 Testing analyze_working_directory...")
            wd_raw_result = await self.client.call_tool(
                "analyze_working_directory",
                {"repository_path": self.repo_path, "include_diffs": False},
            )

            # Extract the actual result from FastMCP's TextContent wrapper
            wd_result = self._extract_result_from_mcp_response(wd_raw_result)

            # Validate return type structure
            required_fields = [
                "repository_path",
                "total_files_changed",
                "has_changes",
                "summary",
                "files",
            ]
            validation = self._validate_return_structure(
                wd_result, required_fields, "WorkingDirectory"
            )

            results["analyze_working_directory"] = {
                "success": True,
                "validation": validation,
                "data": wd_result,
                "chainable_fields": {
                    "has_changes": wd_result.get("has_changes"),
                    "repository_path": wd_result.get("repository_path"),
                    "total_files_changed": wd_result.get("total_files_changed"),
                },
            }

            print(
                f"    ✅ Working directory: {wd_result.get('total_files_changed', 0)} files changed"
            )

            # Test chaining example if there are changes
            if wd_result.get("has_changes"):
                print(
                    "    🔗 Testing chaining: has_changes=True → calling get_untracked_files"
                )
                untracked_raw_result = await self.client.call_tool(
                    "get_untracked_files",
                    {"repository_path": wd_result["repository_path"]},
                )
                untracked_result = self._extract_result_from_mcp_response(
                    untracked_raw_result
                )
                results["chained_untracked"] = untracked_result
                print(
                    f"    ✅ Chained call successful: {untracked_result.get('untracked_count', 0)} untracked files"
                )

        except Exception as e:
            results["analyze_working_directory"] = {"success": False, "error": str(e)}
            print(f"    ❌ analyze_working_directory failed: {e}")

        # Test 2: get_file_diff (if there are modified files)
        if results.get("analyze_working_directory", {}).get("success"):
            wd_data = results["analyze_working_directory"]["data"]
            modified_files = wd_data.get("files", {}).get("modified", [])

            if modified_files:
                try:
                    print("  📄 Testing get_file_diff...")
                    first_file = modified_files[0]["path"]
                    diff_raw_result = await self.client.call_tool(
                        "get_file_diff",
                        {
                            "file_path": first_file,
                            "repository_path": wd_data["repository_path"],
                            "max_lines": 50,
                        },
                    )

                    diff_result = self._extract_result_from_mcp_response(
                        diff_raw_result
                    )

                    # Validate return structure
                    diff_fields = [
                        "file_path",
                        "has_changes",
                        "is_binary",
                        "statistics",
                        "diff_content",
                    ]
                    validation = self._validate_return_structure(
                        diff_result, diff_fields, "FileDiff"
                    )

                    results["get_file_diff"] = {
                        "success": True,
                        "validation": validation,
                        "data": diff_result,
                        "chainable_fields": {
                            "has_changes": diff_result.get("has_changes"),
                            "is_large_change": diff_result.get("is_large_change"),
                            "is_binary": diff_result.get("is_binary"),
                        },
                    }

                    print(
                        f"    ✅ File diff: {first_file} - {diff_result.get('statistics', {}).get('total_changes', 0)} changes"
                    )

                except Exception as e:
                    results["get_file_diff"] = {"success": False, "error": str(e)}
                    print(f"    ❌ get_file_diff failed: {e}")

        return results

    async def test_staging_tools(self) -> dict[str, Any]:
        """Test staging area tools and validate chaining patterns."""
        print("\n📋 Testing Staging Area Tools...")
        results = {}

        # Test 1: analyze_staged_changes
        try:
            print("  🔍 Testing analyze_staged_changes...")
            staged_raw_result = await self.client.call_tool(
                "analyze_staged_changes",
                {"repository_path": self.repo_path, "include_diffs": False},
            )

            staged_result = self._extract_result_from_mcp_response(staged_raw_result)

            # Validate return structure
            required_fields = [
                "repository_path",
                "total_staged_files",
                "ready_to_commit",
                "statistics",
                "staged_files",
            ]
            validation = self._validate_return_structure(
                staged_result, required_fields, "StagedChanges"
            )

            results["analyze_staged_changes"] = {
                "success": True,
                "validation": validation,
                "data": staged_result,
                "chainable_fields": {
                    "ready_to_commit": staged_result.get("ready_to_commit"),
                    "total_staged_files": staged_result.get("total_staged_files"),
                    "repository_path": staged_result.get("repository_path"),
                },
            }

            print(
                f"    ✅ Staged changes: {staged_result.get('total_staged_files', 0)} files staged"
            )

            # Test chaining patterns
            if staged_result.get("ready_to_commit"):
                print(
                    "    🔗 Testing chaining: ready_to_commit=True → calling preview_commit"
                )
                preview_raw_result = await self.client.call_tool(
                    "preview_commit",
                    {"repository_path": staged_result["repository_path"]},
                )
                preview_result = self._extract_result_from_mcp_response(
                    preview_raw_result
                )
                results["chained_preview"] = preview_result
                print(
                    f"    ✅ Chained preview: {preview_result.get('summary', {}).get('total_files', 0)} files to commit"
                )

                # Further chaining: preview → validation
                if preview_result.get("ready_to_commit"):
                    print("    🔗 Testing chaining: preview → validate_staged_changes")
                    validation_raw_result = await self.client.call_tool(
                        "validate_staged_changes",
                        {"repository_path": preview_result["repository_path"]},
                    )
                    validation_result = self._extract_result_from_mcp_response(
                        validation_raw_result
                    )
                    results["chained_validation"] = validation_result
                    print(
                        f"    ✅ Chained validation: {'VALID' if validation_result.get('valid') else 'INVALID'}"
                    )

        except Exception as e:
            results["analyze_staged_changes"] = {"success": False, "error": str(e)}
            print(f"    ❌ analyze_staged_changes failed: {e}")

        return results

    async def test_unpushed_commits_tools(self) -> dict[str, Any]:
        """Test unpushed commits tools and validate return structures."""
        print("\n🚀 Testing Unpushed Commits Tools...")
        results = {}

        # Test 1: analyze_unpushed_commits
        try:
            print("  🔍 Testing analyze_unpushed_commits...")
            unpushed_raw_result = await self.client.call_tool(
                "analyze_unpushed_commits",
                {"repository_path": self.repo_path, "max_commits": 10},
            )

            unpushed_result = self._extract_result_from_mcp_response(
                unpushed_raw_result
            )

            # Validate return structure
            required_fields = [
                "repository_path",
                "branch",
                "total_unpushed_commits",
                "summary",
                "commits",
            ]
            validation = self._validate_return_structure(
                unpushed_result, required_fields, "UnpushedCommits"
            )

            results["analyze_unpushed_commits"] = {
                "success": True,
                "validation": validation,
                "data": unpushed_result,
                "chainable_fields": {
                    "total_unpushed_commits": unpushed_result.get(
                        "total_unpushed_commits", 0
                    ),
                    "repository_path": unpushed_result.get("repository_path"),
                    "branch": unpushed_result.get("branch"),
                },
            }

            print(
                f"    ✅ Unpushed commits: {unpushed_result.get('total_unpushed_commits', 0)} commits"
            )

            # Test chaining: if there are unpushed commits, check push readiness
            if unpushed_result.get("total_unpushed_commits", 0) > 0:
                print(
                    "    🔗 Testing chaining: unpushed_commits > 0 → get_push_readiness"
                )
                push_raw_result = await self.client.call_tool(
                    "get_push_readiness",
                    {"repository_path": unpushed_result["repository_path"]},
                )
                push_result = self._extract_result_from_mcp_response(push_raw_result)
                results["chained_push_readiness"] = push_result
                print(
                    f"    ✅ Chained push check: {'READY' if push_result.get('ready_to_push') else 'NOT READY'}"
                )

        except Exception as e:
            results["analyze_unpushed_commits"] = {"success": False, "error": str(e)}
            print(f"    ❌ analyze_unpushed_commits failed: {e}")

        # Test 2: compare_with_remote
        try:
            print("  🔍 Testing compare_with_remote...")
            remote_raw_result = await self.client.call_tool(
                "compare_with_remote",
                {"remote_name": "origin", "repository_path": self.repo_path},
            )

            remote_result = self._extract_result_from_mcp_response(remote_raw_result)

            # Validate return structure
            required_fields = [
                "repository_path",
                "branch",
                "sync_status",
                "needs_push",
                "needs_pull",
            ]
            validation = self._validate_return_structure(
                remote_result, required_fields, "RemoteComparison"
            )

            results["compare_with_remote"] = {
                "success": True,
                "validation": validation,
                "data": remote_result,
                "chainable_fields": {
                    "needs_push": remote_result.get("needs_push"),
                    "needs_pull": remote_result.get("needs_pull"),
                    "sync_priority": remote_result.get("sync_priority"),
                },
            }

            print(
                f"    ✅ Remote comparison: {remote_result.get('sync_status', 'unknown')}"
            )

        except Exception as e:
            results["compare_with_remote"] = {"success": False, "error": str(e)}
            print(f"    ❌ compare_with_remote failed: {e}")

        return results

    async def test_summary_tools(self) -> dict[str, Any]:
        """Test comprehensive summary tools - the main orchestration tools."""
        print("\n📊 Testing Summary Tools...")
        results = {}

        # Test 1: get_outstanding_summary (the primary orchestrator)
        try:
            print("  🔍 Testing get_outstanding_summary...")
            summary_raw_result = await self.client.call_tool(
                "get_outstanding_summary",
                {"repository_path": self.repo_path, "detailed": True},
            )

            summary_result = self._extract_result_from_mcp_response(summary_raw_result)

            # Validate return structure - this is the most important tool
            required_fields = [
                "repository_path",
                "has_outstanding_work",
                "total_outstanding_changes",
                "quick_stats",
                "branch_status",
                "risk_assessment",
                "recommendations",
            ]
            validation = self._validate_return_structure(
                summary_result, required_fields, "OutstandingSummary"
            )

            results["get_outstanding_summary"] = {
                "success": True,
                "validation": validation,
                "data": summary_result,
                "chainable_fields": {
                    "has_outstanding_work": summary_result.get("has_outstanding_work"),
                    "risk_level": summary_result.get("risk_assessment", {}).get(
                        "risk_level"
                    ),
                    "quick_stats": summary_result.get("quick_stats", {}),
                    "branch_status": summary_result.get("branch_status", {}),
                },
            }

            print(
                f"    ✅ Outstanding summary: {'HAS WORK' if summary_result.get('has_outstanding_work') else 'CLEAN'}"
            )
            print(
                f"    📊 Risk level: {summary_result.get('risk_assessment', {}).get('risk_level', 'unknown')}"
            )

            # Test orchestration chaining patterns
            if summary_result.get("has_outstanding_work"):
                risk_level = summary_result.get("risk_assessment", {}).get("risk_level")
                quick_stats = summary_result.get("quick_stats", {})

                # High-risk workflow
                if risk_level == "high":
                    print(
                        "    🔗 Testing orchestration: high risk → analyze_repository_health"
                    )
                    health_raw_result = await self.client.call_tool(
                        "analyze_repository_health",
                        {"repository_path": summary_result["repository_path"]},
                    )
                    health_result = self._extract_result_from_mcp_response(
                        health_raw_result
                    )
                    results["orchestrated_health"] = health_result
                    print(
                        f"    ✅ Health check: {health_result.get('health_status', 'unknown')}"
                    )

                # Working directory workflow
                elif quick_stats.get("working_directory_changes", 0) > 0:
                    print(
                        "    🔗 Testing orchestration: working changes → analyze_working_directory"
                    )
                    wd_raw_result = await self.client.call_tool(
                        "analyze_working_directory",
                        {
                            "repository_path": summary_result["repository_path"],
                            "include_diffs": False,
                        },
                    )
                    wd_result = self._extract_result_from_mcp_response(wd_raw_result)
                    results["orchestrated_wd"] = wd_result
                    print(
                        f"    ✅ Working directory: {wd_result.get('total_files_changed', 0)} files"
                    )

        except Exception as e:
            results["get_outstanding_summary"] = {"success": False, "error": str(e)}
            print(f"    ❌ get_outstanding_summary failed: {e}")

        # Test 2: analyze_repository_health
        try:
            print("  🔍 Testing analyze_repository_health...")
            health_raw_result = await self.client.call_tool(
                "analyze_repository_health", {"repository_path": self.repo_path}
            )

            health_result = self._extract_result_from_mcp_response(health_raw_result)

            # Validate return structure
            required_fields = [
                "repository_path",
                "health_score",
                "health_status",
                "issues",
                "recommendations",
            ]
            validation = self._validate_return_structure(
                health_result, required_fields, "RepositoryHealth"
            )

            results["analyze_repository_health"] = {
                "success": True,
                "validation": validation,
                "data": health_result,
                "chainable_fields": {
                    "health_score": health_result.get("health_score"),
                    "health_status": health_result.get("health_status"),
                    "issues": health_result.get("issues", []),
                },
            }

            print(
                f"    ✅ Repository health: {health_result.get('health_status')} ({health_result.get('health_score')}/100)"
            )

        except Exception as e:
            results["analyze_repository_health"] = {"success": False, "error": str(e)}
            print(f"    ❌ analyze_repository_health failed: {e}")

        return results

    async def test_workflow_chaining(self) -> dict[str, Any]:
        """Test complete workflow chaining patterns."""
        print("\n🔗 Testing Complete Workflow Chaining...")
        results = {}

        try:
            # Start with the main orchestrator
            print("  1️⃣  Starting with get_outstanding_summary...")
            summary_raw = await self.client.call_tool(
                "get_outstanding_summary",
                {"repository_path": self.repo_path, "detailed": False},
            )

            summary = self._extract_result_from_mcp_response(summary_raw)
            results["step1_summary"] = summary

            if summary.get("has_outstanding_work"):
                print("  2️⃣  Has outstanding work - routing based on risk and type...")

                risk_level = summary.get("risk_assessment", {}).get("risk_level", "low")
                quick_stats = summary.get("quick_stats", {})

                if risk_level == "high":
                    print("    🚨 High risk - comprehensive validation workflow")

                    # Validation workflow
                    validation_raw = await self.client.call_tool(
                        "validate_staged_changes",
                        {"repository_path": summary["repository_path"]},
                    )
                    validation = self._extract_result_from_mcp_response(validation_raw)
                    results["step2_validation"] = validation

                    # Conflict detection
                    conflicts_raw = await self.client.call_tool(
                        "detect_conflicts",
                        {"repository_path": summary["repository_path"]},
                    )
                    conflicts = self._extract_result_from_mcp_response(conflicts_raw)
                    results["step3_conflicts"] = conflicts

                    print(
                        f"    ✅ Validation: {'VALID' if validation.get('valid') else 'INVALID'}"
                    )
                    print(
                        f"    ✅ Conflicts: {'DETECTED' if conflicts.get('has_potential_conflicts') else 'NONE'}"
                    )

                elif quick_stats.get("working_directory_changes", 0) > 0:
                    print("    📁 Working directory changes - analysis workflow")

                    # Working directory analysis
                    wd_raw = await self.client.call_tool(
                        "analyze_working_directory",
                        {
                            "repository_path": summary["repository_path"],
                            "include_diffs": False,
                        },
                    )
                    wd_result = self._extract_result_from_mcp_response(wd_raw)
                    results["step2_working_directory"] = wd_result

                    # If large changes, validate
                    if wd_result.get("total_files_changed", 0) > 5:
                        validation_raw = await self.client.call_tool(
                            "validate_staged_changes",
                            {"repository_path": summary["repository_path"]},
                        )
                        validation = self._extract_result_from_mcp_response(
                            validation_raw
                        )
                        results["step3_validation"] = validation
                        print(
                            f"    ✅ Large changes - validation: {'VALID' if validation.get('valid') else 'INVALID'}"
                        )

                elif quick_stats.get("unpushed_commits", 0) > 0:
                    print("    🚀 Unpushed commits - push workflow")

                    # Push readiness check
                    push_raw = await self.client.call_tool(
                        "get_push_readiness",
                        {"repository_path": summary["repository_path"]},
                    )
                    push_check = self._extract_result_from_mcp_response(push_raw)
                    results["step2_push_readiness"] = push_check

                    # If ready to push, check remote sync
                    if push_check.get("ready_to_push"):
                        remote_raw = await self.client.call_tool(
                            "compare_with_remote",
                            {
                                "remote_name": "origin",
                                "repository_path": summary["repository_path"],
                            },
                        )
                        remote_compare = self._extract_result_from_mcp_response(
                            remote_raw
                        )
                        results["step3_remote_compare"] = remote_compare
                        print(
                            f"    ✅ Push ready - remote sync: {remote_compare.get('sync_status', 'unknown')}"
                        )
                    else:
                        print(
                            f"    ⏳ Not ready to push: {', '.join(push_check.get('blockers', []))}"
                        )

            else:
                print("  ✅ Repository is clean - checking overall health")
                health_raw = await self.client.call_tool(
                    "analyze_repository_health",
                    {"repository_path": summary["repository_path"]},
                )
                health = self._extract_result_from_mcp_response(health_raw)
                results["step2_health"] = health
                print(
                    f"    ✅ Health check: {health.get('health_status')} ({health.get('health_score')}/100)"
                )

            print("  🎉 Workflow chaining test completed successfully!")
            results["workflow_success"] = True

        except Exception as e:
            print(f"  ❌ Workflow chaining failed: {e}")
            results["workflow_success"] = False
            results["workflow_error"] = str(e)

        return results

    def _validate_return_structure(
        self, result: dict[str, Any], required_fields: list[str], tool_name: str
    ) -> dict[str, Any]:
        """Validate that tool return structure matches documentation."""
        validation = {
            "tool_name": tool_name,
            "has_error": "error" in result,
            "required_fields_present": {},
            "missing_fields": [],
            "unexpected_fields": [],
            "type_validation": {},
        }

        if validation["has_error"]:
            validation["error_message"] = result.get("error")
            return validation

        # Check required fields
        for field in required_fields:
            if field in result:
                validation["required_fields_present"][field] = True
                # Basic type validation
                validation["type_validation"][field] = type(result[field]).__name__
            else:
                validation["missing_fields"].append(field)
                validation["required_fields_present"][field] = False

        # Check for unexpected fields (fields not in common patterns)
        expected_common_fields = set(
            required_fields + ["error", "message", "timestamp"]
        )
        actual_fields = set(result.keys())
        validation["unexpected_fields"] = list(actual_fields - expected_common_fields)

        # Overall validation score
        fields_score = len(
            [f for f in validation["required_fields_present"].values() if f]
        ) / len(required_fields)
        validation["validation_score"] = fields_score
        validation["is_valid"] = fields_score >= 0.8 and not validation["has_error"]

        return validation

    async def test_specific_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """Test a specific tool with given parameters."""
        try:
            print(f"🧪 Testing specific tool: {tool_name}")
            raw_result = await self.client.call_tool(tool_name, kwargs)
            result = self._extract_result_from_mcp_response(raw_result)

            print(f"✅ {tool_name} completed successfully")
            return {"success": True, "data": result}

        except Exception as e:
            print(f"❌ {tool_name} failed: {e}")
            return {"success": False, "error": str(e)}

    def print_test_summary(self, all_results: dict[str, Any]):
        """Print a comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)

        total_tests = 0
        successful_tests = 0
        validation_scores = []

        for category, results in all_results.items():
            print(f"\n📁 {category.upper().replace('_', ' ')}")
            print("-" * 40)

            if isinstance(results, dict):
                for test_name, test_result in results.items():
                    total_tests += 1

                    if isinstance(test_result, dict):
                        if test_result.get("success", False):
                            successful_tests += 1
                            status = "✅ PASS"

                            # Check validation if available
                            if "validation" in test_result:
                                validation = test_result["validation"]
                                score = validation.get("validation_score", 0)
                                validation_scores.append(score)
                                status += f" (validation: {score:.1%})"

                                if validation.get("missing_fields"):
                                    status += f" - Missing: {', '.join(validation['missing_fields'])}"

                            # Show chainable fields
                            if "chainable_fields" in test_result:
                                chainable = test_result["chainable_fields"]
                                key_fields = [
                                    f"{k}={v}"
                                    for k, v in chainable.items()
                                    if v is not None
                                ]
                                if key_fields:
                                    status += (
                                        f" - Key fields: {', '.join(key_fields[:2])}"
                                    )
                        else:
                            status = (
                                f"❌ FAIL - {test_result.get('error', 'Unknown error')}"
                            )
                    else:
                        successful_tests += 1
                        status = "✅ PASS"

                    print(f"  {test_name}: {status}")

        # Overall statistics
        print(f"\n{'='*60}")
        print("📈 OVERALL STATISTICS")
        print(f"{'='*60}")
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(
            f"Success rate: {successful_tests/total_tests:.1%}"
            if total_tests > 0
            else "Success rate: N/A"
        )

        if validation_scores:
            avg_validation = sum(validation_scores) / len(validation_scores)
            print(f"Average validation score: {avg_validation:.1%}")
            print(f"Validation scores: {[f'{s:.1%}' for s in validation_scores[:5]]}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        if successful_tests == total_tests:
            print(
                "🎉 All tests passed! Tools are working correctly with proper return types."
            )
        else:
            failed_count = total_tests - successful_tests
            print(f"⚠️  {failed_count} test(s) failed. Review error messages above.")

        if validation_scores and avg_validation < 0.9:
            print("📋 Some tools may be missing documented return fields.")

        print("🔗 Test chaining patterns to ensure tools work together properly.")

    async def run_comprehensive_tests(self) -> dict[str, Any]:
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive Git Analyzer Tests")
        print("=" * 60)

        all_results = {}

        # Basic connection test
        connection_success = await self.test_connection()
        if not connection_success:
            print("❌ Connection failed - cannot continue with tests")
            return {"connection": False}

        all_results["connection"] = {"success": connection_success}

        # Tool category tests
        all_results["working_directory"] = await self.test_working_directory_tools()
        all_results["staging_area"] = await self.test_staging_tools()
        all_results["unpushed_commits"] = await self.test_unpushed_commits_tools()
        all_results["summary_tools"] = await self.test_summary_tools()

        # Workflow chaining tests
        all_results["workflow_chaining"] = await self.test_workflow_chaining()

        # Print comprehensive summary
        self.print_test_summary(all_results)

        return all_results


async def main():
    """Main test execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the Local Git Changes Analyzer server"
    )
    parser.add_argument("--tool", help="Test a specific tool")
    parser.add_argument(
        "--repository-path", default=".", help="Repository path to analyze"
    )
    parser.add_argument(
        "--connection-only", action="store_true", help="Test connection only"
    )
    parser.add_argument(
        "--workflow-only", action="store_true", help="Test workflow chaining only"
    )
    parser.add_argument(
        "--validate-types", action="store_true", help="Focus on return type validation"
    )

    args = parser.parse_args()

    async with GitAnalyzerTestClient(args.repository_path) as test_client:
        if args.connection_only:
            # Test connection only
            success = await test_client.test_connection()
            sys.exit(0 if success else 1)

        elif args.tool:
            # Test specific tool
            kwargs = {"repository_path": args.repository_path}
            result = await test_client.test_specific_tool(args.tool, **kwargs)

            print("\n📄 SPECIFIC TOOL TEST RESULT")
            print("=" * 40)
            print(json.dumps(result, indent=2, default=str))

            sys.exit(0 if result["success"] else 1)

        elif args.workflow_only:
            # Test workflow chaining only
            print("🔗 Testing Workflow Chaining Only...")
            workflow_results = await test_client.test_workflow_chaining()

            success = workflow_results.get("workflow_success", False)
            print(f"\n🎯 Workflow test: {'SUCCESS' if success else 'FAILED'}")
            sys.exit(0 if success else 1)

        else:
            # Run comprehensive tests
            results = await test_client.run_comprehensive_tests()

            # Determine overall success
            overall_success = True
            for _, category_results in results.items():
                if isinstance(category_results, dict):
                    for _, test_result in category_results.items():
                        if isinstance(test_result, dict) and not test_result.get(
                            "success", True
                        ):
                            overall_success = False
                            break
                    if not overall_success:
                        break

            sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    asyncio.run(main())

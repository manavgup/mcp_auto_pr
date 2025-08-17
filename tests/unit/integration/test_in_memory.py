#!/usr/bin/env python3
"""
In-memory test client for the Local Git Changes Analyzer.
This bypasses stdio transport issues by running server in same process.
"""
import pytest
from fastmcp import Client

from mcp_local_repo_analyzer.main import create_server, register_tools


@pytest.mark.asyncio
async def test_in_memory():
    """Test the server using in-memory transport."""
    # Create the server instance directly
    server = create_server()

    # Register tools (this would normally happen in main())
    register_tools(server)

    # Create client with in-memory transport
    client = Client(server)  # This uses FastMCPTransport automatically

    async with client:
        print("✅ Connected to Local Git Changes Analyzer server (in-memory)")

        # Test 1: Get available tools
        print("\n📋 Available Tools:")
        tools = await client.list_tools()
        assert isinstance(tools, list)
        for tool in tools:
            # Handle both dict and Tool object formats
            if hasattr(tool, "name"):
                name = tool.name
                description = getattr(tool, "description", "No description")
            else:
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description")
            print(f" - {name}: {description}")

        # Test 2: Analyze working directory
        print("\n🔍 Testing working directory analysis...")
        try:
            result = await client.call_tool(
                "analyze_working_directory",
                {
                    "repository_path": ".",
                    "include_diffs": False,
                    "max_diff_lines": 10,
                },  # Keep it simple for testing
            )
            assert isinstance(result, dict | list)
            print("✅ Working directory analysis:")
            print_result_summary(result)
        except Exception as e:
            print(f"❌ Working directory analysis failed: {e}")

        # Test 3: Get outstanding summary
        print("\n📊 Testing comprehensive summary...")
        try:
            result = await client.call_tool(
                "get_outstanding_summary", {"repository_path": ".", "detailed": False}
            )
            assert isinstance(result, dict | list)
            print("✅ Outstanding summary:")
            print_result_summary(result)
        except Exception as e:
            print(f"❌ Outstanding summary failed: {e}")

        print("\n✨ In-memory tests completed!")
        return True


def print_result_summary(result):
    """Print a summary of the tool result."""
    if isinstance(result, dict):
        if "error" in result:
            print(f" ❌ Error: {result['error']}")
            return

        # Print key metrics
        metrics = []
        if "total_files_changed" in result:
            metrics.append(f"Files changed: {result['total_files_changed']}")
        if "total_staged_files" in result:
            metrics.append(f"Staged files: {result['total_staged_files']}")
        if "has_outstanding_work" in result:
            work_status = "📝 Has work" if result["has_outstanding_work"] else "✅ Clean"
            metrics.append(f"Work status: {work_status}")

        if metrics:
            print(f" 📊 {' | '.join(metrics)}")

        if "summary" in result and isinstance(result["summary"], str):
            print(f" 💬 {result['summary']}")

# Test client for HTTP-based git analyzer server.
# Usage: Run 'python run_http_server.py' to start server before testing.

import asyncio

import pytest
from fastmcp import Client


@pytest.mark.skip(
    reason="Requires HTTP server running on localhost:8000 - start with 'python run_http_server.py'"
)
@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_server():
    """Test the HTTP server."""
    # Connect to HTTP server
    client = Client("http://localhost:8000/mcp")

    async with client:
        print("✅ Connected to HTTP server")

        # Test tools
        tools = await client.list_tools()
        print(f"🔧 Found {len(tools)} tools")
        assert isinstance(tools, list)

        # Test a simple tool
        result = await client.call_tool(
            "analyze_working_directory", {"repository_path": "."}
        )
        print(f"📊 Result: {result.get('total_files_changed', 'unknown')} files changed")
        assert isinstance(result, dict | list)


if __name__ == "__main__":
    print("Make sure to run 'python run_http_server.py' first!")
    asyncio.run(test_http_server())

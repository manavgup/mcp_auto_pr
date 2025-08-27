#!/usr/bin/env python3
"""
Test the full MCP chain using proper FastMCP clients with STDIO transport
"""

import asyncio
import json
import sys
from pathlib import Path


async def test_repo_analyzer():
    """Test the repository analyzer using FastMCP client"""
    print("📊 Testing Repository Analyzer (STDIO)")
    print("-" * 40)

    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport

        # Create transport for repo analyzer
        transport = StdioTransport(
            command="poetry",
            args=[
                "run",
                "python",
                "-m",
                "mcp_local_repo_analyzer.main",
                "--work-dir",
                "./mcp_local_repo_analyzer",
            ],
        )

        client = Client(transport)

        async with client:
            print("✅ Repo analyzer connection established")

            # Test ping
            await client.ping()
            print("✅ Repo analyzer ping successful")

            # List tools
            tools = await client.list_tools()
            print(f"✅ Available tools: {len(tools)}")
            for tool in tools:
                print(f"   - {tool.name}")

            # Call analyze_working_directory
            print("\n🔍 Analyzing working directory...")
            result = await client.call_tool(
                "analyze_working_directory",
                {"repository_path": ".", "include_diffs": True, "max_diff_lines": 50},
            )

            print("✅ Working directory analysis completed")

            # Extract structured data
            if hasattr(result, "content") and result.content:
                try:
                    # Parse the text content to get structured data
                    content_text = result.content[0].text if result.content else "{}"
                    analysis_data = json.loads(content_text)

                    print(f"📈 Found {analysis_data.get('total_outstanding_files', 0)} outstanding files")
                    print(f"⚠️  Risk level: {analysis_data.get('risk_assessment', {}).get('risk_level', 'unknown')}")

                    return analysis_data

                except (json.JSONDecodeError, AttributeError, KeyError) as e:
                    print(f"⚠️  Could not parse analysis data: {e}")
                    return {}
            else:
                print("⚠️  No content found in result")
                return {}

    except ImportError:
        print("❌ FastMCP not available - install with: pip install fastmcp")
        return None
    except Exception as e:
        print(f"❌ Repo analyzer error: {e}")
        return None


async def test_pr_recommender(analysis_data):
    """Test the PR recommender using FastMCP client"""
    print("\n🎯 Testing PR Recommender (STDIO)")
    print("-" * 40)

    if not analysis_data:
        print("⚠️  Skipping PR recommender - no analysis data")
        return None

    try:
        import os

        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport

        # Create transport for PR recommender with environment variables
        transport = StdioTransport(
            command="poetry",
            args=["run", "python", "-m", "mcp_pr_recommender.main"],
            env={
                **os.environ,  # Pass all current environment variables
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            },
        )

        client = Client(transport)

        async with client:
            print("✅ PR recommender connection established")

            # Test ping
            await client.ping()
            print("✅ PR recommender ping successful")

            # List tools
            tools = await client.list_tools()
            print(f"✅ Available tools: {len(tools)}")
            for tool in tools:
                print(f"   - {tool.name}")

            # Call generate_pr_recommendations
            print("\n💡 Generating PR recommendations...")
            result = await client.call_tool(
                "generate_pr_recommendations",
                {
                    "analysis_data": analysis_data,
                    "strategy": "semantic",
                    "max_files_per_pr": 8,
                },
            )

            print("✅ PR recommendations generated")

            # Extract recommendations
            if hasattr(result, "content") and result.content:
                try:
                    content_text = result.content[0].text if result.content else "{}"
                    pr_data = json.loads(content_text)

                    recommendations = pr_data.get("recommendations", [])
                    print(f"🎯 Generated {len(recommendations)} PR recommendations:")

                    for i, rec in enumerate(recommendations, 1):
                        title = rec.get("title", "Untitled PR")
                        files = rec.get("files", [])
                        priority = rec.get("priority", "unknown")
                        print(f"   {i}. {title}")
                        print(f"      📁 Files: {len(files)}")
                        print(f"      📏 Priority: {priority}")
                        if files:
                            print(f"      📝 Files: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}")

                    return pr_data

                except (json.JSONDecodeError, AttributeError, KeyError) as e:
                    print(f"⚠️  Could not parse PR recommendations: {e}")
                    return {}
            else:
                print("⚠️  No content found in result")
                return {}

    except ImportError:
        print("❌ FastMCP not available - install with: pip install fastmcp")
        return None
    except Exception as e:
        print(f"❌ PR recommender error: {e}")
        return None


async def main():
    """Test the full MCP chain"""
    print("🔗 Testing MCP Chain: Repo Analyzer -> PR Recommender")
    print("🚀 Using FastMCP Client with STDIO Transport")
    print("=" * 60)

    # Test repo analyzer first
    analysis_data = await test_repo_analyzer()

    if analysis_data is None:
        print("\n❌ Cannot proceed - repo analyzer failed")
        return False

    # Test PR recommender with analysis data
    pr_data = await test_pr_recommender(analysis_data)

    if pr_data is None:
        print("\n❌ PR recommender failed")
        return False

    # Save results
    results = {
        "analysis_data": analysis_data,
        "pr_recommendations": pr_data,
        "timestamp": int(asyncio.get_event_loop().time()),
    }

    results_file = Path("mcp_chain_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")
    print("🎉 Chain test completed successfully!")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

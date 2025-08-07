#!/usr/bin/env python3
"""
Simple test script for MCP packages installed from PyPI.

This script tests the two MCP servers:
- mcp-local-repo-analyzer 
- mcp-pr-recommender

Prerequisites:
- pip install mcp-local-repo-analyzer mcp-pr-recommender
- export OPENAI_API_KEY="your-api-key-here"
"""

import asyncio
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def check_installation() -> bool:
    """Check if MCP packages are installed."""
    print("🔍 Checking PyPI package installation...")
    
    packages = ["mcp-local-repo-analyzer", "mcp-pr-recommender"]
    missing = []
    
    for package in packages:
        try:
            result = subprocess.run([sys.executable, "-c", f"import {package.replace('-', '_')}"], 
                                  capture_output=True)
            if result.returncode == 0:
                print(f"✅ {package} is installed")
            else:
                print(f"❌ {package} is not installed")
                missing.append(package)
        except Exception as e:
            print(f"❌ Error checking {package}: {e}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def test_cli_help() -> bool:
    """Test CLI help commands."""
    print("\n🔍 Testing CLI help commands...")
    
    commands = [
        ("local-git-analyzer", "Local Repository Analyzer"),
        ("pr-recommender", "PR Recommender")
    ]
    
    success = True
    for cmd, name in commands:
        try:
            result = subprocess.run([cmd, "--help"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {name} CLI help works")
            else:
                print(f"❌ {name} CLI help failed")
                success = False
        except subprocess.TimeoutExpired:
            print(f"❌ {name} CLI help timed out")
            success = False
        except FileNotFoundError:
            print(f"❌ {name} command not found in PATH")
            success = False
        except Exception as e:
            print(f"❌ {name} CLI help error: {e}")
            success = False
    
    return success


def test_imports() -> bool:
    """Test importing key modules."""
    print("\n🔍 Testing Python imports...")
    
    imports = [
        # Local Repo Analyzer
        "import mcp_local_repo_analyzer",
        "from mcp_local_repo_analyzer.main import main as analyzer_main",
        "from mcp_local_repo_analyzer.cli import main as analyzer_cli",
        
        # PR Recommender
        "import mcp_pr_recommender", 
        "from mcp_pr_recommender.main import main as recommender_main",
        "from mcp_pr_recommender.cli import main as recommender_cli",
        
        # Bundled shared library
        "from mcp_shared_lib.models.git.files import FileStatus",
        "from mcp_shared_lib.services.git.git_client import GitClient",
    ]
    
    success = True
    for imp in imports:
        try:
            exec(imp)
            print(f"✅ {imp}")
        except Exception as e:
            print(f"❌ {imp} - Error: {e}")
            success = False
    
    return success


async def test_mcp_servers() -> bool:
    """Test MCP servers using FastMCP client."""
    print("\n🔍 Testing MCP servers with FastMCP client...")
    
    # Check if FastMCP is available
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        print("❌ FastMCP not available")
        print("   Install with: pip install fastmcp")
        return False
    
    success = True
    
    # Test Local Repo Analyzer
    print("\n--- Testing Local Repo Analyzer ---")
    try:
        transport = StdioTransport(command="local-git-analyzer")
        client = Client(transport)
        
        async with client:
            # Test connection
            await client.ping()
            print("✅ Analyzer server connection successful")
            
            # Test tools list
            tools = await client.list_tools()
            print(f"✅ Analyzer tools available: {len(tools)}")
            
            # Test a simple tool call
            with tempfile.TemporaryDirectory() as temp_dir:
                await client.call_tool(
                    "analyze_working_directory",
                    {"repository_path": temp_dir, "include_diffs": False}
                )
                print("✅ Analyzer tool call successful")
    except Exception as e:
        print(f"❌ Analyzer server test failed: {e}")
        success = False
    
    # Test PR Recommender (only if OpenAI key is set)
    print("\n--- Testing PR Recommender ---")
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY not set, skipping PR Recommender test")
        print("   Set with: export OPENAI_API_KEY='your-key-here'")
    else:
        try:
            transport = StdioTransport(command="pr-recommender")
            client = Client(transport)
            
            async with client:
                # Test connection
                await client.ping()
                print("✅ Recommender server connection successful")
                
                # Test tools list
                tools = await client.list_tools()
                print(f"✅ Recommender tools available: {len(tools)}")
                
                # Test a simple tool call
                await client.call_tool("get_strategy_options", {})
                print("✅ Recommender tool call successful")
        except Exception as e:
            print(f"❌ Recommender server test failed: {e}")
            success = False
    
    return success


def test_git_functionality() -> bool:
    """Test basic git functionality in a temporary repo."""
    print("\n🔍 Testing git repository functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            temp_path = Path(temp_dir)
            
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], 
                         cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], 
                         cwd=temp_dir, check=True, capture_output=True)
            
            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("print('Hello World')\n")
            
            # Add and commit
            subprocess.run(["git", "add", "test.py"], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], 
                         cwd=temp_dir, check=True, capture_output=True)
            
            # Modify file (create working directory changes)
            test_file.write_text("print('Hello World')\nprint('Modified!')\n")
            
            print("✅ Git repository setup successful")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git functionality test failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Git functionality test error: {e}")
            return False


def main() -> bool:
    """Run all tests."""
    print("🚀 MCP PyPI Packages Test Suite")
    print("=" * 50)
    
    tests = [
        ("Package Installation", check_installation),
        ("CLI Help Commands", test_cli_help), 
        ("Python Imports", test_imports),
        ("Git Functionality", test_git_functionality),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {name}")
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            results.append((name, False))
    
    # Test MCP servers (async test)
    print("\n🔍 Running MCP server tests...")
    try:
        mcp_result = asyncio.run(test_mcp_servers())
        results.append(("MCP Servers", mcp_result))
        status = "✅ PASSED" if mcp_result else "❌ FAILED"
        print(f"\n{status}: MCP Servers")
    except Exception as e:
        print(f"\n❌ ERROR in MCP Servers: {e}")
        results.append(("MCP Servers", False))
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n📈 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! MCP packages are working correctly.")
        print("\n🚀 Next steps:")
        print("1. Configure your IDE with the MCP servers")
        print("2. Set OPENAI_API_KEY for PR recommender")
        print("3. Start using the tools in your development workflow!")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check the errors above.")
        if not os.getenv("OPENAI_API_KEY"):
            print("\nNote: Set OPENAI_API_KEY to test PR recommender functionality")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
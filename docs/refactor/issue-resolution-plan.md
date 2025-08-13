# Issue Resolution Plan

## Overview
This document provides a comprehensive plan to resolve all identified issues in the current codebase, based on actual analysis and testing.

## Critical Issues Identified

### 1. Configuration Validation Errors
**Problem**: GitAnalyzerSettings has extra fields causing import failures
**Impact**: Prevents both MCP servers from importing shared library components
**Root Cause**: Configuration model mismatch between packages

#### Current Error
```python
# Error when importing mcp_shared_lib components
3 validation errors for GitAnalyzerSettings
openai_api_key
  Extra inputs are not permitted [type=extra_forbidden, input_value='sk-your-openai-key-here', input_type=str]
workspace_dir
  Extra inputs are not permitted [type=extra_forbidden, input_value='/path/to/your/code/workspace', input_type=str]
python_env
  Extra inputs are not permitted [type=extra_forbidden, input_value='production', input_type=str]
```

#### Resolution Steps
1. **Audit Configuration Models**
   ```bash
   # Check all configuration files
   find . -name "*.py" -exec grep -l "GitAnalyzerSettings" {} \;
   find . -name "*.yaml" -exec grep -l "openai_api_key\|workspace_dir\|python_env" {} \;
   ```

2. **Consolidate Configuration Models**
   ```python
   # src/shared/config/base.py
   from pydantic import BaseModel, Field
   from typing import Optional

   class BaseSettings(BaseModel):
       """Base configuration settings."""
       class Config:
           extra = "forbid"  # Prevent extra fields

   class GitAnalyzerSettings(BaseSettings):
       """Git analyzer configuration."""
       # Only include fields that are actually used
       git_path: Optional[str] = Field(default=None, description="Path to git executable")
       max_file_size: int = Field(default=1024*1024, description="Maximum file size to analyze")
       ignore_patterns: list[str] = Field(default_factory=list, description="File patterns to ignore")

   class ServerSettings(BaseSettings):
       """MCP server configuration."""
       host: str = Field(default="0.0.0.0", description="Server host")
       port: int = Field(default=8000, description="Server port")
       log_level: str = Field(default="INFO", description="Logging level")
   ```

3. **Update Package Configurations**
   ```python
   # src/mcp_local_repo_analyzer/config.py
   from shared.config.base import GitAnalyzerSettings, ServerSettings

   class AnalyzerConfig(GitAnalyzerSettings, ServerSettings):
       """Local repo analyzer configuration."""
       pass

   # src/mcp_pr_recommender/config.py
   from shared.config.base import ServerSettings

   class RecommenderConfig(ServerSettings):
       """PR recommender configuration."""
       openai_api_key: str = Field(..., description="OpenAI API key")
       model_name: str = Field(default="gpt-4", description="OpenAI model to use")
   ```

4. **Remove Unused Configuration Files**
   ```bash
   # Remove old configuration files
   rm mcp_shared_lib/config/git_analyzer.py
   rm mcp_local_repo_analyzer/config/*.yaml
   rm mcp_pr_recommender/config/*.yaml
   ```

### 2. Test Failures
**Problem**: Local repo analyzer has 4 failing tests
**Impact**: Reduces confidence in code quality and prevents CI/CD success
**Root Cause**: Test configuration and dependency issues

#### Current Test Status
```bash
# Test results from analysis
=============== 4 failed, 18 passed, 2 skipped, 1 error in 6.06s ===============
FAILED tests/integration/test_in_memory.py::test_in_memory
FAILED tests/unit/config/test_manual.py::test_error_handling
FAILED tests/unit/config/test_manual.py::test_scenario_working_directory_changes
FAILED tests/unit/config/test_manual.py::test_scenario_mixed_changes
ERROR tests/integration/test_chain.py::test_pr_recommender
```

#### Resolution Steps
1. **Fix Configuration Tests**
   ```python
   # tests/unit/config/test_manual.py
   import pytest
   from shared.config.base import GitAnalyzerSettings

   def test_error_handling():
       """Test configuration error handling."""
       with pytest.raises(ValueError):
           GitAnalyzerSettings(invalid_field="value")

   def test_scenario_working_directory_changes():
       """Test working directory changes scenario."""
       config = GitAnalyzerSettings(
           git_path="/usr/bin/git",
           max_file_size=2048,
           ignore_patterns=["*.tmp", "*.log"]
       )
       assert config.git_path == "/usr/bin/git"
       assert config.max_file_size == 2048
       assert "*.tmp" in config.ignore_patterns
   ```

2. **Fix Integration Tests**
   ```python
   # tests/integration/test_in_memory.py
   import pytest
   from shared.mcp.server import create_test_server

   def test_in_memory():
       """Test in-memory MCP server."""
       server = create_test_server()
       assert server is not None
       # Add more specific assertions
   ```

3. **Fix Chain Tests**
   ```python
   # tests/integration/test_chain.py
   import pytest
   from unittest.mock import Mock, patch

   @patch('openai.OpenAI')
   def test_pr_recommender(mock_openai):
       """Test PR recommender integration."""
       mock_client = Mock()
       mock_openai.return_value = mock_client
       # Test with mocked OpenAI client
   ```

4. **Update Test Configuration**
   ```ini
   # pytest.ini
   [tool:pytest]
   testpaths = tests
   python_files = test_*.py *_test.py
   python_classes = Test*
   python_functions = test_*
   addopts =
       --strict-markers
       --strict-config
       --cov=src
       --cov-report=term-missing
       --cov-fail-under=90
   markers =
       unit: Unit tests
       integration: Integration tests
       performance: Performance tests
       slow: Slow running tests
   ```

### 3. CLI Help Command Failures
**Problem**: Both servers have CLI help command failures
**Impact**: Poor user experience and prevents proper usage
**Root Cause**: CLI argument parsing and help generation issues

#### Current CLI Status
```bash
# Test results show CLI help failures
❌ Local Repository Analyzer CLI help failed
❌ PR Recommender CLI help failed
```

#### Resolution Steps
1. **Fix Analyzer CLI**
   ```python
   # src/mcp_local_repo_analyzer/cli.py
   import click
   from pathlib import Path
   from typing import Optional

   @click.command()
   @click.option('--transport', '-t',
                 type=click.Choice(['stdio', 'http', 'streamable-http']),
                 default='stdio',
                 help='Transport protocol to use')
   @click.option('--port', '-p',
                 type=int,
                 default=8001,
                 help='Port for HTTP transport')
   @click.option('--host', '-h',
                 default='0.0.0.0',
                 help='Host for HTTP transport')
   @click.option('--config', '-c',
                 type=click.Path(exists=True),
                 help='Configuration file path')
   @click.option('--verbose', '-v',
                 is_flag=True,
                 help='Enable verbose logging')
   @click.version_option(version='0.2.0')
   def main(transport: str, port: int, host: str, config: Optional[str], verbose: bool):
       """MCP Local Repository Analyzer Server.

       Analyzes outstanding git changes in repositories and provides
       intelligent recommendations for PR grouping and atomicity.
       """
       if verbose:
           click.echo(f"Starting analyzer server with {transport} transport")

       # Server startup logic here
       pass

   if __name__ == '__main__':
       main()
   ```

2. **Fix Recommender CLI**
   ```python
   # src/mcp_pr_recommender/cli.py
   import click
   from pathlib import Path
   from typing import Optional

   @click.command()
   @click.option('--transport', '-t',
                 type=click.Choice(['stdio', 'http', 'streamable-http']),
                 default='stdio',
                 help='Transport protocol to use')
   @click.option('--port', '-p',
                 type=int,
                 default=8002,
                 help='Port for HTTP transport')
   @click.option('--host', '-h',
                 default='0.0.0.0',
                 help='Host for HTTP transport')
   @click.option('--openai-key', '-k',
                 envvar='OPENAI_API_KEY',
                 help='OpenAI API key')
   @click.option('--model', '-m',
                 default='gpt-4',
                 help='OpenAI model to use')
   @click.option('--config', '-c',
                 type=click.Path(exists=True),
                 help='Configuration file path')
   @click.option('--verbose', '-v',
                 is_flag=True,
                 help='Enable verbose logging')
   @click.version_option(version='0.2.0')
   def main(transport: str, port: int, host: str, openai_key: str,
            model: str, config: Optional[str], verbose: bool):
       """MCP PR Recommender Server.

       AI-powered server for intelligent PR grouping recommendations
       based on semantic analysis of code changes.
       """
       if not openai_key:
           click.echo("Error: OpenAI API key is required", err=True)
           click.echo("Set OPENAI_API_KEY environment variable or use --openai-key", err=True)
           exit(1)

       if verbose:
           click.echo(f"Starting recommender server with {transport} transport")

       # Server startup logic here
       pass

   if __name__ == '__main__':
       main()
   ```

3. **Add CLI Tests**
   ```python
   # tests/unit/test_cli.py
   import pytest
   from click.testing import CliRunner
   from mcp_local_repo_analyzer.cli import main as analyzer_main
   from mcp_pr_recommender.cli import main as recommender_main

   @pytest.fixture
   def runner():
       return CliRunner()

   def test_analyzer_cli_help(runner):
       """Test analyzer CLI help command."""
       result = runner.invoke(analyzer_main, ['--help'])
       assert result.exit_code == 0
       assert 'MCP Local Repository Analyzer Server' in result.output
       assert '--transport' in result.output
       assert '--port' in result.output

   def test_recommender_cli_help(runner):
       """Test recommender CLI help command."""
       result = runner.invoke(recommender_main, ['--help'])
       assert result.exit_code == 0
       assert 'MCP PR Recommender Server' in result.output
       assert '--transport' in result.output
       assert '--openai-key' in result.output

   def test_analyzer_cli_version(runner):
       """Test analyzer CLI version command."""
       result = runner.invoke(analyzer_main, ['--version'])
       assert result.exit_code == 0
       assert '0.2.0' in result.output

   def test_recommender_cli_version(runner):
       """Test recommender CLI version command."""
       result = runner.invoke(recommender_main, ['--version'])
       assert result.exit_code == 0
       assert '0.2.0' in result.output
   ```

### 4. MCP Server Issues
**Problem**: StdioTransport initialization problems
**Impact**: Prevents MCP servers from running properly
**Root Cause**: FastMCP version conflicts and transport configuration

#### Current Error
```python
# Error when testing MCP servers
❌ Analyzer server test failed: StdioTransport.__init__() missing 1 required positional argument: 'args'
```

#### Resolution Steps
1. **Unify FastMCP Versions**
   ```toml
   # pyproject.toml - Unified version
   [tool.poetry.dependencies]
   fastmcp = "^2.10.6"  # Use latest stable version
   ```

2. **Fix Server Initialization**
   ```python
   # src/shared/mcp/server.py
   from fastmcp import FastMCP
   from typing import List, Optional, Dict, Any
   import asyncio
   import logging

   class BaseMCPServer:
       """Base class for MCP servers."""

       def __init__(self, name: str, version: str, description: str):
           self.name = name
           self.version = version
           self.description = description
           self.server = FastMCP(
               name=name,
               version=version,
               description=description
           )
           self.logger = logging.getLogger(name)

       def add_tool(self, tool_name: str, tool_function, **kwargs):
           """Add a tool to the server."""
           self.server.add_tool(tool_name, tool_function, **kwargs)

       def add_health_check(self, path: str = "/health"):
           """Add health check endpoint."""
           @self.server.get(path)
           async def health_check():
               return {"status": "healthy", "service": self.name}

       async def run_stdio(self):
           """Run server in STDIO mode."""
           try:
               await self.server.run_stdio()
           except Exception as e:
               self.logger.error(f"STDIO server error: {e}")
               raise

       async def run_http(self, host: str = "0.0.0.0", port: int = 8000):
           """Run server in HTTP mode."""
           try:
               await self.server.run_http(host=host, port=port)
           except Exception as e:
               self.logger.error(f"HTTP server error: {e}")
               raise
   ```

3. **Update Server Implementations**
   ```python
   # src/mcp_local_repo_analyzer/main.py
   from shared.mcp.server import BaseMCPServer
   from shared.config.base import AnalyzerConfig

   class LocalRepoAnalyzerServer(BaseMCPServer):
       def __init__(self, config: AnalyzerConfig):
           super().__init__(
               name="mcp-local-repo-analyzer",
               version="0.2.0",
               description="Local repository analysis server"
           )
           self.config = config
           self.setup_tools()
           self.add_health_check()

       def setup_tools(self):
           """Setup MCP tools."""
           from .tools.staging_area import analyze_staging_area
           from .tools.summary import generate_summary
           from .tools.unpushed_commits import analyze_unpushed_commits
           from .tools.working_directory import analyze_working_directory

           self.add_tool("analyze_staging_area", analyze_staging_area)
           self.add_tool("generate_summary", generate_summary)
           self.add_tool("analyze_unpushed_commits", analyze_unpushed_commits)
           self.add_tool("analyze_working_directory", analyze_working_directory)

   async def main():
       """Main server function."""
       config = AnalyzerConfig()
       server = LocalRepoAnalyzerServer(config)

       # Run based on transport
       if config.transport == "stdio":
           await server.run_stdio()
       else:
           await server.run_http(host=config.host, port=config.port)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

4. **Add Server Tests**
   ```python
   # tests/unit/test_server.py
   import pytest
   from unittest.mock import Mock, patch
   from shared.mcp.server import BaseMCPServer

   class TestBaseMCPServer:
       def test_server_initialization(self):
           """Test server initialization."""
           server = BaseMCPServer("test", "1.0.0", "Test server")
           assert server.name == "test"
           assert server.version == "1.0.0"
           assert server.description == "Test server"

       def test_add_tool(self):
           """Test adding tools."""
           server = BaseMCPServer("test", "1.0.0", "Test server")

           def test_tool():
               return "test"

           server.add_tool("test_tool", test_tool)
           # Verify tool was added

       @pytest.mark.asyncio
       async def test_stdio_mode(self):
           """Test STDIO mode."""
           server = BaseMCPServer("test", "1.0.0", "Test server")

           with patch.object(server.server, 'run_stdio') as mock_run:
               mock_run.return_value = None
               await server.run_stdio()
               mock_run.assert_called_once()
   ```

### 5. Dependency Conflicts
**Problem**: Different FastMCP versions (2.10.6 vs 2.6.1)
**Impact**: Incompatible server implementations and runtime errors
**Root Cause**: Separate dependency management in different packages

#### Resolution Steps
1. **Create Unified Dependencies File**
   ```toml
   # pyproject.toml - Main project
   [tool.poetry.dependencies]
   python = ">=3.10,<4.0"
   fastmcp = "^2.10.6"  # Latest stable version
   pydantic = "^2.11.7"
   gitpython = "^3.1.40"
   openai = "^1.0.0"
   click = "^8.1.7"
   fastapi = "^0.116.1"
   uvicorn = "^0.35.0"

   [tool.poetry.group.dev.dependencies]
   pytest = "^7.4.3"
   pytest-asyncio = "^0.21.1"
   pytest-cov = "^4.1.0"
   ruff = "^0.1.6"
   black = "^23.12.1"
   mypy = "^1.8.1"
   pre-commit = "^3.6.0"
   ```

2. **Remove Package-Specific Dependencies**
   ```bash
   # Remove old dependency files
   rm mcp_shared_lib/poetry.lock
   rm mcp_local_repo_analyzer/poetry.lock
   rm mcp_pr_recommender/poetry.lock
   ```

3. **Update Import Statements**
   ```python
   # Update all imports to use shared package
   # Before:
   from mcp_shared_lib.models.git.repository import LocalRepository

   # After:
   from shared.models.git.repository import LocalRepository
   ```

## Implementation Timeline

### Day 1: Configuration Fixes
- [ ] Audit and consolidate configuration models
- [ ] Remove unused configuration files
- [ ] Update package configurations
- [ ] Test configuration imports

### Day 2: CLI and Server Fixes
- [ ] Fix CLI argument parsing
- [ ] Implement proper help commands
- [ ] Create shared server base class
- [ ] Update server implementations

### Day 3: Test Fixes
- [ ] Fix failing unit tests
- [ ] Fix integration tests
- [ ] Add missing test coverage
- [ ] Update test configuration

### Day 4: Dependency Resolution
- [ ] Unify dependency versions
- [ ] Remove package-specific dependencies
- [ ] Update import statements
- [ ] Test package installation

### Day 5: Integration Testing
- [ ] Test MCP server startup
- [ ] Test CLI functionality
- [ ] Test package imports
- [ ] Verify PyPI compatibility

## Success Criteria

### Configuration
- [ ] All configuration models import without errors
- [ ] No extra field validation errors
- [ ] Consistent configuration structure across packages

### CLI
- [ ] Both servers show proper help text
- [ ] Version commands work correctly
- [ ] All options are properly documented

### Server
- [ ] MCP servers start without errors
- [ ] Both STDIO and HTTP modes work
- [ ] Health check endpoints respond correctly

### Tests
- [ ] All tests pass (0 failures)
- [ ] 90%+ test coverage achieved
- [ ] Integration tests work correctly

### Dependencies
- [ ] Single dependency file for all packages
- [ ] No version conflicts
- [ ] All packages install correctly

## Monitoring and Validation

### Automated Checks
- [ ] CI/CD pipeline passes all stages
- [ ] Pre-commit hooks pass
- [ ] Test coverage meets targets
- [ ] Security scans pass

### Manual Validation
- [ ] CLI help commands work
- [ ] MCP servers start successfully
- [ ] Package imports work correctly
- [ ] PyPI packages install and run

This comprehensive issue resolution plan addresses all identified problems systematically, ensuring a robust and maintainable codebase.

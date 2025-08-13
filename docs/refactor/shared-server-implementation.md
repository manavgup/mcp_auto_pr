# Shared Server Implementation

## Overview
This document outlines the proper shared server implementation based on analysis of the actual `main.py` files from both MCP servers.

## Code Analysis Results

### Duplicated Functions Found
Both `mcp_local_repo_analyzer/main.py` and `mcp_pr_recommender/main.py` contain nearly identical:

1. **`create_server()`** - Creates FastMCP instance, adds health checks, initializes services
2. **`register_tools()`** - Registers MCP tools (with different tool sets)
3. **`run_stdio_server()`** - Runs server in STDIO mode with error handling
4. **`run_http_server()`** - Runs server in HTTP mode with uvicorn
5. **`main()`** - CLI argument parsing and server startup
6. **`lifespan`** - FastMCP lifecycle management
7. **Health check endpoints** - `/health` and `/healthz` routes

### Key Differences
- **Service initialization** - Different services for each server
- **Tool registration** - Different tool sets
- **Default ports** - Analyzer: 9070, Recommender: 9071
- **Server names and instructions** - Different descriptions

## Proper Shared Server Implementation

### File: `src/shared/mcp/server.py`

```python
#!/usr/bin/env python3
"""Shared MCP server functionality to eliminate code duplication."""

import asyncio
import logging
import sys
import traceback
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """Abstract base class for MCP servers with shared functionality."""

    def __init__(self, name: str, default_port: int = 9070):
        self.name = name
        self.default_port = default_port
        self._server_initialized = False
        self._initialization_lock = asyncio.Lock()

    @property
    def server_initialized(self) -> bool:
        """Get server initialization status."""
        return self._server_initialized

    @asynccontextmanager
    async def lifespan(self, _app: Any) -> AsyncIterator[None]:
        """Manage server lifecycle for proper startup and shutdown."""
        logger.info("FastMCP server starting up...")
        try:
            # Add a small delay to ensure all components are ready
            await asyncio.sleep(0.1)
            async with self._initialization_lock:
                self._server_initialized = True
            logger.info("FastMCP server initialization completed")
            yield
        except Exception as e:
            logger.error(f"Error during server lifecycle: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            logger.info("FastMCP server shutting down...")
            async with self._initialization_lock:
                self._server_initialized = False

    @abstractmethod
    def create_server(self) -> tuple[FastMCP, Dict[str, Any]]:
        """Create and configure the FastMCP server.

        Returns:
            Tuple of (FastMCP server instance, services dict).
        """
        pass

    @abstractmethod
    def register_tools(self, mcp: FastMCP, services: Dict[str, Any]) -> None:
        """Register MCP tools with the server.

        Args:
            mcp: FastMCP server instance.
            services: Dictionary of initialized services.
        """
        pass

    def add_health_checks(self, mcp: FastMCP) -> None:
        """Add health check endpoints to the server.

        Args:
            mcp: FastMCP server instance.
        """
        @mcp.custom_route("/health", methods=["GET"])  # type: ignore[misc]
        async def health_check(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": self.name,
                    "version": "1.0.0",
                    "initialized": self.server_initialized,
                }
            )

        @mcp.custom_route("/healthz", methods=["GET"])  # type: ignore[misc]
        async def health_check_z(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": self.name,
                    "version": "1.0.0",
                    "initialized": self.server_initialized,
                }
            )

    async def run_stdio_server(self) -> None:
        """Run the server in STDIO mode for direct MCP client connections."""
        try:
            logger.info(f"=== Starting {self.name} (STDIO) ===")
            logger.info(f"Python version: {sys.version}")

            # Create server and services
            logger.info("Creating server and services...")
            mcp, services = self.create_server()

            # Register tools with services
            logger.info("Registering tools...")
            self.register_tools(mcp, services)
            logger.info("Tools registration completed")

            # Run the server with enhanced error handling
            try:
                logger.info("Starting FastMCP server in stdio mode...")
                logger.info("Server is ready to receive MCP messages")
                await mcp.run_stdio_async()
            except (BrokenPipeError, EOFError) as e:
                # Handle stdio stream closure gracefully
                logger.info(
                    f"Input stream closed ({type(e).__name__}), shutting down server gracefully"
                )
            except ConnectionResetError as e:
                # Handle connection reset gracefully
                logger.info(f"Connection reset ({e}), shutting down server gracefully")
            except KeyboardInterrupt:
                logger.info("Server stopped by user (KeyboardInterrupt)")
            except Exception as e:
                logger.error(f"Server runtime error: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                sys.exit(1)

        except KeyboardInterrupt:
            logger.info("Server stopped by user during initialization")
        except Exception as e:
            logger.error(f"Server initialization error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)

    def run_http_server(self, host: str = "127.0.0.1", port: int = None,
                       transport: str = "streamable-http") -> None:
        """Run the server in HTTP mode for MCP Gateway integration."""
        if port is None:
            port = self.default_port

        logger.info(f"=== Starting {self.name} (HTTP) ===")
        logger.info(f"🌐 Transport: {transport}")
        logger.info(f"🌐 Endpoint: http://{host}:{port}/mcp")
        logger.info(f"🏥 Health: http://{host}:{port}/health")

        try:
            # Create server and services
            logger.info("Creating server and services...")
            mcp, services = self.create_server()

            # Register tools with services
            logger.info("Registering tools...")
            self.register_tools(mcp, services)
            logger.info("Tools registration completed")

            # Create HTTP app
            app = mcp.http_app(path="/mcp", transport=transport)

            # Run with uvicorn
            import uvicorn
            logger.info("Starting HTTP server...")
            uvicorn.run(app, host=host, port=port, log_level="info")

        except Exception as e:
            logger.error(f"HTTP server error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)


def create_argument_parser(description: str, default_port: int = 9070):
    """Create a standardized argument parser for MCP servers.

    Args:
        description: Server description for help text.
        default_port: Default port for HTTP mode.

    Returns:
        Configured ArgumentParser instance.
    """
    import argparse

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport protocol to use",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (HTTP mode only)"
    )
    parser.add_argument(
        "--port", type=int, default=default_port, help="Port to bind to (HTTP mode only)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    return parser


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging level.

    Args:
        log_level: Logging level string.
    """
    import logging

    level = getattr(logging, log_level.upper())
    logging.getLogger().setLevel(level)


def run_server(server_instance: BaseMCPServer, args) -> None:
    """Run the server based on command line arguments.

    Args:
        server_instance: Instance of BaseMCPServer.
        args: Parsed command line arguments.
    """
    try:
        if args.transport == "stdio":
            # Use asyncio.run to properly manage the event loop for STDIO
            asyncio.run(server_instance.run_stdio_server())
        else:
            # HTTP mode runs synchronously with uvicorn
            server_instance.run_http_server(
                host=args.host,
                port=args.port,
                transport=args.transport
            )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
```

## Usage in MCP Servers

### Example: Local Repo Analyzer

```python
# src/mcp_local_repo_analyzer/main.py
from shared.mcp.server import BaseMCPServer, create_argument_parser, setup_logging, run_server

class LocalRepoAnalyzerServer(BaseMCPServer):
    def __init__(self):
        super().__init__("Local Git Changes Analyzer", default_port=9070)

    def create_server(self) -> tuple[FastMCP, Dict[str, Any]]:
        # Implementation specific to analyzer
        mcp = FastMCP(
            name=self.name,
            lifespan=self.lifespan,
            instructions="...",
        )

        # Add health checks
        self.add_health_checks(mcp)

        # Initialize services
        services = {
            "git_client": GitClient(settings),
            "change_detector": ChangeDetector(git_client),
            # ... other services
        }

        return mcp, services

    def register_tools(self, mcp: FastMCP, services: Dict[str, Any]) -> None:
        # Register analyzer-specific tools
        pass

def main():
    parser = create_argument_parser("MCP Local Repository Analyzer", default_port=9070)
    args = parser.parse_args()

    setup_logging(args.log_level)

    server = LocalRepoAnalyzerServer()
    run_server(server, args)

if __name__ == "__main__":
    main()
```

### Example: PR Recommender

```python
# src/mcp_pr_recommender/main.py
from shared.mcp.server import BaseMCPServer, create_argument_parser, setup_logging, run_server

class PRRecommenderServer(BaseMCPServer):
    def __init__(self):
        super().__init__("PR Recommender", default_port=9071)

    def create_server(self) -> tuple[FastMCP, Dict[str, Any]]:
        # Implementation specific to recommender
        mcp = FastMCP(
            name=self.name,
            version="1.0.0",
            lifespan=self.lifespan,
            instructions="...",
        )

        # Add health checks
        self.add_health_checks(mcp)

        # Initialize services
        services = {
            "pr_generator": PRRecommenderTool(),
            "feasibility_analyzer": FeasibilityAnalyzerTool(),
            # ... other services
        }

        return mcp, services

    def register_tools(self, mcp: FastMCP, services: Dict[str, Any]) -> None:
        # Register recommender-specific tools
        pass

def main():
    parser = create_argument_parser("MCP PR Recommender Server", default_port=9071)
    args = parser.parse_args()

    setup_logging(args.log_level)

    server = PRRecommenderServer()
    run_server(server, args)

if __name__ == "__main__":
    main()
```

## Benefits of This Approach

### 1. **Eliminates Code Duplication**
- Single implementation of `run_stdio_server()` and `run_http_server()`
- Shared error handling and logging patterns
- Consistent health check endpoints

### 2. **Maintains Flexibility**
- Each server can customize service creation and tool registration
- Different default ports and server names
- Custom server instructions and metadata

### 3. **Improves Maintainability**
- Bug fixes in server logic apply to all servers
- Consistent behavior across the ecosystem
- Easier to add new server types

### 4. **Preserves FastMCP Integration**
- Uses FastMCP's native transport handling
- No custom transport implementation needed
- Leverages FastMCP's built-in features

## Migration Steps

### 1. **Create Shared Server Module**
- Create `src/shared/mcp/server.py`
- Implement `BaseMCPServer` abstract class
- Add shared utility functions

### 2. **Update MCP Servers**
- Inherit from `BaseMCPServer`
- Implement abstract methods
- Use shared argument parsing and server running

### 3. **Test Integration**
- Verify both servers work with shared base class
- Test all transport modes
- Ensure health checks work correctly

### 4. **Remove Duplicated Code**
- Delete old server functions from individual servers
- Update imports to use shared module
- Verify no functionality is lost

This approach provides a clean, maintainable solution that eliminates code duplication while preserving the flexibility needed for different MCP server types.

#!/usr/bin/env python3
"""Enhanced main.py with both STDIO and HTTP transport support."""

import argparse
import asyncio
import logging
import os
import sys
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_local_repo_analyzer.services.git import (
    ChangeDetector,
    DiffAnalyzer,
    StatusTracker,
)
# from mcp_shared_lib.config import settings
from mcp_shared_lib.services import GitClient
from mcp_shared_lib.utils import logging_service

logger = logging_service.get_logger(__name__)

# Global initialization state
_server_initialized = False
_initialization_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(_app: Any) -> AsyncIterator[None]:
    """Manage server lifecycle for proper startup and shutdown."""
    global _server_initialized
    logger.info("FastMCP server starting up...")
    try:
        # Add a small delay to ensure all components are ready
        await asyncio.sleep(0.1)
        async with _initialization_lock:
            _server_initialized = True
        logger.info("FastMCP server initialization completed")
        yield
    except Exception as e:
        logger.error(f"Error during server lifecycle: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        logger.info("FastMCP server shutting down...")
        async with _initialization_lock:
            _server_initialized = False


def create_server() -> tuple[FastMCP, dict[str, Any]]:
    """Create and configure the FastMCP server."""
    try:
        logger.info("Creating FastMCP server instance...")

        # Create the FastMCP server with proper lifecycle management
        mcp = FastMCP(
            name="Local Git Changes Analyzer",
            # Removed version argument because FastMCP.__init__ does not accept it
            lifespan=lifespan,
            instructions=""" \
            This server analyzes outstanding local git changes that haven't made their way to GitHub yet.

            Available tools:
            - analyze_working_directory: Check uncommitted changes in working directory
            - analyze_staged_changes: Check staged changes ready for commit
            - analyze_unpushed_commits: Check commits not pushed to remote
            - analyze_stashed_changes: Check stashed changes
            - get_outstanding_summary: Get comprehensive summary of all outstanding changes
            - compare_with_remote: Compare local branch with remote branch
            - get_repository_health: Get overall repository health metrics

            Provide a repository path to analyze, or the tool will attempt to find a git repository
            in the current directory or use the default configured path.
            """,
        )
        logger.info("FastMCP server instance created successfully")

        # Add health check endpoints for HTTP mode
        @mcp.custom_route("/health", methods=["GET"])  # type: ignore[misc]
        async def health_check(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": "Local Git Changes Analyzer",
                    "version": "1.0.0",
                    "initialized": _server_initialized,
                }
            )

        @mcp.custom_route("/healthz", methods=["GET"])  # type: ignore[misc]
        async def health_check_z(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": "Local Git Changes Analyzer",
                    "version": "1.0.0",
                    "initialized": _server_initialized,
                }
            )

        # Initialize services with error handling
        logger.info("Initializing services...")

        try:
            git_client = GitClient(settings)
            logger.info("GitClient initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GitClient: {e}")
            raise

        try:
            change_detector = ChangeDetector(git_client)
            logger.info("ChangeDetector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ChangeDetector: {e}")
            raise

        try:
            diff_analyzer = DiffAnalyzer(settings)
            logger.info("DiffAnalyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DiffAnalyzer: {e}")
            raise

        try:
            status_tracker = StatusTracker(git_client, change_detector)
            logger.info("StatusTracker initialized")
        except Exception as e:
            logger.error(f"Failed to initialize StatusTracker: {e}")
            raise

        # Create services dict for dependency injection
        services = {
            "git_client": git_client,
            "change_detector": change_detector,
            "diff_analyzer": diff_analyzer,
            "status_tracker": status_tracker,
        }

        logger.info("All services initialized successfully")
        return mcp, services

    except Exception as e:
        logger.error(f"Failed to create server: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def register_tools(mcp: FastMCP, services: dict[str, Any]) -> None:
    """Register all tools with the FastMCP server."""
    try:
        logger.info("Starting tool registration")

        # Import and register tool modules with individual error handling
        try:
            from mcp_local_repo_analyzer.tools.working_directory import (
                register_working_directory_tools,
            )

            logger.info("Registering working directory tools")
            register_working_directory_tools(mcp, services)
            logger.info("Working directory tools registered successfully")
        except Exception as e:
            logger.error(f"Failed to register working directory tools: {e}")
            raise

        try:
            from mcp_local_repo_analyzer.tools.staging_area import (
                register_staging_area_tools,
            )

            logger.info("Registering staging area tools")
            register_staging_area_tools(mcp, services)
            logger.info("Staging area tools registered successfully")
        except Exception as e:
            logger.error(f"Failed to register staging area tools: {e}")
            raise

        try:
            from mcp_local_repo_analyzer.tools.unpushed_commits import (
                register_unpushed_commits_tools,
            )

            logger.info("Registering unpushed commits tools")
            register_unpushed_commits_tools(mcp, services)
            logger.info("Unpushed commits tools registered successfully")
        except Exception as e:
            logger.error(f"Failed to register unpushed commits tools: {e}")
            raise

        try:
            from mcp_local_repo_analyzer.tools.summary import register_summary_tools

            logger.info("Registering summary tools")
            register_summary_tools(mcp, services)
            logger.info("Summary tools registered successfully")
        except Exception as e:
            logger.error(f"Failed to register summary tools: {e}")
            raise

        logger.info("All tools registered successfully")

    except Exception as e:
        logger.error(f"Failed to register tools: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def run_stdio_server() -> None:
    """Run the server in STDIO mode for direct MCP client connections."""
    try:
        logger.info("=== Starting Local Repo Analyzer (STDIO) ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")

        # Create server and services
        logger.info("Creating server and services...")
        mcp, services = create_server()

        # Register tools with services
        logger.info("Registering tools...")
        register_tools(mcp, services)
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


def run_http_server(
    host: str = "127.0.0.1", port: int = 9070, transport: str = "streamable-http"
) -> None:
    """Run the server in HTTP mode for MCP Gateway integration."""
    logger.info("=== Starting Local Repo Analyzer (HTTP) ===")
    logger.info(f"🌐 Transport: {transport}")
    logger.info(f"🌐 Endpoint: http://{host}:{port}/mcp")
    logger.info(f"🏥 Health: http://{host}:{port}/health")

    try:
        # Create server and services
        logger.info("Creating server and services...")
        mcp, services = create_server()

        # Register tools with services
        logger.info("Registering tools...")
        register_tools(mcp, services)
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


def main() -> None:
    """Run the main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="MCP Local Repository Analyzer")
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
        "--port", type=int, default=9070, help="Port to bind to (HTTP mode only)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    parser.add_argument(
        "--work-dir", help="Default working directory for Git operations"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Set default work directory - Docker volume mount support
    work_dir = args.work_dir or os.getenv("WORK_DIR")
    if not work_dir:
        # If /repo exists (Docker volume mount), use it, otherwise use current dir
        work_dir = "/repo" if os.path.exists("/repo") else "."

    # Set the working directory
    if work_dir != ".":
        os.chdir(work_dir)
        logger.info(f"Changed working directory to: {work_dir}")

    try:
        if args.transport == "stdio":
            # Use asyncio.run to properly manage the event loop for STDIO
            asyncio.run(run_stdio_server())
        else:
            # HTTP mode runs synchronously with uvicorn
            run_http_server(host=args.host, port=args.port, transport=args.transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()

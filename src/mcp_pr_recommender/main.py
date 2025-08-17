#!/usr/bin/env python3
"""FastMCP PR Recommender Server.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

Main entry point for the PR recommender server with both STDIO and HTTP transport support.
Provides server setup, tool registration, and server execution.
"""
import argparse
import asyncio
import sys
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP
from mcp_shared_lib.utils import logging_service
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_pr_recommender.prompts import (
    get_enhanced_grouping_system_prompt,
    get_grouping_user_prompt,
)
from mcp_pr_recommender.tools import (
    FeasibilityAnalyzerTool,
    PRRecommenderTool,
    StrategyManagerTool,
    ValidatorTool,
)

logger = logging_service.get_logger(__name__)

# Global initialization state
_server_initialized = False
_initialization_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(_app: object) -> AsyncIterator[None]:
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
    """Create and configure the FastMCP server.

    Returns:
        Tuple of (FastMCP server instance, services dict).
    """
    try:
        logger.info("Creating FastMCP server instance...")

        # Create the FastMCP server with proper lifecycle management
        mcp = FastMCP(
            name="PR Recommender",
            version="1.0.0",
            lifespan=lifespan,
            instructions=""" \
            Intelligent PR boundary detection and recommendation system.

            This server analyzes git changes and generates atomic, logically-grouped
            PR recommendations optimized for code review efficiency and deployment safety.

            Available tools:
            - generate_pr_recommendations: Main tool to generate PR recommendations from git analysis
            - analyze_pr_feasibility: Analyze feasibility and risks of specific recommendations
            - get_strategy_options: Get available grouping strategies and settings
            - validate_pr_recommendations: Validate generated recommendations for quality

            Input: Expects git analysis data from mcp_local_repo_analyzer
            Output: Structured PR recommendations with titles, descriptions, and rationale

            Provide git analysis data to generate recommendations, or use individual tools
            for specific analysis tasks.
            """,
        )
        logger.info("FastMCP server instance created successfully")

        # Add health check endpoints for HTTP mode
        @mcp.custom_route("/health", methods=["GET"])  # type: ignore[misc]
        async def health_check(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": "PR Recommender",
                    "version": "1.0.0",
                    "initialized": _server_initialized,
                }
            )

        @mcp.custom_route("/healthz", methods=["GET"])  # type: ignore[misc]
        async def health_check_z(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": "PR Recommender",
                    "version": "1.0.0",
                    "initialized": _server_initialized,
                }
            )

        # Initialize services with error handling
        logger.info("Initializing services...")

        try:
            pr_generator = PRRecommenderTool()
            logger.info("PRRecommenderTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PRRecommenderTool: {e}")
            raise

        try:
            feasibility_analyzer = FeasibilityAnalyzerTool()
            logger.info("FeasibilityAnalyzerTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize FeasibilityAnalyzerTool: {e}")
            raise

        try:
            strategy_manager = StrategyManagerTool()
            logger.info("StrategyManagerTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize StrategyManagerTool: {e}")
            raise

        try:
            validator = ValidatorTool()
            logger.info("ValidatorTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ValidatorTool: {e}")
            raise

        # Create services dict for dependency injection
        services = {
            "pr_generator": pr_generator,
            "feasibility_analyzer": feasibility_analyzer,
            "strategy_manager": strategy_manager,
            "validator": validator,
        }

        logger.info("All services initialized successfully")
        return mcp, services

    except Exception as e:
        logger.error(f"Failed to create server: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def register_prompts(mcp: FastMCP) -> None:
    """Register prompts with the FastMCP server for MCP inspector visibility.

    Args:
        mcp: FastMCP server instance.
    """
    try:
        logger.info("Starting prompt registration")

        @mcp.prompt  # type: ignore[misc]
        def grouping_system_prompt() -> str:
            """Enhanced system prompt for intelligent PR grouping with file analysis and constraints."""
            return get_enhanced_grouping_system_prompt()

        @mcp.prompt  # type: ignore[misc]
        def grouping_user_prompt(
            files_count: int,
            files_with_changes: int,
            files_without_changes: int,
            total_changes: int,
            risk_level: str,
            file_list: str,
            summary: str,
        ) -> str:
            """User prompt template for LLM file grouping with dynamic file information."""
            return get_grouping_user_prompt(
                files_count,
                files_with_changes,
                files_without_changes,
                total_changes,
                risk_level,
                file_list,
                summary,
            )

        logger.info("Prompt registration completed successfully")

    except Exception as e:
        logger.error(f"Failed to register prompts: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the FastMCP server.

    Args:
        mcp: FastMCP server instance.
    """
    try:
        logger.info("Starting tool registration")

        from typing import Any

        from fastmcp import Context
        from pydantic import Field

        @mcp.tool()  # type: ignore[misc]
        async def generate_pr_recommendations(
            ctx: Context,
            analysis_data: dict[str, Any] = Field(
                ..., description="Git analysis data from mcp_local_repo_analyzer"
            ),
            strategy: str = Field(
                default="semantic", description="Grouping strategy to use"
            ),
            max_files_per_pr: int = Field(
                default=8, description="Maximum files per PR"
            ),
        ) -> dict[str, Any]:
            """Generate PR recommendations from git analysis data."""
            await ctx.info(f"Generating PR recommendations using {strategy} strategy")
            try:
                return await mcp.pr_generator.generate_recommendations(  # type: ignore[no-any-return]
                    analysis_data, strategy, max_files_per_pr
                )
            except Exception as e:
                await ctx.error(f"Failed to generate PR recommendations: {str(e)}")
                return {"error": f"Failed to generate recommendations: {str(e)}"}

        @mcp.tool()  # type: ignore[misc]
        async def analyze_pr_feasibility(
            ctx: Context,
            pr_recommendation: dict[str, Any] = Field(
                ..., description="PR recommendation to analyze"
            ),
        ) -> dict[str, Any]:
            """Analyze the feasibility and risks of a specific PR recommendation."""
            await ctx.info("Analyzing PR feasibility")
            try:
                return await mcp.feasibility_analyzer.analyze_feasibility(  # type: ignore[no-any-return]
                    pr_recommendation
                )
            except Exception as e:
                await ctx.error(f"Failed to analyze PR feasibility: {str(e)}")
                return {"error": f"Failed to analyze feasibility: {str(e)}"}

        @mcp.tool()  # type: ignore[misc]
        async def get_strategy_options(
            ctx: Context,
        ) -> dict[str, Any]:
            """Get available PR grouping strategies and their descriptions."""
            await ctx.info("Retrieving available strategies")
            try:
                return await mcp.strategy_manager.get_strategies()  # type: ignore[no-any-return]
            except Exception as e:
                await ctx.error(f"Failed to get strategy options: {str(e)}")
                return {"error": f"Failed to get strategies: {str(e)}"}

        @mcp.tool()  # type: ignore[misc]
        async def validate_pr_recommendations(
            ctx: Context,
            recommendations: list[dict[str, Any]] = Field(
                ..., description="List of PR recommendations to validate"
            ),
        ) -> dict[str, Any]:
            """Validate a set of PR recommendations for completeness and atomicity."""
            await ctx.info(f"Validating {len(recommendations)} PR recommendations")
            try:
                return await mcp.validator.validate_recommendations(recommendations)  # type: ignore[no-any-return]
            except Exception as e:
                await ctx.error(f"Failed to validate PR recommendations: {str(e)}")
                return {"error": f"Failed to validate recommendations: {str(e)}"}

        logger.info("Tool registration completed successfully")

    except Exception as e:
        logger.error(f"Failed to register tools: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def run_stdio_server() -> None:
    """Run the server in STDIO mode for direct MCP client connections."""
    try:
        logger.info("=== Starting PR Recommender (STDIO) ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {sys.path[0] if sys.path else 'unknown'}")

        # Create server and services
        logger.info("Creating server and services...")
        mcp, services = create_server()

        # Store services in the server context for tools to access
        logger.info("Setting up server context...")
        mcp.pr_generator = services["pr_generator"]
        mcp.feasibility_analyzer = services["feasibility_analyzer"]
        mcp.strategy_manager = services["strategy_manager"]
        mcp.validator = services["validator"]
        logger.info("Server context configured")

        # Register prompts first
        logger.info("Registering prompts...")
        register_prompts(mcp)
        logger.info("Prompts registration completed")

        # Register tools
        logger.info("Registering tools...")
        register_tools(mcp)
        logger.info("Tools registration completed")

        # Run the server with enhanced error handling
        try:
            logger.info("Starting FastMCP server in stdio mode...")
            logger.info("Server is ready to receive MCP messages")
            # Use run_async instead of run for better async handling
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
    host: str = "127.0.0.1", port: int = 9071, transport: str = "streamable-http"
) -> None:
    """Run the server in HTTP mode for MCP Gateway integration."""
    logger.info("=== Starting PR Recommender (HTTP) ===")
    logger.info(f"🌐 Transport: {transport}")
    logger.info(f"🌐 Endpoint: http://{host}:{port}/mcp")
    logger.info(f"🏥 Health: http://{host}:{port}/health")

    try:
        # Create server and services
        logger.info("Creating server and services...")
        mcp, services = create_server()

        # Store services in the server context for tools to access
        logger.info("Setting up server context...")
        mcp.pr_generator = services["pr_generator"]
        mcp.feasibility_analyzer = services["feasibility_analyzer"]
        mcp.strategy_manager = services["strategy_manager"]
        mcp.validator = services["validator"]
        logger.info("Server context configured")

        # Register prompts first
        logger.info("Registering prompts...")
        register_prompts(mcp)
        logger.info("Prompts registration completed")

        # Register tools
        logger.info("Registering tools...")
        register_tools(mcp)
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


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging level."""
    # Your existing logging setup through logging_service should handle this
    # Just ensure the level is properly set
    import logging

    level = getattr(logging, log_level.upper())
    logging.getLogger().setLevel(level)


def main() -> None:
    """Run the main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="MCP PR Recommender Server")
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
        "--port",
        type=int,
        default=9071,  # Different default port from local analyzer
        help="Port to bind to (HTTP mode only)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

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

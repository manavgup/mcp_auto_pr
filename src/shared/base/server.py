#!/usr/bin/env python3
"""Base MCP Server with common infrastructure for lifespan, health checks, CLI parsing, and transport configuration."""

import argparse
import asyncio
import os
import sys
import traceback
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..utils import logging_service


class BaseMCPServer(ABC):
    """Base class for MCP servers with common infrastructure patterns."""

    def __init__(self) -> None:
        """Initialize base server with common components."""
        self.logger = logging_service.get_logger(self.__class__.__name__)
        self._server_initialized = False
        self._initialization_lock = asyncio.Lock()
        self.mcp: FastMCP | None = None
        self.services: dict[str, Any] = {}

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return the display name for this service."""
        pass

    @property
    @abstractmethod
    def service_version(self) -> str:
        """Return the version for this service."""
        pass

    @property
    @abstractmethod
    def service_instructions(self) -> str:
        """Return the instructions for this service."""
        pass

    @property
    def default_port(self) -> int:
        """Return the default port for this service. Override if needed."""
        return 9070

    @abstractmethod
    async def register_tools(self, mcp: FastMCP, services: dict[str, Any]) -> None:
        """Register service-specific tools with the MCP server.

        Args:
            mcp: The FastMCP server instance
            services: Dictionary of initialized services
        """
        pass

    @abstractmethod
    async def initialize_services(self) -> dict[str, Any]:
        """Initialize service-specific components.

        Returns:
            Dictionary of initialized services to pass to tools
        """
        pass

    @asynccontextmanager
    async def lifespan(self, _app: Any) -> AsyncIterator[None]:
        """Manage server lifecycle for proper startup and shutdown."""
        self.logger.info("FastMCP server starting up...")
        try:
            # Add a small delay to ensure all components are ready
            await asyncio.sleep(0.1)
            async with self._initialization_lock:
                self._server_initialized = True
            self.logger.info("FastMCP server initialization completed")
            yield
        except Exception as e:
            self.logger.error(f"Error during server lifecycle: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            self.logger.info("FastMCP server shutting down...")
            async with self._initialization_lock:
                self._server_initialized = False

    def add_health_endpoints(self, mcp: FastMCP) -> None:
        """Add standard health check endpoints."""

        @mcp.custom_route("/health", methods=["GET"])
        async def health_check(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": self.service_name,
                    "version": self.service_version,
                    "initialized": self._server_initialized,
                }
            )

        @mcp.custom_route("/healthz", methods=["GET"])
        async def health_check_z(_request: Request) -> JSONResponse:
            return JSONResponse(
                {
                    "status": "ok",
                    "service": self.service_name,
                    "version": self.service_version,
                    "initialized": self._server_initialized,
                }
            )

    async def create_server(self) -> tuple[FastMCP, dict[str, Any]]:
        """Create and configure the FastMCP server."""
        try:
            self.logger.info("Creating FastMCP server instance...")

            # Create the FastMCP server with proper lifecycle management
            self.mcp = FastMCP(
                name=self.service_name,
                lifespan=self.lifespan,
                instructions=self.service_instructions,
            )
            self.logger.info("FastMCP server instance created successfully")

            # Add health check endpoints for HTTP mode
            self.add_health_endpoints(self.mcp)

            # Initialize services with error handling
            self.logger.info("Initializing services...")
            self.services = await self.initialize_services()
            self.logger.info("Services initialized successfully")

            # Register tools with error handling
            self.logger.info("Registering tools...")
            await self.register_tools(self.mcp, self.services)
            self.logger.info("Tools registered successfully")

            return self.mcp, self.services

        except Exception as e:
            self.logger.error(f"Failed to create server: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def create_cli_parser(self) -> argparse.ArgumentParser:
        """Create standard CLI argument parser with common options."""
        parser = argparse.ArgumentParser(description=f"MCP {self.service_name}")
        parser.add_argument(
            "--transport",
            choices=["stdio", "streamable-http", "sse"],
            default="stdio",
            help="Transport protocol to use",
        )
        parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (HTTP mode only)")
        parser.add_argument(
            "--port",
            type=int,
            default=self.default_port,
            help="Port to bind to (HTTP mode only)",
        )
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Logging level",
        )
        parser.add_argument("--work-dir", help="Default working directory for operations")
        return parser

    def setup_logging(self, args: argparse.Namespace) -> None:
        """Configure logging for the server.

        This method can be overridden by subclasses to implement custom logging setup.
        By default, logging is handled by the logging service.
        """
        # Note: Logging is now handled by the logging service
        # The service will configure logging when it's initialized
        # Subclasses can override this method to implement custom logging setup
        # For now, we just log that logging setup was called
        self.logger.debug(f"Logging setup called with level: {args.log_level}")

    def determine_work_dir(self, args: argparse.Namespace) -> str:
        """Determine working directory with Docker volume mount support."""
        work_dir = args.work_dir or os.getenv("WORK_DIR")
        if not work_dir:
            # If /repo exists (Docker volume mount), use it, otherwise use current dir
            work_dir = "/repo" if os.path.exists("/repo") else "."
        return work_dir

    async def run_stdio_mode(self) -> None:
        """Run server in STDIO mode."""
        try:
            self.logger.info(f"Starting {self.service_name} in STDIO mode...")
            mcp, _ = await self.create_server()
            self.logger.info("Running MCP server with stdio transport...")
            await mcp.run(transport="stdio")  # type: ignore[func-returns-value]
        except Exception as e:
            self.logger.error(f"Error in STDIO mode: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)

    async def run_http_mode(self, host: str, port: int) -> None:
        """Run server in HTTP mode."""
        try:
            self.logger.info(f"Starting {self.service_name} in HTTP mode on {host}:{port}...")
            mcp, _ = await self.create_server()
            self.logger.info(f"Running MCP server with streamable-http transport on {host}:{port}...")
            await mcp.run(transport="streamable-http", host=host, port=port)  # type: ignore[func-returns-value]
        except Exception as e:
            self.logger.error(f"Error in HTTP mode: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)

    async def run_sse_mode(self, host: str, port: int) -> None:
        """Run server in SSE mode."""
        try:
            self.logger.info(f"Starting {self.service_name} in SSE mode on {host}:{port}...")
            mcp, _ = await self.create_server()
            self.logger.info(f"Running MCP server with SSE transport on {host}:{port}...")
            await mcp.run(transport="sse", host=host, port=port)  # type: ignore[func-returns-value]
        except Exception as e:
            self.logger.error(f"Error in SSE mode: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)

    def main(self) -> None:
        """Run the server with command line argument parsing and transport selection."""
        parser = self.create_cli_parser()
        args = parser.parse_args()

        # Setup logging
        self.setup_logging(args)

        # Set default work directory with Docker volume mount support
        work_dir = self.determine_work_dir(args)

        # Set the working directory
        if work_dir != ".":
            try:
                os.chdir(work_dir)
                self.logger.info(f"Changed working directory to: {work_dir}")
            except OSError as e:
                self.logger.error(f"Failed to change to directory {work_dir}: {e}")
                sys.exit(1)

        # Run server based on transport mode
        if args.transport == "stdio":
            asyncio.run(self.run_stdio_mode())
        elif args.transport == "streamable-http":
            asyncio.run(self.run_http_mode(args.host, args.port))
        elif args.transport == "sse":
            asyncio.run(self.run_sse_mode(args.host, args.port))
        else:
            self.logger.error(f"Unknown transport: {args.transport}")
            sys.exit(1)

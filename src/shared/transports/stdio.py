"""Stdio transport implementation."""

import sys
from typing import Any

from fastmcp import FastMCP

from .base import BaseTransport
from .config import TransportConfig


class StdioTransport(BaseTransport):
    """Stdio transport for MCP servers.

    This transport uses stdin/stdout for communication, which is the default
    MCP transport mode. It's ideal for development and process-to-process communication.
    """

    def __init__(self, config: TransportConfig, server_name: str = "MCP Server"):
        """Initialize stdio transport.

        Args:
            config: Transport configuration
            server_name: Name of the server for logging and identification
        """
        super().__init__(config, server_name)
        # Stdio doesn't have specific config in the current structure
        self._stdio_config = None

    def run(self, server: FastMCP) -> None:
        """Run the stdio transport server.

        Args:
            server (FastMCP): The FastMCP server instance to run.

        This method starts the MCP server using stdio as the transport mechanism.
        It sets the running state and logs the start and any errors encountered.
        """
        try:
            self.server = server
            self._is_running = True
            self.logger.info(f"Starting {self.server_name} with stdio transport")
            server.run(transport="stdio")
        except Exception as e:
            self.logger.error(f"Stdio transport error: {e}")
            raise
        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stop the stdio transport.

        This is a no-operation method since stdio transport does not require explicit stopping.
        Logs the stop action for informational purposes.
        """
        self.logger.info("Stopping stdio transport (noop)")
        pass

    def is_running(self) -> bool:
        """Check if the stdio transport is currently running.

        Returns:
            bool: True if running, False otherwise.
        """
        return getattr(self, "_is_running", False)

    def get_connection_info(self) -> dict[str, Any]:
        """Get connection information for the stdio transport."""
        return {"transport": "stdio"}

    def get_health_status(self) -> dict[str, Any]:
        """Get health status for stdio transport.

        Returns:
            Dictionary containing health status information
        """
        status = super().get_health_status()

        # Add stdio-specific health checks
        stdio_healthy = (
            not sys.stdin.closed and not sys.stdout.closed and self._is_running
        )

        status.update(
            {
                "stdio_healthy": stdio_healthy,
                "stdin_available": not sys.stdin.closed,
                "stdout_available": not sys.stdout.closed,
            }
        )

        # Override status if stdio streams are not healthy
        if not stdio_healthy:
            status["status"] = "unhealthy"

        return status

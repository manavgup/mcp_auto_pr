"""Base transport class and common utilities."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from fastmcp import FastMCP

from mcp_shared_lib.utils import logging_service

from .config import HTTPConfig, SSEConfig, TransportConfig


class TransportError(Exception):
    """Base exception for transport-related errors."""

    pass


class BaseTransport(ABC):
    """Abstract base class for MCP transports.

    This class defines the interface that all transport implementations must follow.
    It provides common functionality like logging setup and health check endpoints.
    """

    def __init__(self, config: TransportConfig, server_name: str = "MCP Server"):
        """Initialize the transport.

        Args:
            config: Transport configuration
            server_name: Name of the server for logging and identification
        """
        self.config = config
        self.server_name = server_name
        self.logger = logging_service.get_logger(
            f"{__name__}.{self.__class__.__name__}"
        )
        self._setup_logging()

        # Server instance will be set when running
        self.server: FastMCP | None = None
        self._is_running = False

    def _setup_logging(self) -> None:
        """Configure logging based on transport configuration."""
        log_config = self.config.logging

        # Set log level
        log_level = getattr(logging, log_config.level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        if log_config.transport_details:
            self.logger.info(f"Transport configured: {self.config.type}")
            self.logger.debug(f"Transport config: {self.config}")

    @abstractmethod
    def run(self, server: FastMCP) -> None:
        """Run the server with this transport.

        Args:
            server: FastMCP server instance to run

        Raises:
            TransportError: If transport fails to start
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the transport and clean up resources."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if the transport is currently running.

        Returns:
            True if transport is running, False otherwise
        """
        pass

    @abstractmethod
    def get_connection_info(self) -> dict[str, Any]:
        """Get connection information for this transport.

        Returns:
            Dictionary containing connection details (host, port, etc.)
        """
        pass

    def get_health_status(self) -> dict[str, Any]:
        """Get health status information.

        Returns:
            Dictionary containing health status information
        """
        return {
            "status": "healthy" if self.is_running() else "stopped",
            "transport": self.config.type,
            "server_name": self.server_name,
            "connection_info": self.get_connection_info(),
        }

    def _log_request(self, method: str, details: dict[str, Any]) -> None:
        """Log request details if request logging is enabled.

        Args:
            method: HTTP method or operation type
            details: Request details to log
        """
        if self.config.logging.request_logging:
            self.logger.info(f"{method} request: {details}")

    def _log_error(self, error: Exception, context: str = "") -> None:
        """Log error details if error logging is enabled.

        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        if self.config.logging.error_details:
            if context:
                self.logger.error(f"Error in {context}: {error}", exc_info=True)
            else:
                self.logger.error(f"Transport error: {error}", exc_info=True)
        else:
            self.logger.error(f"Transport error: {error}")


class HttpBasedTransport(BaseTransport):
    """Base class for HTTP-based transports (HTTP, WebSocket, SSE).

    Provides common functionality for transports that use HTTP protocols.
    """

    def __init__(self, config: TransportConfig, server_name: str = "MCP Server"):
        """Initialize HTTP-based transport."""
        super().__init__(config, server_name)
        self._server_process: Any | None = None

    def get_connection_info(self) -> dict[str, Any]:
        """Get HTTP connection information."""
        return {
            "protocol": self.config.type,
        }

    def _setup_health_check(self, _server: FastMCP) -> None:
        """Set up health check endpoint for HTTP-based transports.

        Args:
            _server: FastMCP server instance (unused in base implementation)
        """
        transport_config = self.config.get_transport_config()

        # Only add health check if enabled and transport supports it
        if transport_config and getattr(transport_config, "enable_health_check", False):
            health_path = getattr(transport_config, "health_check_path", "/health")

            @_server.resource(f"health://{health_path}")  # type: ignore[misc]
            async def health_check() -> str:
                """Health check endpoint."""
                status = self.get_health_status()
                return (
                    f"Server Status: {status['status']}\n"
                    f"Transport: {status['transport']}\n"
                    f"Server: {status['server_name']}\n"
                )

    def _setup_cors(self, _server: FastMCP) -> None:
        """Set up CORS configuration for HTTP-based transports.

        Args:
            _server: FastMCP server instance (unused in base implementation)
        """
        transport_config = self.config.get_transport_config()

        # CORS configuration (if supported by transport)
        if (
            transport_config
            and hasattr(transport_config, "cors_origins")
            and isinstance(transport_config, HTTPConfig | SSEConfig)
        ):
            self.logger.debug(f"CORS origins: {transport_config.cors_origins}")
            # Note: Actual CORS implementation would depend on FastMCP's capabilities
            # This is a placeholder for future CORS implementation

    def stop(self) -> None:
        """Stop HTTP-based transport."""
        if self._server_process is not None:
            try:
                self._server_process.terminate()
            except Exception as e:
                self._log_error(e, "stopping server")

        self._server_process = None
        self._is_running = False
        self.logger.info(f"{self.server_name} stopped")

    def is_running(self) -> bool:
        """Check if HTTP-based transport is running."""
        if not self._is_running:
            return False
        if self._server_process is None:
            return False
        return self._server_process.poll() is None

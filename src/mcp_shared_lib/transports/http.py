"""HTTP transport implementation."""

from typing import Any

from fastmcp import FastMCP

from .base import HttpBasedTransport, TransportError
from .config import TransportConfig


class HttpTransport(HttpBasedTransport):
    """HTTP transport for MCP servers.

    This transport uses HTTP with streamable requests for communication.
    It's ideal for web-based clients and production deployments.
    """

    def __init__(self, config: TransportConfig, server_name: str = "MCP Server"):
        """Initialize HTTP transport.

        Args:
            config: Transport configuration
            server_name: Name of the server for logging and identification
        """
        super().__init__(config, server_name)
        self._http_config = config.http

    def run(self, server: FastMCP) -> None:
        """Run the server with HTTP transport.

        Args:
            server: FastMCP server instance to run

        Raises:
            TransportError: If transport fails to start
        """
        try:
            self.server = server
            self._is_running = True

            if not self._http_config:
                raise TransportError("HTTP config is required for HTTP transport")

            # Register health check endpoint if enabled
            if self._http_config.enable_health_check:
                self._register_health_endpoint(server)

            self.logger.info(
                f"Starting {self.server_name} with HTTP transport on "
                f"{self._http_config.host}:{self._http_config.port}"
            )
            self.logger.debug(f"HTTP config: {self._http_config}")

            # Run the FastMCP server with streamable HTTP transport
            server.run(
                transport="streamable-http",
                host=self._http_config.host,
                port=self._http_config.port,
            )

        except KeyboardInterrupt:
            self.logger.info("Server stopped by user (Ctrl+C)")
            self.stop()
        except Exception as e:
            self._log_error(e, "running HTTP transport")
            raise TransportError(f"Failed to start HTTP transport: {e}") from e
        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stop the HTTP transport."""
        if self._is_running:
            self.logger.info(f"Stopping {self.server_name} HTTP transport")
            super().stop()

    def is_running(self) -> bool:
        """Check if the HTTP transport is running."""
        return self._is_running

    def get_connection_info(self) -> dict[str, Any]:
        """Get HTTP connection information."""
        if not self._http_config:
            return {"protocol": "http", "error": "No HTTP config"}

        return {
            "url": f"http://{self._http_config.host}:{self._http_config.port}",
            "cors_enabled": bool(self._http_config.cors_origins),
            "cors_origins": self._http_config.cors_origins,
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get health status for HTTP transport."""
        status = super().get_health_status()

        # Add HTTP-specific health information
        if self._http_config:
            status.update(
                {
                    "http_healthy": self._is_running,
                    "endpoint": f"http://{self._http_config.host}:{self._http_config.port}",
                    "health_check_enabled": self._http_config.enable_health_check,
                }
            )
        else:
            status.update(
                {
                    "http_healthy": False,
                    "endpoint": "No HTTP config",
                    "health_check_enabled": False,
                }
            )

        return status

    def _register_health_endpoint(self, server: FastMCP) -> None:
        """Register health check endpoint using FastMCP's custom_route decorator.

        Args:
            server: FastMCP server instance
        """
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        if not self._http_config:
            return

        health_path = self._http_config.health_check_path

        @server.custom_route(health_path, methods=["GET"])  # type: ignore
        async def health_check(_request: Request) -> JSONResponse:
            """Health check endpoint for HTTP transport."""
            try:
                status = self.get_health_status()
                if status["status"] == "healthy":
                    return JSONResponse(
                        {
                            "status": "ok",
                            "message": f"Server is healthy - {self.server_name}",
                            "details": status,
                        }
                    )
                else:
                    return JSONResponse(
                        {
                            "status": "error",
                            "message": f"Server status: {status['status']} - {self.server_name}",
                            "details": status,
                        },
                        status_code=503,
                    )
            except Exception as e:
                return JSONResponse(
                    {"status": "error", "message": f"Health check failed: {str(e)}"},
                    status_code=500,
                )

        self.logger.info(f"Health check endpoint registered at {health_path}")

    async def _handle_health_check(self) -> dict[str, Any]:
        """Handle health check requests.

        Returns:
            Health status dictionary
        """
        return self.get_health_status()

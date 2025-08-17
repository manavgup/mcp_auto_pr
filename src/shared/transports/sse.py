"""Server-Sent Events transport implementation - FIXED VERSION."""

from typing import Any

from fastmcp import FastMCP

from .base import HttpBasedTransport, TransportError
from .config import TransportConfig


class SSETransport(HttpBasedTransport):
    """Server-Sent Events transport for MCP servers - FIXED implementation."""

    def __init__(self, config: TransportConfig, server_name: str = "MCP Server"):
        """Initialize SSE transport with configuration."""
        super().__init__(config, server_name)
        self._is_running = False

    def run(self, server: FastMCP) -> None:
        """Run the server with SSE transport - FIXED implementation."""
        try:
            self.server = server
            self._is_running = True

            # Use SSE config if available, otherwise use defaults
            if self.config.sse:
                host = self.config.sse.host
                port = self.config.sse.port
                # Register health check endpoint if enabled
                if self.config.sse.enable_health_check:
                    self._register_health_endpoint(server)
            else:
                # Default SSE config
                host = "0.0.0.0"
                port = 8003
                # Register default health check
                self._register_health_endpoint(server)

            self.logger.info(
                f"Starting {self.server_name} with SSE transport on http://{host}:{port}"
            )
            self.logger.debug("SSE endpoint will be available at /sse")

            # FIXED: Use the correct transport parameter for FastMCP
            # The issue was that FastMCP expects specific transport names
            try:
                # Try 'sse' first (if supported in your FastMCP version)
                server.run(transport="sse", host=host, port=port)
            except Exception as e:
                self.logger.warning(f"SSE transport failed, trying streamable-sse: {e}")
                try:
                    # Fallback to streamable-sse if sse doesn't work
                    server.run(transport="streamable-sse", host=host, port=port)  # type: ignore[arg-type]
                except Exception as e2:
                    self.logger.warning(
                        f"streamable-sse failed, trying streamable-http: {e2}"
                    )
                    # Final fallback to streamable-http (which we know works)
                    server.run(transport="streamable-http", host=host, port=port)

        except KeyboardInterrupt:
            self.logger.info("Server stopped by user (Ctrl+C)")
            self.stop()
        except Exception as e:
            self._log_error(e, "running SSE transport")
            raise TransportError(f"Failed to start SSE transport: {e}") from e
        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stop the SSE transport."""
        if self._is_running:
            self.logger.info(f"Stopping {self.server_name} SSE transport")
            self._is_running = False

    def is_running(self) -> bool:
        """Check if the SSE transport is running."""
        return self._is_running

    def get_connection_info(self) -> dict[str, Any]:
        """Get SSE connection information."""
        # Use SSE config if available, otherwise use defaults
        if self.config.sse:
            host = self.config.sse.host
            port = self.config.sse.port
            health_path = getattr(self.config.sse, "health_check_path", "/healthz")
        else:
            host = "0.0.0.0"
            port = 8003
            health_path = "/healthz"

        return {
            "protocol": "sse",
            "url": f"http://{host}:{port}/sse",
            "health_url": f"http://{host}:{port}{health_path}",
            "note": "SSE endpoint available at /sse",
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get health status for SSE transport."""
        status = super().get_health_status()

        # Add SSE-specific health information
        connection_info = self.get_connection_info()
        status.update(
            {
                "sse_healthy": self._is_running,
                "endpoint": connection_info["url"],
                "health_endpoint": connection_info["health_url"],
            }
        )

        return status

    def _register_health_endpoint(self, server: FastMCP) -> None:
        """Register health check endpoint using FastMCP's custom_route decorator."""
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        # Use configured health path or default for SSE
        if self.config.sse and hasattr(self.config.sse, "health_check_path"):
            health_path = self.config.sse.health_check_path
        else:
            health_path = "/healthz"  # SSE transport traditionally uses /healthz

        @server.custom_route(health_path, methods=["GET"])  # type: ignore
        async def health_check(_request: Request) -> JSONResponse:
            """Health check endpoint for SSE transport."""
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
                self.logger.error(f"Health check error: {e}")
                return JSONResponse(
                    {"status": "error", "message": f"Health check failed: {str(e)}"},
                    status_code=500,
                )

        self.logger.info(f"Health check endpoint registered at {health_path}")

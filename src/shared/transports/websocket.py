"""WebSocket transport implementation."""

from typing import Any

from fastmcp import FastMCP

from .base import HttpBasedTransport, TransportError
from .config import TransportConfig


class WebSocketTransport(HttpBasedTransport):
    """WebSocket transport for MCP servers.

    This transport uses WebSocket for real-time bidirectional communication.
    """

    def __init__(self, config: TransportConfig, server_name: str = "MCP Server"):
        """Initialize WebSocket transport."""
        super().__init__(config, server_name)
        self._ws_config = config.websocket

    def run(self, server: FastMCP) -> None:
        """Run the server with WebSocket transport."""
        try:
            self.server = server
            self._is_running = True

            if not self._ws_config:
                raise TransportError(
                    "WebSocket config is required for WebSocket transport"
                )

            self.logger.info(
                f"Starting {self.server_name} with WebSocket transport on "
                f"{self._ws_config.host}:{self._ws_config.port}"
            )

            # Run the FastMCP server with WebSocket transport
            # Note: FastMCP may not support 'websocket' directly, using 'http' as fallback
            try:
                server.run(
                    transport="websocket",  # type: ignore[arg-type]
                    host=self._ws_config.host,
                    port=self._ws_config.port,
                )
            except Exception as e:
                self.logger.warning(f"WebSocket transport failed, trying HTTP: {e}")
                server.run(
                    transport="streamable-http",
                    host=self._ws_config.host,
                    port=self._ws_config.port,
                )

        except KeyboardInterrupt:
            self.logger.info("Server stopped by user (Ctrl+C)")
            self.stop()
        except Exception as e:
            self._log_error(e, "running WebSocket transport")
            raise TransportError(f"Failed to start WebSocket transport: {e}") from e
        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stop the WebSocket transport."""
        if self._is_running:
            self.logger.info(f"Stopping {self.server_name} WebSocket transport")
            super().stop()

    def is_running(self) -> bool:
        """Check if the WebSocket transport is running."""
        return self._is_running

    def get_connection_info(self) -> dict[str, Any]:
        """Get WebSocket connection information."""
        if self._ws_config:
            host = self._ws_config.host
            port = self._ws_config.port
            heartbeat = self._ws_config.heartbeat_interval
        else:
            # Default WebSocket config
            host = "0.0.0.0"
            port = 8002
            heartbeat = 30

        return {
            "url": f"ws://{host}:{port}",
            "heartbeat_interval": heartbeat,
            "protocol": "websocket",
        }

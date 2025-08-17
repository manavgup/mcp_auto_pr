"""Transport factory module for creating transport instances based on configuration."""

from .base import BaseTransport
from .config import TransportConfig
from .http import HttpTransport
from .sse import SSETransport
from .stdio import StdioTransport
from .websocket import WebSocketTransport


def get_transport(config: TransportConfig) -> BaseTransport:
    """Get the transport instance based on the provided TransportConfig.

    Args:
        config (TransportConfig): The transport configuration object.

    Returns:
        BaseTransport: An instance of the transport corresponding to the config type.

    Raises:
        ValueError: If the transport type is unknown.
    """
    ttype = config.type.lower()
    if ttype == "stdio":
        return StdioTransport(config)
    elif ttype == "http":
        return HttpTransport(config)
    elif ttype == "websocket":
        return WebSocketTransport(config)
    elif ttype == "sse":
        return SSETransport(config)
    else:
        raise ValueError(f"Unknown transport type: {ttype}")

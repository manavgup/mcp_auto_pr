"""Shared infrastructure components for MCP servers."""

__version__ = "0.1.0"

# Base classes
from .base import BaseMCPCLI, BaseMCPServer, BaseMCPTool

__all__ = [
    "BaseMCPCLI",
    "BaseMCPServer",
    "BaseMCPTool",
]

"""Public API for shared MCP configuration classes."""

from mcp_shared_lib.config.base import BaseMCPSettings
from mcp_shared_lib.config.git_analyzer import GitAnalyzerSettings

__all__ = [
    "BaseMCPSettings",
    "GitAnalyzerSettings",
    "settings",
]

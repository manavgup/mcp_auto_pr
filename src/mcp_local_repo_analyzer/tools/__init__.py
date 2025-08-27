"""MCP tools for repository analysis.

This module contains MCP tool implementations for analyzing repository
changes, staging areas, and working directories.
"""

from .staging_area import register_staging_area_tools
from .summary import register_summary_tools
from .unpushed_commits import register_unpushed_commits_tools
from .working_directory import register_working_directory_tools

__all__ = [
    "register_staging_area_tools",
    "register_summary_tools",
    "register_unpushed_commits_tools",
    "register_working_directory_tools",
]

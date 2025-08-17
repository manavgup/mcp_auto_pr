"""Utility functions for MCP components."""

# File utilities
from mcp_shared_lib.utils.file_utils import get_file_extension, is_binary_file

# Git utilities
from mcp_shared_lib.utils.git_utils import (
    find_git_root,
    format_commit_message,
    format_file_size,
    is_git_repository,
    normalize_path,
    parse_diff_stats,
    parse_git_url,
    safe_filename,
    truncate_text,
)

# Logging utilities
from mcp_shared_lib.utils.logging_utils import (
    get_logger,
    logging_service,
    setup_logging,
)

__all__ = [
    # File utils
    "get_file_extension",
    "is_binary_file",
    # Git utils
    "is_git_repository",
    "find_git_root",
    "parse_git_url",
    "format_file_size",
    "format_commit_message",
    "safe_filename",
    "parse_diff_stats",
    "truncate_text",
    "normalize_path",
    # Logging utils
    "setup_logging",
    "get_logger",
    "logging_service",
]

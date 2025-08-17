"""Utility functions for git operations and analysis.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

This module provides utility functions for git repository detection,
URL parsing, file size formatting, commit message formatting, safe filename
generation, diff stats parsing, text truncation, path normalization, file
extension extraction, and binary file detection.
"""
from __future__ import annotations

import re
from pathlib import Path


def is_git_repository(path: str | Path) -> bool:
    """Check if the given path is a git repository.

    Args:
        path: Path to check.

    Returns:
        True if the path is a git repository, False otherwise.
    """
    path = Path(path)
    return (path / ".git").exists()


def find_git_root(path: str | Path) -> Path | None:
    """Find the root of the git repository containing the given path.

    Args:
        path: Path inside the git repository.

    Returns:
        Path to the git root directory or None if not found.
    """
    path = Path(path).resolve()

    for parent in [path] + list(path.parents):
        if is_git_repository(parent):
            return parent

    return None


def parse_git_url(url: str) -> dict[str, str]:
    """Parse a git URL into components.

    Args:
        url: Git repository URL.

    Returns:
        Dictionary with protocol, host, owner, and repo keys.
    """
    # Handle SSH URLs like git@github.com:user/repo.git
    ssh_pattern = r"git@([^:]+):([^/]+)/(.+?)(?:\.git)?$"
    ssh_match = re.match(ssh_pattern, url)

    if ssh_match:
        return {
            "protocol": "ssh",
            "host": ssh_match.group(1),
            "owner": ssh_match.group(2),
            "repo": ssh_match.group(3),
        }

    # Handle HTTPS URLs like https://github.com/user/repo.git
    https_pattern = r"https://([^/]+)/([^/]+)/(.+?)(?:\.git)?$"
    https_match = re.match(https_pattern, url)

    if https_match:
        return {
            "protocol": "https",
            "host": https_match.group(1),
            "owner": https_match.group(2),
            "repo": https_match.group(3),
        }

    return {"protocol": "unknown", "host": "", "owner": "", "repo": ""}


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Human-readable file size string.
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    size_index = 0
    size = float(size_bytes)

    while size >= 1024 and size_index < len(size_names) - 1:
        size /= 1024
        size_index += 1

    return f"{size:.1f} {size_names[size_index]}"


def format_commit_message(message: str, max_length: int = 72) -> str:
    """Format commit message for display.

    Args:
        message: Commit message string.
        max_length: Maximum length of the formatted message.

    Returns:
        Formatted commit message string.
    """
    lines = message.split("\n")
    first_line = lines[0]

    if len(first_line) <= max_length:
        return first_line

    return first_line[: max_length - 3] + "..."


def safe_filename(filename: str) -> str:
    """Convert a string to a safe filename.

    Args:
        filename: Original filename string.

    Returns:
        Safe filename string.
    """
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing dots and spaces
    safe = safe.strip(". ")
    # Limit length
    if len(safe) > 255:
        safe = safe[:255]

    return safe or "unnamed"


def parse_diff_stats(stats_line: str) -> tuple[int, int]:
    """Parse diff stats line like '5 files changed, 123 insertions(+), 45 deletions(-)'.

    Args:
        stats_line: Diff stats line string.

    Returns:
        Tuple of (insertions, deletions).
    """
    insertions = 0
    deletions = 0

    # Extract insertions
    insertion_match = re.search(r"(\d+) insertion", stats_line)
    if insertion_match:
        insertions = int(insertion_match.group(1))

    # Extract deletions
    deletion_match = re.search(r"(\d+) deletion", stats_line)
    if deletion_match:
        deletions = int(deletion_match.group(1))

    return insertions, deletions


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix.

    Args:
        text: Original text string.
        max_length: Maximum length of truncated text.
        suffix: Suffix to append if truncated.

    Returns:
        Truncated text string.
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def normalize_path(path: str | Path) -> str:
    """Normalize a file path for comparison.

    Args:
        path: File path string or Path object.

    Returns:
        Normalized POSIX-style path string.
    """
    return str(Path(path).as_posix())


def get_file_extension(filename: str) -> str:
    """Get file extension from filename.

    Args:
        filename: Filename string.

    Returns:
        Lowercase file extension string.
    """
    return Path(filename).suffix.lower()


def is_binary_file(file_path: str | Path) -> bool:
    """Check if a file is likely binary based on extension.

    Args:
        file_path: File path string or Path object.

    Returns:
        True if file is binary, False otherwise.
    """
    binary_extensions = {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bin",
        ".obj",
        ".o",
        ".a",
        ".lib",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".ico",
        ".svg",
        ".tiff",
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".wav",
        ".flac",
        ".ogg",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".7z",
        ".rar",
        ".sqlite",
        ".db",
        ".mdb",
    }

    extension = get_file_extension(str(file_path))
    return extension in binary_extensions

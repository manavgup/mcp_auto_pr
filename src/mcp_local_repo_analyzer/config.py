"""Configuration and settings for the Git analyzer.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

This module defines configuration and settings for the Git analyzer,
including thresholds, file patterns, and logging options.
"""

from pydantic import Field

from shared.base.config import BaseMCPSettings


class GitAnalyzerSettings(BaseMCPSettings):
    """Git analysis configuration settings."""

    # Environment variables that may be set in .env
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (may be used by other services)",
    )
    workspace_dir: str = Field(
        default="",
        description="Workspace directory path",
    )
    python_env: str = Field(
        default="development",
        description="Python environment (development, production, etc.)",
    )

    default_repository_path: str | None = Field(
        default=None,
        description="Default repository path to analyze",
    )
    max_diff_lines: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum lines to include in diff output",
    )
    max_commits_to_analyze: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of commits to analyze",
    )
    include_binary_files: bool = Field(
        default=False,
        description="Whether to include binary file changes in analysis",
    )
    critical_file_patterns: list[str] = Field(
        default=[
            "*.config",
            "*.env",
            "Dockerfile",
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
        ],
        description="File patterns considered critical for changes",
    )
    large_file_threshold: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Threshold for considering a file change large (in lines)",
    )


# Global settings instance
# settings = GitAnalyzerSettings()

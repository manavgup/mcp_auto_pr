"""Configuration and settings for the Git analyzer.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

This module defines configuration and settings for the Git analyzer,
including thresholds, file patterns, and logging options.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitAnalyzerSettings(BaseSettings):  # type: ignore[misc]
    """Git analysis configuration settings."""

    # Use model_config instead of nested Config class in Pydantic v2
    model_config = SettingsConfigDict(
        env_prefix="GIT_ANALYZER_",
        env_file=".env",
        case_sensitive=False,
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
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )


# Global settings instance
# settings = GitAnalyzerSettings()

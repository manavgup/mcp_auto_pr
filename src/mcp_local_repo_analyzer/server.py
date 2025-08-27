#!/usr/bin/env python3
"""Local Repository Analyzer Server implementation using BaseMCPServer."""

from typing import Any

from fastmcp import FastMCP

from mcp_local_repo_analyzer.config import GitAnalyzerSettings
from mcp_local_repo_analyzer.services import ChangeDetector, DiffAnalyzer, StatusTracker
from mcp_local_repo_analyzer.services.client import GitClient
from shared.base.server import BaseMCPServer


class LocalRepoAnalyzerServer(BaseMCPServer):
    """Local Repository Analyzer MCP Server with enhanced tools."""

    @property
    def service_name(self) -> str:
        """Return the display name for this service."""
        return "Local Git Changes Analyzer"

    @property
    def service_version(self) -> str:
        """Return the version for this service."""
        return "1.0.0"

    @property
    def default_port(self) -> int:
        """Return the default port for this service."""
        return 9070

    @property
    def service_instructions(self) -> str:
        """Return the instructions for this service."""
        return """ \
            This server analyzes outstanding local git changes that haven't made their way to GitHub yet.

            Available tools:
            - analyze_working_directory: Check uncommitted changes in working directory
            - analyze_staged_changes: Check staged changes ready for commit
            - analyze_unpushed_commits: Check commits not pushed to remote
            - analyze_stashed_changes: Check stashed changes
            - get_outstanding_summary: Get comprehensive summary of all outstanding changes
            - compare_with_remote: Compare local branch with remote branch
            - get_repository_health: Get overall repository health metrics

            Provide a repository path to analyze, or the tool will attempt to find a git repository
            in the current directory or use the default configured path.
            """

    async def initialize_services(self) -> dict[str, Any]:
        """Initialize analyzer-specific services."""
        self.logger.info("Initializing services...")

        # Create default settings for GitClient
        # TODO: Load from configuration file when available
        settings = GitAnalyzerSettings()

        try:
            git_client = GitClient(settings)
            self.logger.info("GitClient initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize GitClient: {e}")
            raise

        try:
            change_detector = ChangeDetector(git_client)
            self.logger.info("ChangeDetector initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize ChangeDetector: {e}")
            raise

        try:
            diff_analyzer = DiffAnalyzer(settings)
            self.logger.info("DiffAnalyzer initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize DiffAnalyzer: {e}")
            raise

        try:
            status_tracker = StatusTracker(git_client, change_detector)
            self.logger.info("StatusTracker initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize StatusTracker: {e}")
            raise

        # Create services dict for dependency injection
        services = {
            "git_client": git_client,
            "change_detector": change_detector,
            "diff_analyzer": diff_analyzer,
            "status_tracker": status_tracker,
        }

        self.logger.info("All services initialized successfully")
        return services

    async def register_tools(self, mcp: FastMCP, services: dict[str, Any]) -> None:
        """Register analyzer-specific tools."""
        try:
            self.logger.info("Starting tool registration")

            # Import and register tool modules with individual error handling
            try:
                from mcp_local_repo_analyzer.tools.working_directory import (
                    register_working_directory_tools,
                )

                self.logger.info("Registering working directory tools")
                register_working_directory_tools(mcp, services)
                self.logger.info("Working directory tools registered successfully")
            except Exception as e:
                self.logger.error(f"Failed to register working directory tools: {e}")
                raise

            try:
                from mcp_local_repo_analyzer.tools.staging_area import (
                    register_staging_area_tools,
                )

                self.logger.info("Registering staging area tools")
                register_staging_area_tools(mcp, services)
                self.logger.info("Staging area tools registered successfully")
            except Exception as e:
                self.logger.error(f"Failed to register staging area tools: {e}")
                raise

            try:
                from mcp_local_repo_analyzer.tools.unpushed_commits import (
                    register_unpushed_commits_tools,
                )

                self.logger.info("Registering unpushed commits tools")
                register_unpushed_commits_tools(mcp, services)
                self.logger.info("Unpushed commits tools registered successfully")
            except Exception as e:
                self.logger.error(f"Failed to register unpushed commits tools: {e}")
                raise

            try:
                from mcp_local_repo_analyzer.tools.summary import register_summary_tools

                self.logger.info("Registering summary tools")
                register_summary_tools(mcp, services)
                self.logger.info("Summary tools registered successfully")
            except Exception as e:
                self.logger.error(f"Failed to register summary tools: {e}")
                raise

            self.logger.info("All tools registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register tools: {e}")
            self.logger.error(f"Traceback: {__import__('traceback').format_exc()}")
            raise

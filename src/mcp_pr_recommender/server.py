#!/usr/bin/env python3
"""PR Recommender Server implementation using BaseMCPServer."""

from typing import Any

from fastmcp import Context, FastMCP

from mcp_pr_recommender.tools import (
    FeasibilityAnalyzerTool,
    PRRecommenderTool,
    StrategyManagerTool,
    ValidatorTool,
)
from shared.base.server import BaseMCPServer


class PRRecommenderServer(BaseMCPServer):
    """PR Recommender MCP Server with AI-powered analysis tools."""

    @property
    def service_name(self) -> str:
        """Return the display name for this service."""
        return "PR Recommender"

    @property
    def service_version(self) -> str:
        """Return the version for this service."""
        return "1.0.0"

    @property
    def default_port(self) -> int:
        """Return the default port for this service."""
        return 9071

    @property
    def service_instructions(self) -> str:
        """Return the instructions for this service."""
        return """ \
            Intelligent PR boundary detection and recommendation system.

            This server analyzes git changes and generates atomic, logically-grouped
            PR recommendations optimized for code review efficiency and deployment safety.

            Available tools:
            - generate_pr_recommendations: Main tool to generate PR recommendations from git analysis
            - analyze_pr_feasibility: Analyze feasibility and risks of specific recommendations
            - get_strategy_options: Get available grouping strategies and settings
            - validate_pr_recommendations: Validate generated recommendations for quality

            Input: Expects git analysis data from mcp_local_repo_analyzer
            Output: Structured PR recommendations with titles, descriptions, and rationale

            Provide git analysis data to generate recommendations, or use individual tools
            for specific analysis tasks.
            """

    async def initialize_services(self) -> dict[str, Any]:
        """Initialize recommender-specific services."""
        self.logger.info("Initializing services...")

        try:
            pr_generator = PRRecommenderTool()
            self.logger.info("PRRecommenderTool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize PRRecommenderTool: {e}")
            raise

        try:
            feasibility_analyzer = FeasibilityAnalyzerTool()
            self.logger.info("FeasibilityAnalyzerTool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize FeasibilityAnalyzerTool: {e}")
            raise

        try:
            strategy_manager = StrategyManagerTool()
            self.logger.info("StrategyManagerTool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize StrategyManagerTool: {e}")
            raise

        try:
            validator = ValidatorTool()
            self.logger.info("ValidatorTool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize ValidatorTool: {e}")
            raise

        # Create services dict for dependency injection
        services = {
            "pr_generator": pr_generator,
            "feasibility_analyzer": feasibility_analyzer,
            "strategy_manager": strategy_manager,
            "validator": validator,
        }

        self.logger.info("All services initialized successfully")
        return services

    async def register_tools(self, mcp: FastMCP, services: dict[str, Any]) -> None:
        """Register recommender-specific tools as MCP functions."""
        try:
            self.logger.info("Starting tool registration")

            # Register main PR recommendation tool
            @mcp.tool()
            async def generate_pr_recommendations(
                ctx: Context,
                analysis_data: dict[str, Any],
                strategy: str = "semantic",
                max_files_per_pr: int = 8,
            ) -> dict[str, Any]:
                """Generate PR recommendations from git analysis data."""
                await ctx.info("Generating PR recommendations")
                try:
                    result = await services["pr_generator"].generate_recommendations(
                        analysis_data, strategy, max_files_per_pr
                    )
                    return result  # type: ignore[no-any-return]
                except Exception as e:
                    await ctx.error(f"Failed to generate recommendations: {str(e)}")
                    return {"error": f"Failed to generate recommendations: {str(e)}"}

            # Register feasibility analysis tool
            @mcp.tool()
            async def analyze_pr_feasibility(
                ctx: Context,
                pr_recommendation: dict[str, Any],
            ) -> dict[str, Any]:
                """Analyze the feasibility and risks of a specific PR recommendation."""
                await ctx.info("Analyzing PR feasibility")
                try:
                    result = await services["feasibility_analyzer"].analyze_feasibility(pr_recommendation)
                    return result  # type: ignore[no-any-return]
                except Exception as e:
                    await ctx.error(f"Failed to analyze PR feasibility: {str(e)}")
                    return {"error": f"Failed to analyze feasibility: {str(e)}"}

            # Register strategy options tool
            @mcp.tool()
            async def get_strategy_options(
                ctx: Context,
            ) -> dict[str, Any]:
                """Get available PR grouping strategies and their descriptions."""
                await ctx.info("Retrieving available strategies")
                try:
                    result = await services["strategy_manager"].get_strategies()
                    return result  # type: ignore[no-any-return]
                except Exception as e:
                    await ctx.error(f"Failed to get strategy options: {str(e)}")
                    return {"error": f"Failed to get strategies: {str(e)}"}

            # Register validation tool
            @mcp.tool()
            async def validate_pr_recommendations(
                ctx: Context,
                recommendations: list[dict[str, Any]],
            ) -> dict[str, Any]:
                """Validate generated PR recommendations for quality and completeness."""
                await ctx.info("Validating PR recommendations")
                try:
                    result = await services["validator"].validate_recommendations(recommendations)
                    return result  # type: ignore[no-any-return]
                except Exception as e:
                    await ctx.error(f"Failed to validate recommendations: {str(e)}")
                    return {"error": f"Failed to validate recommendations: {str(e)}"}

            self.logger.info("All tools registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register tools: {e}")
            self.logger.error(f"Traceback: {__import__('traceback').format_exc()}")
            raise

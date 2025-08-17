"""Strategy management tool."""
import logging
from typing import Any

from mcp_pr_recommender.config import settings


class StrategyManagerTool:
    """Tool for managing PR grouping strategies."""

    def __init__(self) -> None:
        """Initialize strategy manager tool with logging."""
        self.logger = logging.getLogger(__name__)

    async def get_strategies(self) -> dict[str, Any]:
        """Get available PR grouping strategies and their descriptions."""
        self.logger.info("Retrieving available strategies")

        strategies = {
            "semantic": {
                "name": "Semantic Analysis",
                "description": "Uses LLM to understand code relationships and group semantically related changes",
                "best_for": "Complex changes with unclear relationships",
                "requires_llm": True,
                "pros": [
                    "Intelligent understanding of code relationships",
                    "Can identify non-obvious connections",
                    "Considers business logic context",
                ],
                "cons": [
                    "Requires OpenAI API key",
                    "Slower due to LLM calls",
                    "May have API costs",
                ],
            },
            "directory": {
                "name": "Directory-based",
                "description": "Groups files by directory structure and file types",
                "best_for": "Well-organized codebases with clear module boundaries",
                "requires_llm": False,
                "pros": [
                    "Fast and deterministic",
                    "No external dependencies",
                    "Respects code organization",
                ],
                "cons": [
                    "May miss cross-directory relationships",
                    "Relies on good directory structure",
                ],
            },
            "size": {
                "name": "Size-based",
                "description": "Groups files to maintain optimal PR size for review",
                "best_for": "Large changesets that need to be broken down",
                "requires_llm": False,
                "pros": [
                    "Ensures reviewable PR sizes",
                    "Simple and predictable",
                    "Good for bulk changes",
                ],
                "cons": ["May split related changes", "Ignores logical relationships"],
            },
            "dependency": {
                "name": "Dependency-aware",
                "description": "Groups files based on code dependencies and imports",
                "best_for": "Refactoring and structural changes",
                "requires_llm": False,
                "pros": [
                    "Respects code dependencies",
                    "Good for refactoring",
                    "Prevents breaking changes",
                ],
                "cons": [
                    "Requires code analysis",
                    "May create large groups",
                    "Complex to implement fully",
                ],
            },
            "hybrid": {
                "name": "Hybrid Approach",
                "description": "Combines multiple strategies for optimal results",
                "best_for": "Most use cases - balances speed and intelligence",
                "requires_llm": True,
                "pros": [
                    "Best of all approaches",
                    "Adapts to different change types",
                    "Fallback strategies",
                ],
                "cons": ["More complex", "May require tuning"],
            },
        }

        return {
            "available_strategies": strategies,
            "default_strategy": settings().default_strategy,
            "current_settings": {
                "max_files_per_pr": settings().max_files_per_pr,
                "min_files_per_pr": settings().min_files_per_pr,
                "similarity_threshold": settings().similarity_threshold,
                "enable_llm_analysis": settings().enable_llm_analysis,
            },
            "recommendations": self._get_strategy_recommendations(),
        }

    def _get_strategy_recommendations(self) -> dict[str, str]:
        """Get recommendations for when to use each strategy."""
        return {
            "small_changes": "Use 'directory' or 'size' for changes under 10 files",
            "large_refactoring": "Use 'dependency' or 'hybrid' for structural changes",
            "mixed_concerns": "Use 'semantic' to intelligently separate concerns",
            "urgent_fixes": "Use 'size' for quick splitting of urgent changes",
            "new_features": "Use 'semantic' or 'hybrid' for feature development",
            "documentation": "Use 'directory' for documentation-only changes",
            "configuration": "Use 'semantic' to group related config changes",
        }

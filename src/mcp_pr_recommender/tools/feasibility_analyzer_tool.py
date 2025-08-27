"""Tool for analyzing PR feasibility."""

from pathlib import Path
from typing import Any

from mcp_pr_recommender.config import settings
from shared.base.tool import BaseMCPTool
from shared.utils.logging import get_logger


class FeasibilityAnalyzerTool(BaseMCPTool):
    """Tool for analyzing PR feasibility."""

    def __init__(self) -> None:
        """Initialize feasibility analyzer tool."""
        super().__init__()
        self.logger = get_logger(__name__)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool's main functionality.

        Args:
            **kwargs: Keyword arguments including 'pr_recommendation' for analysis

        Returns:
            Dict containing feasibility analysis
        """
        pr_recommendation = kwargs.get("pr_recommendation", {})
        return await self.analyze_feasibility(pr_recommendation)

    async def analyze_feasibility(
        self,
        pr_recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze the feasibility and risks of a specific PR recommendation.

        Args:
            pr_recommendation: PR recommendation to analyze

        Returns:
            Dict containing feasibility analysis
        """
        self.logger.info("Analyzing PR feasibility")

        try:
            files = pr_recommendation.get("files", [])

            # Analyze various aspects
            analysis = {
                "feasible": True,
                "risk_factors": [],
                "recommendations": [],
                "estimated_effort": pr_recommendation.get("estimated_review_time", 0),
                "complexity_breakdown": self._analyze_complexity(files),
                "dependency_analysis": self._analyze_dependencies(files),
                "review_checklist": self._generate_review_checklist(pr_recommendation),
            }

            # Check file count
            if len(files) > settings().max_files_per_pr:
                analysis["risk_factors"].append(f"Large number of files ({len(files)})")
                analysis["recommendations"].append("Consider splitting into smaller PRs")

            # Check for mixed concerns
            file_analysis = self._categorize_files(files)
            if len(file_analysis["file_types"]) > 2:
                analysis["risk_factors"].append("Mixed file types")
                analysis["recommendations"].append("Consider separating by file type")

            # Check for high-risk patterns
            risk_patterns = self._check_risk_patterns(files)
            analysis["risk_factors"].extend(risk_patterns["factors"])
            analysis["recommendations"].extend(risk_patterns["recommendations"])

            # Overall feasibility
            if len(analysis["risk_factors"]) > 2:
                analysis["feasible"] = False

            self.logger.info(f"Feasibility analysis complete: {'feasible' if analysis['feasible'] else 'needs review'}")

            return analysis

        except Exception as e:
            self.logger.error(f"Feasibility analysis failed: {str(e)}")
            return {"error": f"Feasibility analysis failed: {str(e)}"}

    def _categorize_files(self, files: list[str]) -> dict[str, Any]:
        """Categorize files by type and directory."""
        file_types = set()
        directories = set()
        extensions = set()

        for file_path in files:
            path = Path(file_path)

            # Categorize by extension
            if path.suffix:
                extensions.add(path.suffix)

            # Categorize by type
            if path.suffix in [".py", ".js", ".ts", ".java", ".cpp", ".c"]:
                file_types.add("source")
            elif path.suffix in [".md", ".rst", ".txt"]:
                file_types.add("docs")
            elif path.suffix in [".json", ".yaml", ".yml", ".toml", ".ini"]:
                file_types.add("config")
            elif "test" in str(path).lower():
                file_types.add("test")
            else:
                file_types.add("other")

            # Track directories
            directories.add(str(path.parent))

        return {
            "file_types": list(file_types),
            "directories": list(directories),
            "extensions": list(extensions),
            "directory_count": len(directories),
            "type_diversity": len(file_types),
        }

    def _analyze_complexity(self, files: list[str]) -> dict[str, Any]:
        """Analyze complexity factors."""
        return {
            "file_count": len(files),
            "estimated_review_time_per_file": 10,  # minutes
            "complexity_factors": [
                "File count" if len(files) > 5 else None,
                ("Multiple directories" if len({Path(f).parent for f in files}) > 2 else None),
                ("Mixed file types" if len({Path(f).suffix for f in files}) > 3 else None),
            ],
            "complexity_score": min(10, len(files) + len({Path(f).parent for f in files})),
        }

    def _analyze_dependencies(self, files: list[str]) -> dict[str, Any]:
        """Analyze file dependencies."""
        # Simple dependency analysis based on file patterns
        has_migration = any("migration" in f.lower() for f in files)
        has_model = any("model" in f.lower() for f in files)
        has_test = any("test" in f.lower() for f in files)
        has_config = any(f.endswith((".json", ".yaml", ".yml", ".toml")) for f in files)

        return {
            "has_migration": has_migration,
            "has_model": has_model,
            "has_test": has_test,
            "has_config": has_config,
            "dependency_concerns": [
                "Migration with model changes" if has_migration and has_model else None,
                "Config changes without tests" if has_config and not has_test else None,
                "Model changes without tests" if has_model and not has_test else None,
            ],
        }

    def _check_risk_patterns(self, files: list[str]) -> dict[str, Any]:
        """Check for high-risk file patterns."""
        risk_factors = []
        recommendations = []

        # Check for critical file patterns
        critical_patterns = ["migration", "schema", "config", "env", "docker", "deploy"]

        critical_files = [f for f in files if any(pattern in f.lower() for pattern in critical_patterns)]

        if critical_files:
            risk_factors.append(f"Critical files present: {len(critical_files)}")
            recommendations.append("Extra review needed for critical files")

        # Check for large file changes (would need line count data)
        # For now, just flag certain file types as potentially large
        potentially_large = [f for f in files if f.endswith((".sql", ".json", ".lock"))]

        if potentially_large:
            risk_factors.append("Files that might contain large changes")
            recommendations.append("Verify file sizes are reasonable")

        return {
            "factors": [f for f in risk_factors if f],
            "recommendations": [r for r in recommendations if r],
        }

    def _generate_review_checklist(self, pr_recommendation: dict[str, Any]) -> list[str]:
        """Generate a review checklist based on the PR."""
        checklist = [
            "Code follows team style guidelines",
            "All new code has appropriate tests",
            "Documentation is updated if needed",
            "No sensitive information is exposed",
        ]

        # Add specific checks based on PR content
        files = pr_recommendation.get("files", [])

        if any("test" in f.lower() for f in files):
            checklist.append("Test coverage is adequate")

        if any(f.endswith((".json", ".yaml", ".yml")) for f in files):
            checklist.append("Configuration changes are validated")

        if any("migration" in f.lower() for f in files):
            checklist.append("Database migration is reversible")
            checklist.append("Migration has been tested on staging")

        if pr_recommendation.get("risk_level") == "high":
            checklist.append("Extra review by senior team member")
            checklist.append("Consider feature flag for gradual rollout")

        return checklist

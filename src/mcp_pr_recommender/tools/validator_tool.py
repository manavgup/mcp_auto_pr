"""PR recommendation validation tool."""
import logging
from collections import defaultdict
from typing import Any

from mcp_pr_recommender.config import settings


class ValidatorTool:
    """Tool for validating PR recommendations."""

    def __init__(self) -> None:
        """Initialize validator tool with logging."""
        self.logger = logging.getLogger(__name__)

    async def validate_recommendations(
        self,
        recommendations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Validate a set of PR recommendations for completeness and atomicity."""
        self.logger.info(f"Validating {len(recommendations)} PR recommendations")

        validation_results: dict[str, Any] = {
            "overall_valid": True,
            "recommendations_analysis": [],
            "coverage_analysis": {},
            "conflict_analysis": {},
            "suggestions": [],
            "quality_score": 0.0,
        }

        try:
            # Track all files across recommendations
            all_files: set[str] = set()
            file_to_pr_map: dict[str, list[str]] = defaultdict(list)

            # Validate each recommendation individually
            for i, rec in enumerate(recommendations):
                rec_analysis = await self._validate_single_recommendation(rec, i)
                validation_results["recommendations_analysis"].append(rec_analysis)

                if not rec_analysis["valid"]:
                    validation_results["overall_valid"] = False

                # Track file coverage
                files = rec.get("files", [])
                for file_path in files:
                    all_files.add(file_path)
                    file_to_pr_map[file_path].append(rec.get("id", f"rec_{i}"))

            # Coverage analysis
            validation_results["coverage_analysis"] = self._analyze_coverage(
                recommendations, all_files, file_to_pr_map
            )

            # Conflict analysis
            validation_results["conflict_analysis"] = self._analyze_conflicts(
                file_to_pr_map
            )

            # Generate overall suggestions
            validation_results["suggestions"] = self._generate_suggestions(
                validation_results
            )

            # Calculate quality score
            validation_results["quality_score"] = self._calculate_quality_score(
                validation_results
            )

            self.logger.info(
                f"Validation complete: {'VALID' if validation_results['overall_valid'] else 'ISSUES FOUND'} "
                f"(Quality: {validation_results['quality_score']:.1f}/10)"
            )

            return validation_results

        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return {"error": f"Validation failed: {str(e)}"}

    async def _validate_single_recommendation(
        self, rec: dict[str, Any], index: int
    ) -> dict[str, Any]:
        """Validate a single PR recommendation."""
        rec_analysis = {
            "id": rec.get("id", f"rec_{index}"),
            "valid": True,
            "issues": [],
            "warnings": [],
            "suggestions": [],
            "metrics": {},
        }

        files = rec.get("files", [])

        # Check for empty PRs
        if len(files) == 0:
            rec_analysis["valid"] = False
            rec_analysis["issues"].append("No files in PR")

        # Check file count limits
        if len(files) > settings().max_files_per_pr:
            rec_analysis["valid"] = False
            rec_analysis["issues"].append(
                f"Too many files ({len(files)} > {settings().max_files_per_pr})"
            )
            rec_analysis["suggestions"].append("Split into smaller PRs")

        if len(files) < settings().min_files_per_pr and len(files) > 0:
            rec_analysis["warnings"].append(f"Very small PR ({len(files)} files)")

        # Check required fields
        required_fields = ["title", "description", "branch_name"]
        for field in required_fields:
            if not rec.get(field):
                rec_analysis["issues"].append(f"Missing {field}")
                rec_analysis["valid"] = False

        # Check risk level vs size
        risk_level = rec.get("risk_level", "low")
        if risk_level == "high" and len(files) > 5:
            rec_analysis["warnings"].append(
                "High-risk PR with many files - consider extra review"
            )

        # Check estimated review time
        review_time = rec.get("estimated_review_time", 0)
        if review_time > 120:  # 2 hours
            rec_analysis["warnings"].append(
                "Long estimated review time - consider splitting"
            )

        # Analyze file coherence
        coherence_analysis = self._analyze_file_coherence(files)
        if coherence_analysis["coherence_score"] < 0.7:
            rec_analysis["warnings"].append("Files may not be closely related")

        # Store metrics
        rec_analysis["metrics"] = {
            "file_count": len(files),
            "estimated_review_time": review_time,
            "risk_level": risk_level,
            "coherence_score": coherence_analysis["coherence_score"],
            "complexity_score": rec.get("complexity_score", 0),
        }

        return rec_analysis

    def _analyze_coverage(
        self,
        recommendations: list[dict[str, Any]],
        all_files: set[str],
        file_to_pr_map: dict[str, list[str]],
    ) -> dict[str, Any]:
        """Analyze file coverage across recommendations."""
        return {
            "total_files_covered": len(all_files),
            "total_recommendations": len(recommendations),
            "average_files_per_pr": len(all_files) / len(recommendations)
            if recommendations
            else 0,
            "file_distribution": {
                "small_prs": len(
                    [r for r in recommendations if len(r.get("files", [])) <= 3]
                ),
                "medium_prs": len(
                    [r for r in recommendations if 4 <= len(r.get("files", [])) <= 8]
                ),
                "large_prs": len(
                    [r for r in recommendations if len(r.get("files", [])) > 8]
                ),
            },
            "duplicate_files": [
                {"file": file, "prs": prs}
                for file, prs in file_to_pr_map.items()
                if len(prs) > 1
            ],
        }

    def _analyze_conflicts(
        self, file_to_pr_map: dict[str, list[str]]
    ) -> dict[str, Any]:
        """Analyze potential conflicts between PRs."""
        conflicts = []
        for file_path, pr_ids in file_to_pr_map.items():
            if len(pr_ids) > 1:
                conflicts.append(
                    {
                        "file": file_path,
                        "conflicting_prs": pr_ids,
                        "severity": "high" if len(pr_ids) > 2 else "medium",
                    }
                )

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "resolution_suggestions": [
                "Merge conflicting PRs" if len(conflicts) < 3 else None,
                "Review file assignments" if len(conflicts) > 0 else None,
            ],
        }

    def _analyze_file_coherence(self, files: list[str]) -> dict[str, Any]:
        """Analyze how coherent/related the files in a group are."""
        if not files:
            return {"coherence_score": 0.0, "factors": []}

        if len(files) == 1:
            return {"coherence_score": 1.0, "factors": ["Single file"]}

        # Simple coherence metrics
        from pathlib import Path

        directories = {str(Path(f).parent) for f in files}
        extensions = {Path(f).suffix for f in files}

        # Score based on directory and file type similarity
        dir_score = (
            1.0
            if len(directories) == 1
            else max(0.3, 1.0 - (len(directories) - 1) * 0.2)
        )
        ext_score = (
            1.0
            if len(extensions) <= 2
            else max(0.3, 1.0 - (len(extensions) - 2) * 0.15)
        )

        # Check for common patterns
        pattern_score = 1.0
        if any("test" in f.lower() for f in files) and any(
            "test" not in f.lower() for f in files
        ):
            pattern_score *= 0.8  # Mixed test and non-test files

        coherence_score = (dir_score + ext_score + pattern_score) / 3

        factors = []
        if len(directories) == 1:
            factors.append("Same directory")
        if len(extensions) <= 2:
            factors.append("Similar file types")
        if coherence_score < 0.7:
            factors.append("Mixed concerns detected")

        return {
            "coherence_score": coherence_score,
            "factors": factors,
            "directory_diversity": len(directories),
            "extension_diversity": len(extensions),
        }

    def _generate_suggestions(self, validation_results: dict[str, Any]) -> list[str]:
        """Generate overall suggestions for improvement."""
        suggestions = []

        # Coverage suggestions
        coverage = validation_results["coverage_analysis"]
        if coverage["average_files_per_pr"] > 10:
            suggestions.append("Consider creating more granular PRs")
        elif coverage["average_files_per_pr"] < 2:
            suggestions.append("Consider grouping some PRs together")

        # Conflict suggestions
        conflicts = validation_results["conflict_analysis"]
        if conflicts["has_conflicts"]:
            suggestions.append(
                f"Resolve {conflicts['conflict_count']} file conflicts between PRs"
            )

        # Distribution suggestions
        distribution = coverage["file_distribution"]
        if (
            distribution["large_prs"]
            > distribution["small_prs"] + distribution["medium_prs"]
        ):
            suggestions.append("Too many large PRs - consider splitting them")

        # Quality suggestions
        invalid_count = sum(
            1
            for rec in validation_results["recommendations_analysis"]
            if not rec["valid"]
        )
        if invalid_count > 0:
            suggestions.append(f"Fix {invalid_count} invalid PR recommendations")

        return suggestions

    def _calculate_quality_score(self, validation_results: dict[str, Any]) -> float:
        """Calculate overall quality score (0-10)."""
        if not validation_results["recommendations_analysis"]:
            return 0.0

        # Base score
        score: float = 10.0

        # Deduct for invalid recommendations
        invalid_count = sum(
            1
            for rec in validation_results["recommendations_analysis"]
            if not rec["valid"]
        )
        score -= invalid_count * 2

        # Deduct for conflicts
        conflicts = validation_results["conflict_analysis"]
        score -= conflicts["conflict_count"] * 1.5

        # Deduct for poor distribution
        coverage = validation_results["coverage_analysis"]
        if coverage["average_files_per_pr"] > 10:
            score -= 1

        # Deduct for warnings
        warning_count = sum(
            len(rec["warnings"])
            for rec in validation_results["recommendations_analysis"]
        )
        score -= warning_count * 0.2

        return max(0.0, min(10.0, score))

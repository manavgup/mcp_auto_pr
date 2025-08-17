"""PR recommendation generation tool - now using SemanticAnalyzer directly with enhanced file handling."""
import logging
from typing import Any

from shared.models import (
    ChangeCategorization,
    FileStatus,
    OutstandingChangesAnalysis,
    RiskAssessment,
)

from mcp_pr_recommender.services.semantic_analyzer import SemanticAnalyzer


class PRRecommenderTool:
    """Tool for generating PR recommendations from git analysis."""

    def __init__(self) -> None:
        """Initialize PR recommender tool with semantic analyzer."""
        self.semantic_analyzer = SemanticAnalyzer()
        self.logger = logging.getLogger(__name__)

    async def generate_recommendations(
        self,
        analysis_data: dict[str, Any],
        strategy: str = "semantic",
        _max_files_per_pr: int = 8,
    ) -> dict[str, Any]:
        """Generate PR recommendations from git analysis data.

        Args:
            analysis_data: Git analysis data from mcp_local_repo_analyzer (enhanced with untracked files)
            strategy: Grouping strategy to use (always semantic now)
            max_files_per_pr: Maximum files per PR (LLM decides, but this is a hint)

        Returns:
            Dict containing PR recommendations and metadata
        """
        self.logger.info(
            "Generating PR recommendations using LLM-based semantic analysis"
        )

        try:
            # Handle MCP response format - extract structuredContent if present
            actual_data = analysis_data
            if "structuredContent" in analysis_data:
                self.logger.info("Extracting data from MCP structuredContent wrapper")
                actual_data = analysis_data["structuredContent"]
            elif (
                "content" in analysis_data and "repository_status" not in analysis_data
            ):
                self.logger.warning(
                    "Received content wrapper without structuredContent"
                )
                # Try to parse JSON from content if needed
                if (
                    isinstance(analysis_data["content"], list)
                    and len(analysis_data["content"]) > 0
                ):
                    content_item = analysis_data["content"][0]
                    if content_item.get("type") == "text":
                        import json

                        try:
                            actual_data = json.loads(content_item["text"])
                            self.logger.info(
                                "Successfully parsed JSON from content text"
                            )
                        except json.JSONDecodeError:
                            self.logger.error("Failed to parse JSON from content text")

            # ENHANCED: Extract all file types properly from analysis_data
            all_files = self._extract_all_files(actual_data)

            self.logger.info(f"Analyzing {len(all_files)} changed files")

            # Enhanced file type breakdown for debugging
            file_type_counts: dict[str, int] = {}
            files_with_changes = 0
            total_lines_changed = 0

            for f in all_files:
                file_type = getattr(f, "file_type", "unknown")
                file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
                if f.total_changes > 0:
                    files_with_changes += 1
                    total_lines_changed += f.total_changes

            self.logger.info(f"File breakdown: {file_type_counts}")
            self.logger.info(
                f"Files with actual changes: {files_with_changes}/{len(all_files)}"
            )
            self.logger.info(f"Total lines changed: {total_lines_changed:,}")

            if not all_files:
                return {
                    "error": "No files to analyze",
                    "strategy_used": strategy,
                    "total_prs_recommended": 0,
                    "recommendations": [],
                }

            # Create OutstandingChangesAnalysis object with proper data
            analysis: OutstandingChangesAnalysis = self._create_analysis_object(
                actual_data, all_files
            )

            # Generate recommendations using semantic analyzer directly
            pr_recommendations = await self.semantic_analyzer.analyze_and_generate_prs(
                all_files, analysis
            )

            self.logger.info(f"Generated {len(pr_recommendations)} PR recommendations")

            # Calculate summary statistics
            total_files_in_prs = sum(pr.files_count for pr in pr_recommendations)
            average_pr_size = (
                total_files_in_prs / len(pr_recommendations)
                if pr_recommendations
                else 0
            )
            total_changes_in_prs = sum(
                pr.total_lines_changed for pr in pr_recommendations
            )

            # Enhanced validation - check if untracked files are included
            untracked_files = [f for f in all_files if f.change_type == "untracked"]
            untracked_count = len(untracked_files)

            untracked_in_prs = 0
            for pr in pr_recommendations:
                for file_path in pr.files:
                    # Find the file and check if it's untracked
                    for f in all_files:
                        if f.path == file_path and f.change_type == "untracked":
                            untracked_in_prs += 1
                            break

            self.logger.info(
                f"Untracked files: {untracked_count} total, {untracked_in_prs} included in PRs"
            )

            # Format response
            return {
                "strategy_used": "llm_semantic_analysis",
                "total_prs_recommended": len(pr_recommendations),
                "average_pr_size": round(average_pr_size, 1),
                "total_files_analyzed": len(all_files),
                "total_lines_changed": total_changes_in_prs,
                "file_analysis": {
                    "file_type_breakdown": file_type_counts,
                    "files_with_changes": files_with_changes,
                    "untracked_files_found": untracked_count,
                    "untracked_files_in_prs": untracked_in_prs,
                },
                "recommendations": [
                    {
                        "id": pr.id,
                        "title": pr.title,
                        "description": pr.description,
                        "files": pr.files,
                        "files_count": pr.files_count,
                        "branch_name": pr.branch_name,
                        "priority": pr.priority,
                        "estimated_review_time": pr.estimated_review_time,
                        "risk_level": pr.risk_level,
                        "reasoning": pr.reasoning,
                        "labels": pr.labels,
                        "total_lines_changed": pr.total_lines_changed,
                    }
                    for pr in pr_recommendations
                ],
                "summary": f"Generated {len(pr_recommendations)} atomic PRs from {len(all_files)} changed files using LLM analysis",
                "metadata": {
                    "repository_path": str(analysis.repository_path),
                    "analysis_timestamp": analysis.analysis_timestamp.isoformat()
                    if hasattr(analysis, "analysis_timestamp")
                    else None,
                    "risk_level": analysis.risk_assessment.risk_level,
                    "grouping_method": "llm_semantic",
                    "llm_model_used": "gpt-4",  # or get from settings
                    "files_by_type": file_type_counts,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to generate PR recommendations: {str(e)}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": f"PR recommendation generation failed: {str(e)}"}

    def _analyze_file_types(self, all_files: list[FileStatus]) -> dict[str, int]:
        """Analyze file type breakdown."""
        file_type_counts: dict[str, int] = {}
        for f in all_files:
            file_type = f.file_type  # Use the property!
            file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
        return file_type_counts

    def _extract_all_files(self, analysis_data: dict[str, Any]) -> list[FileStatus]:
        """Extract all files from analysis_data, handling different formats."""
        all_files = []

        # Handle new standardized format with repository_status
        if "repository_status" in analysis_data:
            repo_status = analysis_data["repository_status"]
            working_dir = repo_status.get("working_directory", {})

            for file_type in [
                "modified_files",
                "added_files",
                "deleted_files",
                "renamed_files",
                "untracked_files",
            ]:
                for file_data in working_dir.get(file_type, []):
                    file_status = self._create_file_status(file_data)
                    all_files.append(file_status)

        # Fallback: Use comprehensive analysis if available (from enhanced test)
        elif "all_files" in analysis_data:
            self.logger.info(
                f"Using comprehensive file analysis with {len(analysis_data['all_files'])} files"
            )
            for file_data in analysis_data["all_files"]:
                file_status = self._create_file_status(file_data)
                all_files.append(file_status)

        # Fallback: combine individual file arrays (legacy)
        else:
            self.logger.info("Using individual file arrays - combining all types")

            file_arrays = [
                ("working_directory_files", "tracked changes"),
                ("staged_files", "staged files"),
                ("untracked_files", "untracked files"),
            ]

            for array_key, _description in file_arrays:
                for file_data in analysis_data.get(array_key, []):
                    file_status = self._create_file_status(file_data)
                    all_files.append(file_status)

        return all_files

    def _create_file_status(self, file_data: dict[str, Any]) -> FileStatus:
        """Create a FileStatus object from file data dict."""
        file_status = FileStatus(
            path=file_data["path"],
            status_code=file_data.get("status_code", file_data.get("status", "?")),
            staged=file_data.get("staged", False),
            lines_added=file_data.get("lines_added", 0),
            lines_deleted=file_data.get("lines_deleted", 0),
            is_binary=file_data.get("is_binary", False),
            old_path=file_data.get("old_path"),
            working_tree_status=file_data.get("working_tree_status"),
            index_status=file_data.get("index_status"),
        )

        return file_status

    def _create_analysis_object(
        self, analysis_data: dict[str, Any], all_files: list[FileStatus]
    ) -> OutstandingChangesAnalysis:
        """Create OutstandingChangesAnalysis object from the data."""
        from datetime import datetime

        # Extract risk assessment
        risk_data = analysis_data.get("risk_assessment", {})
        risk_assessment = RiskAssessment(
            risk_level=risk_data.get("risk_level", "medium"),
            risk_factors=risk_data.get("risk_factors", []),
            large_changes=risk_data.get("large_changes", []),
            potential_conflicts=risk_data.get("potential_conflicts", []),
            binary_changes=risk_data.get("binary_changes", []),
        )

        # Create categories (will be populated by semantic analyzer)
        categories = ChangeCategorization()

        # Create the analysis object
        analysis = OutstandingChangesAnalysis(
            repository_path=analysis_data.get("repository_path", "."),
            analysis_timestamp=datetime.now(),  # ADD THIS LINE
            total_outstanding_files=len(all_files),
            categories=categories,
            risk_assessment=risk_assessment,
            summary=analysis_data.get("summary", "Git repository analysis"),
            recommendations=[],  # Will be populated later
        )

        # Files will be passed separately to the semantic analyzer

        # Add comprehensive stats if available
        if "comprehensive_stats" in analysis_data:
            stats = analysis_data["comprehensive_stats"]
            self.logger.info(f"Comprehensive stats: {stats}")

            # Update total to include untracked files
            if "untracked_lines" in stats:
                analysis.total_outstanding_files = len(all_files)

        return analysis

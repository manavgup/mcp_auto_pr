"""FastMCP tools for staging area analysis with enhanced return types."""

import time
from pathlib import Path
from typing import Any

from fastmcp import Context, FastMCP
from pydantic import Field

from mcp_shared_lib.models import LocalRepository
from mcp_shared_lib.utils import find_git_root, is_git_repository


def register_staging_area_tools(mcp: FastMCP, services: dict[str, Any]) -> None:
    """Register staging area analysis tools."""

    @mcp.tool()  # type: ignore[misc]
    async def analyze_staged_changes(
        ctx: Context,
        repository_path: str = Field(default=".", description="Path to git repository"),
        include_diffs: bool = Field(
            True, description="Include diff content for staged files"
        ),
    ) -> dict[str, Any]:
        """Analyze changes staged for commit.

        Returns information about all files that have been staged (added to index)
        and are ready to be committed.

        **Return Type**: Dict with StagedChanges structure
        ```python
        {
            "repository_path": str,           # Pass to other repository tools
            "total_staged_files": int,        # Number of files staged - use for conditional logic
            "ready_to_commit": bool,          # Whether staged changes exist - use for commit workflow
            "statistics": {                   # Line change statistics for impact assessment
                "total_additions": int, "total_deletions": int
            },
            "staged_files": List[FileStatus], # List of staged file information for iteration
            "diffs": List[dict] | None        # Diff content if include_diffs=True
        }
        ```

        **Key Fields for Chaining**:
        - `ready_to_commit` (bool): Use to determine if commit validation/preview should run
        - `repository_path` (str): Pass to other repository analysis tools
        - `total_staged_files` (int): Use for conditional workflow logic
        - `staged_files` (list): Individual file information for targeted analysis
        - `statistics` (dict): Change statistics for impact assessment

        **Common Chaining Patterns**:
        ```python
        # Basic commit workflow
        staged_result = await analyze_staged_changes(repo_path)
        if staged_result["ready_to_commit"]:
            validation = await validate_staged_changes(staged_result["repository_path"])
            if validation["valid"]:
                preview = await preview_commit(staged_result["repository_path"])

        # Risk-based validation
        if staged_result["total_staged_files"] > 5:
            validation = await validate_staged_changes(staged_result["repository_path"])

        # File-specific analysis
        for file_info in staged_result["staged_files"]:
            if file_info["total_changes"] > 100:
                # Large change - needs review
                pass
        ```

        **Decision Points**:
        - `ready_to_commit=True`: Has staged changes → run commit validation/preview
        - `ready_to_commit=False`: No staged changes → analyze working directory instead
        - `total_staged_files > X`: Many files → trigger additional validation
        - `statistics.total_additions > X`: Large additions → review for quality
        """
        start_time = time.time()
        await ctx.info(f"Starting staged changes analysis for: {repository_path}")

        repo_path = Path(repository_path).resolve()
        if not is_git_repository(repo_path):
            git_root = find_git_root(repo_path)
            if not git_root:
                await ctx.error(f"No git repository found at or above {repo_path}")
                return {"error": f"No git repository found at or above {repo_path}"}
            repo_path = git_root
            await ctx.debug(f"Found git repository at: {repo_path}")

        try:
            await ctx.report_progress(0, 4)
            await ctx.debug("Creating repository model")

            repo = LocalRepository(
                path=repo_path,
                name=repo_path.name,
                current_branch="main",
                head_commit="unknown",
            )

            await ctx.report_progress(1, 4)
            await ctx.debug("Detecting staged changes")

            # Use existing StagedChanges model
            current_services = services
            staged_changes = await current_services[
                "change_detector"
            ].detect_staged_changes(repo, ctx)

            await ctx.report_progress(2, 4)
            await ctx.info(f"Found {staged_changes.total_staged} staged files")

            result = {
                "repository_path": str(repo_path),
                "total_staged_files": staged_changes.total_staged,
                "ready_to_commit": staged_changes.ready_to_commit,
                "statistics": {
                    "total_additions": staged_changes.total_additions,
                    "total_deletions": staged_changes.total_deletions,
                },
                "staged_files": [
                    {
                        "path": f.path,
                        "status": f.status_code,
                        "status_description": f.status_description,
                        "lines_added": f.lines_added,
                        "lines_deleted": f.lines_deleted,
                        "total_changes": f.total_changes,
                        "is_binary": f.is_binary,
                    }
                    for f in staged_changes.staged_files
                ],
            }

            # Add diffs if requested
            if include_diffs and staged_changes.staged_files:
                await ctx.debug(
                    f"Generating diffs for {min(10, len(staged_changes.staged_files))} staged files"
                )
                diffs = []
                files_to_process = staged_changes.staged_files[:10]  # Limit to 10 files

                for i, file_status in enumerate(files_to_process):
                    await ctx.report_progress(
                        2.5 + (i / len(files_to_process)) * 0.5, 4
                    )

                    try:
                        if file_status.is_binary:
                            await ctx.debug(f"Skipping binary file: {file_status.path}")
                            diffs.append(
                                {
                                    "file_path": file_status.path,
                                    "is_binary": True,
                                    "message": "Binary file - no diff available",
                                }
                            )
                            continue

                        await ctx.debug(f"Getting staged diff for: {file_status.path}")
                        diff_content = await current_services["git_client"].get_diff(
                            repo_path, staged=True, file_path=file_status.path, ctx=ctx
                        )

                        # Truncate long diffs
                        lines = diff_content.split("\n")
                        if len(lines) > 100:
                            diff_content = "\n".join(lines[:100]) + "\n... (truncated)"
                            await ctx.debug(
                                f"Truncated diff for {file_status.path} from {len(lines)} to 100 lines"
                            )

                        diffs.append(
                            {
                                "file_path": file_status.path,
                                "diff_content": diff_content,
                            }
                        )

                    except Exception as e:
                        await ctx.warning(
                            f"Failed to get diff for {file_status.path}: {str(e)}"
                        )
                        diffs.append(
                            {
                                "file_path": file_status.path,
                                "error": f"Failed to get diff: {str(e)}",
                            }
                        )

                result["diffs"] = diffs

            await ctx.report_progress(4, 4)
            duration = time.time() - start_time
            await ctx.info(
                f"Staged changes analysis completed in {duration:.2f} seconds"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            await ctx.error(
                f"Staged changes analysis failed after {duration:.2f} seconds: {str(e)}"
            )
            return {"error": f"Failed to analyze staged changes: {str(e)}"}

    @mcp.tool()  # type: ignore[misc]
    async def preview_commit(
        ctx: Context,
        repository_path: str = Field(default=".", description="Path to git repository"),
    ) -> dict[str, Any]:
        """Preview what would be committed.

        Shows a summary of staged changes that would be included in the next commit.

        **Return Type**: Dict with commit preview information
        ```python
        {
            "repository_path": str,           # Path to analyzed repository
            "ready_to_commit": bool,          # Whether there are staged changes to commit
            "summary": {                      # Change statistics for commit description
                "total_files": int, "total_additions": int, "total_deletions": int
            },
            "file_categories": {              # File categorization for commit organization
                "critical_files": int, "source_code": int, "documentation": int,
                "tests": int, "configuration": int, "other": int
            },
            "file_types": Dict[str, int],     # File extensions and counts
            "files_by_status": {              # Files organized by git status
                "added": List[str], "modified": List[str],
                "deleted": List[str], "renamed": List[str]
            },
            "message": str | None             # Status message if no changes
        }
        ```

        **Key Fields for Chaining**:
        - `ready_to_commit` (bool): Whether commit can proceed
        - `repository_path` (str): Pass to validation or push readiness tools
        - `file_categories` (dict): Use for commit message generation or validation
        - `summary.total_files` (int): Use for validation thresholds

        **Common Chaining Patterns**:
        ```python
        # Commit workflow with validation
        preview = await preview_commit(repo_path)
        if preview["ready_to_commit"]:
            if preview["file_categories"]["critical_files"] > 0:
                validation = await validate_staged_changes(preview["repository_path"])
            elif preview["summary"]["total_files"] > 10:
                validation = await validate_staged_changes(preview["repository_path"])

        # Post-commit workflow
        if preview["ready_to_commit"]:
            # After commit would happen, check push readiness
            push_check = await get_push_readiness(preview["repository_path"])
        ```

        **Decision Points**:
        - `ready_to_commit=False`: No staged changes → analyze working directory
        - `file_categories.critical_files > 0`: Critical files → require validation
        - `summary.total_files > X`: Large commits → require additional review
        - `ready_to_commit=True`: Can commit → check push readiness after commit
        """
        await ctx.info(f"Previewing commit for: {repository_path}")

        repo_path = Path(repository_path).resolve()
        if not is_git_repository(repo_path):
            git_root = find_git_root(repo_path)
            if not git_root:
                await ctx.error(f"No git repository found at or above {repo_path}")
                return {"error": f"No git repository found at or above {repo_path}"}
            repo_path = git_root

        try:
            await ctx.debug("Creating repository model")
            repo = LocalRepository(
                path=repo_path,
                name=repo_path.name,
                current_branch="main",
                head_commit="unknown",
            )

            await ctx.debug("Detecting staged changes")
            current_services = services
            staged_changes = await current_services[
                "change_detector"
            ].detect_staged_changes(repo, ctx)

            if not staged_changes.ready_to_commit:
                await ctx.info("No changes staged for commit")
                return {
                    "repository_path": str(repo_path),
                    "ready_to_commit": False,
                    "message": "No changes staged for commit",
                }

            await ctx.debug("Categorizing staged changes")
            # Categorize changes using existing analyzer
            categories = current_services["diff_analyzer"].categorize_changes(
                staged_changes.staged_files
            )

            await ctx.debug("Analyzing file types")
            # Get file types
            file_types: dict[str, int] = {}
            for file_status in staged_changes.staged_files:
                ext = Path(file_status.path).suffix.lower() or "no_extension"
                file_types[ext] = file_types.get(ext, 0) + 1

            await ctx.info(
                f"Commit preview ready: {staged_changes.total_staged} files, {categories.total_files} categorized"
            )

            return {
                "repository_path": str(repo_path),
                "ready_to_commit": True,
                "summary": {
                    "total_files": staged_changes.total_staged,
                    "total_additions": staged_changes.total_additions,
                    "total_deletions": staged_changes.total_deletions,
                },
                "file_categories": {
                    "critical_files": len(categories.critical_files),
                    "source_code": len(categories.source_code),
                    "documentation": len(categories.documentation),
                    "tests": len(categories.tests),
                    "configuration": len(categories.configuration),
                    "other": len(categories.other),
                },
                "file_types": file_types,
                "files_by_status": {
                    "added": [
                        f.path
                        for f in staged_changes.staged_files
                        if f.status_code == "A"
                    ],
                    "modified": [
                        f.path
                        for f in staged_changes.staged_files
                        if f.status_code == "M"
                    ],
                    "deleted": [
                        f.path
                        for f in staged_changes.staged_files
                        if f.status_code == "D"
                    ],
                    "renamed": [
                        f.path
                        for f in staged_changes.staged_files
                        if f.status_code == "R"
                    ],
                },
            }

        except Exception as e:
            await ctx.error(f"Failed to preview commit: {str(e)}")
            return {"error": f"Failed to preview commit: {str(e)}"}

    @mcp.tool()  # type: ignore[misc]
    async def validate_staged_changes(
        ctx: Context,
        repository_path: str = Field(default=".", description="Path to git repository"),
    ) -> dict[str, Any]:
        """Validate staged changes for common issues.

        Checks staged changes for potential problems like large files,
        critical file changes, or other issues before committing.

        **Return Type**: Dict with validation results
        ```python
        {
            "repository_path": str,           # Path to analyzed repository
            "valid": bool,                    # Whether changes pass validation - use for commit decisions
            "risk_level": str,                # "low"|"medium"|"high" - use for workflow routing
            "risk_score": int,                # 0-10 numeric risk score
            "warnings": List[str],            # Non-blocking issues for review
            "errors": List[str],              # Blocking issues that prevent commit
            "recommendations": List[str],     # Suggested actions for improvement
            "summary": {                      # Validation statistics
                "total_files": int, "high_risk_files": int,
                "critical_files": int, "binary_files": int
            }
        }
        ```

        **Key Fields for Chaining**:
        - `valid` (bool): Whether commit should proceed
        - `risk_level` (str): Route to different validation workflows
        - `errors` (list): Blocking issues that must be resolved
        - `repository_path` (str): Pass to other tools for fixes

        **Common Chaining Patterns**:
        ```python
        # Validation-based commit workflow
        validation = await validate_staged_changes(repo_path)
        if validation["valid"]:
            if validation["risk_level"] == "low":
                # Safe to commit, check push readiness
                push_check = await get_push_readiness(validation["repository_path"])
            else:
                # Medium/high risk - get detailed analysis
                summary = await get_outstanding_summary(validation["repository_path"], detailed=True)
        else:
            # Has errors - analyze working directory for fixes
            wd_result = await analyze_working_directory(validation["repository_path"])

        # Risk-based routing
        if validation["risk_level"] == "high":
            health_check = await analyze_repository_health(validation["repository_path"])
        ```

        **Decision Points**:
        - `valid=True`: Validation passed → proceed with commit or push checks
        - `valid=False`: Has blocking errors → fix issues before committing
        - `risk_level="high"`: High risk → require additional review/analysis
        - `errors`: Specific blocking issues that need resolution
        """
        start_time = time.time()
        await ctx.info(f"Starting staged changes validation for: {repository_path}")

        repo_path = Path(repository_path).resolve()
        if not is_git_repository(repo_path):
            git_root = find_git_root(repo_path)
            if not git_root:
                await ctx.error(f"No git repository found at or above {repo_path}")
                return {"error": f"No git repository found at or above {repo_path}"}
            repo_path = git_root

        try:
            await ctx.debug("Creating repository model")
            repo = LocalRepository(
                path=repo_path,
                name=repo_path.name,
                current_branch="main",
                head_commit="unknown",
            )

            await ctx.debug("Detecting staged changes")
            current_services = services
            staged_changes = await current_services[
                "change_detector"
            ].detect_staged_changes(repo, ctx)

            if not staged_changes.ready_to_commit:
                await ctx.info(
                    "No changes staged for commit - validation not applicable"
                )
                return {
                    "repository_path": str(repo_path),
                    "valid": False,
                    "message": "No changes staged for commit",
                }

            await ctx.debug("Performing risk assessment")
            # Perform validation using existing risk assessment
            risk_assessment = current_services["diff_analyzer"].assess_risk(
                staged_changes.staged_files
            )

            await ctx.debug("Categorizing changes for validation")
            categories = current_services["diff_analyzer"].categorize_changes(
                staged_changes.staged_files
            )

            warnings = []
            errors = []

            # Check for high-risk changes
            if risk_assessment.is_high_risk:
                warning_msg = f"High-risk changes detected: {', '.join(risk_assessment.risk_factors)}"
                warnings.append(warning_msg)
                await ctx.warning(warning_msg)

            # Check for large changes
            if risk_assessment.large_changes:
                warning_msg = (
                    f"Large changes in {len(risk_assessment.large_changes)} files"
                )
                warnings.append(warning_msg)
                await ctx.warning(warning_msg)

            # Check for critical files
            if categories.has_critical_changes:
                warning_msg = (
                    f"Critical files changed: {len(categories.critical_files)}"
                )
                warnings.append(warning_msg)
                await ctx.warning(warning_msg)

            # Check for binary files
            binary_files = [f.path for f in staged_changes.staged_files if f.is_binary]
            if binary_files:
                warning_msg = f"Binary files included: {len(binary_files)}"
                warnings.append(warning_msg)
                await ctx.warning(warning_msg)

            # Check for potential conflicts
            if risk_assessment.potential_conflicts:
                error_msg = f"Potential conflicts detected in: {', '.join(risk_assessment.potential_conflicts)}"
                errors.append(error_msg)
                await ctx.error(error_msg)

            # Overall validation result
            is_valid = len(errors) == 0

            # Generate recommendations
            recommendations = []
            if risk_assessment.large_changes:
                recommendations.append(
                    "Review large changes carefully before committing"
                )
            if categories.has_critical_changes:
                recommendations.append("Double-check critical file changes")
            if staged_changes.total_staged > 10:
                recommendations.append(
                    "Consider splitting large commits into smaller ones"
                )
            if len(categories.source_code) > 0 and len(categories.tests) == 0:
                recommendations.append("Add tests for new functionality")

            # Remove None values
            recommendations = [r for r in recommendations if r]

            duration = time.time() - start_time
            await ctx.info(
                f"Validation completed in {duration:.2f} seconds - {'VALID' if is_valid else 'INVALID'}"
            )

            return {
                "repository_path": str(repo_path),
                "valid": is_valid,
                "risk_level": risk_assessment.risk_level,
                "risk_score": risk_assessment.risk_score,
                "warnings": warnings,
                "errors": errors,
                "recommendations": recommendations,
                "summary": {
                    "total_files": staged_changes.total_staged,
                    "high_risk_files": len(risk_assessment.large_changes),
                    "critical_files": len(categories.critical_files),
                    "binary_files": len(binary_files),
                },
            }

        except Exception as e:
            duration = time.time() - start_time
            await ctx.error(
                f"Staged changes validation failed after {duration:.2f} seconds: {str(e)}"
            )
            return {"error": f"Failed to validate staged changes: {str(e)}"}

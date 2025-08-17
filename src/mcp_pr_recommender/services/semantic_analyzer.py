"""Enhanced semantic analyzer that handles all grouping logic."""
import json
import logging

import openai
from mcp_shared_lib.models import FileStatus, OutstandingChangesAnalysis

from mcp_pr_recommender.config import settings
from mcp_pr_recommender.models.pr.recommendations import ChangeGroup, PRRecommendation
from mcp_pr_recommender.prompts import get_enhanced_grouping_system_prompt


class SemanticAnalyzer:
    """LLM-powered analyzer that handles all file grouping and PR generation."""

    def __init__(self) -> None:
        """Initialize semantic analyzer with OpenAI client."""
        self.client = openai.AsyncOpenAI(api_key=settings().openai_api_key)
        self.logger = logging.getLogger(__name__)

    async def analyze_and_generate_prs(
        self, files: list[FileStatus], analysis: OutstandingChangesAnalysis
    ) -> list[PRRecommendation]:
        """Analyze files and generate PR recommendations."""
        self.logger.info(f"Starting LLM-based analysis of {len(files)} files")

        # Step 1: Basic filtering only
        clean_files = self._filter_files(files)
        self.logger.info(f"Filtered to {len(clean_files)} relevant files")

        if not clean_files:
            self.logger.warning("No files to analyze after filtering")
            return []

        # Step 2: Let LLM do intelligent grouping
        groups = await self._llm_group_files(clean_files, analysis)
        self.logger.info(f"LLM created {len(groups)} logical groups")

        # Step 3: Generate PR recommendations
        pr_recommendations = self._generate_pr_recommendations(groups, analysis)
        self.logger.info(f"Generated {len(pr_recommendations)} PR recommendations")

        return pr_recommendations

    def _filter_files(self, files: list[FileStatus]) -> list[FileStatus]:
        """Filter files - exclude obvious junk files only."""
        clean_files = []
        excluded_count = 0

        for file in files:
            if self._should_exclude_file(file.path):
                excluded_count += 1
                continue
            clean_files.append(file)

        if excluded_count > 0:
            self.logger.info(f"Excluded {excluded_count} cache/generated files")

        return clean_files

    def _should_exclude_file(self, path: str) -> bool:
        """Files that shouldn't be in PRs."""
        path_lower = path.lower()

        exclude_patterns = [
            "__pycache__",
            ".pyc",
            ".pyo",
            ".history/",
            ".git/",
            "node_modules/",
            ".ds_store",
            "thumbs.db",
            ".pytest_cache/",
        ]

        return any(pattern in path_lower for pattern in exclude_patterns)

    async def _llm_group_files(
        self, files: list[FileStatus], analysis: OutstandingChangesAnalysis
    ) -> list[ChangeGroup]:
        """Use LLM to intelligently group files into logical PR units."""
        # Create the grouping prompt
        prompt = self._create_grouping_prompt(files, analysis)

        try:
            response = await self.client.chat.completions.create(
                model=settings().openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": get_enhanced_grouping_system_prompt(),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings().max_tokens_per_request
                * 2,  # Need more tokens for grouping
                temperature=0.1,
            )

            # Parse LLM response into groups
            content = response.choices[0].message.content
            if content is None:
                self.logger.warning("LLM returned None content")
                groups = []
            else:
                groups = self._parse_grouping_response(content, files)

            if not groups:
                self.logger.warning(
                    "LLM grouping failed, falling back to simple grouping"
                )
                return self._fallback_grouping(files)

            return groups

        except Exception as e:
            self.logger.error(f"LLM grouping failed: {e}")
            return self._fallback_grouping(files)

    def _create_grouping_prompt(
        self, files: list[FileStatus], analysis: OutstandingChangesAnalysis
    ) -> str:
        """Create the prompt for LLM grouping."""
        # Prepare file information - prioritize files with actual changes
        files_with_changes = [f for f in files if f.total_changes > 0]
        files_without_changes = [f for f in files if f.total_changes == 0]

        file_info = []
        total_changes = 0

        # First, list files with actual changes
        for file in files_with_changes:
            changes = file.total_changes
            total_changes += changes

            file_info.append(
                {
                    "path": file.path,
                    "status": file.status_code,
                    "lines_added": file.lines_added,
                    "lines_deleted": file.lines_deleted,
                    "total_changes": changes,
                    "is_binary": file.is_binary,
                    "has_changes": True,
                }
            )

        # Then, list files without changes
        for file in files_without_changes:
            file_info.append(
                {
                    "path": file.path,
                    "status": file.status_code,
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "total_changes": 0,
                    "is_binary": file.is_binary,
                    "has_changes": False,
                }
            )

        # Sort by most changes first
        file_info.sort(key=lambda f: f["total_changes"], reverse=True)

        # Format for prompt
        file_list = []
        for f in file_info:
            status_desc = {
                "M": "Modified",
                "A": "Added",
                "D": "Deleted",
                "R": "Renamed",
            }.get(f["status"], f["status"])

            if f["has_changes"]:
                file_list.append(
                    f"- {f['path']} ({status_desc}) +{f['lines_added']}/-{f['lines_deleted']} lines"
                )
            else:
                file_list.append(
                    f"- {f['path']} ({status_desc}) NO CHANGES (likely moved/touched)"
                )

        return f"""Group these {len(files)} files into logical Pull Requests:

**Repository Context:**
- Files with actual changes: {len(files_with_changes)}
- Files without changes: {len(files_without_changes)}
- Total line changes: {total_changes:,}
- Risk level: {analysis.risk_assessment.risk_level}

**Files to group:**
{chr(10).join(file_list)}

**Additional Context:**
{analysis.summary}

**Key Question:** Should files without changes be grouped with related files that DO have changes,
    or should they be in separate cleanup PRs?

Please group these files into the optimal number of logical, atomic Pull Requests."""

    def _parse_grouping_response(
        self, response: str, files: list[FileStatus]
    ) -> list[ChangeGroup]:
        """Parse LLM grouping response into ChangeGroup objects."""
        try:
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")

            json_str = response[start:end]
            data = json.loads(json_str)

            if "groups" not in data:
                raise ValueError("No 'groups' key in response")

            # Create file lookup
            file_lookup = {f.path: f for f in files}

            groups = []
            used_files = set()

            for i, group_data in enumerate(data["groups"]):
                # Get files for this group
                group_files = []
                for file_path in group_data.get("files", []):
                    if file_path in file_lookup and file_path not in used_files:
                        group_files.append(file_lookup[file_path])
                        used_files.add(file_path)

                if group_files:
                    groups.append(
                        ChangeGroup(
                            id=group_data.get("id", f"group_{i}"),
                            files=group_files,
                            category=group_data.get("category", "chore"),
                            confidence=group_data.get("confidence", 0.8),
                            reasoning=group_data.get(
                                "reasoning", "LLM grouped these files"
                            ),
                            semantic_similarity=group_data.get("confidence", 0.8),
                        )
                    )

            # Handle any ungrouped files
            ungrouped_files = [f for f in files if f.path not in used_files]
            if ungrouped_files:
                groups.append(
                    ChangeGroup(
                        id="ungrouped_files",
                        files=ungrouped_files,
                        category="chore",
                        confidence=0.6,
                        reasoning=f"Files not grouped by LLM ({len(ungrouped_files)} files)",
                        semantic_similarity=0.5,
                    )
                )

            self.logger.info(
                f"LLM grouping rationale: {data.get('rationale', 'No rationale provided')}"
            )
            return groups

        except Exception as e:
            self.logger.error(f"Failed to parse LLM grouping response: {e}")
            self.logger.debug(f"Response was: {response[:500]}...")
            return []

    def _fallback_grouping(self, files: list[FileStatus]) -> list[ChangeGroup]:
        """Provide fallback grouping if LLM fails."""
        # Separate files with changes from those without
        files_with_changes = [f for f in files if f.total_changes > 0]
        files_without_changes = [f for f in files if f.total_changes == 0]

        groups = []

        if files_with_changes:
            # Group files with changes by basic type
            source_files = []
            config_files = []
            other_files = []

            for file in files_with_changes:
                path_lower = file.path.lower()

                if (
                    path_lower.endswith((".py", ".js", ".ts", ".java", ".go"))
                    and "test" not in path_lower
                ):
                    source_files.append(file)
                elif any(
                    name in path_lower
                    for name in [
                        "pyproject.toml",
                        "poetry.lock",
                        "requirements.txt",
                        "package.json",
                    ]
                ):
                    config_files.append(file)
                else:
                    other_files.append(file)

            if source_files:
                groups.append(
                    ChangeGroup(
                        id="source_code_changes",
                        files=source_files,
                        category="feature",
                        confidence=0.7,
                        reasoning=f"Source code changes ({len(source_files)} files)",
                        semantic_similarity=0.7,
                    )
                )

            if config_files:
                groups.append(
                    ChangeGroup(
                        id="configuration_changes",
                        files=config_files,
                        category="config",
                        confidence=0.8,
                        reasoning=f"Configuration changes ({len(config_files)} files)",
                        semantic_similarity=0.8,
                    )
                )

            if other_files:
                groups.append(
                    ChangeGroup(
                        id="other_changes",
                        files=other_files,
                        category="chore",
                        confidence=0.6,
                        reasoning=f"Other changes ({len(other_files)} files)",
                        semantic_similarity=0.6,
                    )
                )

        # Group files without changes separately
        if files_without_changes:
            groups.append(
                ChangeGroup(
                    id="no_changes_cleanup",
                    files=files_without_changes,
                    category="chore",
                    confidence=0.5,
                    reasoning=f"Files without changes - likely cleanup/reorganization ({len(files_without_changes)} files)",
                    semantic_similarity=0.9,
                )
            )

        return groups

    def _generate_pr_recommendations(
        self, groups: list[ChangeGroup], _analysis: OutstandingChangesAnalysis
    ) -> list[PRRecommendation]:
        """Generate PR recommendations from groups."""
        recommendations = []

        for i, group in enumerate(groups):
            # Calculate metrics
            total_changes = sum(f.total_changes for f in group.files)
            files_count = len(group.files)
            files_with_changes = len([f for f in group.files if f.total_changes > 0])

            # Generate title and description
            title = self._generate_title(group, files_with_changes)
            description = self._generate_description(group)

            # Determine priority and risk
            priority = self._determine_priority(
                group, total_changes, files_with_changes
            )
            risk_level = self._determine_risk(total_changes, files_count)

            # Estimate review time
            review_time = self._estimate_review_time(files_count, total_changes)

            recommendation = PRRecommendation(
                id=f"pr_{i+1}",
                title=title,
                description=description,
                files=group.file_paths,
                branch_name=self._generate_branch_name(group),
                priority=priority,
                estimated_review_time=review_time,
                risk_level=risk_level,
                reasoning=group.reasoning,
                dependencies=[],
                labels=self._generate_labels(group),
                total_lines_changed=total_changes,
                files_count=files_count,
            )

            recommendations.append(recommendation)

        return recommendations

    def _generate_title(self, group: ChangeGroup, files_with_changes: int) -> str:
        """Generate PR title."""
        category_prefixes = {
            "feature": "feat:",
            "config": "config:",
            "test": "test:",
            "docs": "docs:",
            "chore": "chore:",
        }

        prefix = category_prefixes.get(group.category, "chore:")
        file_count = len(group.files)

        # Use group ID for meaningful title
        if group.id == "source_code_changes":
            return (
                f"{prefix} update core application logic ({files_with_changes} files)"
            )
        elif group.id == "configuration_changes":
            return f"{prefix} update project dependencies ({files_with_changes} files)"
        elif group.id == "no_changes_cleanup":
            return f"{prefix} project cleanup and reorganization ({file_count} files)"
        else:
            # Use group ID, cleaned up
            clean_id = group.id.replace("_", " ").replace("-", " ")
            if files_with_changes > 0:
                return f"{prefix} {clean_id} ({files_with_changes} files with changes)"
            else:
                return f"{prefix} {clean_id} ({file_count} files)"

    def _generate_description(self, group: ChangeGroup) -> str:
        """Generate PR description."""
        total_additions = sum(f.lines_added for f in group.files)
        total_deletions = sum(f.lines_deleted for f in group.files)
        total_changes = total_additions + total_deletions

        files_with_changes = [f for f in group.files if f.total_changes > 0]
        files_without_changes = [f for f in group.files if f.total_changes == 0]

        lines = [
            f"## {group.category.title()} Changes",
            "",
            f"**Files modified:** {len(group.files)}",
            f"**Lines changed:** {total_changes:,} (+{total_additions:,}/-{total_deletions:,})",
            "",
        ]

        if files_with_changes:
            lines.extend([f"### Files with changes ({len(files_with_changes)}):", ""])

            # Show all files with changes
            for file in files_with_changes:
                lines.append(
                    f"- `{file.path}` (+{file.lines_added}/-{file.lines_deleted})"
                )

        if files_without_changes:
            lines.extend(
                [
                    "",
                    f"### Files without changes ({len(files_without_changes)}):",
                    "These files may have been moved, renamed, or touched without content changes:",
                    "",
                ]
            )

            for file in files_without_changes[:10]:  # Show first 10
                lines.append(f"- `{file.path}`")

            if len(files_without_changes) > 10:
                lines.append(f"- ... and {len(files_without_changes) - 10} more")

        lines.extend(
            [
                "",
                "### Reasoning:",
                group.reasoning,
            ]
        )

        # Add context about the overall change
        if total_changes > 1000:
            lines.extend(
                [
                    "",
                    "⚠️ **Large changeset** - please review carefully",
                ]
            )

        return "\n".join(lines)

    def _generate_branch_name(self, group: ChangeGroup) -> str:
        """Generate clean branch names."""
        category = group.category.replace(" ", "-")

        if group.id == "source_code_changes":
            return f"{category}/core-updates"
        elif group.id == "configuration_changes":
            return f"{category}/dependencies"
        elif group.id == "no_changes_cleanup":
            return f"{category}/cleanup"
        else:
            # Clean up the group ID for branch name
            clean_id = group.id.replace("_", "-").replace("changes", "").strip("-")
            return f"{category}/{clean_id}"

    def _determine_priority(
        self, group: ChangeGroup, total_changes: int, files_with_changes: int
    ) -> str:
        """Determine priority."""
        if files_with_changes == 0:
            return "low"  # No actual changes
        elif group.category == "feature" or total_changes > 500:
            return "high"
        elif group.category in ["config", "test"]:
            return "medium"
        else:
            return "low"

    def _determine_risk(self, total_changes: int, files_count: int) -> str:
        """Determine risk level with proper handling for cleanup PRs."""
        # CRITICAL FIX: Files with no actual changes should be low risk
        if total_changes == 0:
            return "low"

        # Risk assessment for files with actual changes
        if total_changes > 1000:
            return "high"
        elif total_changes > 200 or files_count > 8:
            return "medium"
        else:
            return "low"

    def _estimate_review_time(self, files_count: int, total_changes: int) -> int:
        """Estimate review time."""
        if total_changes == 0:
            return 10  # Minimum time for cleanup PRs

        base_time = files_count * 3
        line_time = total_changes // 10 * 0.5
        return max(10, min(120, int(base_time + line_time)))

    def _generate_labels(self, group: ChangeGroup) -> list[str]:
        """Generate labels."""
        labels = [group.category]

        total_changes = sum(f.total_changes for f in group.files)
        files_with_changes = len([f for f in group.files if f.total_changes > 0])

        if total_changes > 500:
            labels.append("large-change")

        if len(group.files) > 10:
            labels.append("multiple-files")

        if files_with_changes == 0:
            labels.append("cleanup")

        return labels

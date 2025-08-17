"""Simple grouping engine that orchestrates the PR recommendation process."""
import logging
from pathlib import Path

from shared.models import FileStatus, OutstandingChangesAnalysis

from mcp_pr_recommender.config import settings
from mcp_pr_recommender.models.pr.recommendations import (
    ChangeGroup,
    PRRecommendation,
    PRStrategy,
)
from mcp_pr_recommender.services.atomicity_validator import AtomicityValidator
from mcp_pr_recommender.services.semantic_analyzer import SemanticAnalyzer


class GroupingEngine:
    """Simple engine for generating PR recommendations."""

    def __init__(self) -> None:
        """Initialize grouping engine with analyzer and validator."""
        self.semantic_analyzer = SemanticAnalyzer()
        self.atomicity_validator = AtomicityValidator()
        self.logger = logging.getLogger(__name__)

    async def generate_pr_recommendations(
        self, analysis: OutstandingChangesAnalysis, strategy_name: str = "semantic"
    ) -> PRStrategy:
        """Generate PR recommendations from git analysis."""
        self.logger.info(
            f"Generating PR recommendations using {strategy_name} strategy"
        )
        self.logger.info(f"Input: {len(analysis.all_changed_files)} files to analyze")

        # Step 1: Simple logical grouping
        initial_groups = self._create_simple_groups(analysis.all_changed_files)
        self.logger.info(f"Initial grouping: {len(initial_groups)} groups")

        # Step 2: Skip semantic analysis if groups are already good
        if (
            len(initial_groups) <= 5
            and settings().enable_llm_analysis
            and strategy_name == "semantic"
        ):
            # Instead of refine_groups, use the main analysis method
            file_statuses = [file for group in initial_groups for file in group.files]
            refined_recommendations = (
                await self.semantic_analyzer.analyze_and_generate_prs(
                    file_statuses, analysis
                )
            )
            # Convert back to groups for consistency
            refined_groups = [
                ChangeGroup(
                    id=rec.id,
                    files=[
                        f for f in analysis.all_changed_files if f.path in rec.files
                    ],
                    category=rec.labels[0] if rec.labels else "other",
                    reasoning=rec.reasoning,
                    confidence=0.8,
                )
                for rec in refined_recommendations
            ]
            self.logger.info(f"Semantic refinement: {len(refined_groups)} groups")
        else:
            refined_groups = initial_groups
            self.logger.info("Skipping semantic analysis - groups already optimal")

        # Step 3: Final validation (but don't split good groups)
        validated_groups = self._validate_groups(refined_groups)
        self.logger.info(f"Final validation: {len(validated_groups)} groups")

        # Step 4: Generate PR recommendations
        pr_recommendations = self._groups_to_prs(validated_groups, analysis)

        return PRStrategy(
            strategy_name=strategy_name,
            source_analysis=analysis,
            change_groups=validated_groups,
            recommended_prs=pr_recommendations,
            metadata={
                "initial_groups": len(initial_groups),
                "semantic_refined": len(refined_groups),
                "final_groups": len(validated_groups),
                "grouping_strategy": "simple_logical",
                "settings_used": {
                    "max_files_per_pr": settings().max_files_per_pr,
                    "similarity_threshold": settings().similarity_threshold,
                },
            },
        )

    def _create_simple_groups(self, files: list[FileStatus]) -> list[ChangeGroup]:
        """Create simple, logical groups - aim for 3-5 total groups."""
        # Filter out files that shouldn't be in PRs
        clean_files = [f for f in files if not self._should_exclude_file(f.path)]
        excluded_count = len(files) - len(clean_files)

        if excluded_count > 0:
            self.logger.info(
                f"Excluded {excluded_count} cache/history files from PR grouping"
            )

        if not clean_files:
            self.logger.warning("No files left after filtering")
            return []

        groups = []

        # Group 1: Core source code changes (highest priority)
        source_files = [f for f in clean_files if self._is_core_source_code(f.path)]
        if source_files:
            groups.append(
                ChangeGroup(
                    id="source_code_changes",
                    files=source_files,
                    category="feature",
                    confidence=0.9,
                    reasoning=f"Core application source code changes ({len(source_files)} files)",
                    semantic_similarity=0.8,
                )
            )

        # Group 2: Project configuration (second priority)
        config_files = [
            f
            for f in clean_files
            if self._is_project_config(f.path) and f not in source_files
        ]
        if config_files:
            groups.append(
                ChangeGroup(
                    id="configuration_changes",
                    files=config_files,
                    category="config",
                    confidence=0.9,
                    reasoning=f"Project configuration and dependencies ({len(config_files)} files)",
                    semantic_similarity=0.9,
                )
            )

        # Group 3: Tests (third priority)
        test_files = [
            f
            for f in clean_files
            if self._is_test_file(f.path) and f not in source_files + config_files
        ]
        if test_files:
            groups.append(
                ChangeGroup(
                    id="test_changes",
                    files=test_files,
                    category="test",
                    confidence=0.9,
                    reasoning=f"Test suite updates ({len(test_files)} files)",
                    semantic_similarity=0.9,
                )
            )

        # Group 4: Documentation
        doc_files = [
            f
            for f in clean_files
            if self._is_documentation(f.path)
            and f not in source_files + config_files + test_files
        ]
        if doc_files:
            groups.append(
                ChangeGroup(
                    id="documentation_changes",
                    files=doc_files,
                    category="docs",
                    confidence=0.8,
                    reasoning=f"Documentation updates ({len(doc_files)} files)",
                    semantic_similarity=0.8,
                )
            )

        # Group 5: Everything else (lowest priority)
        processed_files = source_files + config_files + test_files + doc_files
        other_files = [f for f in clean_files if f not in processed_files]
        if other_files:
            groups.append(
                ChangeGroup(
                    id="miscellaneous_changes",
                    files=other_files,
                    category="chore",
                    confidence=0.7,
                    reasoning=f"Miscellaneous project updates ({len(other_files)} files)",
                    semantic_similarity=0.6,
                )
            )

        self.logger.info(
            f"Created {len(groups)} logical groups: {[g.id for g in groups]}"
        )

        # If we still have too many files in one group, split it
        final_groups = []
        for group in groups:
            if len(group.files) > 15:  # Only split really large groups
                split_groups = self._split_large_group_simple(group)
                final_groups.extend(split_groups)
            else:
                final_groups.append(group)

        return final_groups

    def _should_exclude_file(self, path: str) -> bool:
        """Files that shouldn't be in PRs."""
        path_lower = path.lower()

        # Exclude generated, cache, and history files
        exclude_patterns = [
            "__pycache__",
            ".pyc",
            ".pyo",
            ".history/",
            ".git/",
            "node_modules/",
            ".DS_Store",
            "thumbs.db",
            ".pytest_cache/",
            ".coverage",
            "*.egg-info/",
        ]

        return any(pattern in path_lower for pattern in exclude_patterns)

    def _is_core_source_code(self, path: str) -> bool:
        """Is this core application source code."""
        path_lower = path.lower()

        # Source code extensions
        source_extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".cpp",
            ".c",
            ".h",
        ]

        # Must be source code and not test
        return (
            any(path.endswith(ext) for ext in source_extensions)
            and "test" not in path_lower
            and "spec" not in path_lower
            and not self._should_exclude_file(path)
        )

    def _is_project_config(self, path: str) -> bool:
        """Is this a project configuration file."""
        filename = Path(path).name.lower()

        # Important config files
        config_filenames = [
            "pyproject.toml",
            "poetry.lock",
            "requirements.txt",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "dockerfile",
            "makefile",
            "cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
        ]

        # Config extensions
        config_extensions = [".toml", ".ini", ".env", ".config"]

        return (
            filename in config_filenames
            or any(path.endswith(ext) for ext in config_extensions)
            or filename.startswith(".env")
        )

    def _is_test_file(self, path: str) -> bool:
        """Is this a test file."""
        path_lower = path.lower()

        # Test patterns
        test_patterns = ["test", "spec", "__test__", ".test.", ".spec."]

        # Must be code file and have test pattern
        code_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"]

        return any(path.endswith(ext) for ext in code_extensions) and any(
            pattern in path_lower for pattern in test_patterns
        )

    def _is_documentation(self, path: str) -> bool:
        """Is this a documentation file."""
        path_lower = path.lower()

        # Documentation extensions
        doc_extensions = [".md", ".rst", ".txt", ".adoc"]

        # Documentation directories
        doc_dirs = ["docs/", "doc/", "documentation/"]

        return any(path.endswith(ext) for ext in doc_extensions) or any(
            doc_dir in path_lower for doc_dir in doc_dirs
        )

    def _split_large_group_simple(self, group: ChangeGroup) -> list[ChangeGroup]:
        """Split a large group by directory."""
        files = group.files

        # Group by directory
        dir_groups: dict[str, list[FileStatus]] = {}
        for file in files:
            parent_dir = str(Path(file.path).parent)
            if parent_dir not in dir_groups:
                dir_groups[parent_dir] = []
            dir_groups[parent_dir].append(file)

        # Create groups from directories
        split_groups = []
        for i, (directory, dir_files) in enumerate(dir_groups.items()):
            dir_name = Path(directory).name if directory != "." else "root"

            split_groups.append(
                ChangeGroup(
                    id=f"{group.id}_dir_{i}",
                    files=dir_files,
                    category=group.category,
                    confidence=group.confidence,
                    reasoning=f"{group.reasoning.split('(')[0].strip()} in {dir_name} directory ({len(dir_files)} files)",
                    semantic_similarity=group.semantic_similarity,
                )
            )

        self.logger.info(
            f"Split large group {group.id} into {len(split_groups)} directory-based groups"
        )
        return split_groups

    def _validate_groups(self, groups: list[ChangeGroup]) -> list[ChangeGroup]:
        """Validate groups - only split if really necessary."""
        validated_groups = []

        for group in groups:
            # Only split if group is unreasonably large (>20 files)
            if len(group.files) > 20:
                self.logger.warning(
                    f"Group {group.id} has {len(group.files)} files - splitting"
                )
                split_groups = self._split_large_group_simple(group)
                validated_groups.extend(split_groups)
            else:
                validated_groups.append(group)

        return validated_groups

    def _groups_to_prs(
        self, groups: list[ChangeGroup], analysis: OutstandingChangesAnalysis
    ) -> list[PRRecommendation]:
        """Convert groups to PR recommendations with better titles and descriptions."""
        pr_recommendations = []

        for i, group in enumerate(groups):
            # Generate better titles and descriptions
            title = self._generate_smart_title(group)
            description = self._generate_smart_description(group, analysis)
            branch_name = self._generate_branch_name(group)

            # Calculate real metrics
            total_lines = sum(f.total_changes for f in group.files)
            files_count = len(group.files)

            # Better priority and risk assessment
            priority = self._determine_priority(group)
            risk_level = self._determine_risk_level(group, total_lines, files_count)

            # Realistic review time
            review_time = self._estimate_review_time(files_count, total_lines)

            pr = PRRecommendation(
                id=f"pr_{i+1}",
                title=title,
                description=description,
                files=group.file_paths,
                branch_name=branch_name,
                priority=priority,
                estimated_review_time=review_time,
                risk_level=risk_level,
                reasoning=group.reasoning,
                dependencies=[],
                labels=self._generate_labels(group),
                total_lines_changed=total_lines,
                files_count=files_count,
            )

            pr_recommendations.append(pr)

        return pr_recommendations

    def _generate_smart_title(self, group: ChangeGroup) -> str:
        """Generate smart PR titles based on content."""
        category_prefixes = {
            "feature": "feat:",
            "config": "config:",
            "test": "test:",
            "docs": "docs:",
            "chore": "chore:",
        }

        prefix = category_prefixes.get(group.category, "chore:")
        file_count = len(group.files)

        if group.id == "source_code_changes":
            return f"{prefix} update core application logic ({file_count} files)"
        elif group.id == "configuration_changes":
            return f"{prefix} update project dependencies and configuration ({file_count} files)"
        elif group.id == "test_changes":
            return f"{prefix} update test suite ({file_count} files)"
        elif group.id == "documentation_changes":
            return f"{prefix} update project documentation ({file_count} files)"
        elif group.id == "miscellaneous_changes":
            return f"{prefix} miscellaneous project updates ({file_count} files)"
        else:
            # For split groups, be more specific
            if "dir_" in group.id:
                return f"{prefix} update {group.id.split('_')[-2]} module ({file_count} files)"
            else:
                return f"{prefix} update {group.category} files ({file_count} files)"

    def _generate_smart_description(
        self, group: ChangeGroup, _analysis: OutstandingChangesAnalysis
    ) -> str:
        """Generate smart descriptions with real statistics."""
        # Calculate real statistics
        total_additions = sum(f.lines_added for f in group.files)
        total_deletions = sum(f.lines_deleted for f in group.files)
        total_changes = total_additions + total_deletions

        # Categorize files by actual changes
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

            # Show top 10 files with most changes
            top_files = sorted(
                files_with_changes, key=lambda f: f.total_changes, reverse=True
            )[:10]
            for file in top_files:
                lines.append(
                    f"- `{file.path}` (+{file.lines_added}/-{file.lines_deleted})"
                )

            if len(files_with_changes) > 10:
                lines.append(
                    f"- ... and {len(files_with_changes) - 10} more files with changes"
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

            for file in files_without_changes[:5]:  # Show first 5
                lines.append(f"- `{file.path}`")

            if len(files_without_changes) > 5:
                lines.append(f"- ... and {len(files_without_changes) - 5} more")

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
        elif group.id == "test_changes":
            return f"{category}/test-updates"
        elif group.id == "documentation_changes":
            return f"{category}/docs-updates"
        else:
            # Clean up the group ID for branch name
            clean_id = group.id.replace("_", "-").replace("changes", "").strip("-")
            return f"{category}/{clean_id}"

    def _determine_priority(
        self, group: ChangeGroup
    ) -> str:  # Should return Literal types
        """Determine priority based on category and size."""
        if group.category == "feature":
            return "high"
        elif group.category in ["config", "test"]:
            return "medium"
        else:
            return "low"

    def _determine_risk_level(
        self, group: ChangeGroup, total_lines: int, files_count: int
    ) -> str:  # Should return Literal types
        """Determine risk based on real factors."""
        # High risk: lots of changes OR core files OR config changes
        if total_lines > 1000:
            return "high"
        if group.category == "feature" or (
            group.category in ["config", "test"] and total_lines > 200
        ):
            return "high" if group.category == "feature" else "medium"
        elif files_count > 15:
            return "medium"
        else:
            return "low"

    def _estimate_review_time(self, files_count: int, total_lines: int) -> int:
        """Realistic review time estimation."""
        # Base: 3 minutes per file + 30 seconds per 10 lines
        base_time = files_count * 3
        line_time = total_lines // 10 * 0.5

        estimated = int(base_time + line_time)

        # Minimum 10 minutes, maximum 120 minutes for sanity
        return max(10, min(120, estimated))

    def _generate_labels(self, group: ChangeGroup) -> list[str]:
        """Generate useful labels."""
        labels = [group.category]

        total_changes = sum(f.total_changes for f in group.files)
        file_count = len(group.files)

        if total_changes > 500:
            labels.append("large-change")

        if file_count > 10:
            labels.append("multiple-files")

        if group.category == "config":
            labels.append("dependencies")

        return labels

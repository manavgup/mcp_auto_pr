"""Validates that PR groups are atomic and can stand alone."""
import logging
from pathlib import Path

from mcp_pr_recommender.config import settings
from mcp_pr_recommender.models.pr.recommendations import ChangeGroup


class AtomicityValidator:
    """Validates and ensures PR groups are atomic."""

    def __init__(self) -> None:
        """Initialize atomicity validator with logging."""
        self.logger = logging.getLogger(__name__)

    def validate_and_split(self, groups: list[ChangeGroup]) -> list[ChangeGroup]:
        """Validate groups and split if necessary for atomicity."""
        self.logger.info("Starting atomicity validation")

        validated_groups = []

        for group in groups:
            if self._is_atomic(group):
                validated_groups.append(group)
            else:
                # Split the group
                split_groups = self._split_group(group)
                validated_groups.extend(split_groups)

        self.logger.info(
            f"Atomicity validation: {len(groups)} -> {len(validated_groups)} groups"
        )
        return validated_groups

    def _is_atomic(self, group: ChangeGroup) -> bool:
        """Check if a group represents an atomic change."""
        # Size constraints
        if len(group.files) > settings().max_files_per_pr:
            self.logger.debug(f"Group {group.id} too large: {len(group.files)} files")
            return False

        # Total changes constraint
        total_changes = sum(f.total_changes for f in group.files)
        if total_changes > 1000:  # Configurable threshold
            self.logger.debug(f"Group {group.id} too many changes: {total_changes}")
            return False

        # Mixed concerns check
        if self._has_mixed_concerns(group):
            self.logger.debug(f"Group {group.id} has mixed concerns")
            return False

        # Dependencies check
        if self._has_circular_dependencies(group):
            self.logger.debug(f"Group {group.id} has circular dependencies")
            return False

        return True

    def _has_mixed_concerns(self, group: ChangeGroup) -> bool:
        """Check if group mixes different concerns."""
        file_types = set()
        directories = set()

        for file in group.files:
            path = Path(file.path)

            # Categorize by file extension and path
            if path.suffix in [".py", ".js", ".ts", ".java"]:
                file_types.add("source")
            elif path.suffix in [".md", ".rst", ".txt"]:
                file_types.add("docs")
            elif path.suffix in [".json", ".yaml", ".yml", ".toml"]:
                file_types.add("config")
            elif "test" in str(path).lower():
                file_types.add("test")

            # Track directories
            directories.add(str(path.parent))

        # Check for problematic mixes
        problematic_mixes = [
            {"source", "config"},  # Don't mix source and config changes
            {"docs", "source"},  # Don't mix docs with source (usually)
        ]

        for mix in problematic_mixes:
            if mix.issubset(file_types) and len(file_types) > 1:
                return True

        # Too many different directories
        if len(directories) > 3:
            return True

        return False

    def _has_circular_dependencies(self, group: ChangeGroup) -> bool:
        """Check for circular dependencies (simplified)."""
        # For now, just check for known problematic patterns
        file_paths = [f.path for f in group.files]

        # Database migrations with model changes
        has_migration = any("migration" in path.lower() for path in file_paths)
        has_model = any("model" in path.lower() for path in file_paths)

        if has_migration and has_model:
            # This might need careful ordering
            self.logger.warning(
                "Migration and model changes detected - requires careful review"
            )

        # Schema changes with API changes
        has_schema = any("schema" in path.lower() for path in file_paths)
        has_api = any(
            "api" in path.lower() or "controller" in path.lower() for path in file_paths
        )

        if has_schema and has_api:
            self.logger.warning(
                "Schema and API changes detected - check deployment order"
            )

        return False  # For now, return False but log warnings

    def _split_group(self, group: ChangeGroup) -> list[ChangeGroup]:
        """Split a group that's not atomic."""
        self.logger.info(f"Splitting group {group.id} with {len(group.files)} files")

        # Strategy 1: Split by directory
        if len(group.files) > settings().max_files_per_pr:
            return self._split_by_directory(group)

        # Strategy 2: Split by file type
        if self._has_mixed_concerns(group):
            return self._split_by_concern(group)

        # Strategy 3: Split by size
        return self._split_by_size(group)

    def _split_by_directory(self, group: ChangeGroup) -> list[ChangeGroup]:
        """Split group by directory structure."""
        dir_groups: dict[str, list[object]] = {}

        for file in group.files:
            dir_path = str(Path(file.path).parent)
            if dir_path not in dir_groups:
                dir_groups[dir_path] = []
            dir_groups[dir_path].append(file)

        split_groups = []
        for i, (directory, files) in enumerate(dir_groups.items()):
            split_group = ChangeGroup(
                id=f"{group.id}_split_{i}",
                files=files,
                category=group.category,
                confidence=group.confidence
                * 0.9,  # Slightly lower confidence after split
                reasoning=f"Split from {group.id}: {directory}",
                semantic_similarity=group.semantic_similarity,
            )
            split_groups.append(split_group)

        return split_groups

    def _split_by_concern(self, group: ChangeGroup) -> list[ChangeGroup]:
        """Split group by separating different concerns."""
        concerns: dict[str, list[object]] = {
            "source": [],
            "test": [],
            "config": [],
            "docs": [],
            "other": [],
        }

        for file in group.files:
            path = Path(file.path)

            if "test" in str(path).lower():
                concerns["test"].append(file)
            elif path.suffix in [".md", ".rst", ".txt"]:
                concerns["docs"].append(file)
            elif path.suffix in [".json", ".yaml", ".yml", ".toml"]:
                concerns["config"].append(file)
            elif path.suffix in [".py", ".js", ".ts", ".java"]:
                concerns["source"].append(file)
            else:
                concerns["other"].append(file)

        split_groups = []
        for _i, (concern, files) in enumerate(concerns.items()):
            if not files:
                continue

            split_group = ChangeGroup(
                id=f"{group.id}_{concern}",
                files=files,
                category=concern if concern != "other" else group.category,
                confidence=group.confidence * 0.9,
                reasoning=f"Split by concern: {concern}",
                semantic_similarity=group.semantic_similarity,
            )
            split_groups.append(split_group)

        return split_groups

    def _split_by_size(self, group: ChangeGroup) -> list[ChangeGroup]:
        """Split group by size when it's too large."""
        files = group.files
        max_files = settings().max_files_per_pr

        split_groups = []
        for i in range(0, len(files), max_files):
            chunk_files = files[i : i + max_files]

            split_group = ChangeGroup(
                id=f"{group.id}_chunk_{i // max_files}",
                files=chunk_files,
                category=group.category,
                confidence=group.confidence
                * 0.8,  # Lower confidence for size-based split
                reasoning=f"Size-based split from {group.id}",
                semantic_similarity=group.semantic_similarity,
            )
            split_groups.append(split_group)

        return split_groups

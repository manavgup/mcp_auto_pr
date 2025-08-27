"""Service for analyzing git diffs and generating insights."""

import re
from typing import Any

from fastmcp.server.dependencies import get_context

from mcp_local_repo_analyzer.config import GitAnalyzerSettings
from mcp_local_repo_analyzer.models.categorization import ChangeCategorization
from mcp_local_repo_analyzer.models.files import DiffHunk, FileDiff, FileStatus
from mcp_local_repo_analyzer.models.risk import RiskAssessment
from shared.utils.logging import get_logger

logger = get_logger(__name__)


class DiffAnalyzer:
    """Service for analyzing git diffs and generating insights."""

    def __init__(self, settings: GitAnalyzerSettings):
        """Initialize diff analyzer with settings."""
        self.settings = settings

    def _get_context(self) -> Any:
        """Get FastMCP context if available."""
        try:
            return get_context()
        except RuntimeError:
            # No context available (e.g., during testing)
            return None

    def _log_if_context(self, level: str, message: str) -> None:
        """Log message if context is available."""
        # Try to get context for additional info, but don't await
        try:
            get_context()
            # Add context info to message but use sync logger
            message = f"[FastMCP] {message}"
        except RuntimeError:
            # No context available
            pass

        # Use regular logger (sync, safe)
        getattr(logger, level.lower())(message)

    def parse_diff(self, diff_content: str) -> list[FileDiff]:
        """Parse diff content into FileDiff objects."""
        self._log_if_context("debug", f"Parsing diff content ({len(diff_content)} characters)")

        file_diffs = []

        # Split diff into files
        file_sections = re.split(r"^diff --git", diff_content, flags=re.MULTILINE)

        self._log_if_context("debug", f"Found {len(file_sections)} file sections in diff")

        for i, section in enumerate(file_sections):
            if not section.strip():
                continue

            try:
                file_diff = self._parse_file_diff(section)
                if file_diff:
                    file_diffs.append(file_diff)
            except Exception as e:
                self._log_if_context("warning", f"Failed to parse file diff section {i}: {str(e)}")
                continue

        total_changes = sum(fd.total_changes for fd in file_diffs)
        self._log_if_context(
            "debug",
            f"Parsed {len(file_diffs)} file diffs with {total_changes} total changes",
        )

        return file_diffs

    def _parse_file_diff(self, diff_section: str) -> FileDiff | None:
        """Parse a single file diff section."""
        lines = diff_section.split("\n")

        # Extract file paths
        file_path = None
        old_path = None

        for line in lines:
            if line.startswith("--- a/"):
                old_path = line[6:]
            elif line.startswith("+++ b/"):
                file_path = line[6:]
            elif (line.startswith("a/") or line.startswith(" a/")) and " b/" in line:
                # Handle the git diff header line (may have leading space after split)
                line = line.lstrip()  # Remove leading whitespace
                parts = line.split(" b/")
                if len(parts) == 2:
                    old_path = parts[0][2:]  # Remove 'a/'
                    file_path = parts[1]

        if not file_path:
            self._log_if_context("warning", "Could not extract file path from diff section")
            return None

        # Check if binary
        is_binary = "Binary files" in diff_section

        # Count additions/deletions
        additions = 0
        deletions = 0
        hunks = []

        if not is_binary:
            for line in lines:
                if line.startswith("+") and not line.startswith("+++"):
                    additions += 1
                elif line.startswith("-") and not line.startswith("---"):
                    deletions += 1

            # Parse hunks (simplified)
            hunks = self._parse_hunks(lines)

        return FileDiff(
            file_path=file_path,
            old_path=old_path if old_path != file_path else None,
            diff_content=diff_section,
            hunks=hunks,
            is_binary=is_binary,
            lines_added=additions,
            lines_deleted=deletions,
            file_mode_old=None,
            file_mode_new=None,
        )

    def _parse_hunks(self, lines: list[str]) -> list[DiffHunk]:
        """Parse diff hunks from lines."""
        hunks = []
        current_hunk = None
        hunk_content: list[str] = []

        for line in lines:
            if line.startswith("@@"):
                # Save previous hunk
                if current_hunk:
                    current_hunk.content = "\n".join(hunk_content)
                    hunks.append(current_hunk)
                # Reset for new hunk
                hunk_content.clear()

                # Parse hunk header
                hunk_match = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
                if hunk_match:
                    old_start = int(hunk_match.group(1))
                    old_lines = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                    new_start = int(hunk_match.group(3))
                    new_lines = int(hunk_match.group(4)) if hunk_match.group(4) else 1

                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_lines=old_lines,
                        new_start=new_start,
                        new_lines=new_lines,
                        content="",
                    )
                    hunk_content = []
            elif current_hunk and (line.startswith(" ") or line.startswith("+") or line.startswith("-")):
                hunk_content.append(line)

        # Save last hunk
        if current_hunk:
            current_hunk.content = "\n".join(hunk_content)
            hunks.append(current_hunk)

        return hunks

    def categorize_changes(self, files: list[FileStatus]) -> ChangeCategorization:
        """Categorize changed files by type."""
        self._log_if_context("debug", f"Categorizing {len(files)} changed files")

        critical_files = []
        source_code = []
        documentation = []
        tests = []
        configuration = []
        other = []

        for file_status in files:
            path = file_status.path.lower()

            # Check categories in order of specificity
            if self._is_critical_file(file_status.path):
                critical_files.append(file_status.path)
            elif self._is_test_file(path):
                tests.append(file_status.path)
            elif self._is_source_code(path):
                source_code.append(file_status.path)
            elif self._is_documentation(path):
                documentation.append(file_status.path)
            elif self._is_configuration(path):
                configuration.append(file_status.path)
            else:
                other.append(file_status.path)

        categories = ChangeCategorization(
            critical_files=critical_files,
            source_code=source_code,
            documentation=documentation,
            tests=tests,
            configuration=configuration,
            other=other,
        )

        self._log_if_context(
            "debug",
            f"File categorization: {len(critical_files)} critical, {len(source_code)} source, "
            f"{len(documentation)} docs, {len(tests)} tests, {len(configuration)} config, {len(other)} other",
        )

        if critical_files:
            self._log_if_context("warning", f"Critical files changed: {', '.join(critical_files[:3])}")

        return categories

    def assess_risk(self, changes: list[FileStatus]) -> RiskAssessment:
        """Assess risk level of changes."""
        self._log_if_context("debug", f"Assessing risk for {len(changes)} file changes")

        risk_factors = []
        large_changes = []
        potential_conflicts = []
        binary_changes = []

        total_changes = len(changes)
        critical_file_changes = 0
        total_line_changes = 0

        for file_status in changes:
            # Check for large changes
            if file_status.total_changes > self.settings.large_file_threshold:
                large_changes.append(file_status.path)

            # Track total line changes
            total_line_changes += file_status.total_changes

            # Check for critical files
            if self._is_critical_file(file_status.path):
                critical_file_changes += 1

            # Check for binary files
            if file_status.is_binary:
                binary_changes.append(file_status.path)

            # Check for potential conflicts (simplified heuristics)
            if self._might_cause_conflicts(file_status):
                potential_conflicts.append(file_status.path)

        # Determine risk level and factors
        from typing import Literal

        risk_level: Literal["low", "medium", "high"] = "low"

        # Critical file changes
        if critical_file_changes > 0:
            risk_factors.append(f"{critical_file_changes} critical file(s) changed")
            risk_level = "medium"

        # Large changes
        if len(large_changes) > 0:
            risk_factors.append(f"{len(large_changes)} large change(s)")
            if len(large_changes) > 3:
                risk_level = "high"

        # Too many files changed
        if total_changes > 20:
            risk_factors.append(f"{total_changes} files changed")
            risk_level = "high"

        # Massive line changes
        if total_line_changes > 1000:
            risk_factors.append(f"{total_line_changes} total line changes")
            if risk_level == "low":
                risk_level = "medium"

        # Binary file changes
        if len(binary_changes) > 0:
            risk_factors.append(f"{len(binary_changes)} binary file(s) changed")

        # Potential conflicts
        if len(potential_conflicts) > 0:
            risk_factors.append(f"{len(potential_conflicts)} potential conflict(s)")
            risk_level = "high"

        risk_assessment = RiskAssessment(
            risk_level=risk_level,
            risk_factors=risk_factors,
            large_changes=large_changes,
            potential_conflicts=potential_conflicts,
            binary_changes=binary_changes,
        )

        self._log_if_context(
            "info",
            f"Risk assessment: {risk_level} risk ({risk_assessment.risk_score}/10)",
        )
        if risk_level == "high":
            self._log_if_context("warning", f"High-risk factors: {', '.join(risk_factors)}")
        elif len(risk_factors) > 0:
            self._log_if_context("debug", f"Risk factors: {', '.join(risk_factors)}")

        return risk_assessment

    def _is_critical_file(self, file_path: str) -> bool:
        """Check if file is considered critical."""
        for pattern in self.settings.critical_file_patterns:
            if self._matches_pattern(file_path, pattern):
                return True

        # Additional critical file patterns
        critical_names = [
            "dockerfile",
            "makefile",
            "cmakelists.txt",
            "build.gradle",
            "pom.xml",
            "composer.json",
            "package-lock.json",
            "yarn.lock",
            ".gitignore",
            ".gitattributes",
            "license",
            "readme.md",
        ]

        filename_lower = file_path.lower().split("/")[-1]  # Get just the filename
        return filename_lower in critical_names

    def _is_source_code(self, file_path: str) -> bool:
        """Check if file is source code."""
        code_extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".rs",
            ".go",
            ".rb",
            ".php",
            ".swift",
            ".kt",
            ".scala",
            ".clj",
            ".hs",
            ".ml",
            ".fs",
            ".vb",
            ".dart",
            ".lua",
            ".r",
            ".m",
            ".mm",
        ]
        return any(file_path.endswith(ext) for ext in code_extensions)

    def _is_documentation(self, file_path: str) -> bool:
        """Check if file is documentation."""
        doc_patterns = ["readme", "doc", "docs/", "/doc/", "documentation"]
        doc_extensions = [".md", ".rst", ".txt", ".adoc", ".tex"]

        path_lower = file_path.lower()

        return any(pattern in path_lower for pattern in doc_patterns) or any(
            path_lower.endswith(ext) for ext in doc_extensions
        )

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        test_patterns = [
            "test_",
            "_test.",
            "spec_",
            "_spec.",
            "/tests/",
            "/test/",
            "__tests__/",
            ".test.",
            ".spec.",
            "testing/",
            "spec/",
        ]
        return any(pattern in file_path.lower() for pattern in test_patterns)

    def _is_configuration(self, file_path: str) -> bool:
        """Check if file is configuration."""
        config_extensions = [
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".properties",
            ".xml",
            ".env",
        ]
        config_patterns = ["config", "settings", ".env"]

        path_lower = file_path.lower()

        return any(path_lower.endswith(ext) for ext in config_extensions) or any(
            pattern in path_lower for pattern in config_patterns
        )

    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches pattern (simplified glob)."""
        if "*" in pattern:
            # Simple wildcard matching
            pattern_regex = pattern.replace("*", ".*").replace("?", ".")
            return bool(re.match(pattern_regex, file_path, re.IGNORECASE))

        return pattern.lower() in file_path.lower()

    def _might_cause_conflicts(self, file_status: FileStatus) -> bool:
        """Check if file might cause merge conflicts (simplified)."""
        # Heuristics for potential conflicts
        conflict_indicators = [
            # Large changes are more likely to conflict
            file_status.total_changes > 50,
            # Renamed or copied files can cause conflicts
            file_status.status_code in ["R", "C"],
            # Certain file types are more prone to conflicts
            any(
                file_status.path.endswith(ext)
                for ext in [
                    ".json",
                    ".xml",
                    ".yaml",
                    ".yml",
                    ".lock",
                    "package-lock.json",
                    "yarn.lock",
                    "poetry.lock",
                ]
            ),
            # Files in common conflict-prone directories
            any(pattern in file_status.path.lower() for pattern in ["migration", "schema", "database", "config"]),
        ]

        return any(conflict_indicators)

    def generate_insights(self, changes: list[FileStatus]) -> dict[str, Any]:
        """Generate comprehensive insights about the changes."""
        self._log_if_context("debug", "Generating comprehensive change insights")

        categories = self.categorize_changes(changes)
        risk_assessment = self.assess_risk(changes)

        # Calculate statistics
        total_additions = sum(f.lines_added for f in changes)
        total_deletions = sum(f.lines_deleted for f in changes)
        total_changes = sum(f.total_changes for f in changes)

        # Analyze change patterns
        file_types: dict[str, int] = {}

        for file_status in changes:
            # Count file types
            if "." in file_status.path:
                ext = file_status.path.split(".")[-1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1

        # Most changed files
        most_changed = sorted(changes, key=lambda f: f.total_changes, reverse=True)[:5]

        insights = {
            "categories": categories,
            "risk_assessment": risk_assessment,
            "statistics": {
                "total_files": len(changes),
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "total_changes": total_changes,
                "average_changes_per_file": (total_changes / len(changes) if changes else 0),
            },
            "file_types": file_types,
            "most_changed_files": [
                {
                    "path": f.path,
                    "changes": f.total_changes,
                    "status": f.status_description,
                }
                for f in most_changed
            ],
            "patterns": {
                "has_critical_changes": categories.has_critical_changes,
                "has_large_changes": len(risk_assessment.large_changes) > 0,
                "has_binary_changes": len(risk_assessment.binary_changes) > 0,
                "change_spread": "focused" if len(file_types) <= 2 else "diverse",
            },
        }

        self._log_if_context(
            "info",
            (
                f"Generated insights: {len(changes)} files, "
                f"{risk_assessment.risk_level} risk, "
                f"{len(file_types)} file types"
            ),
        )

        return insights

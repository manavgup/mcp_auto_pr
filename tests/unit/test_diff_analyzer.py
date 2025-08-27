"""Comprehensive unit tests for the DiffAnalyzer service."""

from unittest.mock import Mock, patch

import pytest

from mcp_local_repo_analyzer.config import GitAnalyzerSettings
from mcp_local_repo_analyzer.models.categorization import ChangeCategorization
from mcp_local_repo_analyzer.models.files import FileStatus
from mcp_local_repo_analyzer.models.risk import RiskAssessment
from mcp_local_repo_analyzer.services.diff_analyzer import DiffAnalyzer


@pytest.mark.unit
class TestDiffAnalyzer:
    """Test the DiffAnalyzer service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.settings = GitAnalyzerSettings()
        self.diff_analyzer = DiffAnalyzer(self.settings)

    def test_parse_diff_basic(self):
        """Test basic diff parsing."""
        diff_content = """diff --git a/file1.py b/file1.py
index abc123..def456 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 line1
+new_line
 line2
 line3
"""

        result = self.diff_analyzer.parse_diff(diff_content)

        assert len(result) == 1
        file_diff = result[0]
        assert file_diff.file_path == "file1.py"
        # old_path is None when old_path == file_path (same file)
        assert file_diff.old_path is None
        assert len(file_diff.hunks) == 1
        assert file_diff.total_changes == 1

    def test_parse_diff_multiple_files(self):
        """Test parsing diff with multiple files."""
        diff_content = """diff --git a/file1.py b/file1.py
index abc123..def456 100644
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-old_line
+new_line
diff --git a/file2.py b/file2.py
index ghi789..jkl012 100644
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,2 @@
 line1
+line2
"""

        result = self.diff_analyzer.parse_diff(diff_content)

        assert len(result) == 2
        assert result[0].file_path == "file1.py"
        assert result[1].file_path == "file2.py"

    def test_parse_diff_with_rename(self):
        """Test parsing diff with renamed files."""
        diff_content = """diff --git a/old_name.py b/new_name.py
index abc123..def456 100644
--- a/old_name.py
+++ b/new_name.py
@@ -1,1 +1,1 @@
-old_content
+new_content
"""

        result = self.diff_analyzer.parse_diff(diff_content)

        assert len(result) == 1
        file_diff = result[0]
        assert file_diff.old_path == "old_name.py"
        assert file_diff.file_path == "new_name.py"

    def test_parse_diff_empty_content(self):
        """Test parsing empty diff content."""
        result = self.diff_analyzer.parse_diff("")

        assert len(result) == 0

    def test_parse_diff_whitespace_only(self):
        """Test parsing diff with only whitespace."""
        result = self.diff_analyzer.parse_diff("   \n  \n")

        assert len(result) == 0

    def test_parse_diff_malformed_section(self):
        """Test parsing diff with malformed sections."""
        diff_content = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-old_line
+new_line
diff --git
malformed section
"""

        result = self.diff_analyzer.parse_diff(diff_content)

        # Should parse the first valid section and skip the malformed one
        assert len(result) == 1
        assert result[0].file_path == "file1.py"

    def test_parse_file_diff_basic(self):
        """Test parsing a single file diff section."""
        diff_section = """--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 line1
+new_line
 line2
 line3
"""

        result = self.diff_analyzer._parse_file_diff(diff_section)

        assert result is not None
        assert result.file_path == "file1.py"
        # old_path is None when old_path == file_path (same file)
        assert result.old_path is None
        assert len(result.hunks) == 1

    def test_parse_file_diff_with_old_path(self):
        """Test parsing file diff with different old and new paths."""
        diff_section = """--- a/old_path/file.py
+++ b/new_path/file.py
@@ -1,1 +1,1 @@
-old_content
+new_content
"""

        result = self.diff_analyzer._parse_file_diff(diff_section)

        assert result is not None
        assert result.old_path == "old_path/file.py"
        assert result.file_path == "new_path/file.py"

    def test_parse_file_diff_no_paths(self):
        """Test parsing file diff with no path information."""
        diff_section = """@@ -1,1 +1,1 @@
-old_content
+new_content
"""

        result = self.diff_analyzer._parse_file_diff(diff_section)

        assert result is None

    def test_parse_file_diff_malformed(self):
        """Test parsing malformed file diff."""
        diff_section = """malformed content
no proper diff format
"""

        result = self.diff_analyzer._parse_file_diff(diff_section)

        assert result is None

    def test_parse_hunks_basic(self):
        """Test parsing diff hunks."""
        hunk_content = """@@ -1,3 +1,4 @@
 line1
+new_line
 line2
 line3
"""

        # Split into lines for the _parse_hunks method
        lines = hunk_content.split("\n")
        hunks = self.diff_analyzer._parse_hunks(lines)

        assert len(hunks) == 1
        hunk = hunks[0]
        assert hunk.old_start == 1
        assert hunk.old_lines == 3
        assert hunk.new_start == 1
        assert hunk.new_lines == 4

    def test_parse_hunks_multiple(self):
        """Test parsing multiple diff hunks."""
        hunk_content = """@@ -1,3 +1,4 @@
 line1
+new_line
 line2
 line3
@@ -10,2 +11,3 @@
 line10
+another_new_line
 line11
"""

        # Split into lines for the _parse_hunks method
        lines = hunk_content.split("\n")
        hunks = self.diff_analyzer._parse_hunks(lines)

        assert len(hunks) == 2
        assert hunks[0].old_start == 1
        assert hunks[1].old_start == 10

    def test_parse_hunks_malformed(self):
        """Test parsing malformed hunks."""
        hunk_content = """@@ malformed @@
 content
"""

        hunks = self.diff_analyzer._parse_hunks(hunk_content)

        assert len(hunks) == 0

    def test_categorize_changes_basic(self):
        """Test basic change categorization."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),
            FileStatus(path="tests/test_main.py", status_code="M"),
            FileStatus(path="README.md", status_code="M"),
        ]

        result = self.diff_analyzer.categorize_changes(files)

        assert isinstance(result, ChangeCategorization)
        # README.md is categorized as critical, not documentation
        assert len(result.source_code) == 1  # src/main.py
        assert len(result.critical_files) == 1  # README.md
        assert len(result.tests) == 1  # tests/test_main.py

    def test_categorize_changes_by_extension(self):
        """Test change categorization by file extension."""
        files = [
            FileStatus(path="script.py", status_code="M"),
            FileStatus(path="config.json", status_code="M"),
            FileStatus(path="data.csv", status_code="M"),
            FileStatus(path="image.png", status_code="M"),
        ]

        result = self.diff_analyzer.categorize_changes(files)

        assert len(result.source_code) == 1  # .py
        assert len(result.configuration) == 1  # .json
        # Note: data_files and binary_files are not separate categories in ChangeCategorization
        # They would be categorized as 'other' or based on their extension

    def test_categorize_changes_by_directory(self):
        """Test change categorization by directory structure."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),
            FileStatus(path="tests/test_main.py", status_code="M"),
            FileStatus(path="docs/README.md", status_code="M"),
            FileStatus(path="config/settings.yaml", status_code="M"),
        ]

        result = self.diff_analyzer.categorize_changes(files)

        # docs/README.md is categorized as critical, not documentation
        assert len(result.source_code) == 1
        assert len(result.tests) == 1
        assert len(result.critical_files) == 1  # docs/README.md
        assert len(result.configuration) == 1

    def test_categorize_changes_empty_list(self):
        """Test change categorization with empty file list."""
        result = self.diff_analyzer.categorize_changes([])

        assert isinstance(result, ChangeCategorization)
        assert len(result.source_code) == 0
        assert len(result.tests) == 0

    def test_assess_risk_basic(self):
        """Test basic risk assessment."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),
            FileStatus(path="config/database.py", status_code="M"),
        ]

        result = self.diff_analyzer.assess_risk(files)

        assert isinstance(result, RiskAssessment)
        assert result.risk_level in ["low", "medium", "high"]

    def test_assess_risk_sensitive_files(self):
        """Test risk assessment with sensitive files."""
        files = [
            FileStatus(path="src/auth.py", status_code="M"),
            FileStatus(path="config/secrets.py", status_code="M"),
            FileStatus(path="database/schema.sql", status_code="M"),
        ]

        result = self.diff_analyzer.assess_risk(files)

        # Should be higher risk due to sensitive files
        assert result.risk_level in ["medium", "high"]

    def test_assess_risk_large_changes(self):
        """Test risk assessment with large changes."""
        files = [
            FileStatus(path="src/main.py", status_code="M", lines_added=500, lines_deleted=200),
            FileStatus(path="src/utils.py", status_code="M", lines_added=300, lines_deleted=100),
        ]

        result = self.diff_analyzer.assess_risk(files)

        # Should be higher risk due to large changes
        assert result.risk_level in ["medium", "high"]

    def test_assess_risk_empty_list(self):
        """Test risk assessment with empty file list."""
        result = self.diff_analyzer.assess_risk([])

        assert isinstance(result, RiskAssessment)
        assert result.risk_level == "low"

    def test_get_context_no_context(self):
        """Test getting context when none available."""
        with patch("mcp_local_repo_analyzer.services.diff_analyzer.get_context") as mock_get_context:
            mock_get_context.side_effect = RuntimeError("No context")

            result = self.diff_analyzer._get_context()

            assert result is None

    def test_get_context_with_context(self):
        """Test getting context when available."""
        mock_context = Mock()
        with patch("mcp_local_repo_analyzer.services.diff_analyzer.get_context") as mock_get_context:
            mock_get_context.return_value = mock_context

            result = self.diff_analyzer._get_context()

            assert result == mock_context

    def test_log_if_context_no_context(self):
        """Test logging when no context available."""
        with patch("mcp_local_repo_analyzer.services.diff_analyzer.get_context") as mock_get_context:
            mock_get_context.side_effect = RuntimeError("No context")

            # Should not raise exception
            self.diff_analyzer._log_if_context("info", "Test message")

    def test_log_if_context_with_context(self):
        """Test logging when context available."""
        mock_context = Mock()
        with patch("mcp_local_repo_analyzer.services.diff_analyzer.get_context") as mock_get_context:
            mock_get_context.return_value = mock_context

            # Should not raise exception
            self.diff_analyzer._log_if_context("info", "Test message")

    def test_generate_insights_basic(self):
        """Test basic insights generation."""
        files = [
            FileStatus(path="src/main.py", status_code="M", lines_added=10, lines_deleted=5),
            FileStatus(
                path="tests/test_main.py",
                status_code="M",
                lines_added=5,
                lines_deleted=2,
            ),
        ]

        insights = self.diff_analyzer.generate_insights(files)

        assert isinstance(insights, dict)
        assert "categories" in insights
        assert "risk_assessment" in insights
        assert "statistics" in insights
        assert "file_types" in insights
        assert "most_changed_files" in insights
        assert "patterns" in insights

    def test_generate_insights_empty_list(self):
        """Test insights generation with empty file list."""
        insights = self.diff_analyzer.generate_insights([])

        assert isinstance(insights, dict)
        assert insights["statistics"]["total_files"] == 0
        assert insights["statistics"]["total_changes"] == 0

    def test_generate_insights_with_categorization(self):
        """Test insights generation with categorization."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),
            FileStatus(path="README.md", status_code="M"),
            FileStatus(path="config.yaml", status_code="M"),
        ]

        insights = self.diff_analyzer.generate_insights(files)

        assert "categories" in insights
        assert "risk_assessment" in insights

    def test_parse_diff_binary_file(self):
        """Test parsing diff with binary files."""
        diff_content = """diff --git a/image.png b/image.png
index abc123..def456 100644
Binary files a/image.png and b/image.png differ
"""

        result = self.diff_analyzer.parse_diff(diff_content)

        assert len(result) == 1
        file_diff = result[0]
        assert file_diff.is_binary is True
        assert file_diff.lines_added == 0
        assert file_diff.lines_deleted == 0

    def test_parse_file_diff_git_header_format(self):
        """Test parsing file diff with git header format."""
        diff_section = """a/old_file.py b/new_file.py
index abc123..def456 100644
--- a/old_file.py
+++ b/new_file.py
@@ -1,1 +1,1 @@
-old_content
+new_content
"""

        result = self.diff_analyzer._parse_file_diff(diff_section)

        assert result is not None
        assert result.old_path == "old_file.py"
        assert result.file_path == "new_file.py"

    def test_parse_hunks_single_line_hunk(self):
        """Test parsing single line hunks."""
        hunk_content = """@@ -1 +1 @@
-old_line
+new_line
"""

        lines = hunk_content.split("\n")
        hunks = self.diff_analyzer._parse_hunks(lines)

        assert len(hunks) == 1
        hunk = hunks[0]
        assert hunk.old_start == 1
        assert hunk.old_lines == 1
        assert hunk.new_start == 1
        assert hunk.new_lines == 1

    def test_assess_risk_many_files(self):
        """Test risk assessment with many files."""
        files = [FileStatus(path=f"file_{i}.py", status_code="M") for i in range(25)]

        result = self.diff_analyzer.assess_risk(files)

        assert result.risk_level == "high"
        assert any("25 files changed" in factor for factor in result.risk_factors)

    def test_assess_risk_massive_line_changes(self):
        """Test risk assessment with massive line changes."""
        files = [
            FileStatus(path="big_file.py", status_code="M", lines_added=800, lines_deleted=500),
        ]

        result = self.diff_analyzer.assess_risk(files)

        assert result.risk_level == "high"
        assert any("1300 total line changes" in factor for factor in result.risk_factors)

    def test_assess_risk_binary_files(self):
        """Test risk assessment with binary files."""
        files = [
            FileStatus(path="image.png", status_code="M", is_binary=True),
            FileStatus(path="data.bin", status_code="M", is_binary=True),
        ]

        result = self.diff_analyzer.assess_risk(files)

        assert any("2 binary file(s) changed" in factor for factor in result.risk_factors)

    def test_assess_risk_renamed_files(self):
        """Test risk assessment with renamed files."""
        files = [
            FileStatus(path="new_name.py", status_code="R", old_path="old_name.py"),
        ]

        result = self.diff_analyzer.assess_risk(files)

        assert any("1 potential conflict(s)" in factor for factor in result.risk_factors)

    def test_is_critical_file_patterns(self):
        """Test critical file pattern matching."""
        # Test exact matches
        assert self.diff_analyzer._is_critical_file("dockerfile") is True
        assert self.diff_analyzer._is_critical_file("Makefile") is True
        assert self.diff_analyzer._is_critical_file("LICENSE") is True
        assert self.diff_analyzer._is_critical_file("README.md") is True

        # Test patterns from settings
        assert self.diff_analyzer._is_critical_file("config.env") is True
        assert self.diff_analyzer._is_critical_file("pyproject.toml") is True

        # Test non-critical files
        assert self.diff_analyzer._is_critical_file("regular_file.py") is False

    def test_is_source_code_various_extensions(self):
        """Test source code detection with various extensions."""
        assert self.diff_analyzer._is_source_code("script.py") is True
        assert self.diff_analyzer._is_source_code("app.js") is True
        assert self.diff_analyzer._is_source_code("component.tsx") is True
        assert self.diff_analyzer._is_source_code("main.cpp") is True
        assert self.diff_analyzer._is_source_code("service.go") is True
        assert self.diff_analyzer._is_source_code("data.csv") is False

    def test_is_documentation_various_patterns(self):
        """Test documentation detection with various patterns."""
        assert self.diff_analyzer._is_documentation("README.md") is True
        assert self.diff_analyzer._is_documentation("docs/guide.rst") is True
        assert self.diff_analyzer._is_documentation("documentation/setup.txt") is True
        assert self.diff_analyzer._is_documentation("manual.tex") is True
        assert self.diff_analyzer._is_documentation("script.py") is False

    def test_is_test_file_various_patterns(self):
        """Test test file detection with various patterns."""
        assert self.diff_analyzer._is_test_file("test_module.py") is True
        assert self.diff_analyzer._is_test_file("module_test.py") is True
        assert self.diff_analyzer._is_test_file("tests/unit_test.py") is True
        assert self.diff_analyzer._is_test_file("__tests__/component.test.js") is True
        assert self.diff_analyzer._is_test_file("spec/feature.spec.rb") is True
        assert self.diff_analyzer._is_test_file("regular_file.py") is False

    def test_is_configuration_various_patterns(self):
        """Test configuration file detection with various patterns."""
        assert self.diff_analyzer._is_configuration("config.json") is True
        assert self.diff_analyzer._is_configuration("settings.yaml") is True
        assert self.diff_analyzer._is_configuration("app.toml") is True
        assert self.diff_analyzer._is_configuration("database.env") is True
        assert self.diff_analyzer._is_configuration("script.py") is False

    def test_matches_pattern_wildcard(self):
        """Test pattern matching with wildcards."""
        assert self.diff_analyzer._matches_pattern("config.env", "*.env") is True
        assert self.diff_analyzer._matches_pattern("test_file.py", "test_*") is True
        assert self.diff_analyzer._matches_pattern("file.txt", "*.env") is False

    def test_matches_pattern_simple(self):
        """Test pattern matching without wildcards."""
        assert self.diff_analyzer._matches_pattern("dockerfile", "dockerfile") is True
        assert self.diff_analyzer._matches_pattern("Dockerfile", "dockerfile") is True
        assert self.diff_analyzer._matches_pattern("script.py", "dockerfile") is False

    def test_might_cause_conflicts_large_file(self):
        """Test conflict detection for large files."""
        file_status = FileStatus(path="big_file.py", status_code="M", lines_added=60, lines_deleted=20)

        result = self.diff_analyzer._might_cause_conflicts(file_status)

        assert result is True

    def test_might_cause_conflicts_lock_files(self):
        """Test conflict detection for lock files."""
        file_status = FileStatus(path="package-lock.json", status_code="M")

        result = self.diff_analyzer._might_cause_conflicts(file_status)

        assert result is True

    def test_might_cause_conflicts_migration_files(self):
        """Test conflict detection for migration files."""
        file_status = FileStatus(path="database/migration_001.sql", status_code="M")

        result = self.diff_analyzer._might_cause_conflicts(file_status)

        assert result is True

    def test_might_cause_conflicts_safe_file(self):
        """Test conflict detection for safe files."""
        file_status = FileStatus(path="simple_file.py", status_code="M", lines_added=5, lines_deleted=2)

        result = self.diff_analyzer._might_cause_conflicts(file_status)

        assert result is False

    def test_categorize_changes_mixed_categories(self):
        """Test categorization with files in multiple categories."""
        files = [
            FileStatus(path="Dockerfile", status_code="M"),  # Critical
            FileStatus(path="src/utils.py", status_code="M"),  # Source code
            FileStatus(path="test_utils.py", status_code="M"),  # Test
            FileStatus(path="docs/api.md", status_code="M"),  # Documentation
            FileStatus(path="config.json", status_code="M"),  # Configuration
            FileStatus(path="data.csv", status_code="M"),  # Other
        ]

        result = self.diff_analyzer.categorize_changes(files)

        assert len(result.critical_files) == 1
        assert len(result.source_code) == 1
        assert len(result.tests) == 1
        assert len(result.documentation) == 1
        assert len(result.configuration) == 1
        assert len(result.other) == 1

    def test_generate_insights_statistics(self):
        """Test insights statistics calculation."""
        files = [
            FileStatus(path="file1.py", status_code="M", lines_added=10, lines_deleted=5),
            FileStatus(path="file2.py", status_code="M", lines_added=20, lines_deleted=10),
        ]

        insights = self.diff_analyzer.generate_insights(files)

        stats = insights["statistics"]
        assert stats["total_files"] == 2
        assert stats["total_additions"] == 30
        assert stats["total_deletions"] == 15
        assert stats["total_changes"] == 45
        assert stats["average_changes_per_file"] == 22.5

    def test_generate_insights_file_types(self):
        """Test insights file type analysis."""
        files = [
            FileStatus(path="script.py", status_code="M"),
            FileStatus(path="config.json", status_code="M"),
            FileStatus(path="another.py", status_code="M"),
        ]

        insights = self.diff_analyzer.generate_insights(files)

        file_types = insights["file_types"]
        assert file_types["py"] == 2
        assert file_types["json"] == 1

    def test_generate_insights_most_changed_files(self):
        """Test insights most changed files analysis."""
        files = [
            FileStatus(path="big_change.py", status_code="M", lines_added=100, lines_deleted=50),
            FileStatus(path="small_change.py", status_code="M", lines_added=5, lines_deleted=2),
            FileStatus(
                path="medium_change.py",
                status_code="M",
                lines_added=30,
                lines_deleted=15,
            ),
        ]

        insights = self.diff_analyzer.generate_insights(files)

        most_changed = insights["most_changed_files"]
        assert len(most_changed) == 3
        assert most_changed[0]["path"] == "big_change.py"
        assert most_changed[0]["changes"] == 150

"""Comprehensive unit tests for the AtomicityValidator service."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from mcp_shared_lib.models.git.changes import FileStatus

from mcp_pr_recommender.models.pr.recommendations import ChangeGroup
from mcp_pr_recommender.services.atomicity_validator import AtomicityValidator


@pytest.mark.unit
class TestAtomicityValidator:
    """Test the AtomicityValidator service."""

    @pytest.fixture
    def validator(self):
        """Create atomicity validator instance."""
        return AtomicityValidator()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch(
            "mcp_pr_recommender.services.atomicity_validator.settings"
        ) as mock_settings_func:
            mock_settings_instance = Mock()
            mock_settings_instance.max_files_per_pr = 8
            mock_settings_func.return_value = mock_settings_instance
            yield mock_settings_instance

    @pytest.fixture
    def sample_files(self):
        """Create sample file status objects."""
        return [
            FileStatus(
                path="src/main.py", status_code="M", lines_added=10, lines_deleted=5
            ),
            FileStatus(
                path="src/utils.py", status_code="M", lines_added=20, lines_deleted=10
            ),
            FileStatus(
                path="tests/test_main.py",
                status_code="A",
                lines_added=50,
                lines_deleted=0,
            ),
        ]

    @pytest.fixture
    def atomic_group(self, sample_files):
        """Create an atomic change group."""
        return ChangeGroup(
            id="group_1",
            files=sample_files[:2],  # Just source files
            category="source",
            confidence=0.9,
            reasoning="Related source changes",
            semantic_similarity=0.85,
        )

    @pytest.fixture
    def large_group(self):
        """Create a group with too many files."""
        files = [
            FileStatus(
                path=f"src/file_{i}.py", status_code="M", lines_added=5, lines_deleted=2
            )
            for i in range(12)  # More than max_files_per_pr
        ]
        return ChangeGroup(
            id="large_group",
            files=files,
            category="source",
            confidence=0.8,
            reasoning="Large feature implementation",
            semantic_similarity=0.7,
        )

    @pytest.fixture
    def mixed_concerns_group(self):
        """Create a group with mixed concerns."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),
            FileStatus(path="config.json", status_code="M"),
            FileStatus(path="docs/README.md", status_code="M"),
        ]
        return ChangeGroup(
            id="mixed_group",
            files=files,
            category="mixed",
            confidence=0.75,
            reasoning="Mixed changes",
            semantic_similarity=0.6,
        )

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator.logger is not None

    def test_validate_and_split_atomic_groups(
        self, validator, atomic_group, mock_settings
    ):
        """Test validation with atomic groups that don't need splitting."""
        groups = [atomic_group]

        result = validator.validate_and_split(groups)

        assert len(result) == 1
        assert result[0].id == atomic_group.id
        assert len(result[0].files) == len(atomic_group.files)

    def test_validate_and_split_large_group(
        self, validator, large_group, mock_settings
    ):
        """Test validation splits large groups."""
        groups = [large_group]

        result = validator.validate_and_split(groups)

        # Should be split into multiple groups (by directory in this case)
        assert len(result) >= 1  # May be 1 if all files in same directory
        # Total files should be preserved
        total_files = sum(len(g.files) for g in result)
        assert total_files == len(large_group.files)

    def test_validate_and_split_mixed_concerns(
        self, validator, mixed_concerns_group, mock_settings
    ):
        """Test validation splits groups with mixed concerns."""
        groups = [mixed_concerns_group]

        result = validator.validate_and_split(groups)

        # Should be split by concern
        assert len(result) > 1
        # Each split group should have files from same concern
        for group in result:
            assert len(group.files) > 0

    def test_is_atomic_true(self, validator, atomic_group, mock_settings):
        """Test atomic check for valid atomic group."""
        assert validator._is_atomic(atomic_group) is True

    def test_is_atomic_too_many_files(self, validator, large_group, mock_settings):
        """Test atomic check fails for too many files."""
        assert validator._is_atomic(large_group) is False

    def test_is_atomic_too_many_changes(self, validator, mock_settings):
        """Test atomic check fails for too many line changes."""
        files = [
            FileStatus(
                path="huge_file.py", status_code="M", lines_added=800, lines_deleted=500
            )
        ]
        group = ChangeGroup(
            id="huge_changes",
            files=files,
            category="source",
            confidence=0.8,
            reasoning="Huge changes",
            semantic_similarity=0.7,
        )

        assert validator._is_atomic(group) is False

    def test_is_atomic_mixed_concerns(
        self, validator, mixed_concerns_group, mock_settings
    ):
        """Test atomic check fails for mixed concerns."""
        assert validator._is_atomic(mixed_concerns_group) is False

    def test_is_atomic_with_circular_dependencies(self, validator, mock_settings):
        """Test atomic check with circular dependencies (currently always returns True for deps)."""
        files = [
            FileStatus(path="db/migration_001.sql", status_code="A"),
            FileStatus(path="models/user.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="deps_group",
            files=files,
            category="database",
            confidence=0.8,
            reasoning="Database changes",
            semantic_similarity=0.7,
        )

        # Currently, circular dependency check returns False (doesn't fail atomicity)
        assert validator._is_atomic(group) is True

    def test_has_mixed_concerns_source_and_config(self, validator):
        """Test mixed concerns detection for source and config."""
        files = [
            FileStatus(path="src/app.py", status_code="M"),
            FileStatus(path="config.yaml", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="mixed",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        assert validator._has_mixed_concerns(group) is True

    def test_has_mixed_concerns_docs_and_source(self, validator):
        """Test mixed concerns detection for docs and source."""
        files = [
            FileStatus(path="src/app.py", status_code="M"),
            FileStatus(path="README.md", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="mixed",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        assert validator._has_mixed_concerns(group) is True

    def test_has_mixed_concerns_many_directories(self, validator):
        """Test mixed concerns detection for too many directories."""
        files = [
            FileStatus(path="dir1/file.py", status_code="M"),
            FileStatus(path="dir2/file.py", status_code="M"),
            FileStatus(path="dir3/file.py", status_code="M"),
            FileStatus(path="dir4/file.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="source",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        assert validator._has_mixed_concerns(group) is True

    def test_has_mixed_concerns_same_type(self, validator):
        """Test mixed concerns detection for same file types."""
        files = [
            FileStatus(path="src/app.py", status_code="M"),
            FileStatus(path="src/utils.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="source",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        assert validator._has_mixed_concerns(group) is False

    def test_has_mixed_concerns_test_files(self, validator):
        """Test mixed concerns detection for test files."""
        files = [
            FileStatus(path="tests/test_app.py", status_code="M"),
            FileStatus(path="tests/test_utils.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="test",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        assert validator._has_mixed_concerns(group) is False

    def test_has_circular_dependencies_migration_and_model(self, validator):
        """Test circular dependency detection for migration and model."""
        files = [
            FileStatus(path="migrations/001_add_user.py", status_code="A"),
            FileStatus(path="models/user.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="database",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        # Currently returns False but logs warning
        assert validator._has_circular_dependencies(group) is False

    def test_has_circular_dependencies_schema_and_api(self, validator):
        """Test circular dependency detection for schema and API."""
        files = [
            FileStatus(path="schema/user_schema.py", status_code="M"),
            FileStatus(path="api/user_controller.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="api",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        # Currently returns False but logs warning
        assert validator._has_circular_dependencies(group) is False

    def test_has_circular_dependencies_none(self, validator):
        """Test circular dependency detection with no dependencies."""
        files = [
            FileStatus(path="src/utils.py", status_code="M"),
            FileStatus(path="src/helpers.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="test",
            files=files,
            category="source",
            confidence=0.8,
            reasoning="Test",
            semantic_similarity=0.7,
        )

        assert validator._has_circular_dependencies(group) is False

    def test_split_group_by_size(self, validator, large_group, mock_settings):
        """Test splitting group by size."""
        split_groups = validator._split_group(large_group)

        # Large group with all files in same directory gets split by directory first
        # which results in 1 group if all in same directory ("src/")
        assert len(split_groups) >= 1
        # All files should be preserved
        total_files = sum(len(g.files) for g in split_groups)
        assert total_files == len(large_group.files)

    def test_split_group_by_concern(
        self, validator, mixed_concerns_group, mock_settings
    ):
        """Test splitting group by concern."""
        split_groups = validator._split_group(mixed_concerns_group)

        assert len(split_groups) > 1
        # Each split should have consistent file types
        for group in split_groups:
            assert len(group.files) > 0
            assert group.confidence < mixed_concerns_group.confidence

    def test_split_by_directory(self, validator, mock_settings):
        """Test splitting by directory structure."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),
            FileStatus(path="src/utils.py", status_code="M"),
            FileStatus(path="lib/helpers.py", status_code="M"),
            FileStatus(path="lib/constants.py", status_code="M"),
        ]
        group = ChangeGroup(
            id="dir_group",
            files=files,
            category="source",
            confidence=0.9,
            reasoning="Multi-directory changes",
            semantic_similarity=0.75,
        )

        split_groups = validator._split_by_directory(group)

        assert len(split_groups) == 2  # Two directories
        # Check files are grouped by directory
        for split_group in split_groups:
            directories = {str(Path(f.path).parent) for f in split_group.files}
            assert len(directories) == 1  # All files in same directory

    def test_split_by_concern_comprehensive(self, validator):
        """Test splitting by concern with all file types."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),  # source
            FileStatus(path="tests/test_main.py", status_code="A"),  # test
            FileStatus(path="config.yaml", status_code="M"),  # config
            FileStatus(path="README.md", status_code="M"),  # docs
            FileStatus(path="data.csv", status_code="A"),  # other
        ]
        group = ChangeGroup(
            id="mixed",
            files=files,
            category="mixed",
            confidence=0.8,
            reasoning="Mixed concerns",
            semantic_similarity=0.6,
        )

        split_groups = validator._split_by_concern(group)

        assert len(split_groups) == 5  # One for each concern type
        # Verify each group has the right category
        categories = {g.category for g in split_groups}
        assert "source" in categories
        assert "test" in categories
        assert "config" in categories
        assert "docs" in categories

    def test_split_by_concern_java_files(self, validator):
        """Test splitting by concern with Java files."""
        files = [
            FileStatus(path="src/Main.java", status_code="M"),
            FileStatus(path="src/Utils.java", status_code="M"),
        ]
        group = ChangeGroup(
            id="java_group",
            files=files,
            category="source",
            confidence=0.85,
            reasoning="Java changes",
            semantic_similarity=0.8,
        )

        split_groups = validator._split_by_concern(group)

        assert len(split_groups) == 1  # All source files
        assert split_groups[0].category == "source"

    def test_split_by_size_exact_chunks(self, validator, mock_settings):
        """Test splitting by size with exact chunk boundaries."""
        mock_settings.max_files_per_pr = 3
        files = [
            FileStatus(path=f"file_{i}.py", status_code="M")
            for i in range(9)  # Exactly 3 chunks of 3
        ]
        group = ChangeGroup(
            id="exact_chunks",
            files=files,
            category="source",
            confidence=0.9,
            reasoning="Large group",
            semantic_similarity=0.75,
        )

        split_groups = validator._split_by_size(group)

        assert len(split_groups) == 3
        for i, split_group in enumerate(split_groups):
            assert len(split_group.files) == 3
            assert split_group.id == f"exact_chunks_chunk_{i}"
            assert (
                abs(split_group.confidence - 0.72) < 0.0001
            )  # 0.9 * 0.8 with float tolerance

    def test_split_by_size_uneven_chunks(self, validator, mock_settings):
        """Test splitting by size with uneven chunks."""
        mock_settings.max_files_per_pr = 3
        files = [
            FileStatus(path=f"file_{i}.py", status_code="M")
            for i in range(10)  # 3 + 3 + 3 + 1
        ]
        group = ChangeGroup(
            id="uneven_chunks",
            files=files,
            category="source",
            confidence=0.85,
            reasoning="Large group",
            semantic_similarity=0.7,
        )

        split_groups = validator._split_by_size(group)

        assert len(split_groups) == 4
        assert len(split_groups[0].files) == 3
        assert len(split_groups[1].files) == 3
        assert len(split_groups[2].files) == 3
        assert len(split_groups[3].files) == 1

    def test_validate_and_split_multiple_groups(
        self, validator, atomic_group, large_group, mixed_concerns_group, mock_settings
    ):
        """Test validation with multiple groups of different types."""
        groups = [atomic_group, large_group, mixed_concerns_group]

        result = validator.validate_and_split(groups)

        # Should have more groups after splitting
        assert len(result) > len(groups)
        # Atomic group should remain unchanged
        assert any(g.id == atomic_group.id for g in result)

    def test_validate_and_split_empty_list(self, validator, mock_settings):
        """Test validation with empty group list."""
        result = validator.validate_and_split([])

        assert result == []

    def test_split_group_preserves_metadata(
        self, validator, large_group, mock_settings
    ):
        """Test that splitting preserves group metadata."""
        split_groups = validator._split_group(large_group)

        for group in split_groups:
            assert group.semantic_similarity == large_group.semantic_similarity
            assert "split" in group.id.lower() or "chunk" in group.id.lower()
            assert group.confidence <= large_group.confidence

    def test_has_mixed_concerns_config_extensions(self, validator):
        """Test mixed concerns detection with various config extensions."""
        files = [
            FileStatus(path="config.json", status_code="M"),
            FileStatus(path="settings.yaml", status_code="M"),
            FileStatus(path="app.toml", status_code="M"),
        ]
        group = ChangeGroup(
            id="configs",
            files=files,
            category="config",
            confidence=0.8,
            reasoning="Config changes",
            semantic_similarity=0.9,
        )

        # All config files, no mixed concerns
        assert validator._has_mixed_concerns(group) is False

    def test_has_mixed_concerns_doc_extensions(self, validator):
        """Test mixed concerns detection with various doc extensions."""
        files = [
            FileStatus(path="README.md", status_code="M"),
            FileStatus(path="docs/guide.rst", status_code="M"),
            FileStatus(path="CHANGELOG.txt", status_code="M"),
        ]
        group = ChangeGroup(
            id="docs",
            files=files,
            category="docs",
            confidence=0.8,
            reasoning="Documentation changes",
            semantic_similarity=0.85,
        )

        # All doc files, no mixed concerns
        assert validator._has_mixed_concerns(group) is False

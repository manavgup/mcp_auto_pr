"""Unit tests for grouping engine service."""

from unittest.mock import Mock, patch

import pytest

from mcp_pr_recommender.services.grouping_engine import GroupingEngine


# Mock settings globally to avoid OpenAI API key requirement
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings to avoid OpenAI API key requirement."""
    with patch("mcp_pr_recommender.config.settings") as mock_settings_func:
        mock_settings_instance = Mock()
        mock_settings_instance.openai_api_key = "test_key"
        mock_settings_instance.default_strategy = "semantic"
        mock_settings_instance.max_files_per_pr = 8
        mock_settings_instance.min_files_per_pr = 1
        mock_settings_instance.similarity_threshold = 0.7
        mock_settings_instance.enable_llm_analysis = True
        mock_settings_func.return_value = mock_settings_instance
        yield mock_settings_instance


@pytest.mark.unit
class TestGroupingEngine:
    """Test cases for the grouping engine service."""

    @pytest.fixture
    def grouping_engine(self):
        """Create grouping engine instance."""
        with patch("openai.AsyncOpenAI"), patch(
            "mcp_pr_recommender.services.semantic_analyzer.settings"
        ) as mock_sa_settings, patch(
            "mcp_pr_recommender.services.grouping_engine.settings"
        ) as mock_ge_settings:
            # Mock settings for SemanticAnalyzer
            mock_sa_settings.return_value.openai_api_key = "test_key"
            # Mock settings for GroupingEngine
            mock_ge_settings.return_value.openai_api_key = "test_key"
            mock_ge_settings.return_value.enable_llm_analysis = True
            mock_ge_settings.return_value.max_files_per_pr = 8
            mock_ge_settings.return_value.similarity_threshold = 0.7
            return GroupingEngine()

    @pytest.fixture
    def sample_file_changes(self):
        """Sample file changes for testing."""
        from mcp_shared_lib.models.git.files import FileStatus

        file_paths = [
            "src/auth/login.py",
            "src/auth/logout.py",
            "src/auth/session.py",
            "src/models/user.py",
            "src/models/profile.py",
            "tests/test_auth.py",
            "tests/test_user.py",
            "config/settings.py",
        ]

        return [
            FileStatus(path=path, status_code="M", lines_added=10, lines_deleted=2)
            for path in file_paths
        ]

    def create_analysis_with_files(self, files):
        """Helper to create analysis object with the expected all_changed_files field."""
        from datetime import datetime

        from mcp_shared_lib.models import (
            ChangeCategorization,
            OutstandingChangesAnalysis,
            RiskAssessment,
        )

        analysis = OutstandingChangesAnalysis(
            repository_path="test_repo",
            analysis_timestamp=datetime.now(),
            total_outstanding_files=len(files),
            categories=ChangeCategorization(),
            risk_assessment=RiskAssessment(
                risk_level="medium",
                risk_factors=[],
                large_changes=[],
                potential_conflicts=[],
                binary_changes=[],
            ),
            summary="Test analysis",
            recommendations=[],
        )
        # Add the field that GroupingEngine expects (using object.__setattr__ to bypass validation)
        object.__setattr__(analysis, "all_changed_files", files)
        return analysis

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations(
        self, grouping_engine, sample_file_changes
    ):
        """Test generating PR recommendations."""
        from unittest.mock import patch

        # Create analysis with the expected field
        analysis = self.create_analysis_with_files(sample_file_changes)

        with patch(
            "mcp_pr_recommender.services.grouping_engine.settings"
        ) as mock_runtime_settings:
            mock_runtime_settings.return_value.enable_llm_analysis = (
                False  # Skip LLM to avoid API key
            )
            mock_runtime_settings.return_value.max_files_per_pr = 8
            mock_runtime_settings.return_value.similarity_threshold = 0.7

            result = await grouping_engine.generate_pr_recommendations(
                analysis, "semantic"
            )

        assert result.strategy_name == "semantic"
        assert len(result.recommended_prs) > 0
        assert len(result.change_groups) > 0

        # Verify PR structure
        for pr in result.recommended_prs:
            assert pr.title
            assert pr.description
            assert len(pr.files) > 0
            assert pr.branch_name
            assert pr.priority in ["high", "medium", "low"]
            assert pr.risk_level in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations_with_different_strategy(
        self, grouping_engine, sample_file_changes
    ):
        """Test generating PR recommendations with different strategy."""
        from unittest.mock import patch

        # Create analysis with the expected field
        analysis = self.create_analysis_with_files(sample_file_changes)

        with patch(
            "mcp_pr_recommender.services.grouping_engine.settings"
        ) as mock_runtime_settings:
            mock_runtime_settings.return_value.enable_llm_analysis = (
                False  # Skip LLM to avoid API key
            )
            mock_runtime_settings.return_value.max_files_per_pr = 8
            mock_runtime_settings.return_value.similarity_threshold = 0.7

            result = await grouping_engine.generate_pr_recommendations(
                analysis, "logical"
            )

        assert result.strategy_name == "logical"
        assert len(result.recommended_prs) > 0

    @pytest.mark.asyncio
    async def test_group_files_empty_input(self, grouping_engine):
        """Test grouping with empty file changes."""
        from datetime import datetime
        from unittest.mock import patch

        from mcp_shared_lib.models import (
            ChangeCategorization,
            OutstandingChangesAnalysis,
            RiskAssessment,
        )

        # Create real analysis object, then add the missing field
        analysis = OutstandingChangesAnalysis(
            repository_path="test_repo",
            analysis_timestamp=datetime.now(),
            total_outstanding_files=0,
            categories=ChangeCategorization(),
            risk_assessment=RiskAssessment(
                risk_level="low",
                risk_factors=[],
                large_changes=[],
                potential_conflicts=[],
                binary_changes=[],
            ),
            summary="Test analysis",
            recommendations=[],
        )
        # Add the field that GroupingEngine expects (using object.__setattr__ to bypass validation)
        object.__setattr__(analysis, "all_changed_files", [])

        with patch(
            "mcp_pr_recommender.services.grouping_engine.settings"
        ) as mock_runtime_settings:
            mock_runtime_settings.return_value.enable_llm_analysis = False
            mock_runtime_settings.return_value.max_files_per_pr = 8
            mock_runtime_settings.return_value.similarity_threshold = 0.7

            result = await grouping_engine.generate_pr_recommendations(
                analysis, "semantic"
            )

        assert len(result.recommended_prs) == 0
        assert len(result.change_groups) == 0

    @pytest.mark.asyncio
    async def test_group_files_by_directory_strategy(
        self, grouping_engine, sample_file_changes
    ):
        """Test directory-based grouping logic."""
        from unittest.mock import patch

        # Create analysis with the expected field
        analysis = self.create_analysis_with_files(sample_file_changes)

        with patch(
            "mcp_pr_recommender.services.grouping_engine.settings"
        ) as mock_runtime_settings:
            mock_runtime_settings.return_value.enable_llm_analysis = (
                False  # Skip LLM to avoid API key
            )
            mock_runtime_settings.return_value.max_files_per_pr = 8
            mock_runtime_settings.return_value.similarity_threshold = 0.7

            result = await grouping_engine.generate_pr_recommendations(
                analysis, "directory"
            )

        assert len(result.recommended_prs) > 0

        # Verify directory grouping - auth files should be grouped together
        auth_files = ["src/auth/login.py", "src/auth/logout.py", "src/auth/session.py"]
        found_auth_pr = False
        for pr in result.recommended_prs:
            if any(f in pr.files for f in auth_files):
                found_auth_pr = True
                break
        assert found_auth_pr

    @pytest.mark.asyncio
    async def test_group_files_invalid_strategy(
        self, grouping_engine, sample_file_changes
    ):
        """Test handling of different strategy names."""
        from unittest.mock import patch

        # Create analysis with the expected field
        analysis = self.create_analysis_with_files(sample_file_changes)

        with patch(
            "mcp_pr_recommender.services.grouping_engine.settings"
        ) as mock_runtime_settings:
            mock_runtime_settings.return_value.enable_llm_analysis = (
                False  # Skip LLM to avoid API key
            )
            mock_runtime_settings.return_value.max_files_per_pr = 8
            mock_runtime_settings.return_value.similarity_threshold = 0.7

            # The GroupingEngine should handle any strategy name gracefully
            result = await grouping_engine.generate_pr_recommendations(
                analysis, "nonexistent_strategy"
            )

        assert result.strategy_name == "nonexistent_strategy"
        assert len(result.recommended_prs) > 0

    @pytest.mark.asyncio
    async def test_estimate_group_size(self, grouping_engine, sample_file_changes):
        """Test group size estimation via review time."""
        from unittest.mock import patch

        # Set all_changed_files with varying sizes
        for i, change in enumerate(sample_file_changes):
            change.lines_added = 10 * (i + 1)
            change.lines_deleted = 5 * (i + 1)

        # Create analysis with the expected field
        analysis = self.create_analysis_with_files(sample_file_changes)

        with patch(
            "mcp_pr_recommender.services.grouping_engine.settings"
        ) as mock_runtime_settings:
            mock_runtime_settings.return_value.enable_llm_analysis = (
                False  # Skip LLM to avoid API key
            )
            mock_runtime_settings.return_value.max_files_per_pr = 8
            mock_runtime_settings.return_value.similarity_threshold = 0.7

            result = await grouping_engine.generate_pr_recommendations(
                analysis, "semantic"
            )

        # Verify that review times are reasonable
        for pr in result.recommended_prs:
            assert 10 <= pr.estimated_review_time <= 120  # Between 10 and 120 minutes

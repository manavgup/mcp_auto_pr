"""Comprehensive unit tests for the SemanticAnalyzer service."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from mcp_shared_lib.models import (
    ChangeCategorization,
    OutstandingChangesAnalysis,
    RiskAssessment,
)
from mcp_shared_lib.models.git.changes import FileStatus

from mcp_pr_recommender.models.pr.recommendations import ChangeGroup, PRRecommendation
from mcp_pr_recommender.services.semantic_analyzer import SemanticAnalyzer


@pytest.mark.unit
class TestSemanticAnalyzer:
    """Test the SemanticAnalyzer service."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch(
            "mcp_pr_recommender.services.semantic_analyzer.settings"
        ) as mock_settings_func:
            mock_settings_instance = Mock()
            mock_settings_instance.openai_api_key = "test_key"
            mock_settings_instance.openai_model = "gpt-4"
            mock_settings_instance.max_tokens_per_request = 1000
            mock_settings_func.return_value = mock_settings_instance
            yield mock_settings_instance

    @pytest.fixture
    def analyzer(self, mock_settings):
        """Create semantic analyzer instance."""
        with patch("mcp_pr_recommender.services.semantic_analyzer.openai.AsyncOpenAI"):
            return SemanticAnalyzer()

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
            FileStatus(
                path="README.md", status_code="M", lines_added=5, lines_deleted=2
            ),
            FileStatus(
                path="config.yaml", status_code="M", lines_added=3, lines_deleted=1
            ),
        ]

    @pytest.fixture
    def sample_analysis(self):
        """Create sample analysis object."""
        from pathlib import Path

        return OutstandingChangesAnalysis(
            repository_path=Path("/test/repo"),
            summary="Multiple changes across source, tests, and configuration",
            risk_assessment=RiskAssessment(
                risk_level="medium",
                risk_factors=["Multiple file types changed"],
                large_changes=[],
                potential_conflicts=[],
                binary_changes=[],
            ),
            categorization=ChangeCategorization(
                critical_files=[],
                source_code=["src/main.py", "src/utils.py"],
                documentation=["README.md"],
                tests=["tests/test_main.py"],
                configuration=["config.yaml"],
                other=[],
            ),
            recommendations=[],
            metadata={},
        )

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, mock_settings):
        """Test analyzer initialization."""
        with patch(
            "mcp_pr_recommender.services.semantic_analyzer.openai.AsyncOpenAI"
        ) as mock_openai:
            analyzer = SemanticAnalyzer()

            assert analyzer.client is not None
            assert analyzer.logger is not None
            mock_openai.assert_called_once_with(api_key="test_key")

    @pytest.mark.asyncio
    async def test_analyze_and_generate_prs_success(
        self, analyzer, sample_files, sample_analysis
    ):
        """Test successful PR generation."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "groups": [
                    {
                        "id": "source_changes",
                        "files": ["src/main.py", "src/utils.py"],
                        "category": "feature",
                        "confidence": 0.9,
                        "reasoning": "Core source code changes",
                    },
                    {
                        "id": "test_changes",
                        "files": ["tests/test_main.py"],
                        "category": "test",
                        "confidence": 0.85,
                        "reasoning": "Related test updates",
                    },
                ],
                "rationale": "Grouped by functionality",
            }
        )

        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await analyzer.analyze_and_generate_prs(sample_files, sample_analysis)

        assert len(result) >= 2  # May include ungrouped files as 3rd group
        assert all(isinstance(pr, PRRecommendation) for pr in result)
        # Check that we have feat and test PRs (in any order)
        titles = [pr.title for pr in result]
        assert any(title.startswith("feat:") for title in titles)
        assert any(title.startswith("test:") for title in titles)

    @pytest.mark.asyncio
    async def test_analyze_and_generate_prs_empty_files(
        self, analyzer, sample_analysis
    ):
        """Test PR generation with empty file list."""
        result = await analyzer.analyze_and_generate_prs([], sample_analysis)

        assert result == []

    @pytest.mark.asyncio
    async def test_analyze_and_generate_prs_filtered_files(
        self, analyzer, sample_analysis
    ):
        """Test PR generation filters out junk files."""
        files = [
            FileStatus(
                path="src/main.py", status_code="M", lines_added=10, lines_deleted=5
            ),
            FileStatus(path="__pycache__/cache.pyc", status_code="A"),
            FileStatus(path=".DS_Store", status_code="M"),
        ]

        # Mock LLM to return fallback grouping
        analyzer.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Test error")
        )

        result = await analyzer.analyze_and_generate_prs(files, sample_analysis)

        # Should only process src/main.py
        assert len(result) >= 1
        assert "src/main.py" in result[0].files

    @pytest.mark.asyncio
    async def test_llm_group_files_success(
        self, analyzer, sample_files, sample_analysis
    ):
        """Test successful LLM grouping."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "groups": [
                    {
                        "id": "group_1",
                        "files": ["src/main.py", "src/utils.py"],
                        "category": "feature",
                        "confidence": 0.9,
                        "reasoning": "Related source changes",
                    }
                ]
            }
        )

        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

        groups = await analyzer._llm_group_files(sample_files, sample_analysis)

        assert len(groups) >= 1  # May include ungrouped files
        assert groups[0].id == "group_1"
        assert len(groups[0].files) == 2

    @pytest.mark.asyncio
    async def test_llm_group_files_none_response(
        self, analyzer, sample_files, sample_analysis
    ):
        """Test LLM grouping with None response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None

        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

        groups = await analyzer._llm_group_files(sample_files, sample_analysis)

        # Should fallback to simple grouping
        assert len(groups) > 0

    @pytest.mark.asyncio
    async def test_llm_group_files_exception(
        self, analyzer, sample_files, sample_analysis
    ):
        """Test LLM grouping with exception."""
        analyzer.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API error")
        )

        groups = await analyzer._llm_group_files(sample_files, sample_analysis)

        # Should fallback to simple grouping
        assert len(groups) > 0
        assert any(g.id in ["source_code_changes", "other_changes"] for g in groups)

    def test_filter_files(self, analyzer):
        """Test file filtering."""
        files = [
            FileStatus(path="src/main.py", status_code="M"),
            FileStatus(path="__pycache__/compiled.pyc", status_code="A"),
            FileStatus(path="node_modules/package/file.js", status_code="M"),
            FileStatus(path=".pytest_cache/data", status_code="A"),
            FileStatus(path="src/utils.py", status_code="M"),
        ]

        result = analyzer._filter_files(files)

        assert len(result) == 2
        assert all(f.path in ["src/main.py", "src/utils.py"] for f in result)

    def test_should_exclude_file(self, analyzer):
        """Test file exclusion logic."""
        assert analyzer._should_exclude_file("__pycache__/file.pyc") is True
        assert analyzer._should_exclude_file("file.pyc") is True
        assert analyzer._should_exclude_file(".git/config") is True
        assert analyzer._should_exclude_file("node_modules/package.js") is True
        assert analyzer._should_exclude_file(".ds_store") is True  # Lowercase version
        assert analyzer._should_exclude_file("thumbs.db") is True
        assert analyzer._should_exclude_file(".pytest_cache/data") is True
        assert analyzer._should_exclude_file("src/main.py") is False
        assert analyzer._should_exclude_file("README.md") is False

    def test_create_grouping_prompt(self, analyzer, sample_files, sample_analysis):
        """Test grouping prompt creation."""
        prompt = analyzer._create_grouping_prompt(sample_files, sample_analysis)

        assert "Group these 5 files" in prompt
        assert "src/main.py" in prompt
        assert "Risk level: medium" in prompt
        assert "Total line changes:" in prompt

    def test_create_grouping_prompt_with_no_changes(self, analyzer, sample_analysis):
        """Test grouping prompt with files having no changes."""
        files = [
            FileStatus(
                path="file1.py", status_code="M", lines_added=10, lines_deleted=5
            ),
            FileStatus(
                path="file2.py", status_code="M", lines_added=0, lines_deleted=0
            ),
        ]

        prompt = analyzer._create_grouping_prompt(files, sample_analysis)

        assert "Files with actual changes: 1" in prompt
        assert "Files without changes: 1" in prompt
        assert "NO CHANGES" in prompt

    def test_parse_grouping_response_valid_json(self, analyzer, sample_files):
        """Test parsing valid JSON grouping response."""
        response = """Here are the groups:
        {
            "groups": [
                {
                    "id": "feature_group",
                    "files": ["src/main.py", "src/utils.py"],
                    "category": "feature",
                    "confidence": 0.9,
                    "reasoning": "Core feature implementation"
                }
            ],
            "rationale": "Grouped by functionality"
        }
        """

        groups = analyzer._parse_grouping_response(response, sample_files)

        assert len(groups) >= 1
        assert groups[0].id == "feature_group"
        assert len(groups[0].files) == 2

    def test_parse_grouping_response_invalid_json(self, analyzer, sample_files):
        """Test parsing invalid JSON response."""
        response = "This is not valid JSON"

        groups = analyzer._parse_grouping_response(response, sample_files)

        assert groups == []

    def test_parse_grouping_response_missing_groups_key(self, analyzer, sample_files):
        """Test parsing response without groups key."""
        response = '{"data": "something else"}'

        groups = analyzer._parse_grouping_response(response, sample_files)

        assert groups == []

    def test_parse_grouping_response_with_ungrouped(self, analyzer, sample_files):
        """Test parsing response with ungrouped files."""
        response = json.dumps(
            {
                "groups": [
                    {
                        "id": "group_1",
                        "files": ["src/main.py"],
                        "category": "feature",
                        "confidence": 0.9,
                    }
                ]
            }
        )

        groups = analyzer._parse_grouping_response(response, sample_files)

        # Should have group_1 plus ungrouped files
        assert len(groups) == 2
        assert groups[1].id == "ungrouped_files"
        assert len(groups[1].files) == 4  # All except src/main.py

    def test_fallback_grouping_with_changes(self, analyzer):
        """Test fallback grouping with files having changes."""
        files = [
            FileStatus(
                path="src/main.py", status_code="M", lines_added=10, lines_deleted=5
            ),
            FileStatus(
                path="tests/test_main.py",
                status_code="A",
                lines_added=50,
                lines_deleted=0,
            ),
            FileStatus(
                path="pyproject.toml", status_code="M", lines_added=2, lines_deleted=1
            ),
            FileStatus(
                path="docs/guide.md", status_code="M", lines_added=5, lines_deleted=2
            ),
        ]

        groups = analyzer._fallback_grouping(files)

        assert len(groups) >= 2
        assert any(g.id == "source_code_changes" for g in groups)
        assert any(g.id == "configuration_changes" for g in groups)

    def test_fallback_grouping_without_changes(self, analyzer):
        """Test fallback grouping with files having no changes."""
        files = [
            FileStatus(
                path="file1.py", status_code="M", lines_added=0, lines_deleted=0
            ),
            FileStatus(
                path="file2.py", status_code="M", lines_added=0, lines_deleted=0
            ),
        ]

        groups = analyzer._fallback_grouping(files)

        assert len(groups) == 1
        assert groups[0].id == "no_changes_cleanup"
        assert len(groups[0].files) == 2

    def test_fallback_grouping_mixed(self, analyzer):
        """Test fallback grouping with mixed file types."""
        files = [
            FileStatus(path="app.js", status_code="M", lines_added=10, lines_deleted=5),
            FileStatus(
                path="Main.java", status_code="A", lines_added=100, lines_deleted=0
            ),
            FileStatus(
                path="server.go", status_code="M", lines_added=20, lines_deleted=10
            ),
            FileStatus(
                path="requirements.txt", status_code="M", lines_added=2, lines_deleted=1
            ),
        ]

        groups = analyzer._fallback_grouping(files)

        assert any(g.id == "source_code_changes" for g in groups)
        assert any(g.id == "configuration_changes" for g in groups)

    def test_generate_pr_recommendations(self, analyzer, sample_analysis):
        """Test PR recommendation generation."""
        groups = [
            ChangeGroup(
                id="feature_group",
                files=[
                    FileStatus(
                        path="src/main.py",
                        status_code="M",
                        lines_added=10,
                        lines_deleted=5,
                    ),
                    FileStatus(
                        path="src/utils.py",
                        status_code="M",
                        lines_added=20,
                        lines_deleted=10,
                    ),
                ],
                category="feature",
                confidence=0.9,
                reasoning="Core feature implementation",
                semantic_similarity=0.85,
            )
        ]

        recommendations = analyzer._generate_pr_recommendations(groups, sample_analysis)

        assert len(recommendations) == 1
        pr = recommendations[0]
        assert pr.id == "pr_1"
        assert "feat:" in pr.title
        assert pr.priority == "high"
        assert pr.risk_level in ["low", "medium", "high"]

    def test_generate_title_source_code(self, analyzer):
        """Test title generation for source code changes."""
        group = ChangeGroup(
            id="source_code_changes",
            files=[
                FileStatus(
                    path="src/main.py", status_code="M", lines_added=10, lines_deleted=5
                )
            ],
            category="feature",
            confidence=0.9,
            reasoning="Test",
            semantic_similarity=0.8,
        )

        title = analyzer._generate_title(group, 1)

        assert "feat:" in title
        assert "core application logic" in title

    def test_generate_title_config(self, analyzer):
        """Test title generation for config changes."""
        group = ChangeGroup(
            id="configuration_changes",
            files=[FileStatus(path="config.yaml", status_code="M")],
            category="config",
            confidence=0.9,
            reasoning="Test",
            semantic_similarity=0.8,
        )

        title = analyzer._generate_title(group, 1)

        assert "config:" in title
        assert "dependencies" in title

    def test_generate_title_cleanup(self, analyzer):
        """Test title generation for cleanup."""
        group = ChangeGroup(
            id="no_changes_cleanup",
            files=[
                FileStatus(
                    path="file.py", status_code="M", lines_added=0, lines_deleted=0
                )
            ],
            category="chore",
            confidence=0.5,
            reasoning="Test",
            semantic_similarity=0.8,
        )

        title = analyzer._generate_title(group, 0)

        assert "chore:" in title
        assert "cleanup" in title

    def test_generate_title_custom(self, analyzer):
        """Test title generation for custom group."""
        group = ChangeGroup(
            id="auth_system_update",
            files=[
                FileStatus(
                    path="auth.py", status_code="M", lines_added=10, lines_deleted=5
                )
            ],
            category="feature",
            confidence=0.9,
            reasoning="Test",
            semantic_similarity=0.8,
        )

        title = analyzer._generate_title(group, 1)

        assert "feat:" in title
        assert "auth system update" in title

    def test_generate_description(self, analyzer):
        """Test PR description generation."""
        group = ChangeGroup(
            id="test_group",
            files=[
                FileStatus(
                    path="file1.py", status_code="M", lines_added=10, lines_deleted=5
                ),
                FileStatus(
                    path="file2.py", status_code="A", lines_added=20, lines_deleted=0
                ),
                FileStatus(
                    path="file3.py", status_code="M", lines_added=0, lines_deleted=0
                ),
            ],
            category="feature",
            confidence=0.9,
            reasoning="Test reasoning",
            semantic_similarity=0.8,
        )

        description = analyzer._generate_description(group)

        assert "## Feature Changes" in description
        assert "**Files modified:** 3" in description
        assert "Lines changed:" in description
        assert "file1.py" in description
        assert "Files without changes" in description
        assert "Test reasoning" in description

    def test_generate_description_large_changeset(self, analyzer):
        """Test description for large changeset."""
        group = ChangeGroup(
            id="large_group",
            files=[
                FileStatus(
                    path=f"file{i}.py",
                    status_code="M",
                    lines_added=100,
                    lines_deleted=50,
                )
                for i in range(10)
            ],
            category="feature",
            confidence=0.9,
            reasoning="Large changes",
            semantic_similarity=0.7,
        )

        description = analyzer._generate_description(group)

        assert "Large changeset" in description
        assert "review carefully" in description

    def test_generate_branch_name(self, analyzer):
        """Test branch name generation."""
        test_cases = [
            ("source_code_changes", "feature", "feature/core-updates"),
            ("configuration_changes", "config", "config/dependencies"),
            ("no_changes_cleanup", "chore", "chore/cleanup"),
            ("auth_system_changes", "feature", "feature/auth-system"),
        ]

        for group_id, category, expected in test_cases:
            group = ChangeGroup(
                id=group_id,
                files=[],
                category=category,
                confidence=0.9,
                reasoning="Test",
                semantic_similarity=0.8,
            )

            branch_name = analyzer._generate_branch_name(group)
            assert branch_name == expected

    def test_determine_priority(self, analyzer):
        """Test priority determination."""
        group = ChangeGroup(
            id="test",
            files=[
                FileStatus(
                    path="file.py", status_code="M", lines_added=10, lines_deleted=5
                )
            ],
            category="feature",
            confidence=0.9,
            reasoning="Test",
            semantic_similarity=0.8,
        )

        # Feature with changes -> high
        assert analyzer._determine_priority(group, 15, 1) == "high"

        # Config -> medium
        group.category = "config"
        assert analyzer._determine_priority(group, 15, 1) == "medium"

        # No changes -> low
        assert analyzer._determine_priority(group, 0, 0) == "low"

        # Large changes -> high
        group.category = "chore"
        assert analyzer._determine_priority(group, 600, 1) == "high"

    def test_determine_risk(self, analyzer):
        """Test risk determination."""
        # No changes -> low risk
        assert analyzer._determine_risk(0, 5) == "low"

        # Small changes -> low risk
        assert analyzer._determine_risk(50, 2) == "low"

        # Medium changes -> medium risk
        assert analyzer._determine_risk(300, 5) == "medium"

        # Large changes -> high risk
        assert analyzer._determine_risk(1500, 10) == "high"

        # Many files -> medium risk
        assert analyzer._determine_risk(100, 10) == "medium"

    def test_estimate_review_time(self, analyzer):
        """Test review time estimation."""
        # No changes -> minimum time
        assert analyzer._estimate_review_time(5, 0) == 10

        # Small changes
        assert analyzer._estimate_review_time(2, 50) >= 10

        # Large changes
        time = analyzer._estimate_review_time(10, 1000)
        assert 10 <= time <= 120

    def test_generate_labels(self, analyzer):
        """Test label generation."""
        group = ChangeGroup(
            id="test",
            files=[
                FileStatus(
                    path=f"file{i}.py",
                    status_code="M",
                    lines_added=60,
                    lines_deleted=40,
                )
                for i in range(12)
            ],
            category="feature",
            confidence=0.9,
            reasoning="Test",
            semantic_similarity=0.8,
        )

        labels = analyzer._generate_labels(group)

        assert "feature" in labels
        assert "large-change" in labels  # >500 total changes
        assert "multiple-files" in labels  # >10 files

        # Test cleanup label
        group.files = [
            FileStatus(path="file.py", status_code="M", lines_added=0, lines_deleted=0)
        ]
        labels = analyzer._generate_labels(group)
        assert "cleanup" in labels

    @pytest.mark.asyncio
    async def test_analyze_and_generate_prs_integration(
        self, analyzer, sample_analysis
    ):
        """Test full integration of analyze_and_generate_prs."""
        files = [
            FileStatus(
                path="src/main.py", status_code="M", lines_added=100, lines_deleted=50
            ),
            FileStatus(
                path="src/utils.py", status_code="M", lines_added=20, lines_deleted=10
            ),
            FileStatus(
                path="tests/test_main.py",
                status_code="A",
                lines_added=200,
                lines_deleted=0,
            ),
            FileStatus(
                path="__pycache__/cache.pyc", status_code="A"
            ),  # Should be filtered
            FileStatus(
                path="config.yaml", status_code="M", lines_added=5, lines_deleted=2
            ),
            FileStatus(
                path="README.md", status_code="M", lines_added=10, lines_deleted=5
            ),
        ]

        # Mock successful LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "groups": [
                    {
                        "id": "core_feature",
                        "files": ["src/main.py", "src/utils.py", "tests/test_main.py"],
                        "category": "feature",
                        "confidence": 0.95,
                        "reasoning": "Core feature with tests",
                    },
                    {
                        "id": "docs_and_config",
                        "files": ["config.yaml", "README.md"],
                        "category": "chore",
                        "confidence": 0.8,
                        "reasoning": "Documentation and configuration updates",
                    },
                ],
                "rationale": "Grouped by logical units",
            }
        )

        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

        recommendations = await analyzer.analyze_and_generate_prs(
            files, sample_analysis
        )

        assert len(recommendations) == 2

        # Check first PR
        pr1 = recommendations[0]
        assert pr1.title.startswith("feat:")
        assert len(pr1.files) == 3
        assert pr1.priority == "high"
        assert pr1.total_lines_changed == 380

        # Check second PR
        pr2 = recommendations[1]
        assert pr2.title.startswith("chore:")
        assert len(pr2.files) == 2
        assert pr2.total_lines_changed == 22

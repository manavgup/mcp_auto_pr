"""Unit tests for PR recommender MCP tool."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.utils.factories import create_file_changes


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
class TestPRRecommenderTool:
    """Test cases for the PR recommender MCP tool."""

    @pytest.fixture
    def pr_recommender_tool(self):
        """Create PR recommender tool instance."""
        with patch("openai.AsyncOpenAI"), patch(
            "mcp_pr_recommender.services.semantic_analyzer.settings"
        ) as mock_sa_settings, patch(
            "mcp_pr_recommender.tools.pr_recommender_tool.SemanticAnalyzer"
        ) as mock_semantic_analyzer_class:
            # Mock settings for SemanticAnalyzer
            mock_sa_settings.return_value.openai_api_key = "test_key"

            # Create a mock instance for the SemanticAnalyzer class
            mock_analyzer_instance = Mock()
            mock_semantic_analyzer_class.return_value = mock_analyzer_instance

            from mcp_pr_recommender.tools.pr_recommender_tool import PRRecommenderTool

            tool = PRRecommenderTool()

            # Ensure the tool has the mocked semantic analyzer
            tool.semantic_analyzer = mock_analyzer_instance

            return tool

    @pytest.fixture
    def mock_context(self):
        """Mock MCP context."""
        ctx = AsyncMock()
        ctx.info = AsyncMock()
        ctx.debug = AsyncMock()
        ctx.warning = AsyncMock()
        ctx.error = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_file_changes(self):
        """Sample file changes for testing."""
        return create_file_changes(
            count=6,
            patterns=[
                "src/auth/login.py",
                "src/auth/logout.py",
                "src/models/user.py",
                "tests/test_auth.py",
                "tests/test_user.py",
                "config/settings.py",
            ],
        )

    @pytest.fixture
    def mock_grouping_engine(self):
        """Mock grouping engine."""
        engine = Mock()
        engine.group_files_by_strategy.return_value = [
            {
                "group_id": "auth_features",
                "files": [
                    "src/auth/login.py",
                    "src/auth/logout.py",
                    "tests/test_auth.py",
                ],
                "description": "Authentication feature updates",
                "cohesion_score": 0.85,
                "estimated_size": "medium",
                "risk_level": "medium",
            },
            {
                "group_id": "user_model",
                "files": ["src/models/user.py", "tests/test_user.py"],
                "description": "User model enhancements",
                "cohesion_score": 0.92,
                "estimated_size": "small",
                "risk_level": "low",
            },
        ]
        return engine

    @pytest.fixture
    def mock_semantic_analyzer(self):
        """Mock semantic analyzer."""
        analyzer = Mock()
        analyzer.analyze_file_relationships.return_value = {
            "similarity_matrix": {
                ("src/auth/login.py", "src/auth/logout.py"): 0.9,
                ("src/models/user.py", "tests/test_user.py"): 0.8,
            },
            "semantic_clusters": [
                ["src/auth/login.py", "src/auth/logout.py"],
                ["src/models/user.py"],
            ],
        }
        return analyzer

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations_success(
        self, pr_recommender_tool, sample_file_changes
    ):
        """Test successful PR recommendation generation."""
        analysis_data = {
            "file_changes": sample_file_changes,
            "risk_assessment": {"overall_risk": 0.6, "high_risk_files": []},
            "categories": {
                "source_code": [
                    "src/auth/login.py",
                    "src/auth/logout.py",
                    "src/models/user.py",
                ],
                "tests": ["tests/test_auth.py", "tests/test_user.py"],
                "configuration": ["config/settings.py"],
            },
        }

        # Mock file status objects
        from mcp_shared_lib.models.git.files import FileStatus

        mock_files = [
            FileStatus(
                path="src/auth/login.py",
                status_code="M",
                lines_added=10,
                lines_deleted=2,
            ),
            FileStatus(
                path="src/auth/logout.py",
                status_code="M",
                lines_added=5,
                lines_deleted=1,
            ),
            FileStatus(
                path="tests/test_auth.py",
                status_code="A",
                lines_added=20,
                lines_deleted=0,
            ),
        ]

        # Mock the _extract_all_files method and semantic analyzer
        with patch.object(
            pr_recommender_tool, "_extract_all_files", return_value=mock_files
        ):
            # Mock the semantic analyzer's response - make it async
            from mcp_pr_recommender.models.pr.recommendations import PRRecommendation

            pr_recommender_tool.semantic_analyzer.analyze_and_generate_prs = AsyncMock(
                return_value=[
                    PRRecommendation(
                        id="pr_001",
                        title="Add authentication system",
                        description="Implement user authentication",
                        files=[
                            "src/auth/login.py",
                            "src/auth/logout.py",
                            "tests/test_auth.py",
                        ],
                        branch_name="feature/auth-system",
                        priority="high",
                        estimated_review_time=30,
                        risk_level="medium",
                        reasoning="Authentication files are logically related and should be reviewed together",
                        files_count=3,
                        total_lines_changed=38,
                    )
                ]
            )

            result = await pr_recommender_tool.generate_recommendations(
                analysis_data=analysis_data, strategy="semantic"
            )

        # Verify result structure
        assert "recommendations" in result
        assert "metadata" in result
        assert len(result["recommendations"]) > 0

        # Verify recommendation structure
        for rec in result["recommendations"]:
            assert "title" in rec
            assert "description" in rec
            assert "files" in rec
            assert "estimated_review_time" in rec  # Changed from estimated_size
            assert "risk_level" in rec
            assert "priority" in rec

        # Verify the mock was called
        pr_recommender_tool.semantic_analyzer.analyze_and_generate_prs.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations_empty_changes(self, pr_recommender_tool):
        """Test PR recommendation generation with no file changes."""
        analysis_data = {
            "file_changes": [],
            "risk_assessment": {"overall_risk": 0.0, "high_risk_files": []},
            "categories": {},
        }

        # Mock _extract_all_files to return empty list
        with patch.object(pr_recommender_tool, "_extract_all_files", return_value=[]):
            result = await pr_recommender_tool.generate_recommendations(
                analysis_data=analysis_data
            )

        assert result["error"] == "No files to analyze"
        assert result["recommendations"] == []

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations_invalid_strategy(
        self, pr_recommender_tool, sample_file_changes
    ):
        """Test PR recommendation generation with invalid strategy."""
        analysis_data = {
            "file_changes": sample_file_changes,
            "risk_assessment": {"overall_risk": 0.6, "high_risk_files": []},
            "categories": {"source_code": ["src/test.py"]},
        }

        # Mock file status objects
        from mcp_shared_lib.models.git.files import FileStatus

        mock_files = [
            FileStatus(
                path="src/test.py", status_code="M", lines_added=10, lines_deleted=2
            ),
        ]

        # Mock the _extract_all_files method and semantic analyzer
        with patch.object(
            pr_recommender_tool, "_extract_all_files", return_value=mock_files
        ):
            # Mock the semantic analyzer's response - it handles strategy internally
            from mcp_pr_recommender.models.pr.recommendations import PRRecommendation

            pr_recommender_tool.semantic_analyzer.analyze_and_generate_prs = AsyncMock(
                return_value=[
                    PRRecommendation(
                        id="pr_test_001",
                        title="Test changes",
                        description="Update test file",
                        files=["src/test.py"],
                        branch_name="feature/test-updates",
                        priority="medium",
                        estimated_review_time=15,
                        risk_level="low",
                        reasoning="Single test file change, low complexity",
                        files_count=1,
                        total_lines_changed=12,
                    )
                ]
            )

            result = await pr_recommender_tool.generate_recommendations(
                analysis_data=analysis_data, strategy="invalid_strategy"
            )

        # Should handle invalid strategy gracefully and still generate recommendations
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations_large_changeset(
        self, pr_recommender_tool
    ):
        """Test PR recommendation generation with large changeset."""
        analysis_data = {
            "file_changes": [],  # Not used, we'll mock _extract_all_files
            "risk_assessment": {"overall_risk": 0.8, "high_risk_files": []},
            "categories": {"source_code": [f"src/file_{i}.py" for i in range(30)]},
        }

        # Mock large number of file status objects
        from mcp_shared_lib.models.git.files import FileStatus

        mock_files = [
            FileStatus(
                path=f"src/file_{i}.py", status_code="M", lines_added=5, lines_deleted=2
            )
            for i in range(30)
        ]

        # Mock the _extract_all_files method and semantic analyzer
        with patch.object(
            pr_recommender_tool, "_extract_all_files", return_value=mock_files
        ):
            # Mock semantic analyzer to return multiple recommendations for large changeset
            from mcp_pr_recommender.models.pr.recommendations import PRRecommendation

            pr_recommender_tool.semantic_analyzer.analyze_and_generate_prs = AsyncMock(
                return_value=[
                    PRRecommendation(
                        id=f"pr_group_{i}",
                        title=f"Group {i} changes",
                        description=f"Changes for group {i}",
                        files=[f"src/file_{i}.py", f"src/file_{i+1}.py"],
                        branch_name=f"feature/group-{i}-changes",
                        priority="medium",
                        estimated_review_time=20,
                        risk_level="medium",
                        reasoning=f"Files in group {i} are related by functionality",
                        files_count=2,
                        total_lines_changed=14,
                    )
                    for i in range(0, min(20, 30), 2)  # Limit to 10 PRs
                ][:10]
            )  # Ensure max 10 PRs

            result = await pr_recommender_tool.generate_recommendations(
                analysis_data=analysis_data
            )

        assert len(result["recommendations"]) <= 10  # Should respect reasonable limits
        assert len(result["recommendations"]) > 0  # Should have some recommendations

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations_high_risk_files(
        self, pr_recommender_tool
    ):
        """Test PR recommendation generation with high-risk files."""
        analysis_data = {
            "file_changes": [],  # Not used, we'll mock _extract_all_files
            "risk_assessment": {
                "overall_risk": 0.9,
                "high_risk_files": [
                    "config/production.json",
                    "migrations/001_critical.sql",
                ],
            },
            "categories": {
                "configuration": ["config/production.json"],
                "source_code": ["src/core/auth.py"],
                "database": ["migrations/001_critical.sql"],
            },
        }

        # Mock high-risk file status objects
        from mcp_shared_lib.models.git.files import FileStatus

        mock_files = [
            FileStatus(
                path="config/production.json",
                status_code="M",
                lines_added=5,
                lines_deleted=2,
            ),
            FileStatus(
                path="src/core/auth.py",
                status_code="M",
                lines_added=15,
                lines_deleted=3,
            ),
            FileStatus(
                path="migrations/001_critical.sql",
                status_code="A",
                lines_added=20,
                lines_deleted=0,
            ),
        ]

        # Mock the _extract_all_files method and semantic analyzer
        with patch.object(
            pr_recommender_tool, "_extract_all_files", return_value=mock_files
        ):
            # Mock semantic analyzer to separate high-risk files
            from mcp_pr_recommender.models.pr.recommendations import PRRecommendation

            pr_recommender_tool.semantic_analyzer.analyze_and_generate_prs = AsyncMock(
                return_value=[
                    PRRecommendation(
                        id="pr_config_critical",
                        title="Critical configuration changes",
                        description="Update production configuration",
                        files=["config/production.json"],
                        branch_name="hotfix/production-config",
                        priority="high",
                        estimated_review_time=45,
                        risk_level="high",  # Changed from "critical" to "high" (valid enum value)
                        reasoning="Production configuration changes require careful review",
                        files_count=1,
                        total_lines_changed=7,
                    ),
                    PRRecommendation(
                        id="pr_migration_critical",
                        title="Critical database migration",
                        description="Database schema updates",
                        files=["migrations/001_critical.sql"],
                        branch_name="hotfix/critical-migration",
                        priority="high",
                        estimated_review_time=60,
                        risk_level="high",  # Changed from "critical" to "high" (valid enum value)
                        reasoning="Database migrations need thorough testing",
                        files_count=1,
                        total_lines_changed=20,
                    ),
                    PRRecommendation(
                        id="pr_auth_changes",
                        title="Authentication system changes",
                        description="Core authentication updates",
                        files=["src/core/auth.py"],
                        branch_name="feature/auth-improvements",
                        priority="high",
                        estimated_review_time=40,
                        risk_level="high",
                        reasoning="Core authentication changes affect security",
                        files_count=1,
                        total_lines_changed=18,
                    ),
                ]
            )

            result = await pr_recommender_tool.generate_recommendations(
                analysis_data=analysis_data
            )

        # Verify high-risk files are isolated
        high_risk_recs = [
            r for r in result["recommendations"] if r["risk_level"] in ["high"]
        ]
        assert len(high_risk_recs) >= 2

        # Verify small PR sizes for high-risk changes
        for rec in high_risk_recs:
            if rec["risk_level"] == "high":
                assert len(rec["files"]) <= 2  # High-risk changes should be isolated

    @pytest.mark.asyncio
    async def test_generate_pr_recommendations_error_handling(
        self, pr_recommender_tool, sample_file_changes
    ):
        """Test error handling in PR recommendation generation."""
        analysis_data = {
            "file_changes": sample_file_changes,
            "risk_assessment": {"overall_risk": 0.6, "high_risk_files": []},
            "categories": {"source_code": ["src/test.py"]},
        }

        # Mock file status objects
        from mcp_shared_lib.models.git.files import FileStatus

        mock_files = [
            FileStatus(
                path="src/test.py", status_code="M", lines_added=10, lines_deleted=2
            ),
        ]

        # Mock the _extract_all_files method and make semantic analyzer raise an exception
        with patch.object(
            pr_recommender_tool, "_extract_all_files", return_value=mock_files
        ):
            # The semantic analyzer is already mocked in the fixture, so we can set the side effect directly
            pr_recommender_tool.semantic_analyzer.analyze_and_generate_prs.side_effect = Exception(
                "Analysis failed"
            )

            result = await pr_recommender_tool.generate_recommendations(
                analysis_data=analysis_data
            )

        assert "error" in result
        assert "analysis failed" in result["error"].lower()

"""Comprehensive unit tests for the FeasibilityAnalyzerTool."""

from unittest.mock import Mock, patch

import pytest

from mcp_pr_recommender.tools.feasibility_analyzer_tool import FeasibilityAnalyzerTool


@pytest.mark.unit
class TestFeasibilityAnalyzerTool:
    """Test the FeasibilityAnalyzerTool."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("mcp_pr_recommender.config.settings") as mock_settings_func:
            mock_settings_instance = Mock()
            mock_settings_instance.max_files_per_pr = 8
            mock_settings_func.return_value = mock_settings_instance
            yield mock_settings_instance

    @pytest.fixture
    def tool(self, mock_settings):
        """Create feasibility analyzer tool instance."""
        return FeasibilityAnalyzerTool()

    @pytest.fixture
    def sample_pr_simple(self):
        """Create simple PR recommendation."""
        return {
            "id": "pr_1",
            "title": "Simple bug fix",
            "files": ["src/main.py", "tests/test_main.py"],
            "estimated_review_time": 30,
            "risk_level": "low",
        }

    @pytest.fixture
    def sample_pr_complex(self):
        """Create complex PR recommendation."""
        return {
            "id": "pr_2",
            "title": "Major feature implementation",
            "files": [
                "src/auth/login.py",
                "src/auth/logout.py",
                "src/models/user.py",
                "config/database.yaml",
                "migrations/001_add_user.sql",
                "tests/test_auth.py",
                "tests/test_user_model.py",
                "docs/auth_guide.md",
                "docker-compose.yml",
            ],
            "estimated_review_time": 120,
            "risk_level": "high",
        }

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool.logger is not None

    @pytest.mark.asyncio
    async def test_analyze_feasibility_simple_pr(self, tool, sample_pr_simple):
        """Test feasibility analysis for simple PR."""
        result = await tool.analyze_feasibility(sample_pr_simple)

        assert "feasible" in result
        assert result["feasible"] is True
        assert "risk_factors" in result
        assert "recommendations" in result
        assert "estimated_effort" in result
        assert result["estimated_effort"] == 30
        assert "complexity_breakdown" in result
        assert "dependency_analysis" in result
        assert "review_checklist" in result

    @pytest.mark.asyncio
    async def test_analyze_feasibility_complex_pr(self, tool, sample_pr_complex):
        """Test feasibility analysis for complex PR."""
        result = await tool.analyze_feasibility(sample_pr_complex)

        assert "feasible" in result
        # May be feasible or not depending on risk factors
        assert isinstance(result["feasible"], bool)
        assert len(result["risk_factors"]) > 0  # Should have some risk factors
        assert len(result["recommendations"]) > 0  # Should have recommendations

    @pytest.mark.asyncio
    async def test_analyze_feasibility_too_many_files(self, tool, mock_settings):
        """Test feasibility analysis with too many files."""
        mock_settings.max_files_per_pr = 5

        pr = {
            "files": [f"file_{i}.py" for i in range(10)],  # More than max
            "estimated_review_time": 60,
        }

        result = await tool.analyze_feasibility(pr)

        assert any("Large number of files" in factor for factor in result["risk_factors"])
        assert any("splitting into smaller PRs" in rec for rec in result["recommendations"])

    @pytest.mark.asyncio
    async def test_analyze_feasibility_mixed_file_types(self, tool):
        """Test feasibility analysis with mixed file types."""
        pr = {
            "files": [
                "src/app.py",  # source
                "config.json",  # config
                "README.md",  # docs
                "script.sh",  # other
            ],
            "estimated_review_time": 45,
        }

        result = await tool.analyze_feasibility(pr)

        assert any("Mixed file types" in factor for factor in result["risk_factors"])
        assert any("separating by file type" in rec for rec in result["recommendations"])

    @pytest.mark.asyncio
    async def test_analyze_feasibility_exception_handling(self, tool):
        """Test feasibility analysis exception handling."""
        # Pass invalid PR data to trigger exception
        pr = None

        result = await tool.analyze_feasibility(pr)

        assert "error" in result
        assert "Feasibility analysis failed" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_feasibility_high_risk_factors(self, tool):
        """Test feasibility analysis with many risk factors."""
        pr = {
            "files": [
                "migrations/001_schema.sql",  # critical
                "config/production.env",  # critical
                "deploy/docker-compose.yml",  # critical
                "src/large_file.json",  # potentially large
            ],
            "estimated_review_time": 90,
        }

        result = await tool.analyze_feasibility(pr)

        # Should be marked as not feasible due to many risk factors
        if len(result["risk_factors"]) > 2:
            assert result["feasible"] is False

    def test_categorize_files_source_code(self, tool):
        """Test file categorization for source code."""
        files = ["src/main.py", "app.js", "Utils.java", "service.cpp"]

        result = tool._categorize_files(files)

        assert "source" in result["file_types"]
        assert result["type_diversity"] == 1
        assert len(result["extensions"]) == 4

    def test_categorize_files_mixed_types(self, tool):
        """Test file categorization for mixed types."""
        files = [
            "src/main.py",  # source
            "README.md",  # docs
            "config.json",  # config
            "tests/test_file",  # test (no extension, so checks path)
            "data.csv",  # other
        ]

        result = tool._categorize_files(files)

        expected_types = {"source", "docs", "config", "test", "other"}
        assert set(result["file_types"]) == expected_types
        assert result["type_diversity"] == 5

    def test_categorize_files_by_directory(self, tool):
        """Test file categorization by directory."""
        files = [
            "src/app.py",
            "src/utils.py",
            "tests/test_app.py",
            "config/settings.yaml",
        ]

        result = tool._categorize_files(files)

        assert result["directory_count"] == 3
        assert "src" in result["directories"]
        assert "tests" in result["directories"]
        assert "config" in result["directories"]

    def test_categorize_files_extensions(self, tool):
        """Test file categorization by extension."""
        files = [
            "script.py",
            "config.json",
            "README.md",
            "data.csv",
            "Makefile",  # no extension
        ]

        result = tool._categorize_files(files)

        extensions = set(result["extensions"])
        assert ".py" in extensions
        assert ".json" in extensions
        assert ".md" in extensions
        assert ".csv" in extensions
        # Files without extensions don't add to the set

    def test_analyze_complexity_simple(self, tool):
        """Test complexity analysis for simple case."""
        files = ["main.py", "utils.py"]

        result = tool._analyze_complexity(files)

        assert result["file_count"] == 2
        assert result["estimated_review_time_per_file"] == 10
        assert result["complexity_score"] <= 10
        assert isinstance(result["complexity_factors"], list)

    def test_analyze_complexity_high(self, tool):
        """Test complexity analysis for high complexity."""
        files = [f"dir{i}/file{j}.py" for i in range(5) for j in range(3)]  # 15 files across 5 directories

        result = tool._analyze_complexity(files)

        assert result["file_count"] == 15
        assert result["complexity_score"] == 10  # capped at 10

        factors = [f for f in result["complexity_factors"] if f is not None]
        assert "File count" in factors
        assert "Multiple directories" in factors

    def test_analyze_complexity_mixed_extensions(self, tool):
        """Test complexity analysis with many file types."""
        files = ["file.py", "file.js", "file.cpp", "file.java", "file.go"]

        result = tool._analyze_complexity(files)

        factors = [f for f in result["complexity_factors"] if f is not None]
        assert "Mixed file types" in factors

    def test_analyze_dependencies_basic(self, tool):
        """Test basic dependency analysis."""
        files = ["src/app.py", "tests/test_app.py"]

        result = tool._analyze_dependencies(files)

        assert result["has_migration"] is False
        assert result["has_model"] is False
        assert result["has_test"] is True
        assert result["has_config"] is False
        assert isinstance(result["dependency_concerns"], list)

    def test_analyze_dependencies_migration_model(self, tool):
        """Test dependency analysis with migration and model."""
        files = ["migrations/001_add_user.sql", "models/user.py"]

        result = tool._analyze_dependencies(files)

        assert result["has_migration"] is True
        assert result["has_model"] is True

        concerns = [c for c in result["dependency_concerns"] if c is not None]
        assert any("Migration with model changes" in c for c in concerns)

    def test_analyze_dependencies_config_without_tests(self, tool):
        """Test dependency analysis with config but no tests."""
        files = ["config.yaml", "settings.json"]

        result = tool._analyze_dependencies(files)

        assert result["has_config"] is True
        assert result["has_test"] is False

        concerns = [c for c in result["dependency_concerns"] if c is not None]
        assert any("Config changes without tests" in c for c in concerns)

    def test_analyze_dependencies_model_without_tests(self, tool):
        """Test dependency analysis with model but no tests."""
        files = ["models/user.py", "models/post.py"]

        result = tool._analyze_dependencies(files)

        assert result["has_model"] is True
        assert result["has_test"] is False

        concerns = [c for c in result["dependency_concerns"] if c is not None]
        assert any("Model changes without tests" in c for c in concerns)

    def test_check_risk_patterns_critical_files(self, tool):
        """Test risk pattern checking for critical files."""
        files = [
            "migrations/schema_update.sql",
            "config/production.env",
            "docker/Dockerfile",
            "deploy/kubernetes.yaml",
        ]

        result = tool._check_risk_patterns(files)

        assert len(result["factors"]) > 0
        assert any("Critical files present" in factor for factor in result["factors"])
        assert any("Extra review needed" in rec for rec in result["recommendations"])

    def test_check_risk_patterns_large_files(self, tool):
        """Test risk pattern checking for potentially large files."""
        files = [
            "data/large_dataset.sql",
            "package-lock.json",
            "config/large_config.json",
        ]

        result = tool._check_risk_patterns(files)

        assert any("large changes" in factor for factor in result["factors"])
        assert any("Verify file sizes" in rec for rec in result["recommendations"])

    def test_check_risk_patterns_no_risks(self, tool):
        """Test risk pattern checking with no risk patterns."""
        files = ["src/simple.py", "tests/test_simple.py"]

        result = tool._check_risk_patterns(files)

        assert len(result["factors"]) == 0
        assert len(result["recommendations"]) == 0

    def test_generate_review_checklist_basic(self, tool):
        """Test basic review checklist generation."""
        pr = {"files": ["src/app.py"], "risk_level": "low"}

        checklist = tool._generate_review_checklist(pr)

        basic_items = [
            "Code follows team style guidelines",
            "All new code has appropriate tests",
            "Documentation is updated if needed",
            "No sensitive information is exposed",
        ]

        for item in basic_items:
            assert item in checklist

    def test_generate_review_checklist_with_tests(self, tool):
        """Test review checklist generation with tests."""
        pr = {"files": ["src/app.py", "tests/test_app.py"], "risk_level": "low"}

        checklist = tool._generate_review_checklist(pr)

        assert "Test coverage is adequate" in checklist

    def test_generate_review_checklist_with_config(self, tool):
        """Test review checklist generation with config files."""
        pr = {"files": ["config.yaml", "settings.json"], "risk_level": "medium"}

        checklist = tool._generate_review_checklist(pr)

        assert "Configuration changes are validated" in checklist

    def test_generate_review_checklist_with_migration(self, tool):
        """Test review checklist generation with migrations."""
        pr = {"files": ["migrations/001_add_table.sql"], "risk_level": "medium"}

        checklist = tool._generate_review_checklist(pr)

        assert "Database migration is reversible" in checklist
        assert "Migration has been tested on staging" in checklist

    def test_generate_review_checklist_high_risk(self, tool):
        """Test review checklist generation for high risk PR."""
        pr = {"files": ["src/critical.py"], "risk_level": "high"}

        checklist = tool._generate_review_checklist(pr)

        assert "Extra review by senior team member" in checklist
        assert "Consider feature flag for gradual rollout" in checklist

    def test_generate_review_checklist_comprehensive(self, tool):
        """Test review checklist generation with all features."""
        pr = {
            "files": [
                "src/app.py",
                "tests/test_app.py",
                "config.yaml",
                "migrations/schema.sql",
            ],
            "risk_level": "high",
        }

        checklist = tool._generate_review_checklist(pr)

        # Should include all specialized checks
        assert "Test coverage is adequate" in checklist
        assert "Configuration changes are validated" in checklist
        assert "Database migration is reversible" in checklist
        assert "Extra review by senior team member" in checklist

    @pytest.mark.asyncio
    async def test_analyze_feasibility_edge_cases(self, tool):
        """Test feasibility analysis edge cases."""
        # Empty files list
        pr_empty = {"files": [], "estimated_review_time": 0}
        result = await tool.analyze_feasibility(pr_empty)
        assert result["feasible"] is True

        # Missing estimated_review_time
        pr_no_time = {"files": ["file.py"]}
        result = await tool.analyze_feasibility(pr_no_time)
        assert result["estimated_effort"] == 0

    @pytest.mark.asyncio
    async def test_analyze_feasibility_integration(self, tool):
        """Test full integration of feasibility analysis."""
        pr = {
            "id": "integration_test",
            "title": "Complex feature with migration",
            "files": [
                "src/auth/models.py",
                "src/auth/views.py",
                "migrations/002_auth_tables.sql",
                "tests/test_auth.py",
                "config/auth_settings.yaml",
                "docs/auth.md",
            ],
            "estimated_review_time": 75,
            "risk_level": "medium",
        }

        result = await tool.analyze_feasibility(pr)

        # Verify all components are present
        assert "feasible" in result
        assert "risk_factors" in result
        assert "recommendations" in result
        assert "complexity_breakdown" in result
        assert "dependency_analysis" in result
        assert "review_checklist" in result

        # Check complexity breakdown
        complexity = result["complexity_breakdown"]
        assert complexity["file_count"] == 6
        assert "complexity_score" in complexity

        # Check dependency analysis
        deps = result["dependency_analysis"]
        assert deps["has_migration"] is True
        assert deps["has_model"] is True
        assert deps["has_test"] is True
        assert deps["has_config"] is True

        # Should have migration concern
        concerns = [c for c in deps["dependency_concerns"] if c is not None]
        assert any("Migration with model" in c for c in concerns)

        # Check review checklist includes relevant items
        checklist = result["review_checklist"]
        assert "Test coverage is adequate" in checklist
        assert "Configuration changes are validated" in checklist
        assert "Database migration is reversible" in checklist

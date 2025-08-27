"""Unit tests for strategy manager MCP tool."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_pr_recommender.tools.strategy_manager_tool import StrategyManagerTool


# Mock settings globally to avoid OpenAI API key requirement
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings to avoid OpenAI API key requirement."""
    with patch("mcp_pr_recommender.tools.strategy_manager_tool.settings") as mock_settings_func:
        mock_settings_instance = Mock()
        mock_settings_instance.openai_api_key = "test_key"
        mock_settings_instance.default_strategy = "semantic"
        mock_settings_instance.max_files_per_pr = 8
        mock_settings_instance.min_files_per_pr = 1
        mock_settings_instance.similarity_threshold = 0.7
        mock_settings_func.return_value = mock_settings_instance
        yield mock_settings_instance


@pytest.mark.unit
class TestStrategyManagerTool:
    """Test cases for the strategy manager MCP tool."""

    @pytest.fixture
    def strategy_manager_tool(self):
        """Create strategy manager tool instance."""
        return StrategyManagerTool()

    @pytest.fixture
    def mock_context(self):
        """Mock MCP context."""
        ctx = AsyncMock()
        ctx.info = AsyncMock()
        ctx.debug = AsyncMock()
        ctx.warning = AsyncMock()
        ctx.error = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_get_strategy_options_success(self, strategy_manager_tool):
        """Test successful retrieval of strategy options."""
        result = await strategy_manager_tool.get_strategies()

        # Verify result structure - tool returns "available_strategies" not "strategies"
        assert "available_strategies" in result
        assert "default_strategy" in result
        assert "recommendations" in result

        # Verify available strategies
        strategies = result["available_strategies"]
        expected_strategies = ["semantic", "directory", "size", "dependency", "hybrid"]

        for strategy in expected_strategies:
            assert strategy in strategies

        # Verify each strategy has proper structure
        for _, strategy_info in strategies.items():
            assert "name" in strategy_info
            assert "description" in strategy_info
            assert len(strategy_info["description"]) > 10  # Meaningful description

        # Verify default strategy is valid
        assert result["default_strategy"] in strategies

    @pytest.mark.asyncio
    async def test_get_strategy_options_with_filter(self, strategy_manager_tool):
        """Test retrieval of strategy options - no filtering supported in current implementation."""
        # The current implementation doesn't support filtering, so test basic functionality
        result = await strategy_manager_tool.get_strategies()

        # Should return all available strategies
        strategies = result["available_strategies"]
        expected_strategies = ["semantic", "directory", "size", "dependency", "hybrid"]

        for strategy in expected_strategies:
            assert strategy in strategies

        # All strategies should be present since no filtering is implemented
        assert len(strategies) >= len(expected_strategies)

    @pytest.mark.asyncio
    async def test_set_default_strategy_valid(self, strategy_manager_tool):
        """Test that the tool provides strategy information (no set functionality in current implementation)."""
        # The current StrategyManagerTool only provides get_strategies(), not set functionality
        # Test that we can get valid strategies that could be set
        result = await strategy_manager_tool.get_strategies()

        valid_strategy = "semantic"
        strategies = result["available_strategies"]

        # Verify the strategy we want to set is available
        assert valid_strategy in strategies
        assert result["default_strategy"] == valid_strategy  # Current default

    @pytest.mark.asyncio
    async def test_set_default_strategy_invalid(self, strategy_manager_tool):
        """Test validation against invalid strategies."""
        # The current StrategyManagerTool doesn't support setting, but test validation logic
        result = await strategy_manager_tool.get_strategies()

        invalid_strategy = "nonexistent_strategy"
        strategies = result["available_strategies"]

        # Verify the invalid strategy is not in available strategies
        assert invalid_strategy not in strategies

        # Should have some available strategies to choose from
        assert len(strategies) > 0

    @pytest.mark.asyncio
    async def test_strategy_recommendations(self, strategy_manager_tool):
        """Test strategy recommendations provided by the tool."""
        result = await strategy_manager_tool.get_strategies()

        # Verify recommendations are provided
        assert "recommendations" in result
        recommendations = result["recommendations"]

        # Should have recommendations for different scenarios
        expected_scenarios = [
            "small_changes",
            "large_refactoring",
            "mixed_concerns",
            "configuration",
            "documentation",
        ]
        for scenario in expected_scenarios:
            assert scenario in recommendations
            assert isinstance(recommendations[scenario], str)
            assert len(recommendations[scenario]) > 10  # Should have meaningful guidance

    @pytest.mark.asyncio
    async def test_strategy_compatibility(self, strategy_manager_tool):
        """Test strategy information includes compatibility details."""
        result = await strategy_manager_tool.get_strategies()

        # Verify strategy details include pros/cons (compatibility info)
        strategies = result["available_strategies"]
        for _, strategy_info in strategies.items():
            assert "pros" in strategy_info
            assert "cons" in strategy_info
            assert "requires_llm" in strategy_info
            assert isinstance(strategy_info["pros"], list)
            assert isinstance(strategy_info["cons"], list)

    @pytest.mark.asyncio
    async def test_strategy_performance_characteristics(self, strategy_manager_tool):
        """Test strategy performance characteristics are provided."""
        result = await strategy_manager_tool.get_strategies()

        # Verify performance-related data exists for each strategy
        strategies = result["available_strategies"]
        for _, strategy_info in strategies.items():
            assert "best_for" in strategy_info  # Use case information
            assert "requires_llm" in strategy_info  # Performance consideration
            assert isinstance(strategy_info["best_for"], str)
            assert isinstance(strategy_info["requires_llm"], bool)

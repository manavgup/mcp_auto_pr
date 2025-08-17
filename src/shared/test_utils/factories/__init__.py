"""Test data factories for the MCP ecosystem (moved to test_utils).

This package provides modular, atomic factories for creating realistic test data.
Each factory module focuses on a specific domain (git, analysis, recommendations, etc.)
making them easy to maintain and extend.

Usage:
    from mcp_shared_lib.test_utils.factories import FileChangeFactory, create_file_changes
    from mcp_shared_lib.test_utils.factories.git import GitCommitFactory
    from mcp_shared_lib.test_utils.factories.analysis import AnalysisResultFactory
"""

from .analysis import AnalysisResultFactory, RiskAssessmentFactory

# Import all factories for easy access
from .base import BaseFactory, Faker
from .files import FileChangeFactory, create_file_changes
from .git import GitBranchFactory, GitCommitFactory, GitRepositoryStateFactory
from .recommendations import PRRecommendationFactory, create_pr_recommendation_set
from .scenarios import TestScenarioFactory, create_repository_with_realistic_state
from .tools import MCPClientFactory, MCPServerFactory, MCPToolResultFactory

# Convenience imports for most common use cases
__all__ = [
    # Base classes
    "BaseFactory",
    "Faker",
    # Git factories
    "GitCommitFactory",
    "GitBranchFactory",
    "GitRepositoryStateFactory",
    # File factories
    "FileChangeFactory",
    "create_file_changes",
    # Analysis factories
    "AnalysisResultFactory",
    "RiskAssessmentFactory",
    # Recommendation factories
    "PRRecommendationFactory",
    "create_pr_recommendation_set",
    # Scenario factories
    "TestScenarioFactory",
    "create_repository_with_realistic_state",
    # Tool factories
    "MCPToolResultFactory",
    "MCPServerFactory",
    "MCPClientFactory",
]

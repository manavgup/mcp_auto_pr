#!/usr/bin/env python3
"""CI/CD validation tests to ensure our infrastructure works correctly."""

import pytest


class TestCIValidation:
    """Tests to validate CI/CD infrastructure."""

    @pytest.mark.unit
    def test_imports_work(self) -> None:
        """Test that core imports work correctly."""
        # Test shared imports
        from mcp_local_repo_analyzer.models.files import FileStatus
        from mcp_local_repo_analyzer.services.client import GitClient
        from shared.base.tool import BaseMCPTool

        assert FileStatus is not None
        assert GitClient is not None
        assert BaseMCPTool is not None

    @pytest.mark.unit
    def test_server_imports_work(self) -> None:
        """Test that server imports work correctly."""
        from mcp_local_repo_analyzer.server import LocalRepoAnalyzerServer
        from mcp_pr_recommender.server import PRRecommenderServer

        assert LocalRepoAnalyzerServer is not None
        assert PRRecommenderServer is not None

    @pytest.mark.unit
    def test_server_inheritance(self) -> None:
        """Test that servers properly inherit from BaseMCPServer."""
        from mcp_local_repo_analyzer.server import LocalRepoAnalyzerServer
        from mcp_pr_recommender.server import PRRecommenderServer
        from shared.base.server import BaseMCPServer

        assert issubclass(LocalRepoAnalyzerServer, BaseMCPServer)
        assert issubclass(PRRecommenderServer, BaseMCPServer)

    @pytest.mark.unit
    def test_fastmcp_available(self) -> None:
        """Test that FastMCP is available and importable."""
        import fastmcp

        assert fastmcp is not None

    @pytest.mark.unit
    def test_dependencies_available(self) -> None:
        """Test that all required dependencies are available."""
        import git  # gitpython is imported as 'git'
        import httpx
        import pydantic
        import uvicorn
        import yaml

        assert git is not None
        assert pydantic is not None
        assert uvicorn is not None
        assert httpx is not None
        assert yaml is not None

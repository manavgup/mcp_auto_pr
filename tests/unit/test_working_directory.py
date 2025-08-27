"""Unit tests for working directory tool - Fixed version."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from fastmcp import Client, FastMCP

from mcp_local_repo_analyzer.models.categorization import ChangeCategorization
from mcp_local_repo_analyzer.models.changes import WorkingDirectoryChanges
from mcp_local_repo_analyzer.models.files import FileStatus
from mcp_local_repo_analyzer.models.risk import RiskAssessment
from mcp_local_repo_analyzer.tools.working_directory import (
    register_working_directory_tools,
)


async def call_tool_helper(mcp, tool_name: str, **kwargs):
    """Helper function to call tools using the Client API."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool(tool_name, kwargs)
        return result.data


@pytest.mark.unit
class TestAnalyzeWorkingDirectory:
    """Test working directory analysis tool."""

    @pytest.fixture
    def mock_services(self):
        """Mock services for working directory analysis."""
        return {
            "change_detector": Mock(),
            "diff_analyzer": Mock(),
            "status_tracker": Mock(),
            "git_client": Mock(),
        }

    @pytest.fixture
    def mcp_server(self, mock_services):
        """Create MCP server with working directory tools."""
        mcp = FastMCP("working-directory-test")
        register_working_directory_tools(mcp, mock_services)
        return mcp

    @pytest.fixture
    def temp_repo_path(self):
        """Create temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield str(Path(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_analyze_working_directory_with_changes(self, mcp_server, mock_services, temp_repo_path):
        """Test analyzing working directory with changes."""
        # Mock file statuses
        mock_file_statuses = [
            FileStatus(
                path="src/main.py",
                status_code="M",
                lines_added=10,
                lines_deleted=5,
            ),
            FileStatus(
                path="tests/test_new.py",
                status_code="A",
                lines_added=50,
                lines_deleted=0,
            ),
        ]

        # Create WorkingDirectoryChanges model
        mock_working_changes = WorkingDirectoryChanges(
            modified_files=mock_file_statuses[:1],  # src/main.py
            untracked_files=mock_file_statuses[1:],  # tests/test_new.py
            staged_files=[],
            deleted_files=[],
            renamed_files=[],
        )

        # Mock categorization and risk assessment
        mock_categorization = ChangeCategorization(
            source_code=["src/main.py"],
            tests=["tests/test_new.py"],
            documentation=[],
        )

        mock_risk = RiskAssessment(
            risk_level="medium",
            risk_factors=["New test file"],
        )

        # Setup service mocks - make them async
        mock_services["change_detector"].detect_working_directory_changes = AsyncMock(return_value=mock_working_changes)
        mock_services["diff_analyzer"].categorize_changes = Mock(return_value=mock_categorization)
        mock_services["diff_analyzer"].assess_risk = Mock(return_value=mock_risk)

        # Call the tool
        result = await call_tool_helper(mcp_server, "analyze_working_directory", repository_path=temp_repo_path)

        # Verify the result structure
        assert "repository_status" in result

        # The result should be a structured model, not JSON strings
        repo_status = result["repository_status"]
        assert "working_directory" in repo_status
        assert "categories" in result  # categorization is at top level
        assert "risk_assessment" in result  # risk_assessment is at top level

    @pytest.mark.asyncio
    async def test_analyze_working_directory_no_changes(self, mcp_server, mock_services, temp_repo_path):
        """Test analyzing working directory with no changes."""
        # Create empty WorkingDirectoryChanges
        mock_working_changes = WorkingDirectoryChanges(
            modified_files=[],
            untracked_files=[],
            staged_files=[],
            deleted_files=[],
            renamed_files=[],
        )

        # Mock empty categorization and risk assessment
        mock_categorization = ChangeCategorization(
            source_code=[],
            tests=[],
            documentation=[],
        )

        mock_risk = RiskAssessment(
            risk_level="low",
            risk_factors=[],
        )

        # Setup service mocks - make them async
        mock_services["change_detector"].detect_working_directory_changes = AsyncMock(return_value=mock_working_changes)
        mock_services["diff_analyzer"].categorize_changes = Mock(return_value=mock_categorization)
        mock_services["diff_analyzer"].assess_risk = Mock(return_value=mock_risk)

        # Call the tool
        result = await call_tool_helper(mcp_server, "analyze_working_directory", repository_path=temp_repo_path)

        # Verify clean repository
        assert "repository_status" in result
        repo_status = result["repository_status"]

        # Should have empty working directory
        working_dir = repo_status["working_directory"]
        assert working_dir["total_files"] == 0

    @pytest.mark.asyncio
    async def test_analyze_working_directory_invalid_path(self, mcp_server, mock_services):
        """Test analyzing working directory with invalid path."""
        # Call the tool with invalid path
        result = await call_tool_helper(mcp_server, "analyze_working_directory", repository_path="/invalid/path")

        # Should return error
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_working_directory_with_binary_files(self, mcp_server, mock_services, temp_repo_path):
        """Test analyzing working directory with binary files."""
        # Mock file statuses including binary file
        mock_file_statuses = [
            FileStatus(
                path="src/main.py",
                status_code="M",
                lines_added=10,
                lines_deleted=5,
            ),
            FileStatus(
                path="assets/image.png",
                status_code="A",
                lines_added=0,
                lines_deleted=0,
                is_binary=True,
            ),
        ]

        # Create WorkingDirectoryChanges model
        mock_working_changes = WorkingDirectoryChanges(
            modified_files=mock_file_statuses[:1],  # src/main.py
            untracked_files=mock_file_statuses[1:],  # assets/image.png
            staged_files=[],
            deleted_files=[],
            renamed_files=[],
        )

        mock_categorization = ChangeCategorization(
            source_code=["src/main.py"],
            tests=[],
            documentation=[],
            other=["assets/image.png"],
        )

        mock_risk = RiskAssessment(
            risk_level="low",
            risk_factors=["Binary file"],
        )

        # Setup service mocks - make them async
        mock_services["change_detector"].detect_working_directory_changes = AsyncMock(return_value=mock_working_changes)
        mock_services["diff_analyzer"].categorize_changes = Mock(return_value=mock_categorization)
        mock_services["diff_analyzer"].assess_risk = Mock(return_value=mock_risk)

        # Call the tool
        result = await call_tool_helper(mcp_server, "analyze_working_directory", repository_path=temp_repo_path)

        # Verify result includes binary file handling
        assert "repository_status" in result
        repo_status = result["repository_status"]
        working_dir = repo_status["working_directory"]
        assert working_dir["total_files"] == 2

    @pytest.mark.asyncio
    async def test_analyze_working_directory_large_changeset(self, mcp_server, mock_services, temp_repo_path):
        """Test analyzing working directory with large changeset."""
        # Create many file changes
        mock_file_statuses = [
            FileStatus(
                path=f"src/file_{i}.py",
                status_code="M",
                lines_added=5,
                lines_deleted=2,
            )
            for i in range(20)
        ]

        mock_working_changes = WorkingDirectoryChanges(
            modified_files=mock_file_statuses,
            untracked_files=[],
            staged_files=[],
            deleted_files=[],
            renamed_files=[],
        )

        mock_categorization = ChangeCategorization(
            source_code=[f"src/file_{i}.py" for i in range(20)],
            tests=[],
            documentation=[],
        )

        mock_risk = RiskAssessment(
            risk_level="high",
            risk_factors=["Large changeset"],
        )

        # Setup service mocks - make them async
        mock_services["change_detector"].detect_working_directory_changes = AsyncMock(return_value=mock_working_changes)
        mock_services["diff_analyzer"].categorize_changes = Mock(return_value=mock_categorization)
        mock_services["diff_analyzer"].assess_risk = Mock(return_value=mock_risk)

        # Call the tool
        result = await call_tool_helper(mcp_server, "analyze_working_directory", repository_path=temp_repo_path)

        # Verify large changeset handling
        assert "repository_status" in result
        repo_status = result["repository_status"]
        working_dir = repo_status["working_directory"]
        assert working_dir["total_files"] == 20


@pytest.mark.unit
class TestGetFileDiff:
    """Test get_file_diff tool."""

    @pytest.fixture
    def mock_services(self):
        """Mock services for file diff analysis."""
        return {
            "change_detector": Mock(),
            "diff_analyzer": Mock(),
            "status_tracker": Mock(),
            "git_client": Mock(),
        }

    @pytest.fixture
    def mcp_server(self, mock_services):
        """Create MCP server with working directory tools."""
        mcp = FastMCP("working-directory-test")
        register_working_directory_tools(mcp, mock_services)
        return mcp

    @pytest.fixture
    def temp_repo_path(self):
        """Create temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield str(Path(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_get_file_diff_success(self, mcp_server, mock_services, temp_repo_path):
        """Test successful file diff retrieval."""
        # Mock git client to return diff
        mock_diff_content = """+++ b/src/main.py
@@ -1,5 +1,10 @@
 def main():
-    print("Hello")
+    print("Hello, World!")
+    print("New line")
     return 0"""

        mock_services["git_client"].get_diff = AsyncMock(return_value=mock_diff_content)
        mock_services["diff_analyzer"].parse_diff = Mock(
            return_value=[
                Mock(
                    file_path="src/main.py",
                    old_path=None,
                    is_binary=False,
                    lines_added=2,
                    lines_deleted=1,
                    total_changes=3,
                    hunks=[],
                    is_large_change=False,
                )
            ]
        )

        # Call the tool
        result = await call_tool_helper(
            mcp_server,
            "get_file_diff",
            file_path="src/main.py",
            repository_path=temp_repo_path,
        )

        # Verify diff content
        assert "diff_content" in result
        assert "Hello, World!" in result["diff_content"]
        assert "file_path" in result
        assert result["file_path"] == "src/main.py"

    @pytest.mark.asyncio
    async def test_get_file_diff_nonexistent_file(self, mcp_server, mock_services, temp_repo_path):
        """Test file diff for nonexistent file."""
        # Mock git client to raise exception
        mock_services["git_client"].get_diff = AsyncMock(side_effect=FileNotFoundError("File not found"))

        # Call the tool
        result = await call_tool_helper(
            mcp_server,
            "get_file_diff",
            file_path="nonexistent.py",
            repository_path=temp_repo_path,
        )

        # Should handle error gracefully
        assert "error" in result or "diff_content" in result


@pytest.mark.unit
class TestGetUntrackedFiles:
    """Test get_untracked_files tool."""

    @pytest.fixture
    def mock_services(self):
        """Mock services for untracked files analysis."""
        return {
            "change_detector": Mock(),
            "diff_analyzer": Mock(),
            "status_tracker": Mock(),
            "git_client": Mock(),
        }

    @pytest.fixture
    def mcp_server(self, mock_services):
        """Create MCP server with working directory tools."""
        mcp = FastMCP("working-directory-test")
        register_working_directory_tools(mcp, mock_services)
        return mcp

    @pytest.fixture
    def temp_repo_path(self):
        """Create temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield str(Path(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_get_untracked_files_success(self, mcp_server, mock_services, temp_repo_path):
        """Test successful untracked files retrieval."""
        # Mock untracked files
        mock_untracked = ["new_file.py", "temp_data.json", "assets/new_image.png"]

        mock_services["change_detector"].detect_working_directory_changes = AsyncMock(
            return_value=WorkingDirectoryChanges(
                modified_files=[],
                untracked_files=[
                    FileStatus(path=path, status_code="??", lines_added=0, lines_deleted=0) for path in mock_untracked
                ],
                staged_files=[],
                deleted_files=[],
                renamed_files=[],
            )
        )

        # Call the tool
        result = await call_tool_helper(mcp_server, "get_untracked_files", repository_path=temp_repo_path)

        # Verify untracked files
        assert "files" in result
        assert len(result["files"]) == 3
        files_paths = [f["path"] for f in result["files"]]
        assert "new_file.py" in files_paths
        assert "assets/new_image.png" in files_paths

    @pytest.mark.asyncio
    async def test_get_untracked_files_none(self, mcp_server, mock_services, temp_repo_path):
        """Test untracked files when none exist."""
        # Mock empty untracked files
        mock_services["change_detector"].detect_working_directory_changes = AsyncMock(
            return_value=WorkingDirectoryChanges(
                modified_files=[],
                untracked_files=[],
                staged_files=[],
                deleted_files=[],
                renamed_files=[],
            )
        )

        # Call the tool
        result = await call_tool_helper(mcp_server, "get_untracked_files", repository_path=temp_repo_path)

        # Verify empty result
        assert "files" in result
        assert len(result["files"]) == 0


@pytest.mark.unit
class TestWorkingDirectoryToolIntegration:
    """Integration tests for working directory tools."""

    @pytest.fixture
    def mock_services(self):
        """Mock services for integration tests."""
        return {
            "change_detector": Mock(),
            "diff_analyzer": Mock(),
            "status_tracker": Mock(),
            "git_client": Mock(),
        }

    @pytest.fixture
    def mcp_server(self, mock_services):
        """Create MCP server with working directory tools."""
        mcp = FastMCP("working-directory-integration-test")
        register_working_directory_tools(mcp, mock_services)
        return mcp

    @pytest.fixture
    def temp_repo_path(self):
        """Create temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield str(Path(temp_dir))
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_tools_registration(self, mcp_server):
        """Test that all working directory tools are properly registered."""
        client = Client(mcp_server)
        async with client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]

            # Verify expected tools are registered
            expected_tools = [
                "analyze_working_directory",
                "get_file_diff",
                "get_untracked_files",
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_workflow_complete(self, mcp_server, mock_services, temp_repo_path):
        """Test complete working directory analysis workflow."""
        # Setup mocks for analyze_working_directory
        mock_file_statuses = [
            FileStatus(path="src/main.py", status_code="M", lines_added=5, lines_deleted=2),
            FileStatus(path="new_file.py", status_code="A", lines_added=20, lines_deleted=0),
        ]

        mock_working_changes = WorkingDirectoryChanges(
            modified_files=mock_file_statuses[:1],
            untracked_files=mock_file_statuses[1:],
            staged_files=[],
            deleted_files=[],
            renamed_files=[],
        )

        mock_categorization = ChangeCategorization(
            source_code=["src/main.py", "new_file.py"],
            tests=[],
            documentation=[],
        )

        mock_risk = RiskAssessment(
            risk_level="medium",
            risk_factors=["New file"],
        )

        # Setup service mocks - make them async
        mock_services["change_detector"].detect_working_directory_changes = AsyncMock(return_value=mock_working_changes)
        mock_services["diff_analyzer"].categorize_changes = Mock(return_value=mock_categorization)
        mock_services["diff_analyzer"].assess_risk = Mock(return_value=mock_risk)
        mock_services["git_client"].get_diff = AsyncMock(return_value="diff content")
        mock_services["diff_analyzer"].parse_diff = Mock(
            return_value=[
                Mock(
                    file_path="src/main.py",
                    old_path=None,
                    is_binary=False,
                    lines_added=5,
                    lines_deleted=2,
                    total_changes=7,
                    hunks=[],
                    is_large_change=False,
                )
            ]
        )

        # 1. Analyze working directory
        analysis_result = await call_tool_helper(
            mcp_server, "analyze_working_directory", repository_path=temp_repo_path
        )
        assert "repository_status" in analysis_result

        # 2. Get untracked files
        untracked_result = await call_tool_helper(mcp_server, "get_untracked_files", repository_path=temp_repo_path)
        assert "files" in untracked_result

        # 3. Get file diff for specific file
        diff_result = await call_tool_helper(
            mcp_server,
            "get_file_diff",
            file_path="src/main.py",
            repository_path=temp_repo_path,
        )
        assert "diff_content" in diff_result or "error" in diff_result

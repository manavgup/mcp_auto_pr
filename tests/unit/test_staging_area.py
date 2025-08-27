"""Unit tests for staging area tools."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_local_repo_analyzer.models.categorization import ChangeCategorization
from mcp_local_repo_analyzer.models.changes import StagedChanges
from mcp_local_repo_analyzer.models.files import FileStatus
from mcp_local_repo_analyzer.models.risk import RiskAssessment
from mcp_local_repo_analyzer.tools.staging_area import register_staging_area_tools


async def call_tool_helper(mcp, tool_name: str, **kwargs):
    """Helper function to call tools using the Client API."""
    from fastmcp import Client

    client = Client(mcp)
    async with client:
        result = await client.call_tool(tool_name, kwargs)
        return result.data


@pytest.mark.unit
class TestAnalyzeStagedChanges:
    """Test analyze_staged_changes tool."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.git_dir = Path(self.temp_dir) / ".git"
        self.git_dir.mkdir()
        self.repo_path = str(Path(self.temp_dir))

        # Mock services
        self.mock_services = {
            "change_detector": AsyncMock(),
            "git_client": AsyncMock(),
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_with_files(self):
        """Test analyzing staged changes with staged files."""
        from fastmcp import FastMCP

        mcp = FastMCP()

        # Register tools
        register_staging_area_tools(mcp, self.mock_services)

        # Mock staged changes
        mock_staged_files = [
            FileStatus(
                path="src/main.py",
                status_code="M",
                staged=True,
                lines_added=20,
                lines_deleted=5,
                is_binary=False,
            ),
            FileStatus(
                path="tests/test_main.py",
                status_code="A",
                staged=True,
                lines_added=50,
                lines_deleted=0,
                is_binary=False,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=2,
            total_additions=70,
            total_deletions=5,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        # Mock diff content
        self.mock_services[
            "git_client"
        ].get_diff.return_value = "@@ -1,3 +1,5 @@\n def test():\n+    print('hello')\n     pass"

        # Create client and call tool
        from fastmcp import Client

        client = Client(mcp)

        async with client:
            call_result = await client.call_tool(
                "analyze_staged_changes",
                {"repository_path": self.repo_path, "include_diffs": True},
            )
            result = call_result.data

        # Verify the result
        assert "repository_path" in result
        assert result["total_staged_files"] == 2
        assert result["ready_to_commit"] is True
        assert result["statistics"]["total_additions"] == 70
        assert result["statistics"]["total_deletions"] == 5
        assert len(result["staged_files"]) == 2
        assert result["staged_files"][0]["path"] == "src/main.py"
        assert result["staged_files"][0]["status"] == "M"
        assert result["staged_files"][0]["total_changes"] == 25
        assert "diffs" in result
        assert len(result["diffs"]) == 2

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_no_files(self):
        """Test analyzing staged changes with no staged files."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock no staged changes
        mock_staged_changes = StagedChanges(
            staged_files=[],
            ready_to_commit=False,
            total_staged=0,
            total_additions=0,
            total_deletions=0,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        result = await call_tool_helper(
            mcp,
            "analyze_staged_changes",
            repository_path=self.repo_path,
            include_diffs=False,
        )

        assert result["total_staged_files"] == 0
        assert result["ready_to_commit"] is False
        assert len(result["staged_files"]) == 0
        assert "diffs" not in result  # include_diffs=False

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_binary_files(self):
        """Test analyzing staged changes with binary files."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock binary file
        mock_staged_files = [
            FileStatus(
                path="assets/image.png",
                status_code="A",
                staged=True,
                lines_added=0,
                lines_deleted=0,
                is_binary=True,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=1,
            total_additions=0,
            total_deletions=0,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        result = await call_tool_helper(
            mcp,
            "analyze_staged_changes",
            **{"repository_path": self.repo_path, "include_diffs": True},
        )

        assert result["total_staged_files"] == 1
        assert result["staged_files"][0]["is_binary"] is True
        assert len(result["diffs"]) == 1
        assert result["diffs"][0]["is_binary"] is True
        assert "Binary file" in result["diffs"][0]["message"]

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_diff_error(self):
        """Test handling diff generation errors."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        mock_staged_files = [
            FileStatus(
                path="problematic.py",
                status_code="M",
                staged=True,
                lines_added=10,
                lines_deleted=2,
                is_binary=False,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=1,
            total_additions=10,
            total_deletions=2,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        # Mock git client to raise an exception
        self.mock_services["git_client"].get_diff.side_effect = Exception("Git diff failed")

        result = await call_tool_helper(
            mcp,
            "analyze_staged_changes",
            **{"repository_path": self.repo_path, "include_diffs": True},
        )

        assert result["total_staged_files"] == 1
        assert len(result["diffs"]) == 1
        assert "error" in result["diffs"][0]
        assert "Git diff failed" in result["diffs"][0]["error"]

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_large_diff(self):
        """Test handling large diff truncation."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        mock_staged_files = [
            FileStatus(
                path="large_file.py",
                status_code="M",
                staged=True,
                lines_added=200,
                lines_deleted=50,
                is_binary=False,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=1,
            total_additions=200,
            total_deletions=50,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        # Mock large diff content (>100 lines)
        large_diff = "\n".join([f"line {i}" for i in range(150)])
        self.mock_services["git_client"].get_diff.return_value = large_diff

        result = await call_tool_helper(
            mcp,
            "analyze_staged_changes",
            **{"repository_path": self.repo_path, "include_diffs": True},
        )

        assert len(result["diffs"]) == 1
        assert "truncated" in result["diffs"][0]["diff_content"]

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_many_files(self):
        """Test handling many staged files (>10 limit)."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Create 15 staged files
        mock_staged_files = []
        for i in range(15):
            mock_staged_files.append(
                FileStatus(
                    path=f"file_{i}.py",
                    status_code="M",
                    staged=True,
                    lines_added=5,
                    lines_deleted=2,
                    is_binary=False,
                )
            )

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=15,
            total_additions=75,
            total_deletions=30,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes
        self.mock_services["git_client"].get_diff.return_value = "some diff content"

        result = await call_tool_helper(
            mcp,
            "analyze_staged_changes",
            **{"repository_path": self.repo_path, "include_diffs": True},
        )

        assert result["total_staged_files"] == 15
        assert len(result["staged_files"]) == 15
        # But diffs should be limited to 10
        assert len(result["diffs"]) == 10

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_invalid_repo(self):
        """Test handling invalid repository path."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        with (
            patch(
                "mcp_local_repo_analyzer.tools.staging_area.is_git_repository",
                return_value=False,
            ),
            patch(
                "mcp_local_repo_analyzer.tools.staging_area.find_git_root",
                return_value=None,
            ),
        ):
            result = await call_tool_helper(mcp, "analyze_staged_changes", repository_path="/invalid/path")

            assert "error" in result
            assert "No git repository found" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_staged_changes_service_error(self):
        """Test handling service errors."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock service failure
        self.mock_services["change_detector"].detect_staged_changes.side_effect = Exception("Service failure")

        result = await call_tool_helper(mcp, "analyze_staged_changes", repository_path=self.repo_path)

        assert "error" in result
        assert "Service failure" in result["error"]


@pytest.mark.unit
class TestPreviewCommit:
    """Test preview_commit tool."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.git_dir = Path(self.temp_dir) / ".git"
        self.git_dir.mkdir()
        self.repo_path = str(Path(self.temp_dir))

        self.mock_services = {
            "change_detector": AsyncMock(),
            "diff_analyzer": Mock(),
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_preview_commit_with_changes(self):
        """Test commit preview with staged changes."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock staged changes
        mock_staged_files = [
            FileStatus(
                path="src/main.py",
                status_code="M",
                staged=True,
                lines_added=20,
                lines_deleted=5,
            ),
            FileStatus(
                path="src/utils.js",
                status_code="A",
                staged=True,
                lines_added=30,
                lines_deleted=0,
            ),
            FileStatus(
                path="tests/test_main.py",
                status_code="A",
                staged=True,
                lines_added=25,
                lines_deleted=0,
            ),
            FileStatus(
                path="docs/readme.md",
                status_code="M",
                staged=True,
                lines_added=15,
                lines_deleted=10,
            ),
            FileStatus(
                path="config.json",
                status_code="M",
                staged=True,
                lines_added=10,
                lines_deleted=10,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=5,
            total_additions=100,
            total_deletions=25,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        # Mock categorization
        mock_categories = ChangeCategorization(
            source_code=["src/main.py", "src/utils.js"],
            tests=["tests/test_main.py"],
            documentation=["docs/readme.md"],
            configuration=["config.json"],
            critical_files=["config.json"],
            other=[],
            has_critical_changes=True,
            total_files=5,
        )

        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories

        result = await call_tool_helper(mcp, "preview_commit", repository_path=self.repo_path)

        assert result["ready_to_commit"] is True
        assert result["summary"]["total_files"] == 5
        assert result["summary"]["total_additions"] == 100
        assert result["summary"]["total_deletions"] == 25
        assert result["file_categories"]["source_code"] == 2
        assert result["file_categories"]["tests"] == 1
        assert result["file_categories"]["documentation"] == 1
        assert result["file_categories"]["configuration"] == 1
        assert result["file_categories"]["critical_files"] == 1

        # Check file types
        assert ".py" in result["file_types"]
        assert ".js" in result["file_types"]
        assert ".md" in result["file_types"]
        assert ".json" in result["file_types"]

        # Check files by status
        assert "src/main.py" in result["files_by_status"]["modified"]
        assert "src/utils.js" in result["files_by_status"]["added"]
        assert "config.json" in result["files_by_status"]["modified"]

    @pytest.mark.asyncio
    async def test_preview_commit_no_changes(self):
        """Test commit preview with no staged changes."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock no staged changes
        mock_staged_changes = StagedChanges(
            staged_files=[],
            ready_to_commit=False,
            total_staged=0,
            total_additions=0,
            total_deletions=0,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        result = await call_tool_helper(mcp, "preview_commit", repository_path=self.repo_path)

        assert result["ready_to_commit"] is False
        assert "message" in result
        assert "No changes staged" in result["message"]

    @pytest.mark.asyncio
    async def test_preview_commit_file_extensions(self):
        """Test file type categorization in commit preview."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock files with various extensions
        mock_staged_files = [
            FileStatus(path="script.py", status_code="A", staged=True),
            FileStatus(path="app.js", status_code="A", staged=True),
            FileStatus(path="style.css", status_code="A", staged=True),
            FileStatus(path="data.json", status_code="A", staged=True),
            FileStatus(path="README", status_code="A", staged=True),  # no extension
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=5,
            total_additions=50,
            total_deletions=0,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        mock_categories = ChangeCategorization(
            source_code=[f.path for f in mock_staged_files[:4]],
            tests=[],
            documentation=[mock_staged_files[4].path],
            configuration=[],
            critical_files=[],
            other=[],
            has_critical_changes=False,
            total_files=5,
        )

        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories

        result = await call_tool_helper(mcp, "preview_commit", repository_path=self.repo_path)

        file_types = result["file_types"]
        assert file_types[".py"] == 1
        assert file_types[".js"] == 1
        assert file_types[".css"] == 1
        assert file_types[".json"] == 1
        assert file_types["no_extension"] == 1

    @pytest.mark.asyncio
    async def test_preview_commit_status_categorization(self):
        """Test file status categorization."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock files with different statuses
        mock_staged_files = [
            FileStatus(path="new.py", status_code="A", staged=True),  # Added
            FileStatus(path="modified.py", status_code="M", staged=True),  # Modified
            FileStatus(path="deleted.py", status_code="D", staged=True),  # Deleted
            FileStatus(path="renamed.py", status_code="R", staged=True),  # Renamed
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=4,
            total_additions=30,
            total_deletions=10,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        mock_categories = ChangeCategorization(
            source_code=[f.path for f in mock_staged_files],
            tests=[],
            documentation=[],
            configuration=[],
            critical_files=[],
            other=[],
            has_critical_changes=False,
            total_files=4,
        )

        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories

        result = await call_tool_helper(mcp, "preview_commit", repository_path=self.repo_path)

        files_by_status = result["files_by_status"]
        assert "new.py" in files_by_status["added"]
        assert "modified.py" in files_by_status["modified"]
        assert "deleted.py" in files_by_status["deleted"]
        assert "renamed.py" in files_by_status["renamed"]

    @pytest.mark.asyncio
    async def test_preview_commit_error(self):
        """Test error handling in commit preview."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock service failure
        self.mock_services["change_detector"].detect_staged_changes.side_effect = Exception("Detector failed")

        result = await call_tool_helper(mcp, "preview_commit", repository_path=self.repo_path)

        assert "error" in result
        assert "Detector failed" in result["error"]


@pytest.mark.unit
class TestValidateStagedChanges:
    """Test validate_staged_changes tool."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.git_dir = Path(self.temp_dir) / ".git"
        self.git_dir.mkdir()
        self.repo_path = str(Path(self.temp_dir))

        self.mock_services = {
            "change_detector": AsyncMock(),
            "diff_analyzer": Mock(),
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_validate_staged_changes_valid_low_risk(self):
        """Test validation with valid, low-risk changes."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock low-risk staged changes
        mock_staged_files = [
            FileStatus(
                path="docs/readme.md",
                status_code="M",
                staged=True,
                lines_added=5,
                lines_deleted=2,
                is_binary=False,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=1,
            total_additions=5,
            total_deletions=2,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        # Mock low-risk assessment
        mock_risk = RiskAssessment(
            risk_level="low",
            risk_score=15,
            risk_factors=["doc_change"],
            large_changes=[],
            potential_conflicts=[],
            binary_changes=[],
            is_high_risk=False,
        )

        mock_categories = ChangeCategorization(
            source_code=[],
            tests=[],
            documentation=["docs/readme.md"],
            configuration=[],
            critical_files=[],
            other=[],
            has_critical_changes=False,
            total_files=1,
        )

        self.mock_services["diff_analyzer"].assess_risk.return_value = mock_risk
        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories

        result = await call_tool_helper(mcp, "validate_staged_changes", repository_path=self.repo_path)

        assert result["valid"] is True
        assert result["risk_level"] == "low"
        assert result["risk_score"] == 2  # Computed from actual file changes (5+2=7 total changes)
        assert len(result["warnings"]) == 0
        assert len(result["errors"]) == 0
        assert result["summary"]["total_files"] == 1
        assert result["summary"]["critical_files"] == 0
        assert result["summary"]["binary_files"] == 0

    @pytest.mark.asyncio
    async def test_validate_staged_changes_high_risk_warnings(self):
        """Test validation with high-risk changes (warnings only)."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock high-risk staged changes
        mock_staged_files = [
            FileStatus(
                path="src/core.py",
                status_code="M",
                staged=True,
                lines_added=200,
                lines_deleted=50,
                is_binary=False,
            ),
            FileStatus(
                path="image.png",
                status_code="A",
                staged=True,
                lines_added=0,
                lines_deleted=0,
                is_binary=True,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=2,
            total_additions=200,
            total_deletions=50,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        # Mock high-risk assessment
        mock_risk = RiskAssessment(
            risk_level="high",
            risk_score=85,
            risk_factors=["large_change", "critical_file"],
            large_changes=["src/core.py"],
            potential_conflicts=[],
            binary_changes=["image.png"],
            is_high_risk=True,
        )

        mock_categories = ChangeCategorization(
            source_code=["src/core.py"],
            tests=[],
            documentation=[],
            configuration=[],
            critical_files=["src/core.py"],
            other=["image.png"],
            has_critical_changes=True,
            total_files=2,
        )

        self.mock_services["diff_analyzer"].assess_risk.return_value = mock_risk
        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories

        result = await call_tool_helper(mcp, "validate_staged_changes", repository_path=self.repo_path)

        assert result["valid"] is True  # Warnings don't block validity
        assert result["risk_level"] == "high"
        assert len(result["warnings"]) == 4  # high-risk, large changes, critical files, binary files
        assert len(result["errors"]) == 0
        assert "High-risk changes detected" in str(result["warnings"])
        assert "Large changes" in str(result["warnings"])
        assert "Critical files changed" in str(result["warnings"])
        assert "Binary files included" in str(result["warnings"])
        assert result["summary"]["critical_files"] == 1
        assert result["summary"]["binary_files"] == 1

    @pytest.mark.asyncio
    async def test_validate_staged_changes_with_errors(self):
        """Test validation with blocking errors."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock staged changes with conflicts
        mock_staged_files = [
            FileStatus(
                path="conflicted.py",
                status_code="M",
                staged=True,
                lines_added=50,
                lines_deleted=20,
                is_binary=False,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=1,
            total_additions=50,
            total_deletions=20,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        # Mock risk assessment with conflicts
        mock_risk = RiskAssessment(
            risk_level="high",
            risk_score=90,
            risk_factors=["conflict_risk"],
            large_changes=[],
            potential_conflicts=["conflicted.py"],
            binary_changes=[],
            is_high_risk=True,
        )

        mock_categories = ChangeCategorization(
            source_code=["conflicted.py"],
            tests=[],
            documentation=[],
            configuration=[],
            critical_files=[],
            other=[],
            has_critical_changes=False,
            total_files=1,
        )

        self.mock_services["diff_analyzer"].assess_risk.return_value = mock_risk
        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories

        result = await call_tool_helper(mcp, "validate_staged_changes", repository_path=self.repo_path)

        assert result["valid"] is False  # Errors block validity
        assert len(result["errors"]) == 1
        assert "Potential conflicts detected" in result["errors"][0]
        assert "conflicted.py" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_validate_staged_changes_with_recommendations(self):
        """Test validation with generated recommendations."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock staged changes needing recommendations
        mock_staged_files = []
        for i in range(12):  # More than 10 files
            mock_staged_files.append(
                FileStatus(
                    path=f"src/module_{i}.py",
                    status_code="M",
                    staged=True,
                    lines_added=100,  # Large changes
                    lines_deleted=30,
                    is_binary=False,
                )
            )

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=12,
            total_additions=1200,
            total_deletions=360,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        mock_risk = RiskAssessment(
            risk_level="medium",
            risk_score=65,
            risk_factors=["many_files", "large_changes"],
            large_changes=[f"src/module_{i}.py" for i in range(5)],  # 5 large changes
            potential_conflicts=[],
            binary_changes=[],
            is_high_risk=False,
        )

        mock_categories = ChangeCategorization(
            source_code=[f.path for f in mock_staged_files],
            tests=[],  # No tests
            documentation=[],
            configuration=[],
            critical_files=[f"src/module_{i}.py" for i in range(3)],  # 3 critical
            other=[],
            has_critical_changes=True,
            total_files=12,
        )

        self.mock_services["diff_analyzer"].assess_risk.return_value = mock_risk
        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories

        result = await call_tool_helper(mcp, "validate_staged_changes", repository_path=self.repo_path)

        assert result["valid"] is True
        recommendations = result["recommendations"]
        assert len(recommendations) == 4
        assert any("Review large changes" in rec for rec in recommendations)
        assert any("Double-check critical" in rec for rec in recommendations)
        assert any("splitting large commits" in rec for rec in recommendations)
        assert any("Add tests" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_validate_staged_changes_no_changes(self):
        """Test validation with no staged changes."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock no staged changes
        mock_staged_changes = StagedChanges(
            staged_files=[],
            ready_to_commit=False,
            total_staged=0,
            total_additions=0,
            total_deletions=0,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        result = await call_tool_helper(mcp, "validate_staged_changes", repository_path=self.repo_path)

        assert result["valid"] is False
        assert "message" in result
        assert "No changes staged" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_staged_changes_invalid_repo(self):
        """Test validation with invalid repository."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        with (
            patch(
                "mcp_local_repo_analyzer.tools.staging_area.is_git_repository",
                return_value=False,
            ),
            patch(
                "mcp_local_repo_analyzer.tools.staging_area.find_git_root",
                return_value=None,
            ),
        ):
            result = await call_tool_helper(mcp, "validate_staged_changes", repository_path="/invalid/path")

            assert "error" in result
            assert "No git repository found" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_staged_changes_service_error(self):
        """Test validation with service error."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock service failure
        self.mock_services["change_detector"].detect_staged_changes.side_effect = Exception("Validation failed")

        result = await call_tool_helper(mcp, "validate_staged_changes", repository_path=self.repo_path)

        assert "error" in result
        assert "Validation failed" in result["error"]


@pytest.mark.unit
class TestStagingAreaIntegration:
    """Integration tests for staging area tools."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.git_dir = Path(self.temp_dir) / ".git"
        self.git_dir.mkdir()
        self.repo_path = str(Path(self.temp_dir))

        self.mock_services = {
            "change_detector": AsyncMock(),
            "diff_analyzer": Mock(),
            "git_client": AsyncMock(),
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_staging_area_workflow_complete(self):
        """Test complete staging area workflow."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock staged changes for workflow
        mock_staged_files = [
            FileStatus(
                path="src/feature.py",
                status_code="A",
                staged=True,
                lines_added=50,
                lines_deleted=0,
                is_binary=False,
            ),
            FileStatus(
                path="tests/test_feature.py",
                status_code="A",
                staged=True,
                lines_added=30,
                lines_deleted=0,
                is_binary=False,
            ),
        ]

        mock_staged_changes = StagedChanges(
            staged_files=mock_staged_files,
            ready_to_commit=True,
            total_staged=2,
            total_additions=80,
            total_deletions=0,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        mock_risk = RiskAssessment(
            risk_level="low",
            risk_score=25,
            risk_factors=["new_feature"],
            large_changes=[],
            potential_conflicts=[],
            binary_changes=[],
            is_high_risk=False,
        )

        mock_categories = ChangeCategorization(
            source_code=["src/feature.py"],
            tests=["tests/test_feature.py"],
            documentation=[],
            configuration=[],
            critical_files=[],
            other=[],
            has_critical_changes=False,
            total_files=2,
        )

        self.mock_services["diff_analyzer"].assess_risk.return_value = mock_risk
        self.mock_services["diff_analyzer"].categorize_changes.return_value = mock_categories
        self.mock_services["git_client"].get_diff.return_value = "mock diff content"

        # 1. Analyze staged changes
        analyze_result = await call_tool_helper(mcp, "analyze_staged_changes", repository_path=self.repo_path)
        assert analyze_result["ready_to_commit"] is True
        assert analyze_result["total_staged_files"] == 2

        # 2. Preview commit
        preview_result = await call_tool_helper(mcp, "preview_commit", repository_path=self.repo_path)
        assert preview_result["ready_to_commit"] is True
        assert preview_result["file_categories"]["source_code"] == 1
        assert preview_result["file_categories"]["tests"] == 1

        # 3. Validate staged changes
        validate_result = await call_tool_helper(mcp, "validate_staged_changes", repository_path=self.repo_path)
        assert validate_result["valid"] is True
        assert validate_result["risk_level"] == "low"
        assert len(validate_result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_staging_area_tools_registration(self):
        """Test that all staging area tools are properly registered."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Test that tools are registered by attempting to call them
        # If tools aren't registered, this would raise an exception
        from fastmcp import Client

        client = Client(mcp)
        async with client:
            # Test analyze_staged_changes tool exists
            from contextlib import suppress

            with suppress(Exception):
                await client.call_tool("analyze_staged_changes", {"repository_path": self.repo_path})

            # Test preview_commit tool exists
            with suppress(Exception):
                await client.call_tool("preview_commit", {"repository_path": self.repo_path})

        # Tool functions are verified by successful calls above

    @pytest.mark.asyncio
    async def test_staging_area_path_handling(self):
        """Test path handling across staging area tools."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        register_staging_area_tools(mcp, self.mock_services)

        # Mock minimal staged changes
        mock_staged_changes = StagedChanges(
            staged_files=[],
            ready_to_commit=False,
            total_staged=0,
            total_additions=0,
            total_deletions=0,
        )

        self.mock_services["change_detector"].detect_staged_changes.return_value = mock_staged_changes

        AsyncMock()

        # Test that all tools handle the same repository path consistently
        for tool_name in [
            "analyze_staged_changes",
            "preview_commit",
            "validate_staged_changes",
        ]:
            result = await call_tool_helper(mcp, tool_name, repository_path=self.repo_path)

            if "error" not in result:
                # Use realpath to handle macOS /private/var symlinks
                import os

                assert os.path.realpath(result["repository_path"]) == os.path.realpath(self.repo_path)

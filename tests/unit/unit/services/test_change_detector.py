"""Comprehensive unit tests for the ChangeDetector service."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from mcp_local_repo_analyzer.services.git.change_detector import ChangeDetector
from mcp_shared_lib.models.git.changes import StagedChanges, WorkingDirectoryChanges
from mcp_shared_lib.models.git.repository import LocalRepository
from mcp_shared_lib.services.git.git_client import GitClient


@pytest.mark.unit
class TestChangeDetector:
    """Test the ChangeDetector service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.git_client = Mock(spec=GitClient)
        self.change_detector = ChangeDetector(self.git_client)

        # Create test repo without validation
        self.test_repo = LocalRepository.model_construct(
            path=Path("/tmp/test_repo"),
            name="test_repo",
            current_branch="main",
            head_commit="abc123",
            remote_url=None,
            remote_branches=[],
            is_dirty=False,
            is_bare=False,
            upstream_branch=None,
            remotes=[],
            branches=[],
        )

        # Mock context
        self.mock_ctx = Mock()
        self.mock_ctx.debug = AsyncMock()
        self.mock_ctx.info = AsyncMock()
        self.mock_ctx.error = AsyncMock()
        self.mock_ctx.warning = AsyncMock()

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_basic(self):
        """Test basic working directory change detection."""
        # Mock git status response
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "file1.py",
                        "status_code": "M",
                        "working_status": "M",
                        "index_status": None,
                    },
                    {
                        "filename": "file2.py",
                        "status_code": "A",
                        "working_status": "A",
                        "index_status": None,
                    },
                    {
                        "filename": "file3.py",
                        "status_code": "?",
                        "working_status": "?",
                        "index_status": None,
                    },
                ]
            }
        )

        # Mock diff stats for modified file
        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 10,
                "lines_deleted": 5,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo, self.mock_ctx
        )

        assert isinstance(result, WorkingDirectoryChanges)
        assert result.total_files == 3
        assert len(result.modified_files) == 1
        assert len(result.added_files) == 1
        assert len(result.untracked_files) == 1

        # Check modified file details
        modified_file = result.modified_files[0]
        assert modified_file.path == "file1.py"
        assert modified_file.status_code == "M"
        assert modified_file.staged is False
        assert modified_file.lines_added == 10
        assert modified_file.lines_deleted == 5

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_with_rename(self):
        """Test working directory change detection with renamed files."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "new_name.py",
                        "status_code": "R",
                        "working_status": "R",
                        "index_status": None,
                        "old_filename": "old_name.py",
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 0,
                "lines_deleted": 0,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result.renamed_files) == 1
        renamed_file = result.renamed_files[0]
        assert renamed_file.path == "new_name.py"
        assert renamed_file.old_path == "old_name.py"
        assert renamed_file.status_code == "R"

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_deleted_file(self):
        """Test working directory change detection with deleted files."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "deleted_file.py",
                        "status_code": "D",
                        "working_status": "D",
                        "index_status": None,
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 0,
                "lines_deleted": 15,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result.deleted_files) == 1
        deleted_file = result.deleted_files[0]
        assert deleted_file.path == "deleted_file.py"
        assert deleted_file.lines_deleted == 15

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_binary_file(self):
        """Test working directory change detection with binary files."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "image.png",
                        "status_code": "M",
                        "working_status": "M",
                        "index_status": None,
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 0,
                "lines_deleted": 0,
                "is_binary": True,
            }
        )

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result.modified_files) == 1
        modified_file = result.modified_files[0]
        assert modified_file.is_binary is True

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_mixed_status(self):
        """Test working directory change detection with mixed status files."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "mixed_file.py",
                        "status_code": "MM",
                        "working_status": "M",
                        "index_status": "M",
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 20,
                "lines_deleted": 10,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result.modified_files) == 1
        modified_file = result.modified_files[0]
        assert modified_file.index_status == "M"  # Should preserve index status

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_diff_stats_error(self):
        """Test working directory change detection when diff stats fail."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "error_file.py",
                        "status_code": "M",
                        "working_status": "M",
                        "index_status": None,
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(side_effect=Exception("Git error"))

        with pytest.raises(Exception, match="Git error"):
            await self.change_detector.detect_working_directory_changes(
                self.test_repo, self.mock_ctx
            )

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_no_working_status(self):
        """Test working directory change detection with no working status."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "staged_only.py",
                        "status_code": "M",
                        "working_status": None,
                        "index_status": "M",
                    }
                ]
            }
        )

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo, self.mock_ctx
        )

        # Should not include files with no working status
        assert result.total_files == 0
        assert len(result.modified_files) == 0

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_empty_status(self):
        """Test working directory change detection with empty status."""
        self.git_client.get_status = AsyncMock(return_value={"files": []})

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo, self.mock_ctx
        )

        assert result.total_files == 0
        assert len(result.modified_files) == 0
        assert len(result.added_files) == 0
        assert len(result.deleted_files) == 0
        assert len(result.renamed_files) == 0
        assert len(result.untracked_files) == 0

    @pytest.mark.asyncio
    async def test_detect_staged_changes_basic(self):
        """Test basic staged changes detection."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "staged_file.py",
                        "status_code": "A",
                        "working_status": None,
                        "index_status": "A",
                    },
                    {
                        "filename": "modified_staged.py",
                        "status_code": "M",
                        "working_status": None,
                        "index_status": "M",
                    },
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 25,
                "lines_deleted": 5,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_staged_changes(
            self.test_repo, self.mock_ctx
        )

        assert isinstance(result, StagedChanges)
        assert result.total_staged == 2
        assert result.ready_to_commit is True

        # Check staged file details
        staged_file = result.staged_files[0]
        assert staged_file.path == "staged_file.py"
        assert staged_file.staged is True
        assert staged_file.index_status == "A"

    @pytest.mark.asyncio
    async def test_detect_staged_changes_with_rename(self):
        """Test staged changes detection with renamed files."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "new_name.py",
                        "status_code": "R",
                        "working_status": None,
                        "index_status": "R",
                        "old_filename": "old_name.py",
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 0,
                "lines_deleted": 0,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_staged_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result.staged_files) == 1
        staged_file = result.staged_files[0]
        assert staged_file.old_path == "old_name.py"

    @pytest.mark.asyncio
    async def test_detect_staged_changes_excludes_untracked(self):
        """Test staged changes detection excludes untracked files."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "untracked.py",
                        "status_code": "?",
                        "working_status": "?",
                        "index_status": None,
                    }
                ]
            }
        )

        result = await self.change_detector.detect_staged_changes(
            self.test_repo, self.mock_ctx
        )

        assert result.total_staged == 0
        assert result.ready_to_commit is False

    @pytest.mark.asyncio
    async def test_detect_staged_changes_excludes_empty_index_status(self):
        """Test staged changes detection excludes files with empty index status."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "no_index.py",
                        "status_code": "M",
                        "working_status": "M",
                        "index_status": " ",
                    }
                ]
            }
        )

        result = await self.change_detector.detect_staged_changes(
            self.test_repo, self.mock_ctx
        )

        assert result.total_staged == 0

    @pytest.mark.asyncio
    async def test_detect_staged_changes_diff_stats_error(self):
        """Test staged changes detection when diff stats fail."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "error_file.py",
                        "status_code": "M",
                        "working_status": None,
                        "index_status": "M",
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(side_effect=Exception("Git error"))

        with pytest.raises(Exception, match="Git error"):
            await self.change_detector.detect_staged_changes(
                self.test_repo, self.mock_ctx
            )

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_basic(self):
        """Test basic unpushed commits detection."""
        self.git_client.get_unpushed_commits = AsyncMock(
            return_value=[
                {
                    "sha": "abc123",
                    "message": "Test commit",
                    "author": "Test Author",
                    "email": "test@example.com",
                    "date": "2024-01-01T00:00:00Z",
                }
            ]
        )

        result = await self.change_detector.detect_unpushed_commits(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 1
        commit = result[0]
        assert commit.sha == "abc123"
        assert commit.message == "Test commit"
        assert commit.author == "Test Author"
        assert commit.author_email == "test@example.com"
        assert isinstance(commit.date, datetime)

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_multiple_commits(self):
        """Test unpushed commits detection with multiple commits."""
        self.git_client.get_unpushed_commits = AsyncMock(
            return_value=[
                {
                    "sha": "abc123",
                    "message": "First commit",
                    "author": "Author 1",
                    "email": "author1@example.com",
                    "date": "2024-01-01T00:00:00Z",
                },
                {
                    "sha": "def456",
                    "message": "Second commit",
                    "author": "Author 2",
                    "email": "author2@example.com",
                    "date": "2024-01-02T00:00:00Z",
                },
            ]
        )

        result = await self.change_detector.detect_unpushed_commits(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 2
        assert result[0].sha == "abc123"
        assert result[1].sha == "def456"

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_date_parsing_iso_with_timezone(self):
        """Test unpushed commits detection with ISO date format with timezone."""
        self.git_client.get_unpushed_commits = AsyncMock(
            return_value=[
                {
                    "sha": "abc123",
                    "message": "Test commit",
                    "author": "Test Author",
                    "email": "test@example.com",
                    "date": "2024-01-01T00:00:00+00:00",
                }
            ]
        )

        result = await self.change_detector.detect_unpushed_commits(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 1
        assert isinstance(result[0].date, datetime)

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_date_parsing_iso_no_timezone(self):
        """Test unpushed commits detection with ISO date format without timezone."""
        self.git_client.get_unpushed_commits = AsyncMock(
            return_value=[
                {
                    "sha": "abc123",
                    "message": "Test commit",
                    "author": "Test Author",
                    "email": "test@example.com",
                    "date": "2024-01-01T00:00:00",
                }
            ]
        )

        result = await self.change_detector.detect_unpushed_commits(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 1
        assert isinstance(result[0].date, datetime)

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_date_parsing_fallback(self):
        """Test unpushed commits detection with invalid date format."""
        self.git_client.get_unpushed_commits = AsyncMock(
            return_value=[
                {
                    "sha": "abc123",
                    "message": "Test commit",
                    "author": "Test Author",
                    "email": "test@example.com",
                    "date": "invalid_date",
                }
            ]
        )

        result = await self.change_detector.detect_unpushed_commits(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 1
        assert isinstance(result[0].date, datetime)  # Should fallback to current time

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_missing_data(self):
        """Test unpushed commits detection with missing commit data."""
        self.git_client.get_unpushed_commits = AsyncMock(
            return_value=[
                {
                    "sha": "abc123",
                    # Missing required fields
                }
            ]
        )

        result = await self.change_detector.detect_unpushed_commits(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 0  # Should skip invalid commits

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_git_error(self):
        """Test unpushed commits detection when git client fails."""
        self.git_client.get_unpushed_commits = AsyncMock(
            side_effect=Exception("Git error")
        )

        with pytest.raises(Exception, match="Git error"):
            await self.change_detector.detect_unpushed_commits(
                self.test_repo, self.mock_ctx
            )

    @pytest.mark.asyncio
    async def test_detect_stashed_changes_basic(self):
        """Test basic stashed changes detection."""
        self.git_client.get_stash_list = AsyncMock(
            return_value=[
                {
                    "index": 0,
                    "message": "WIP: Test stash",
                }
            ]
        )

        result = await self.change_detector.detect_stashed_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 1
        stash = result[0]
        assert stash.stash_index == 0
        assert stash.message == "WIP: Test stash"
        assert stash.branch == "main"  # From test_repo
        assert isinstance(stash.date, datetime)

    @pytest.mark.asyncio
    async def test_detect_stashed_changes_multiple_stashes(self):
        """Test stashed changes detection with multiple stashes."""
        self.git_client.get_stash_list = AsyncMock(
            return_value=[
                {
                    "index": 0,
                    "message": "First stash",
                },
                {
                    "index": 1,
                    "message": "Second stash",
                },
            ]
        )

        result = await self.change_detector.detect_stashed_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 2
        assert result[0].stash_index == 0
        assert result[1].stash_index == 1

    @pytest.mark.asyncio
    async def test_detect_stashed_changes_missing_data(self):
        """Test stashed changes detection with missing stash data."""
        self.git_client.get_stash_list = AsyncMock(
            return_value=[
                {
                    # Missing required fields
                }
            ]
        )

        result = await self.change_detector.detect_stashed_changes(
            self.test_repo, self.mock_ctx
        )

        assert len(result) == 0  # Should skip invalid stashes

    @pytest.mark.asyncio
    async def test_detect_stashed_changes_git_error(self):
        """Test stashed changes detection when git client fails."""
        self.git_client.get_stash_list = AsyncMock(side_effect=Exception("Git error"))

        with pytest.raises(Exception, match="Git error"):
            await self.change_detector.detect_stashed_changes(
                self.test_repo, self.mock_ctx
            )

    @pytest.mark.asyncio
    async def test_detect_working_directory_changes_no_context(self):
        """Test working directory change detection without context."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "file1.py",
                        "status_code": "M",
                        "working_status": "M",
                        "index_status": None,
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 10,
                "lines_deleted": 5,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_working_directory_changes(
            self.test_repo
        )

        assert len(result.modified_files) == 1
        # Should work without context

    @pytest.mark.asyncio
    async def test_detect_staged_changes_no_context(self):
        """Test staged changes detection without context."""
        self.git_client.get_status = AsyncMock(
            return_value={
                "files": [
                    {
                        "filename": "staged_file.py",
                        "status_code": "A",
                        "working_status": None,
                        "index_status": "A",
                    }
                ]
            }
        )

        self.git_client.get_diff_stats = AsyncMock(
            return_value={
                "lines_added": 25,
                "lines_deleted": 5,
                "is_binary": False,
            }
        )

        result = await self.change_detector.detect_staged_changes(self.test_repo)

        assert len(result.staged_files) == 1
        # Should work without context

    @pytest.mark.asyncio
    async def test_detect_unpushed_commits_no_context(self):
        """Test unpushed commits detection without context."""
        self.git_client.get_unpushed_commits = AsyncMock(
            return_value=[
                {
                    "sha": "abc123",
                    "message": "Test commit",
                    "author": "Test Author",
                    "email": "test@example.com",
                    "date": "2024-01-01T00:00:00Z",
                }
            ]
        )

        result = await self.change_detector.detect_unpushed_commits(self.test_repo)

        assert len(result) == 1
        # Should work without context

    @pytest.mark.asyncio
    async def test_detect_stashed_changes_no_context(self):
        """Test stashed changes detection without context."""
        self.git_client.get_stash_list = AsyncMock(
            return_value=[
                {
                    "index": 0,
                    "message": "WIP: Test stash",
                }
            ]
        )

        result = await self.change_detector.detect_stashed_changes(self.test_repo)

        assert len(result) == 1
        # Should work without context

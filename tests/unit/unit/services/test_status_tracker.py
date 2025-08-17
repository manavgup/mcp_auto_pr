"""Comprehensive unit tests for the StatusTracker service."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from mcp_local_repo_analyzer.services.git.change_detector import ChangeDetector
from mcp_local_repo_analyzer.services.git.status_tracker import StatusTracker
from mcp_shared_lib.models.analysis.repository import BranchStatus, RepositoryStatus
from mcp_shared_lib.models.git.repository import LocalRepository
from mcp_shared_lib.services.git.git_client import GitClient


@pytest.mark.unit
class TestStatusTracker:
    """Test the StatusTracker service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.git_client = Mock(spec=GitClient)
        self.change_detector = Mock(spec=ChangeDetector)
        self.status_tracker = StatusTracker(self.git_client, self.change_detector)

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
    async def test_get_repository_status_basic(self):
        """Test basic repository status retrieval."""
        # Mock change detector responses with proper model instances
        from mcp_shared_lib.models.git.changes import (
            StagedChanges,
            WorkingDirectoryChanges,
        )
        from mcp_shared_lib.models.git.commits import StashedChanges, UnpushedCommit

        # Create mock working directory changes
        mock_working_changes = Mock(spec=WorkingDirectoryChanges)
        mock_working_changes.total_files = 2
        mock_working_changes.has_changes = True

        # Create mock staged changes
        mock_staged_changes = Mock(spec=StagedChanges)
        mock_staged_changes.total_staged = 1
        mock_staged_changes.ready_to_commit = True

        # Create mock unpushed commit
        mock_unpushed_commit = Mock(spec=UnpushedCommit)
        mock_unpushed_commit.sha = "abc123"
        mock_unpushed_commit.message = "Test commit"

        # Create mock stashed changes
        mock_stashed_change = Mock(spec=StashedChanges)
        mock_stashed_change.stash_index = 0
        mock_stashed_change.message = "Test stash"

        self.change_detector.detect_working_directory_changes = AsyncMock(
            return_value=mock_working_changes
        )
        self.change_detector.detect_staged_changes = AsyncMock(
            return_value=mock_staged_changes
        )
        self.change_detector.detect_unpushed_commits = AsyncMock(
            return_value=[mock_unpushed_commit]
        )
        self.change_detector.detect_stashed_changes = AsyncMock(
            return_value=[mock_stashed_change]
        )

        # Mock git client response
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 1,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_repository_status(
            self.test_repo, self.mock_ctx
        )

        assert isinstance(result, RepositoryStatus)
        assert result.repository == self.test_repo
        assert result.working_directory.has_changes is True
        assert result.staged_changes.ready_to_commit is True
        assert len(result.unpushed_commits) == 1
        assert len(result.stashed_changes) == 1
        assert result.branch_status.current_branch == "main"

    @pytest.mark.asyncio
    async def test_get_repository_status_no_context(self):
        """Test repository status retrieval without context."""
        # Mock change detector responses with proper model instances
        from mcp_shared_lib.models.git.changes import (
            StagedChanges,
            WorkingDirectoryChanges,
        )

        # Create mock working directory changes
        mock_working_changes = Mock(spec=WorkingDirectoryChanges)
        mock_working_changes.total_files = 0
        mock_working_changes.has_changes = False

        # Create mock staged changes
        mock_staged_changes = Mock(spec=StagedChanges)
        mock_staged_changes.total_staged = 0
        mock_staged_changes.ready_to_commit = False

        self.change_detector.detect_working_directory_changes = AsyncMock(
            return_value=mock_working_changes
        )
        self.change_detector.detect_staged_changes = AsyncMock(
            return_value=mock_staged_changes
        )
        self.change_detector.detect_unpushed_commits = AsyncMock(return_value=[])
        self.change_detector.detect_stashed_changes = AsyncMock(return_value=[])

        # Mock git client response
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 0,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_repository_status(self.test_repo)

        assert isinstance(result, RepositoryStatus)
        assert result.working_directory.has_changes is False
        assert result.staged_changes.ready_to_commit is False
        assert len(result.unpushed_commits) == 0
        assert len(result.stashed_changes) == 0

    @pytest.mark.asyncio
    async def test_get_branch_status_basic(self):
        """Test basic branch status retrieval."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 2,
                "behind": 1,
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert isinstance(result, BranchStatus)
        assert result.current_branch == "main"
        assert result.upstream_branch == "origin/main"
        assert result.ahead_by == 2
        assert result.behind_by == 1
        assert result.is_up_to_date is False
        assert result.needs_push is True
        assert result.needs_pull is True

    @pytest.mark.asyncio
    async def test_get_branch_status_up_to_date(self):
        """Test branch status when up to date."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 0,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert result.is_up_to_date is True
        assert result.needs_push is False
        assert result.needs_pull is False

    @pytest.mark.asyncio
    async def test_get_branch_status_needs_push_only(self):
        """Test branch status when only needs push."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 3,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert result.is_up_to_date is False
        assert result.needs_push is True
        assert result.needs_pull is False

    @pytest.mark.asyncio
    async def test_get_branch_status_needs_pull_only(self):
        """Test branch status when only needs pull."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 0,
                "behind": 2,
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert result.is_up_to_date is False
        assert result.needs_push is False
        assert result.needs_pull is True

    @pytest.mark.asyncio
    async def test_get_branch_status_no_upstream(self):
        """Test branch status when no upstream branch."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": None,
                "ahead": 0,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert result.upstream_branch is None
        assert result.ahead_by == 0
        assert result.behind_by == 0
        assert result.is_up_to_date is True
        assert result.needs_push is False
        assert result.needs_pull is False

    @pytest.mark.asyncio
    async def test_get_branch_status_missing_info(self):
        """Test branch status when git client returns missing information."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                # Missing upstream, ahead, behind
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert result.current_branch == "main"
        assert result.upstream_branch is None
        assert result.ahead_by == 0
        assert result.behind_by == 0
        assert result.is_up_to_date is True
        assert result.needs_push is False
        assert result.needs_pull is False

    @pytest.mark.asyncio
    async def test_get_branch_status_no_context(self):
        """Test branch status retrieval without context."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 1,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_branch_status(self.test_repo)

        assert isinstance(result, BranchStatus)
        assert result.current_branch == "main"
        assert result.needs_push is True

    @pytest.mark.asyncio
    async def test_get_health_metrics_basic(self):
        """Test basic health metrics retrieval."""
        # Mock repository status
        mock_status = Mock()
        mock_status.total_outstanding_changes = 5
        mock_status.working_directory.has_changes = True
        mock_status.staged_changes.ready_to_commit = True
        mock_status.staged_changes.total_staged = 2
        mock_status.unpushed_commits = [Mock(), Mock()]  # 2 commits
        mock_status.stashed_changes = [Mock()]  # 1 stash
        mock_status.branch_status.sync_status = "ahead"
        mock_status.has_outstanding_work = True

        # Mock the get_repository_status method
        self.status_tracker.get_repository_status = AsyncMock(return_value=mock_status)

        result = await self.status_tracker.get_health_metrics(
            self.test_repo, self.mock_ctx
        )

        assert isinstance(result, dict)
        assert result["total_outstanding_files"] == 5
        assert result["has_uncommitted_changes"] is True
        assert result["has_staged_changes"] is True
        assert result["staged_changes_count"] == 2
        assert result["unpushed_commits_count"] == 2
        assert result["stashed_changes_count"] == 1
        assert result["branch_sync_status"] == "ahead"
        assert result["needs_attention"] is True

    @pytest.mark.asyncio
    async def test_get_health_metrics_clean_repo(self):
        """Test health metrics for a clean repository."""
        # Mock clean repository status
        mock_status = Mock()
        mock_status.total_outstanding_changes = 0
        mock_status.working_directory.has_changes = False
        mock_status.staged_changes.ready_to_commit = False
        mock_status.staged_changes.total_staged = 0
        mock_status.unpushed_commits = []
        mock_status.stashed_changes = []
        mock_status.branch_status.sync_status = "up_to_date"
        mock_status.has_outstanding_work = False

        # Mock the get_repository_status method
        self.status_tracker.get_repository_status = AsyncMock(return_value=mock_status)

        result = await self.status_tracker.get_health_metrics(
            self.test_repo, self.mock_ctx
        )

        assert result["total_outstanding_files"] == 0
        assert result["has_uncommitted_changes"] is False
        assert result["has_staged_changes"] is False
        assert result["staged_changes_count"] == 0
        assert result["unpushed_commits_count"] == 0
        assert result["stashed_changes_count"] == 0
        assert result["branch_sync_status"] == "up_to_date"
        assert result["needs_attention"] is False

    @pytest.mark.asyncio
    async def test_get_health_metrics_no_context(self):
        """Test health metrics retrieval without context."""
        # Mock repository status
        mock_status = Mock()
        mock_status.total_outstanding_changes = 1
        mock_status.working_directory.has_changes = True
        mock_status.staged_changes.ready_to_commit = False
        mock_status.staged_changes.total_staged = 0
        mock_status.unpushed_commits = []
        mock_status.stashed_changes = []
        mock_status.branch_status.sync_status = "up_to_date"
        mock_status.has_outstanding_work = True

        # Mock the get_repository_status method
        self.status_tracker.get_repository_status = AsyncMock(return_value=mock_status)

        result = await self.status_tracker.get_health_metrics(self.test_repo)

        assert isinstance(result, dict)
        assert result["total_outstanding_files"] == 1
        assert result["has_uncommitted_changes"] is True
        assert result["needs_attention"] is True

    @pytest.mark.asyncio
    async def test_get_repository_status_with_errors(self):
        """Test repository status retrieval when change detector fails."""
        # Mock change detector to raise an exception
        self.change_detector.detect_working_directory_changes = AsyncMock(
            side_effect=Exception("Change detector failed")
        )

        with pytest.raises(Exception, match="Change detector failed"):
            await self.status_tracker.get_repository_status(
                self.test_repo, self.mock_ctx
            )

    @pytest.mark.asyncio
    async def test_get_branch_status_with_errors(self):
        """Test branch status retrieval when git client fails."""
        # Mock git client to raise an exception
        self.git_client.get_branch_info = AsyncMock(
            side_effect=Exception("Git client failed")
        )

        with pytest.raises(Exception, match="Git client failed"):
            await self.status_tracker.get_branch_status(self.test_repo, self.mock_ctx)

    @pytest.mark.asyncio
    async def test_get_health_metrics_with_errors(self):
        """Test health metrics retrieval when repository status fails."""
        # Mock get_repository_status to raise an exception
        self.status_tracker.get_repository_status = AsyncMock(
            side_effect=Exception("Repository status failed")
        )

        with pytest.raises(Exception, match="Repository status failed"):
            await self.status_tracker.get_health_metrics(self.test_repo, self.mock_ctx)

    @pytest.mark.asyncio
    async def test_get_repository_status_partial_failures(self):
        """Test repository status when some detectors fail but others succeed."""
        # Mock some detectors to succeed and others to fail
        self.change_detector.detect_working_directory_changes = AsyncMock(
            return_value=Mock(total_files=1, has_changes=True)
        )
        self.change_detector.detect_staged_changes = AsyncMock(
            side_effect=Exception("Staged changes failed")
        )

        with pytest.raises(Exception, match="Staged changes failed"):
            await self.status_tracker.get_repository_status(
                self.test_repo, self.mock_ctx
            )

    @pytest.mark.asyncio
    async def test_get_branch_status_edge_cases(self):
        """Test branch status with edge case values."""
        # Test with very large ahead/behind values
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 999999,
                "behind": 999999,
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert result.ahead_by == 999999
        assert result.behind_by == 999999
        assert result.is_up_to_date is False
        assert result.needs_push is True
        assert result.needs_pull is True

    @pytest.mark.asyncio
    async def test_get_branch_status_zero_values(self):
        """Test branch status with zero values."""
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 0,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_branch_status(
            self.test_repo, self.mock_ctx
        )

        assert result.ahead_by == 0
        assert result.behind_by == 0
        assert result.is_up_to_date is True
        assert result.needs_push is False
        assert result.needs_pull is False

    @pytest.mark.asyncio
    async def test_get_repository_status_empty_changes(self):
        """Test repository status with empty change lists."""
        # Mock change detector responses with empty lists and proper model instances
        from mcp_shared_lib.models.git.changes import (
            StagedChanges,
            WorkingDirectoryChanges,
        )

        # Create mock working directory changes
        mock_working_changes = Mock(spec=WorkingDirectoryChanges)
        mock_working_changes.total_files = 0
        mock_working_changes.has_changes = False

        # Create mock staged changes
        mock_staged_changes = Mock(spec=StagedChanges)
        mock_staged_changes.total_staged = 0
        mock_staged_changes.ready_to_commit = False

        self.change_detector.detect_working_directory_changes = AsyncMock(
            return_value=mock_working_changes
        )
        self.change_detector.detect_staged_changes = AsyncMock(
            return_value=mock_staged_changes
        )
        self.change_detector.detect_unpushed_commits = AsyncMock(return_value=[])
        self.change_detector.detect_stashed_changes = AsyncMock(return_value=[])

        # Mock git client response
        self.git_client.get_branch_info = AsyncMock(
            return_value={
                "current_branch": "main",
                "upstream": "origin/main",
                "ahead": 0,
                "behind": 0,
            }
        )

        result = await self.status_tracker.get_repository_status(
            self.test_repo, self.mock_ctx
        )

        assert isinstance(result, RepositoryStatus)
        assert result.working_directory.has_changes is False
        assert result.staged_changes.ready_to_commit is False
        assert len(result.unpushed_commits) == 0
        assert len(result.stashed_changes) == 0
        assert result.branch_status.is_up_to_date is True

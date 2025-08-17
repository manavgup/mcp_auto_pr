"""Service for tracking repository status and health."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_local_repo_analyzer.services.git import ChangeDetector
from mcp_shared_lib.models import BranchStatus, LocalRepository, RepositoryStatus
from mcp_shared_lib.services import GitClient

if TYPE_CHECKING:
    from fastmcp import Context


class StatusTracker:
    """Service for tracking repository status and health."""

    def __init__(self, git_client: GitClient, change_detector: ChangeDetector):
        """Initialize status tracker with required services."""
        self.git_client = git_client
        self.change_detector = change_detector

    async def get_repository_status(
        self, repo: LocalRepository, ctx: Optional["Context"] = None
    ) -> RepositoryStatus:
        """Get complete repository status."""
        # Get all types of changes
        working_directory = await self.change_detector.detect_working_directory_changes(
            repo, ctx
        )
        staged_changes = await self.change_detector.detect_staged_changes(repo, ctx)
        unpushed_commits = await self.change_detector.detect_unpushed_commits(repo, ctx)
        stashed_changes = await self.change_detector.detect_stashed_changes(repo, ctx)

        # Get branch status
        branch_status = await self.get_branch_status(repo, ctx)

        return RepositoryStatus(
            repository=repo,
            working_directory=working_directory,
            staged_changes=staged_changes,
            unpushed_commits=unpushed_commits,
            stashed_changes=stashed_changes,
            branch_status=branch_status,
        )

    async def get_branch_status(
        self, repo: LocalRepository, ctx: Optional["Context"] = None
    ) -> BranchStatus:
        """Get branch status information."""
        branch_info = await self.git_client.get_branch_info(repo.path, ctx)

        ahead_by = branch_info.get("ahead", 0)
        behind_by = branch_info.get("behind", 0)

        is_up_to_date = ahead_by == 0 and behind_by == 0
        needs_push = ahead_by > 0
        needs_pull = behind_by > 0

        return BranchStatus(
            current_branch=branch_info.get("current_branch", repo.current_branch),
            upstream_branch=branch_info.get("upstream"),
            ahead_by=ahead_by,
            behind_by=behind_by,
            is_up_to_date=is_up_to_date,
            needs_push=needs_push,
            needs_pull=needs_pull,
        )

    async def get_health_metrics(
        self, repo: LocalRepository, ctx: Optional["Context"] = None
    ) -> dict[str, Any]:
        """Get repository health metrics."""
        status = await self.get_repository_status(repo, ctx)

        return {
            "total_outstanding_files": status.total_outstanding_changes,
            "has_uncommitted_changes": status.working_directory.has_changes,
            "has_staged_changes": status.staged_changes.ready_to_commit,
            "staged_changes_count": status.staged_changes.total_staged,
            "unpushed_commits_count": len(status.unpushed_commits),
            "stashed_changes_count": len(status.stashed_changes),
            "branch_sync_status": status.branch_status.sync_status,
            "needs_attention": status.has_outstanding_work,
        }

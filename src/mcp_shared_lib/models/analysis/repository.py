"""Repository status models."""

from pydantic import BaseModel, Field

from mcp_shared_lib.models.git.changes import StagedChanges, WorkingDirectoryChanges
from mcp_shared_lib.models.git.commits import StashedChanges, UnpushedCommit
from mcp_shared_lib.models.git.repository import LocalRepository


class BranchStatus(BaseModel):
    """Status of a git branch relative to its upstream."""

    current_branch: str = Field(..., description="Current branch name")
    upstream_branch: str | None = Field(None, description="Upstream branch reference")
    ahead_by: int = Field(0, ge=0, description="Commits ahead of upstream")
    behind_by: int = Field(0, ge=0, description="Commits behind upstream")
    is_up_to_date: bool = Field(True, description="Branch is up to date with upstream")
    needs_push: bool = Field(False, description="Branch needs to be pushed")
    needs_pull: bool = Field(False, description="Branch needs to be pulled")

    @property
    def sync_status(self) -> str:
        """Get a human-readable sync status."""
        if self.is_up_to_date:
            return "up to date"
        elif self.ahead_by > 0 and self.behind_by > 0:
            return f"diverged ({self.ahead_by} ahead, {self.behind_by} behind)"
        elif self.ahead_by > 0:
            return f"{self.ahead_by} commit(s) ahead"
        elif self.behind_by > 0:
            return f"{self.behind_by} commit(s) behind"
        else:
            return "unknown"


class RepositoryStatus(BaseModel):
    """Complete status of a repository's outstanding changes."""

    repository: LocalRepository = Field(..., description="Repository information")
    working_directory: WorkingDirectoryChanges = Field(
        ..., description="Working directory changes"
    )
    staged_changes: StagedChanges = Field(..., description="Staged changes")
    unpushed_commits: list[UnpushedCommit] = Field(
        default_factory=list, description="Commits not yet pushed"
    )
    stashed_changes: list[StashedChanges] = Field(
        default_factory=list, description="Stashed changes"
    )
    branch_status: BranchStatus = Field(..., description="Branch status information")

    @property
    def has_outstanding_work(self) -> bool:
        """Check if there's any outstanding work in the repository."""
        return (
            bool(self.working_directory.has_changes)
            or bool(self.staged_changes.ready_to_commit)
            or len(self.unpushed_commits) > 0
            or len(self.stashed_changes) > 0
        )

    @property
    def total_outstanding_changes(self) -> int:
        """Total number of outstanding changes across all categories."""
        return (  # type: ignore[no-any-return]
            int(self.working_directory.total_files)  # type: ignore
            + int(self.staged_changes.total_staged)  # type: ignore
            + len(self.unpushed_commits)
            + len(self.stashed_changes)
        )

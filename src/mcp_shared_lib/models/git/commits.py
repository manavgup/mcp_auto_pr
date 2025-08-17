"""Git commit and stash models."""

from datetime import datetime

from pydantic import BaseModel, Field


class UnpushedCommit(BaseModel):
    """Represents a commit that hasn't been pushed to remote."""

    sha: str = Field(..., description="Commit SHA")
    message: str = Field(..., description="Commit message")
    author: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email")
    date: datetime = Field(..., description="Commit date")
    files_changed: list[str] = Field(
        default_factory=list, description="List of changed files"
    )
    insertions: int = Field(0, ge=0, description="Number of insertions")
    deletions: int = Field(0, ge=0, description="Number of deletions")

    @property
    def short_sha(self) -> str:
        """Get short version of SHA."""
        return self.sha[:8]

    @property
    def short_message(self) -> str:
        """Get first line of commit message."""
        return str(self.message).split("\n", maxsplit=1)[0]

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return self.insertions + self.deletions


class StashedChanges(BaseModel):
    """Represents stashed changes."""

    stash_index: int = Field(..., ge=0, description="Stash index")
    message: str = Field(..., description="Stash message")
    branch: str = Field(..., description="Branch where stash was created")
    date: datetime = Field(..., description="Stash creation date")
    files_affected: list[str] = Field(
        default_factory=list, description="Files affected by stash"
    )

    @property
    def stash_name(self) -> str:
        """Get stash name (stash@{index})."""
        return f"stash@{{{self.stash_index}}}"

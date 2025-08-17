"""Git repository related data models.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

This module defines data models representing git remotes, branches,
and local repository metadata.
"""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo


class GitRemote(BaseModel):
    """Represents a git remote."""

    name: str = Field(..., description="Remote name (e.g., 'origin')")
    url: str = Field(..., description="Remote URL")
    fetch_url: str = Field(..., description="Fetch URL")
    push_url: str = Field(..., description="Push URL")

    @field_validator("push_url", mode="before")
    @classmethod
    def set_push_url(cls, v: str | None, info: FieldValidationInfo) -> str:
        """Set push_url to url if not provided."""
        if not v and info.data and "url" in info.data:
            return str(info.data["url"])
        return v or ""


class GitBranch(BaseModel):
    """Represents a git branch."""

    name: str = Field(..., description="Branch name")
    is_current: bool = Field(False, description="Is this the current branch")
    is_remote: bool = Field(False, description="Is this a remote branch")
    upstream: str | None = Field(None, description="Upstream branch reference")
    ahead_count: int = Field(0, ge=0, description="Commits ahead of upstream")
    behind_count: int = Field(0, ge=0, description="Commits behind upstream")
    last_commit_sha: str | None = Field(None, description="Last commit SHA")
    last_commit_date: str | None = Field(None, description="Last commit date")


class LocalRepository(BaseModel):
    """Represents a local git repository."""

    path: Path = Field(..., description="Repository root path")
    name: str = Field(..., description="Repository name")
    current_branch: str = Field(..., description="Current active branch")
    remote_url: str | None = Field(default=None, description="Remote origin URL")
    remote_branches: list[str] = Field(
        default_factory=list, description="Remote branches"
    )
    is_dirty: bool = Field(default=False, description="Has uncommitted changes")
    is_bare: bool = Field(default=False, description="Is bare repository")
    head_commit: str = Field(..., description="HEAD commit SHA")
    upstream_branch: str | None = Field(default=None, description="Upstream branch")
    remotes: list[GitRemote] = Field(
        default_factory=list, description="Repository remotes"
    )
    branches: list[GitBranch] = Field(
        default_factory=list, description="Repository branches"
    )

    @field_validator("path")
    @classmethod
    def validate_git_repo(cls, v: Path | str) -> Path:
        """Validate that path is a git repository."""
        if not isinstance(v, Path):
            v = Path(v)

        git_dir = v / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a git repository: {v}")
        return v

    @field_validator("name", mode="before")
    @classmethod
    def set_name(cls, v: str | None, info: FieldValidationInfo) -> str:
        """Set repository name from path if not provided."""
        if not v and info.data and "path" in info.data:
            path = info.data["path"]
            if isinstance(path, str | Path):
                return Path(path).name
        return v or "unknown"

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True

    @property
    def is_clean(self) -> bool:
        """Check if repository is clean (opposite of dirty)."""
        return not self.is_dirty

    @property
    def has_remote(self) -> bool:
        """Check if repository has any remotes."""
        return len(self.remotes) > 0

    @property
    def origin_remote(self) -> GitRemote | None:
        """Get the origin remote if it exists."""
        for remote in self.remotes:
            if remote.name == "origin":
                return remote
        return None

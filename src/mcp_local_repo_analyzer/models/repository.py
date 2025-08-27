"""Repository models for local repository analysis."""

from pathlib import Path

from pydantic import BaseModel, Field


class LocalRepository(BaseModel):
    """Local repository information."""

    path: Path = Field(..., description="Repository path")
    name: str = Field(..., description="Repository name")
    current_branch: str = Field(..., description="Current branch name")
    head_commit: str = Field("unknown", description="Current HEAD commit hash")
    remote_url: str | None = Field(None, description="Primary remote URL")
    remote_branches: list[str] = Field(default_factory=list, description="Remote branch names")
    is_dirty: bool = Field(False, description="Repository has uncommitted changes")
    is_bare: bool = Field(False, description="Repository is bare")
    upstream_branch: str | None = Field(None, description="Upstream branch reference")
    remotes: list[str] = Field(default_factory=list, description="Remote names")
    branches: list[str] = Field(default_factory=list, description="Local branch names")

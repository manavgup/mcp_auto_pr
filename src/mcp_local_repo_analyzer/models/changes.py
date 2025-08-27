"""Git changes related data models.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

This module defines data models representing git file statuses, diffs,
working directory changes, staged changes, unpushed commits, and stashed changes.
"""

from pydantic import BaseModel, Field, computed_field

from .files import FileStatus


class WorkingDirectoryChanges(BaseModel):
    """Status of working directory changes."""

    modified_files: list[FileStatus] = Field(default_factory=list, description="Modified files")
    added_files: list[FileStatus] = Field(default_factory=list, description="Added files")
    deleted_files: list[FileStatus] = Field(default_factory=list, description="Deleted files")
    renamed_files: list[FileStatus] = Field(default_factory=list, description="Renamed files")
    untracked_files: list[FileStatus] = Field(default_factory=list, description="Untracked files")

    @computed_field
    def total_files(self) -> int:
        """Total number of changed files."""
        return (
            len(self.modified_files)
            + len(self.added_files)
            + len(self.deleted_files)
            + len(self.renamed_files)
            + len(self.untracked_files)
        )

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return self.total_files > 0  # type: ignore

    @computed_field
    def all_files(self) -> list[FileStatus]:
        """Get all changed files as a single list."""
        return self.modified_files + self.added_files + self.deleted_files + self.renamed_files + self.untracked_files


class StagedChanges(BaseModel):
    """Changes staged for commit."""

    staged_files: list[FileStatus] = Field(default_factory=list, description="Staged files")

    @computed_field
    def total_staged(self) -> int:
        """Total number of staged files."""
        return len(self.staged_files)

    @property
    def ready_to_commit(self) -> bool:
        """Check if there are staged changes ready to commit."""
        return self.total_staged > 0  # type: ignore

    @computed_field
    def total_additions(self) -> int:
        """Total lines added across all staged files."""
        return sum(f.lines_added for f in self.staged_files)

    @computed_field
    def total_deletions(self) -> int:
        """Total lines deleted across all staged files."""
        return sum(f.lines_deleted for f in self.staged_files)

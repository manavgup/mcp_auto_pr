"""Git file status and diff models."""

from typing import Literal, cast

from pydantic import BaseModel, Field


class FileStatus(BaseModel):
    """Represents the status of a single file."""

    path: str = Field(..., description="File path relative to repository root")
    status_code: str = Field(..., description="Git status code (M, A, D, R, etc.)")
    staged: bool = Field(False, description="File is staged for commit")
    working_tree_status: str | None = Field(None, description="Working tree status")
    index_status: str | None = Field(None, description="Index status")
    lines_added: int = Field(0, ge=0, description="Lines added")
    lines_deleted: int = Field(0, ge=0, description="Lines deleted")
    is_binary: bool = Field(False, description="File is binary")
    old_path: str | None = Field(None, description="Original path for renames")

    @property
    def total_changes(self) -> int:
        """Total number of line changes."""
        return self.lines_added + self.lines_deleted

    @property
    def status_description(self) -> str:
        """Human-readable status description."""
        status_map = {
            "M": "Modified",
            "A": "Added",
            "D": "Deleted",
            "R": "Renamed",
            "C": "Copied",
            "U": "Unmerged",
            "?": "Untracked",
            "!": "Ignored",
        }
        return status_map.get(self.status_code, self.status_code)

    @property
    def change_type(
        self,
    ) -> Literal["addition", "modification", "deletion", "rename", "copy", "untracked"]:
        """Categorize the type of change."""
        mapping = {
            "A": "addition",
            "M": "modification",
            "D": "deletion",
            "R": "rename",
            "C": "copy",
            "?": "untracked",
        }
        return cast(
            Literal["addition", "modification", "deletion", "rename", "copy", "untracked"],
            mapping.get(self.status_code, "modification"),
        )

    @property
    def file_type(self) -> str:
        """Determine file type based on extension."""
        if not self.path:
            return "unknown"

        # Get file extension
        ext = self.path.split(".")[-1].lower() if "." in self.path else ""

        # Map extensions to file types
        if ext in ["py", "pyx", "pyi"]:
            return "python"
        elif ext in ["js", "ts", "jsx", "tsx"]:
            return "javascript"
        elif ext in ["html", "htm", "xml"]:
            return "markup"
        elif ext in ["css", "scss", "sass", "less"]:
            return "stylesheet"
        elif ext in ["md", "rst", "txt"]:
            return "documentation"
        elif ext in ["json", "yaml", "yml", "toml", "ini", "cfg"]:
            return "configuration"
        elif ext in ["sh", "bash", "zsh", "fish"]:
            return "shell"
        elif ext in ["sql", "db", "sqlite"]:
            return "database"
        elif ext in ["png", "jpg", "jpeg", "gif", "svg", "ico"]:
            return "image"
        elif ext in ["pdf", "doc", "docx"]:
            return "document"
        elif self.path.startswith("."):
            return "dotfile"
        elif "/" not in self.path and "." not in self.path:
            return "executable"
        else:
            return ext if ext else "unknown"


class DiffHunk(BaseModel):
    """Represents a single diff hunk."""

    old_start: int = Field(..., ge=0, description="Starting line in old file")
    old_lines: int = Field(..., ge=0, description="Number of lines in old file")
    new_start: int = Field(..., ge=0, description="Starting line in new file")
    new_lines: int = Field(..., ge=0, description="Number of lines in new file")
    content: str = Field(..., description="Hunk content")
    context_lines: list[str] = Field(default_factory=list, description="Context lines")


class FileDiff(BaseModel):
    """Represents a file diff with detailed information."""

    file_path: str = Field(..., description="File path")
    old_path: str | None = Field(None, description="Original path for renames")
    diff_content: str = Field(..., description="Full diff content")
    hunks: list[DiffHunk] = Field(default_factory=list, description="Diff hunks")
    is_binary: bool = Field(False, description="Is binary file")
    lines_added: int = Field(0, ge=0, description="Lines added")
    lines_deleted: int = Field(0, ge=0, description="Lines deleted")
    file_mode_old: str | None = Field(None, description="Old file mode")
    file_mode_new: str | None = Field(None, description="New file mode")

    @property
    def total_changes(self) -> int:
        """Total number of line changes."""
        return self.lines_added + self.lines_deleted

    @property
    def is_large_change(self) -> bool:
        """Check if this is a large change (>100 lines)."""
        return self.total_changes > 100

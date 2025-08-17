"""File categorization models."""

from pydantic import BaseModel, Field


class ChangeCategorization(BaseModel):
    """Categorization of changed files by type."""

    critical_files: list[str] = Field(
        default_factory=list, description="Config, core files that are critical"
    )
    source_code: list[str] = Field(
        default_factory=list, description="Source code files"
    )
    documentation: list[str] = Field(
        default_factory=list, description="Documentation files"
    )
    tests: list[str] = Field(default_factory=list, description="Test files")
    configuration: list[str] = Field(
        default_factory=list, description="Configuration files"
    )
    other: list[str] = Field(
        default_factory=list, description="Other files that don't fit categories"
    )

    @property
    def total_files(self) -> int:
        """Total number of categorized files."""
        return (
            len(self.critical_files)
            + len(self.source_code)
            + len(self.documentation)
            + len(self.tests)
            + len(self.configuration)
            + len(self.other)
        )

    @property
    def has_critical_changes(self) -> bool:
        """Check if there are changes to critical files."""
        return len(self.critical_files) > 0

"""PR recommendation models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# Cross-bounded context import (ideally should be avoided in DDD)
from mcp_local_repo_analyzer.models import FileStatus, OutstandingChangesAnalysis


class ChangeGroup(BaseModel):
    """A group of related changes."""

    id: str = Field(..., description="Unique group identifier")
    files: list[FileStatus] = Field(..., description="Files in this group")
    category: str = Field(..., description="Category (feature, bugfix, refactor, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in grouping")
    reasoning: str = Field(..., description="Why these files belong together")
    semantic_similarity: float = Field(default=0.0, description="Semantic similarity score")
    dependencies: list[str] = Field(default_factory=list, description="Other group IDs this depends on")

    @property
    def total_changes(self) -> int:
        """Get the total number of changes across all files in the group."""
        return sum(f.total_changes for f in self.files)

    @property
    def file_paths(self) -> list[str]:
        """Get a list of file paths in the group."""
        return [f.path for f in self.files]


class PRRecommendation(BaseModel):
    """A recommendation for a single PR."""

    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Suggested PR title")
    description: str = Field(..., description="Detailed PR description")
    files: list[str] = Field(..., description="Files to include")
    branch_name: str = Field(..., description="Suggested branch name")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority")
    estimated_review_time: int = Field(..., description="Review time in minutes")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Risk level")
    reasoning: str = Field(..., description="Grouping rationale")
    dependencies: list[str] = Field(default_factory=list, description="Other PR IDs")
    labels: list[str] = Field(default_factory=list, description="Suggested labels")

    # Metrics
    total_lines_changed: int = Field(0, description="Total lines changed")
    files_count: int = Field(0, description="Number of files")

    @property
    def complexity_score(self) -> int:
        """Simple complexity score based on files and lines."""
        return min(10, (self.files_count * 2) + (self.total_lines_changed // 100))


class PRStrategy(BaseModel):
    """Complete PR recommendation strategy."""

    strategy_name: str = Field(..., description="Strategy used")
    source_analysis: OutstandingChangesAnalysis = Field(..., description="Input analysis")
    change_groups: list[ChangeGroup] = Field(..., description="Identified groups")
    recommended_prs: list[PRRecommendation] = Field(..., description="Final recommendations")
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_prs(self) -> int:
        """Get the total number of PRs recommended."""
        return len(self.recommended_prs)

    @property
    def average_pr_size(self) -> float:
        """Get the average number of files per PR."""
        if not self.recommended_prs:
            return 0.0
        return sum(pr.files_count for pr in self.recommended_prs) / len(self.recommended_prs)

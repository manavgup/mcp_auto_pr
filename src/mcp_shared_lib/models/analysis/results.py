"""Analysis result data models.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

This module defines data models for analysis results including branch status,
change categorization, risk assessment, repository status, and outstanding changes analysis.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mcp_shared_lib.models.analysis.categorization import ChangeCategorization
from mcp_shared_lib.models.analysis.repository import RepositoryStatus
from mcp_shared_lib.models.analysis.risk import RiskAssessment


class OutstandingChangesAnalysis(BaseModel):
    """Comprehensive analysis of all outstanding changes in a repository."""

    repository_path: Path = Field(..., description="Path to the analyzed repository")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When this analysis was performed"
    )
    total_outstanding_files: int = Field(
        0, ge=0, description="Total number of files with outstanding changes"
    )
    categories: ChangeCategorization = Field(
        default_factory=ChangeCategorization,
        description="Categorization of changed files",
    )
    risk_assessment: RiskAssessment = Field(
        ..., description="Risk assessment of the changes"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommended actions based on analysis"
    )
    summary: str = Field(..., description="Human-readable summary of the analysis")
    repository_status: RepositoryStatus | None = Field(
        None, description="Complete repository status (optional)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the analysis"
    )

    @property
    def is_ready_for_commit(self) -> bool:
        """Check if changes are ready to be committed."""
        if not self.repository_status:
            return False
        return (
            bool(self.repository_status.working_directory.has_changes)
            and not self.risk_assessment.is_high_risk
        )

    @property
    def is_ready_for_push(self) -> bool:
        """Check if repository is ready to be pushed."""
        if not self.repository_status:
            return False
        return (
            len(self.repository_status.unpushed_commits) > 0
            and not bool(self.repository_status.working_directory.has_changes)
            and not bool(self.repository_status.staged_changes.ready_to_commit)
        )

    @property
    def needs_attention(self) -> bool:
        """Check if the repository needs immediate attention."""
        return (
            self.risk_assessment.is_high_risk
            or len(self.risk_assessment.potential_conflicts) > 0
            or self.total_outstanding_files > 50
        )

    class Config:
        """Pydantic configuration for the Analysis Results model.

        Allows arbitrary types to be used within the model.
        """

        arbitrary_types_allowed = True

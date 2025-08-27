"""Risk assessment models."""

from typing import Literal

from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    """Assessment of risk level for the current changes."""

    risk_level: Literal["low", "medium", "high"] = Field(..., description="Overall risk level of the changes")
    risk_factors: list[str] = Field(default_factory=list, description="Factors contributing to the risk level")
    large_changes: list[str] = Field(default_factory=list, description="Files with >100 line changes")
    potential_conflicts: list[str] = Field(default_factory=list, description="Files that might cause merge conflicts")
    binary_changes: list[str] = Field(default_factory=list, description="Binary files that have changed")

    @property
    def is_high_risk(self) -> bool:
        """Check if this is a high-risk change set."""
        return self.risk_level == "high"

    @property
    def risk_score(self) -> int:
        """Get a numeric risk score (0-10)."""
        risk_map = {"low": 2, "medium": 5, "high": 8}
        base_score = risk_map[self.risk_level]

        # Adjust based on risk factors
        if len(self.large_changes) > 5:
            base_score += 1
        if len(self.potential_conflicts) > 0:
            base_score += 1

        return min(base_score, 10)

"""Common base classes and enums for all models."""

from enum import Enum
from typing import Literal


class GitStatusCode(Enum):
    """Standard git status codes."""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNMERGED = "U"
    UNTRACKED = "?"
    IGNORED = "!"


class RiskLevel(Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PRPriority(Enum):
    """PR priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Type aliases for better type hints
RiskLevelType = Literal["low", "medium", "high"]
PRPriorityType = Literal["low", "medium", "high"]

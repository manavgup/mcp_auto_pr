"""Public API for all shared MCP model classes and enums."""

# Git-related models
# Analysis models
from mcp_shared_lib.models.analysis import (
    BranchStatus,
    ChangeCategorization,
    OutstandingChangesAnalysis,
    RepositoryStatus,
    RiskAssessment,
)

# Common enums and type aliases
from mcp_shared_lib.models.base.common import (
    GitStatusCode,
    PRPriority,
    PRPriorityType,
    RiskLevel,
    RiskLevelType,
)
from mcp_shared_lib.models.git.changes import StagedChanges, WorkingDirectoryChanges
from mcp_shared_lib.models.git.commits import StashedChanges, UnpushedCommit
from mcp_shared_lib.models.git.files import DiffHunk, FileDiff, FileStatus
from mcp_shared_lib.models.git.repository import GitBranch, GitRemote, LocalRepository

__all__ = [
    # Git
    "FileStatus",
    "WorkingDirectoryChanges",
    "StagedChanges",
    "LocalRepository",
    "GitRemote",
    "GitBranch",
    "DiffHunk",
    "FileDiff",
    "StashedChanges",
    "UnpushedCommit",
    # Analysis
    "ChangeCategorization",
    "RepositoryStatus",
    "OutstandingChangesAnalysis",
    "RiskAssessment",
    "BranchStatus",
    # Enums and Aliases
    "GitStatusCode",
    "RiskLevel",
    "PRPriority",
    "RiskLevelType",
    "PRPriorityType",
]

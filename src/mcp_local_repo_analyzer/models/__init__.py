"""Domain models for the local repository analyzer."""

# Git models
from .analysis_repository import BranchStatus, RepositoryStatus

# Analysis models
from .categorization import ChangeCategorization
from .changes import StagedChanges, WorkingDirectoryChanges
from .commits import StashedChanges, UnpushedCommit
from .files import DiffHunk, FileDiff, FileStatus
from .repository import LocalRepository
from .results import OutstandingChangesAnalysis
from .risk import RiskAssessment

__all__ = [
    # Git models
    "FileStatus",
    "FileDiff",
    "DiffHunk",
    "UnpushedCommit",
    "StashedChanges",
    "WorkingDirectoryChanges",
    "StagedChanges",
    "LocalRepository",
    # Analysis models
    "ChangeCategorization",
    "RiskAssessment",
    "OutstandingChangesAnalysis",
    "RepositoryStatus",
    "BranchStatus",
]

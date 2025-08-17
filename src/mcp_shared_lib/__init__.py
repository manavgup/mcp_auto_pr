"""MCP Shared Library - Common models and services for MCP components."""

__version__ = "0.1.0"

# Configuration
from mcp_shared_lib.config.base import BaseMCPSettings
from mcp_shared_lib.config.git_analyzer import GitAnalyzerSettings
from mcp_shared_lib.models.analysis.categorization import ChangeCategorization
from mcp_shared_lib.models.analysis.repository import RepositoryStatus
from mcp_shared_lib.models.analysis.results import OutstandingChangesAnalysis
from mcp_shared_lib.models.analysis.risk import RiskAssessment

# Models
from mcp_shared_lib.models.git.changes import StagedChanges, WorkingDirectoryChanges
from mcp_shared_lib.models.git.commits import StashedChanges, UnpushedCommit
from mcp_shared_lib.models.git.files import FileStatus
from mcp_shared_lib.models.git.repository import GitBranch, GitRemote, LocalRepository

# Services
from mcp_shared_lib.services.git.git_client import GitClient

__all__ = [
    # Models
    "FileStatus",
    "WorkingDirectoryChanges",
    "StagedChanges",
    "ChangeCategorization",
    "RiskAssessment",
    "RepositoryStatus",
    "OutstandingChangesAnalysis",
    "LocalRepository",
    "GitRemote",
    "GitBranch",
    "StashedChanges",
    "UnpushedCommit",
    # Services
    "GitClient",

    # Configuration
    "BaseMCPSettings",
    "GitAnalyzerSettings",
]

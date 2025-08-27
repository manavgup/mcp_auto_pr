"""Unit tests for unpushed commits tools."""

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client, FastMCP

from mcp_local_repo_analyzer.models.analysis_repository import BranchStatus
from mcp_local_repo_analyzer.models.commits import UnpushedCommit
from mcp_local_repo_analyzer.tools.unpushed_commits import (
    register_unpushed_commits_tools,
)


async def call_tool_helper(mcp, tool_name: str, **kwargs):
    """Helper function to call tools using the Client API."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool(tool_name, kwargs)
        return result.data


# --- Test Fixtures ---
@pytest.fixture
def temp_repo_path():
    """A pytest fixture that creates a temporary git repository path."""
    temp_dir = tempfile.mkdtemp()
    git_dir = Path(temp_dir) / ".git"
    git_dir.mkdir()
    yield str(Path(temp_dir))
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_services():
    """A pytest fixture for mock services used by the FastMCP server."""
    return {
        "git_client": AsyncMock(),
        "change_detector": AsyncMock(),
        "status_tracker": AsyncMock(),
    }


@pytest.fixture
def mcp_server(mock_services):
    """A pytest fixture for a FastMCP server with registered tools."""
    mcp = FastMCP()
    register_unpushed_commits_tools(mcp, mock_services)
    return mcp


# --- Test Classes ---
@pytest.mark.unit
class TestAnalyzeUnpushedCommits:
    """Test analyze_unpushed_commits tool."""

    @pytest.mark.asyncio
    async def test_analyze_unpushed_commits_with_commits(self, mcp_server, mock_services, temp_repo_path):
        """Test analyzing unpushed commits with actual commits."""

        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "feature/test",
            "upstream": "origin/feature/test",
        }

        mock_commits = [
            UnpushedCommit(
                sha="abc123def456",
                short_sha="abc123de",
                message="Add new feature implementation",
                short_message="Add new feature",
                author="John Doe",
                author_email="john@example.com",
                date=datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
                insertions=150,
                deletions=20,
                files_changed=["src/feature.py", "tests/test_feature.py"],
            ),
            UnpushedCommit(
                sha="def456ghi789",
                short_sha="def456gh",
                message="Fix bug in feature logic",
                short_message="Fix bug",
                author="Jane Smith",
                author_email="jane@example.com",
                date=datetime(2025, 1, 16, 14, 15, 0, tzinfo=timezone.utc),
                insertions=25,
                deletions=10,
                files_changed=["src/feature.py"],
            ),
        ]

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(
            mcp_server,
            "analyze_unpushed_commits",
            repository_path=temp_repo_path,
            max_commits=20,
        )

        assert "repository_path" in result
        assert result["branch"] == "feature/test"
        assert result["upstream_branch"] == "origin/feature/test"
        assert result["total_unpushed_commits"] == 2
        assert result["commits_analyzed"] == 2

        summary = result["summary"]
        assert summary["total_insertions"] == 175
        assert summary["total_deletions"] == 30
        assert summary["total_changes"] == 205
        assert summary["unique_authors"] == 2
        assert "John Doe" in summary["authors"]
        assert "Jane Smith" in summary["authors"]

        commits = result["commits"]
        assert len(commits) == 2
        assert commits[0]["sha"] == "abc123def456"
        assert commits[0]["short_sha"] == "abc123de"
        assert commits[0]["message"] == "Add new feature implementation"
        assert commits[0]["author"] == "John Doe"
        assert commits[0]["total_changes"] == 170
        assert len(commits[0]["files_changed"]) == 2

        assert commits[1]["sha"] == "def456ghi789"
        assert commits[1]["author"] == "Jane Smith"
        assert commits[1]["total_changes"] == 35

    @pytest.mark.asyncio
    async def test_analyze_unpushed_commits_no_commits(self, mcp_server, mock_services, temp_repo_path):
        """Test analyzing unpushed commits with no commits."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "main",
            "upstream": "origin/main",
        }

        mock_services["change_detector"].detect_unpushed_commits.return_value = []

        result = await call_tool_helper(mcp_server, "analyze_unpushed_commits", repository_path=temp_repo_path)

        assert result["total_unpushed_commits"] == 0
        assert result["commits_analyzed"] == 0
        assert len(result["commits"]) == 0
        assert result["summary"]["unique_authors"] == 0
        assert result["summary"]["total_insertions"] == 0
        assert result["summary"]["total_deletions"] == 0

    @pytest.mark.asyncio
    async def test_analyze_unpushed_commits_max_limit(self, mcp_server, mock_services, temp_repo_path):
        """Test commit limiting with max_commits parameter."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "main",
            "upstream": "origin/main",
        }

        mock_commits = []
        for i in range(15):
            mock_commits.append(
                UnpushedCommit(
                    sha=f"commit{i:02d}abcd",
                    short_sha=f"commit{i:02d}",
                    message=f"Commit {i}",
                    short_message=f"Commit {i}",
                    author="Test Author",
                    author_email="test@example.com",
                    date=datetime.now(timezone.utc),
                    insertions=10,
                    deletions=5,
                    files_changed=[f"file{i}.py"],
                )
            )

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(
            mcp_server,
            "analyze_unpushed_commits",
            repository_path=temp_repo_path,
            max_commits=10,
        )

        assert result["total_unpushed_commits"] == 15
        assert result["commits_analyzed"] == 10
        assert len(result["commits"]) == 10

        for i in range(10):
            assert result["commits"][i]["short_sha"] == f"commit{i:02d}"

    @pytest.mark.asyncio
    async def test_analyze_unpushed_commits_specific_branch(self, mcp_server, mock_services, temp_repo_path):
        """Test analyzing specific branch."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "main",
            "upstream": "origin/main",
        }

        mock_commits = [
            UnpushedCommit(
                sha="abc123",
                short_sha="abc123",
                message="Test commit",
                short_message="Test",
                author="Test Author",
                author_email="test@example.com",
                date=datetime.now(timezone.utc),
                insertions=10,
                deletions=5,
                files_changed=["test.py"],
            )
        ]

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(
            mcp_server,
            "analyze_unpushed_commits",
            repository_path=temp_repo_path,
            branch="feature/test",
        )

        assert result["branch"] == "feature/test"

    @pytest.mark.asyncio
    async def test_analyze_unpushed_commits_invalid_repo(self, mcp_server):
        """Test handling invalid repository path."""
        with (
            patch(
                "mcp_local_repo_analyzer.tools.unpushed_commits.is_git_repository",
                return_value=False,
            ),
            patch(
                "mcp_local_repo_analyzer.tools.unpushed_commits.find_git_root",
                return_value=None,
            ),
        ):
            result = await call_tool_helper(mcp_server, "analyze_unpushed_commits", repository_path="/invalid/path")

            assert "error" in result
            assert "No git repository found" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_unpushed_commits_service_error(self, mcp_server, mock_services, temp_repo_path):
        """Test handling service errors."""
        mock_services["git_client"].get_branch_info.return_value = {"current_branch": "main"}

        mock_services["change_detector"].detect_unpushed_commits.side_effect = Exception("Git error")

        result = await call_tool_helper(mcp_server, "analyze_unpushed_commits", repository_path=temp_repo_path)

        assert "error" in result
        assert "Git error" in result["error"]


@pytest.mark.unit
class TestCompareWithRemote:
    """Test compare_with_remote tool."""

    @pytest.mark.asyncio
    async def test_compare_with_remote_ahead(self, mcp_server, mock_services, temp_repo_path):
        """Test comparison when local is ahead of remote."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "feature/test",
            "upstream": "origin/feature/test",
        }

        mock_branch_status = BranchStatus(
            current_branch="feature/test",
            upstream_branch="origin/feature/test",
            ahead_by=3,
            behind_by=0,
            sync_status="ahead",
            is_up_to_date=False,
            needs_push=True,
            needs_pull=False,
        )

        mock_services["status_tracker"].get_branch_status.return_value = mock_branch_status

        result = await call_tool_helper(
            mcp_server,
            "compare_with_remote",
            remote_name="origin",
            repository_path=temp_repo_path,
        )

        assert result["branch"] == "feature/test"
        assert result["remote"] == "origin"
        assert result["upstream_branch"] == "origin/feature/test"
        assert "ahead" in result["sync_status"]
        assert result["is_up_to_date"] is False
        assert result["ahead_by"] == 3
        assert result["behind_by"] == 0
        assert result["needs_push"] is True
        assert result["needs_pull"] is False
        assert "push" in result["actions_needed"]
        assert result["sync_priority"] == "low"
        assert "Push when ready" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_compare_with_remote_behind(self, mcp_server, mock_services, temp_repo_path):
        """Test comparison when local is behind remote."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "main",
            "upstream": "origin/main",
        }

        mock_branch_status = BranchStatus(
            current_branch="main",
            upstream_branch="origin/main",
            ahead_by=0,
            behind_by=7,
            sync_status="behind",
            is_up_to_date=False,
            needs_push=False,
            needs_pull=True,
        )

        mock_services["status_tracker"].get_branch_status.return_value = mock_branch_status

        result = await call_tool_helper(
            mcp_server,
            "compare_with_remote",
            remote_name="origin",
            repository_path=temp_repo_path,
        )

        assert result["behind_by"] == 7
        assert result["needs_pull"] is True
        assert result["needs_push"] is False
        assert "pull" in result["actions_needed"]
        assert result["sync_priority"] == "medium"
        assert "Pull latest changes" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_compare_with_remote_diverged(self, mcp_server, mock_services, temp_repo_path):
        """Test comparison when branches have diverged."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "feature/branch",
            "upstream": "origin/feature/branch",
        }

        mock_branch_status = BranchStatus(
            current_branch="feature/branch",
            upstream_branch="origin/feature/branch",
            ahead_by=5,
            behind_by=3,
            sync_status="diverged",
            is_up_to_date=False,
            needs_push=True,
            needs_pull=True,
        )

        mock_services["status_tracker"].get_branch_status.return_value = mock_branch_status

        result = await call_tool_helper(mcp_server, "compare_with_remote", repository_path=temp_repo_path)

        assert result["ahead_by"] == 5
        assert result["behind_by"] == 3
        assert "diverged" in result["sync_status"]
        assert result["needs_push"] is True
        assert result["needs_pull"] is True
        assert "push" in result["actions_needed"]
        assert "pull" in result["actions_needed"]
        assert result["sync_priority"] == "high"
        assert "Pull and merge/rebase" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_compare_with_remote_up_to_date(self, mcp_server, mock_services, temp_repo_path):
        """Test comparison when branches are up to date."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "main",
            "upstream": "origin/main",
        }

        mock_branch_status = BranchStatus(
            current_branch="main",
            upstream_branch="origin/main",
            ahead_by=0,
            behind_by=0,
            sync_status="up_to_date",
            is_up_to_date=True,
            needs_push=False,
            needs_pull=False,
        )

        mock_services["status_tracker"].get_branch_status.return_value = mock_branch_status
        result = await call_tool_helper(mcp_server, "compare_with_remote", repository_path=temp_repo_path)

        assert result["is_up_to_date"] is True
        assert result["ahead_by"] == 0
        assert result["behind_by"] == 0
        assert result["needs_push"] is False
        assert result["needs_pull"] is False
        assert len(result["actions_needed"]) == 0
        assert result["sync_priority"] == "none"
        assert "up to date" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_compare_with_remote_many_commits_ahead(self, mcp_server, mock_services, temp_repo_path):
        """Test comparison with many commits ahead (medium priority)."""
        mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "feature/big",
            "upstream": "origin/feature/big",
        }

        mock_branch_status = BranchStatus(
            current_branch="feature/big",
            upstream_branch="origin/feature/big",
            ahead_by=8,
            behind_by=0,
            sync_status="ahead",
            is_up_to_date=False,
            needs_push=True,
            needs_pull=False,
        )

        mock_services["status_tracker"].get_branch_status.return_value = mock_branch_status

        result = await call_tool_helper(mcp_server, "compare_with_remote", repository_path=temp_repo_path)

        assert result["ahead_by"] == 8
        assert result["sync_priority"] == "medium"
        assert "Push commits to remote" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_compare_with_remote_error(self, mcp_server, mock_services, temp_repo_path):
        """Test error handling in remote comparison."""
        mock_services["git_client"].get_branch_info.side_effect = Exception("Remote access failed")

        result = await call_tool_helper(mcp_server, "compare_with_remote", repository_path=temp_repo_path)

        assert "error" in result
        assert "Remote access failed" in result["error"]


@pytest.mark.unit
class TestAnalyzeCommitHistory:
    """Test analyze_commit_history tool."""

    @pytest.mark.asyncio
    async def test_analyze_commit_history_comprehensive(self, mcp_server, mock_services, temp_repo_path):
        """Test comprehensive commit history analysis."""

        mock_commits = [
            UnpushedCommit(
                sha="fix123",
                short_sha="fix123",
                message="fix: resolve authentication bug",
                short_message="fix auth bug",
                author="Alice Johnson",
                author_email="alice@example.com",
                date=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                insertions=15,
                deletions=8,
                files_changed=["auth.py"],
            ),
            UnpushedCommit(
                sha="feat456",
                short_sha="feat456",
                message="feat: add new user dashboard",
                short_message="add dashboard",
                author="Bob Smith",
                author_email="bob@example.com",
                date=datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
                insertions=120,
                deletions=5,
                files_changed=["dashboard.py", "templates/dashboard.html"],
            ),
            UnpushedCommit(
                sha="docs789",
                short_sha="docs789",
                message="docs: update README with installation instructions",
                short_message="update README",
                author="Alice Johnson",
                author_email="alice@example.com",
                date=datetime(2025, 1, 16, 9, 15, 0, tzinfo=timezone.utc),
                insertions=25,
                deletions=10,
                files_changed=["README.md"],
            ),
            UnpushedCommit(
                sha="test101",
                short_sha="test101",
                message="test: add unit tests for dashboard",
                short_message="add tests",
                author="Charlie Brown",
                author_email="charlie@example.com",
                date=datetime(2025, 1, 16, 16, 45, 0, tzinfo=timezone.utc),
                insertions=80,
                deletions=2,
                files_changed=["test_dashboard.py"],
            ),
            UnpushedCommit(
                sha="refactor202",
                short_sha="refactor202",
                message="refactor: clean up old utility functions",
                short_message="clean utils",
                author="Bob Smith",
                author_email="bob@example.com",
                date=datetime(2025, 1, 17, 11, 20, 0, tzinfo=timezone.utc),
                insertions=5,
                deletions=45,
                files_changed=["utils.py"],
            ),
        ]

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(
            mcp_server,
            "analyze_commit_history",
            repository_path=temp_repo_path,
            max_commits=50,
        )

        assert result["total_commits_found"] == 5
        assert result["commits_analyzed"] == 5

        stats = result["statistics"]
        assert stats["total_authors"] == 3
        assert stats["total_insertions"] == 245
        assert stats["total_deletions"] == 70
        expected_avg = (23 + 125 + 35 + 82 + 50) / 5
        assert abs(stats["average_changes_per_commit"] - expected_avg) < 0.1

        authors = result["authors"]
        assert "Alice Johnson" in authors
        assert "Bob Smith" in authors
        assert "Charlie Brown" in authors
        assert authors["Alice Johnson"]["commits"] == 2
        assert authors["Bob Smith"]["commits"] == 2
        assert authors["Charlie Brown"]["commits"] == 1

        daily = result["daily_activity"]
        assert "2025-01-15" in daily
        assert "2025-01-16" in daily
        assert "2025-01-17" in daily
        assert daily["2025-01-15"] == 2
        assert daily["2025-01-16"] == 2
        assert daily["2025-01-17"] == 1

        patterns = result["message_patterns"]
        assert patterns["fix"] == 1
        assert patterns["feat"] == 1
        assert patterns["docs"] == 1
        assert patterns["test"] == 1
        assert patterns["refactor"] == 1
        assert patterns["other"] == 0

        recent = result["recent_commits"]
        assert len(recent) == 5
        assert recent[0]["sha"] == "fix123"
        assert recent[1]["sha"] == "feat456"

    @pytest.mark.asyncio
    async def test_analyze_commit_history_author_filter(self, mcp_server, mock_services, temp_repo_path):
        """Test commit history with author filtering."""

        mock_commits = [
            UnpushedCommit(
                sha="alice1",
                short_sha="alice1",
                message="Alice commit 1",
                short_message="Alice 1",
                author="Alice Johnson",
                author_email="alice@example.com",
                date=datetime.now(timezone.utc),
                insertions=10,
                deletions=5,
                files_changed=["file1.py"],
            ),
            UnpushedCommit(
                sha="bob1",
                short_sha="bob1",
                message="Bob commit 1",
                short_message="Bob 1",
                author="Bob Smith",
                author_email="bob@example.com",
                date=datetime.now(timezone.utc),
                insertions=20,
                deletions=10,
                files_changed=["file2.py"],
            ),
            UnpushedCommit(
                sha="alice2",
                short_sha="alice2",
                message="Alice commit 2",
                short_message="Alice 2",
                author="Alice Johnson",
                author_email="alice@example.com",
                date=datetime.now(timezone.utc),
                insertions=15,
                deletions=8,
                files_changed=["file3.py"],
            ),
        ]

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(
            mcp_server,
            "analyze_commit_history",
            repository_path=temp_repo_path,
            author="Alice",
        )

        assert result["total_commits_found"] == 3
        assert result["commits_analyzed"] == 2
        assert result["statistics"]["total_authors"] == 1
        assert "Alice Johnson" in result["authors"]
        assert "Bob Smith" not in result["authors"]
        assert result["analysis_filters"]["author"] == "Alice"

    @pytest.mark.asyncio
    async def test_analyze_commit_history_max_commits_limit(self, mcp_server, mock_services, temp_repo_path):
        """Test commit history with max commits limit."""

        mock_commits = []
        for i in range(25):
            mock_commits.append(
                UnpushedCommit(
                    sha=f"commit{i:03d}",
                    short_sha=f"c{i:03d}",
                    message=f"Commit {i}",
                    short_message=f"Commit {i}",
                    author="Test Author",
                    author_email="test@example.com",
                    date=datetime.now(timezone.utc),
                    insertions=10,
                    deletions=5,
                    files_changed=[f"file{i}.py"],
                )
            )

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(
            mcp_server,
            "analyze_commit_history",
            repository_path=temp_repo_path,
            max_commits=15,
        )

        assert result["total_commits_found"] == 25
        assert result["commits_analyzed"] == 15
        assert len(result["recent_commits"]) == 10

    @pytest.mark.asyncio
    async def test_analyze_commit_history_message_patterns(self, mcp_server, mock_services, temp_repo_path):
        """Test message pattern categorization."""

        mock_commits = [
            UnpushedCommit(
                sha="fix1",
                short_sha="fix1",
                message="fix: critical bug in payment",
                short_message="fix",
                author="Dev",
                author_email="dev@test.com",
                date=datetime.now(timezone.utc),
                insertions=5,
                deletions=2,
                files_changed=["payment.py"],
            ),
            UnpushedCommit(
                sha="feat1",
                short_sha="feat1",
                message="feat: add new search feature",
                short_message="feat",
                author="Dev",
                author_email="dev@test.com",
                date=datetime.now(timezone.utc),
                insertions=50,
                deletions=0,
                files_changed=["search.py"],
            ),
            UnpushedCommit(
                sha="doc1",
                short_sha="doc1",
                message="docs: update documentation for API",
                short_message="docs",
                author="Dev",
                author_email="dev@test.com",
                date=datetime.now(timezone.utc),
                insertions=20,
                deletions=5,
                files_changed=["docs.md"],
            ),
            UnpushedCommit(
                sha="test1",
                short_sha="test1",
                message="test: add test cases for validator",
                short_message="test",
                author="Dev",
                author_email="dev@test.com",
                date=datetime.now(timezone.utc),
                insertions=30,
                deletions=0,
                files_changed=["test_val.py"],
            ),
            UnpushedCommit(
                sha="refactor1",
                short_sha="refactor1",
                message="refactor: clean up old utility functions",
                short_message="refactor",
                author="Dev",
                author_email="dev@test.com",
                date=datetime.now(timezone.utc),
                insertions=15,
                deletions=25,
                files_changed=["user.py"],
            ),
            UnpushedCommit(
                sha="other1",
                short_sha="other1",
                message="random commit message",
                short_message="random",
                author="Dev",
                author_email="dev@test.com",
                date=datetime.now(timezone.utc),
                insertions=10,
                deletions=10,
                files_changed=["random.py"],
            ),
        ]

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(mcp_server, "analyze_commit_history", repository_path=temp_repo_path)

        patterns = result["message_patterns"]
        assert patterns["fix"] == 1
        assert patterns["feat"] == 1
        assert patterns["docs"] == 1
        assert patterns["test"] == 1
        assert patterns["refactor"] == 1
        assert patterns["other"] == 1

    @pytest.mark.asyncio
    async def test_analyze_commit_history_since_parameter(self, mcp_server, mock_services, temp_repo_path):
        """Test since parameter (currently not implemented)."""

        mock_commits = [
            UnpushedCommit(
                sha="test1",
                short_sha="test1",
                message="test commit",
                short_message="test",
                author="Dev",
                author_email="dev@test.com",
                date=datetime.now(timezone.utc),
                insertions=10,
                deletions=5,
                files_changed=["test.py"],
            )
        ]

        mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        result = await call_tool_helper(
            mcp_server,
            "analyze_commit_history",
            repository_path=temp_repo_path,
            since="2025-01-01",
        )

        assert result["analysis_filters"]["since"] == "2025-01-01"
        assert result["commits_analyzed"] == 1

    @pytest.mark.asyncio
    async def test_analyze_commit_history_no_commits(self, mcp_server, mock_services, temp_repo_path):
        """Test commit history analysis with no commits."""

        mock_services["change_detector"].detect_unpushed_commits.return_value = []

        result = await call_tool_helper(mcp_server, "analyze_commit_history", repository_path=temp_repo_path)

        assert result["total_commits_found"] == 0
        assert result["commits_analyzed"] == 0
        assert result["statistics"]["total_authors"] == 0
        assert result["statistics"]["average_changes_per_commit"] == 0
        assert len(result["recent_commits"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_commit_history_error(self, mcp_server, mock_services, temp_repo_path):
        """Test error handling in commit history analysis."""

        mock_services["change_detector"].detect_unpushed_commits.side_effect = Exception("History error")

        result = await call_tool_helper(mcp_server, "analyze_commit_history", repository_path=temp_repo_path)

        assert "error" in result
        assert "History error" in result["error"]


@pytest.mark.unit
class TestUnpushedCommitsIntegration:
    """Integration tests for unpushed commits tools."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.git_dir = Path(self.temp_dir) / ".git"
        self.git_dir.mkdir()
        self.repo_path = str(Path(self.temp_dir))

        self.mock_services = {
            "git_client": AsyncMock(),
            "change_detector": AsyncMock(),
            "status_tracker": AsyncMock(),
        }
        self.mcp = FastMCP()
        register_unpushed_commits_tools(self.mcp, self.mock_services)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_unpushed_commits_workflow_integration(self):
        """Test complete unpushed commits workflow."""

        self.mock_services["git_client"].get_branch_info.return_value = {
            "current_branch": "feature/integration",
            "upstream": "origin/feature/integration",
        }

        mock_commits = [
            UnpushedCommit(
                sha="commit1",
                short_sha="commit1",
                message="feat: Initial feature implementation",  # Corrected message
                short_message="Initial feature",
                author="Developer",
                author_email="dev@example.com",
                date=datetime.now(timezone.utc),
                insertions=100,
                deletions=20,
                files_changed=["feature.py", "test_feature.py"],
            ),
            UnpushedCommit(
                sha="commit2",
                short_sha="commit2",
                message="docs: Add documentation",  # Corrected message
                short_message="Add docs",
                author="Developer",
                author_email="dev@example.com",
                date=datetime.now(timezone.utc),
                insertions=50,
                deletions=5,
                files_changed=["README.md"],
            ),
        ]

        self.mock_services["change_detector"].detect_unpushed_commits.return_value = mock_commits

        mock_branch_status = BranchStatus(
            current_branch="feature/integration",
            upstream_branch="origin/feature/integration",
            ahead_by=2,
            behind_by=0,
            sync_status="ahead",
            is_up_to_date=False,
            needs_push=True,
            needs_pull=False,
        )

        self.mock_services["status_tracker"].get_branch_status.return_value = mock_branch_status

        # 1. Analyze unpushed commits
        analyze_result = await call_tool_helper(self.mcp, "analyze_unpushed_commits", repository_path=self.repo_path)

        assert analyze_result["total_unpushed_commits"] == 2
        assert analyze_result["summary"]["total_insertions"] == 150

        # 2. Compare with remote
        compare_result = await call_tool_helper(self.mcp, "compare_with_remote", repository_path=self.repo_path)

        assert compare_result["needs_push"] is True
        assert compare_result["ahead_by"] == 2
        assert "push" in compare_result["actions_needed"]

        # 3. Analyze commit history
        history_result = await call_tool_helper(self.mcp, "analyze_commit_history", repository_path=self.repo_path)

        assert history_result["commits_analyzed"] == 2
        assert history_result["statistics"]["total_authors"] == 1
        assert history_result["message_patterns"]["feat"] == 1
        assert history_result["message_patterns"]["docs"] == 1

    @pytest.mark.asyncio
    async def test_unpushed_commits_tools_registration(self):
        """Test that all unpushed commits tools are properly registered."""

        tools = await self.mcp.get_tools()
        tool_names = [tool.name for tool in tools.values()]

        assert "analyze_unpushed_commits" in tool_names
        assert "compare_with_remote" in tool_names
        assert "analyze_commit_history" in tool_names

        assert await self.mcp.get_tool("analyze_unpushed_commits") is not None
        assert await self.mcp.get_tool("compare_with_remote") is not None
        assert await self.mcp.get_tool("analyze_commit_history") is not None

    @pytest.mark.asyncio
    async def test_unpushed_commits_error_consistency(self):
        """Test consistent error handling across all tools."""

        tools_to_test = [
            "analyze_unpushed_commits",
            "compare_with_remote",
            "analyze_commit_history",
        ]

        with (
            patch(
                "mcp_local_repo_analyzer.tools.unpushed_commits.is_git_repository",
                return_value=False,
            ),
            patch(
                "mcp_local_repo_analyzer.tools.unpushed_commits.find_git_root",
                return_value=None,
            ),
        ):
            for tool_name in tools_to_test:
                result = await call_tool_helper(self.mcp, tool_name, repository_path="/invalid/path")

                assert "error" in result
                assert "No git repository found" in result["error"]

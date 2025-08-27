"""FastMCP tools for unpushed commits analysis with enhanced return types."""

import time
from pathlib import Path
from typing import Any

from fastmcp import Context, FastMCP
from pydantic import Field

from mcp_local_repo_analyzer.models.repository import LocalRepository
from shared.utils import find_git_root, is_git_repository


def register_unpushed_commits_tools(mcp: FastMCP, services: dict[str, Any]) -> None:
    """Register unpushed commits analysis tools."""

    @mcp.tool()
    async def analyze_unpushed_commits(
        ctx: Context,
        repository_path: str = Field(default=".", description="Path to git repository"),
        branch: str | None = Field(None, description="Specific branch to analyze (default: current branch)"),
        max_commits: int = Field(20, ge=1, le=100, description="Maximum number of commits to analyze"),
    ) -> dict[str, Any]:
        """Analyze commits that haven't been pushed to remote.

        Returns detailed information about local commits that exist locally
        but haven't been pushed to the remote repository.

        **Return Type**: Dict with unpushed commits information
        ```python
        {
            "repository_path": str,           # Pass to other repository tools
            "branch": str,                    # Branch that was analyzed
            "upstream_branch": str | None,    # Upstream branch reference
            "total_unpushed_commits": int,    # Total unpushed commits - use for push decisions
            "commits_analyzed": int,          # Number included in results (limited by max_commits)
            "summary": {                      # Commit statistics for analysis
                "total_insertions": int, "total_deletions": int, "total_changes": int,
                "unique_authors": int, "authors": List[str]
            },
            "commits": List[{                 # Individual commit information
                "sha": str, "short_sha": str, "message": str, "short_message": str,
                "author": str, "author_email": str, "date": str,
                "insertions": int, "deletions": int, "total_changes": int,
                "files_changed": List[str]
            }]
        }
        ```

        **Key Fields for Chaining**:
        - `total_unpushed_commits` (int): Use to determine if push is needed (>0 means unpushed work)
        - `repository_path` (str): Pass to push readiness or remote comparison tools
        - `branch` (str): Current branch for branch-specific operations
        - `commits` (list): Individual commit data for detailed analysis
        - `summary.unique_authors` (int): Use for collaboration analysis

        **Common Chaining Patterns**:
        ```python
        # Basic push workflow
        unpushed_result = await analyze_unpushed_commits(repo_path)
        if unpushed_result["total_unpushed_commits"] > 0:
            push_check = await get_push_readiness(unpushed_result["repository_path"])
            if push_check["ready_to_push"]:
                remote_compare = await compare_with_remote("origin", unpushed_result["repository_path"])

        # Collaboration analysis
        if unpushed_result["summary"]["unique_authors"] > 1:
            # Multiple authors - check for conflicts before push
            conflicts = await detect_conflicts(unpushed_result["repository_path"])

        # Commit quality analysis
        for commit in unpushed_result["commits"]:
            if commit["total_changes"] > 500:
                # Large commit - might need splitting for PR
                pass
        ```

        **Decision Points**:
        - `total_unpushed_commits > 0`: Has unpushed work → check push readiness
        - `total_unpushed_commits == 0`: No unpushed work → focus on local changes
        - `total_unpushed_commits > 10`: Many commits → consider squashing/organizing
        - `summary.unique_authors > 1`: Multiple authors → check for collaboration issues
        """
        start_time = time.time()
        await ctx.info(f"Starting unpushed commits analysis for: {repository_path}")

        repo_path = Path(repository_path).resolve()
        if not is_git_repository(repo_path):
            git_root = find_git_root(repo_path)
            if not git_root:
                await ctx.error(f"No git repository found at or above {repo_path}")
                return {"error": f"No git repository found at or above {repo_path}"}
            repo_path = git_root
            await ctx.debug(f"Found git repository at: {repo_path}")

        try:
            await ctx.report_progress(0, 5)
            await ctx.debug("Getting branch information")

            # Get branch info first
            # Access services from closure
            current_services = services
            branch_info = await services["git_client"].get_branch_info(repo_path, ctx)
            current_branch = branch or branch_info.get("current_branch", "main")

            await ctx.info(f"Analyzing branch: {current_branch}")

            await ctx.report_progress(1, 5)
            await ctx.debug("Creating repository model")

            repo = LocalRepository(
                path=repo_path,
                name=repo_path.name,
                current_branch=current_branch,
                head_commit="unknown",
                remote_url=None,
                is_dirty=False,
                is_bare=False,
                upstream_branch=None,
            )

            await ctx.report_progress(2, 5)
            await ctx.debug("Detecting unpushed commits")

            # Use existing UnpushedCommit model
            unpushed_commits = await current_services["change_detector"].detect_unpushed_commits(repo, ctx)

            # Limit commits if requested
            original_count = len(unpushed_commits)
            if len(unpushed_commits) > max_commits:
                unpushed_commits = unpushed_commits[:max_commits]
                await ctx.info(f"Limited results to {max_commits} commits (total found: {original_count})")

            await ctx.report_progress(3, 5)
            await ctx.debug(f"Processing {len(unpushed_commits)} commits")

            commits_data = []
            total_insertions = 0
            total_deletions = 0

            for i, commit in enumerate(unpushed_commits):
                if i % 5 == 0:  # Update progress every 5 commits
                    await ctx.report_progress(3 + (i / len(unpushed_commits)) * 1, 5)

                commit_data = {
                    "sha": commit.sha,
                    "short_sha": commit.short_sha,
                    "message": commit.message,
                    "short_message": commit.short_message,
                    "author": commit.author,
                    "author_email": commit.author_email,
                    "date": commit.date.isoformat(),
                    "insertions": commit.insertions,
                    "deletions": commit.deletions,
                    "total_changes": commit.total_changes,
                    "files_changed": commit.files_changed,
                }
                commits_data.append(commit_data)
                total_insertions += commit.insertions
                total_deletions += commit.deletions

            await ctx.report_progress(4, 5)
            await ctx.debug("Analyzing commit authors and statistics")

            # Get unique authors
            authors = list({commit.author for commit in unpushed_commits})

            await ctx.report_progress(5, 5)
            duration = time.time() - start_time
            await ctx.info(
                f"Unpushed commits analysis completed in {duration:.2f} seconds - found {len(unpushed_commits)} commits"
            )

            return {
                "repository_path": str(repo_path),
                "branch": current_branch,
                "upstream_branch": branch_info.get("upstream"),
                "total_unpushed_commits": original_count,  # Use original count, not limited
                "commits_analyzed": len(commits_data),
                "summary": {
                    "total_insertions": total_insertions,
                    "total_deletions": total_deletions,
                    "total_changes": total_insertions + total_deletions,
                    "unique_authors": len(authors),
                    "authors": authors,
                },
                "commits": commits_data,
            }

        except Exception as e:
            duration = time.time() - start_time
            await ctx.error(f"Unpushed commits analysis failed after {duration:.2f} seconds: {str(e)}")
            return {"error": f"Failed to analyze unpushed commits: {str(e)}"}

    @mcp.tool()
    async def compare_with_remote(
        ctx: Context,
        remote_name: str = Field("origin", description="Remote name to compare against"),
        repository_path: str = Field(default=".", description="Path to git repository"),
    ) -> dict[str, Any]:
        """Compare local branch with remote branch.

        Shows how many commits the local branch is ahead of or behind
        the remote branch, and provides sync status information.

        **Return Type**: Dict with branch comparison information
        ```python
        {
            "repository_path": str,           # Path to analyzed repository
            "branch": str,                    # Current local branch
            "remote": str,                    # Remote name (e.g., "origin")
            "upstream_branch": str | None,    # Upstream branch reference
            "sync_status": str,               # Human-readable sync status
            "is_up_to_date": bool,            # Whether branch is synchronized
            "ahead_by": int,                  # Commits ahead of remote
            "behind_by": int,                 # Commits behind remote
            "needs_push": bool,               # Whether push is needed
            "needs_pull": bool,               # Whether pull is needed
            "actions_needed": List[str],      # Required actions ("push", "pull")
            "sync_priority": str,             # "none"|"low"|"medium"|"high" urgency
            "recommendation": str             # Human-readable action recommendation
        }
        ```

        **Key Fields for Chaining**:
        - `needs_push` (bool): Whether push operation should be performed
        - `needs_pull` (bool): Whether pull operation is needed first
        - `sync_priority` (str): Urgency level for routing workflows
        - `is_up_to_date` (bool): Whether any sync action is needed
        - `ahead_by`/`behind_by` (int): Specific sync metrics for decisions

        **Common Chaining Patterns**:
        ```python
        # Push workflow with sync check
        remote_result = await compare_with_remote("origin", repo_path)
        if remote_result["needs_pull"]:
            # Must pull first - analyze potential conflicts
            conflicts = await detect_conflicts(remote_result["repository_path"])
        elif remote_result["needs_push"]:
            # Can push - check readiness
            push_check = await get_push_readiness(remote_result["repository_path"])

        # Priority-based routing
        if remote_result["sync_priority"] == "high":
            # Urgent sync needed - get detailed analysis
            summary = await get_outstanding_summary(remote_result["repository_path"])
        elif remote_result["is_up_to_date"]:
            # Already synced - focus on local work
            wd_result = await analyze_working_directory(remote_result["repository_path"])
        ```

        **Decision Points**:
        - `needs_pull=True`: Must pull before push → check for conflicts
        - `needs_push=True`: Can push → verify push readiness
        - `sync_priority="high"`: Urgent sync → prioritize sync operations
        - `is_up_to_date=True`: Already synced → focus on local development
        """
        await ctx.info(f"Comparing local branch with remote '{remote_name}' for: {repository_path}")

        repo_path = Path(repository_path).resolve()
        if not is_git_repository(repo_path):
            git_root = find_git_root(repo_path)
            if not git_root:
                await ctx.error(f"No git repository found at or above {repo_path}")
                return {"error": f"No git repository found at or above {repo_path}"}
            repo_path = git_root

        try:
            await ctx.debug("Getting branch information")
            # Access services from closure
            current_services = services
            branch_info = await services["git_client"].get_branch_info(repo_path, ctx)

            await ctx.debug("Creating repository model")
            repo = LocalRepository(
                path=repo_path,
                name=repo_path.name,
                current_branch=branch_info.get("current_branch", "main"),
                head_commit="unknown",
                remote_url=None,
                is_dirty=False,
                is_bare=False,
                upstream_branch=None,
            )

            await ctx.debug("Getting branch status")
            # Use existing BranchStatus model
            branch_status = await current_services["status_tracker"].get_branch_status(repo, ctx)

            # Determine sync actions needed
            actions_needed = []
            if branch_status.needs_push:
                actions_needed.append("push")
            if branch_status.needs_pull:
                actions_needed.append("pull")

            await ctx.debug("Determining sync priority and recommendations")

            # Determine sync priority
            if branch_status.ahead_by > 0 and branch_status.behind_by > 0:
                sync_priority = "high"  # Diverged
                sync_recommendation = "Pull and merge/rebase, then push"
                await ctx.warning(
                    f"Branch has diverged: {branch_status.ahead_by} ahead, {branch_status.behind_by} behind"
                )
            elif branch_status.ahead_by > 5:
                sync_priority = "medium"  # Many commits ahead
                sync_recommendation = "Push commits to remote"
                await ctx.info(f"Branch is {branch_status.ahead_by} commits ahead - consider pushing")
            elif branch_status.behind_by > 5:
                sync_priority = "medium"  # Many commits behind
                sync_recommendation = "Pull latest changes"
                await ctx.info(f"Branch is {branch_status.behind_by} commits behind - consider pulling")
            elif branch_status.ahead_by > 0:
                sync_priority = "low"  # Few commits ahead
                sync_recommendation = "Push when ready"
            elif branch_status.behind_by > 0:
                sync_priority = "low"  # Few commits behind
                sync_recommendation = "Pull latest changes"
            else:
                sync_priority = "none"  # Up to date
                sync_recommendation = "Branch is up to date"
                await ctx.info("Branch is up to date with remote")

            return {
                "repository_path": str(repo_path),
                "branch": branch_status.current_branch,
                "remote": remote_name,
                "upstream_branch": branch_status.upstream_branch,
                "sync_status": branch_status.sync_status,
                "is_up_to_date": branch_status.is_up_to_date,
                "ahead_by": branch_status.ahead_by,
                "behind_by": branch_status.behind_by,
                "needs_push": branch_status.needs_push,
                "needs_pull": branch_status.needs_pull,
                "actions_needed": actions_needed,
                "sync_priority": sync_priority,
                "recommendation": sync_recommendation,
            }

        except Exception as e:
            await ctx.error(f"Failed to compare with remote: {str(e)}")
            return {"error": f"Failed to compare with remote: {str(e)}"}

    @mcp.tool()
    async def analyze_commit_history(
        ctx: Context,
        repository_path: str = Field(default=".", description="Path to git repository"),
        since: str | None = Field(None, description="Analyze commits since date (YYYY-MM-DD) or commit SHA"),
        author: str | None = Field(None, description="Filter commits by author name or email"),
        max_commits: int = Field(50, ge=1, le=200, description="Maximum number of commits to analyze"),
    ) -> dict[str, Any]:
        """Analyze recent commit history.

        Provides detailed analysis of recent commits with optional filtering
        by date, author, or other criteria.

        **Return Type**: Dict with commit history analysis
        ```python
        {
            "repository_path": str,           # Path to analyzed repository
            "analysis_filters": {             # Applied filters for context
                "since": str | None, "author": str | None, "max_commits": int
            },
            "total_commits_found": int,       # Total commits before filtering
            "commits_analyzed": int,          # Commits included in analysis
            "statistics": {                   # Aggregate commit statistics
                "total_authors": int, "total_insertions": int, "total_deletions": int,
                "average_changes_per_commit": float
            },
            "authors": Dict[str, {            # Per-author statistics
                "commits": int, "insertions": int, "deletions": int
            }],
            "daily_activity": Dict[str, int], # Commits per day (YYYY-MM-DD format)
            "message_patterns": {             # Commit message categorization
                "fix": int, "feat": int, "docs": int, "test": int, "refactor": int, "other": int
            },
            "recent_commits": List[{          # Most recent commits summary
                "sha": str, "message": str, "author": str, "date": str, "changes": int
            }]
        }
        ```

        **Key Fields for Chaining**:
        - `commits_analyzed` (int): Number of commits for statistical validity
        - `statistics.total_authors` (int): Use for collaboration analysis
        - `authors` (dict): Per-author data for team analysis
        - `message_patterns` (dict): Commit quality patterns for standards analysis
        - `repository_path` (str): Pass to other analysis tools

        **Common Chaining Patterns**:
        ```python
        # Team collaboration analysis
        history_result = await analyze_commit_history(repo_path, max_commits=100)
        if history_result["statistics"]["total_authors"] > 3:
            # Multiple contributors - check for conflicts
            conflicts = await detect_conflicts(history_result["repository_path"])

        # Commit quality analysis
        if history_result["message_patterns"]["other"] > history_result["commits_analyzed"] * 0.3:
            # Poor commit message patterns - might need standards
            health = await analyze_repository_health(history_result["repository_path"])

        # Activity-based analysis
        if history_result["commits_analyzed"] > 20:
            # Active repository - analyze current state
            summary = await get_outstanding_summary(history_result["repository_path"])
        ```

        **Decision Points**:
        - `commits_analyzed > X`: Sufficient data for statistical analysis
        - `statistics.total_authors > 1`: Multi-contributor project → check collaboration
        - `message_patterns.other > 30%`: Poor commit messages → review standards
        - `daily_activity`: Activity patterns for workflow optimization
        """
        start_time = time.time()
        await ctx.info(f"Starting commit history analysis for: {repository_path}")

        if author:
            await ctx.info(f"Filtering by author: {author}")
        if since:
            await ctx.info(f"Analyzing commits since: {since}")

        repo_path = Path(repository_path).resolve()
        if not is_git_repository(repo_path):
            git_root = find_git_root(repo_path)
            if not git_root:
                await ctx.error(f"No git repository found at or above {repo_path}")
                return {"error": f"No git repository found at or above {repo_path}"}
            repo_path = git_root

        try:
            await ctx.debug("Creating repository model")
            repo = LocalRepository(
                path=repo_path,
                name=repo_path.name,
                current_branch="main",
                head_commit="unknown",
                remote_url=None,
                is_dirty=False,
                is_bare=False,
                upstream_branch=None,
            )

            await ctx.debug("Getting unpushed commits for analysis")
            # Get unpushed commits (this is our main commit source for now)
            # Access services from closure
            current_services = services
            all_commits = await current_services["change_detector"].detect_unpushed_commits(repo, ctx)

            await ctx.debug(f"Found {len(all_commits)} total commits, applying filters")

            # Apply filters
            filtered_commits = all_commits

            if author:
                original_count = len(filtered_commits)
                filtered_commits = [
                    c
                    for c in filtered_commits
                    if author.lower() in c.author.lower() or author.lower() in c.author_email.lower()
                ]
                await ctx.info(f"Author filter reduced commits from {original_count} to {len(filtered_commits)}")

            # TODO: Add date filtering when 'since' is provided
            if since:
                await ctx.warning("Date filtering not yet implemented - ignoring 'since' parameter")

            # Limit results
            original_count = len(filtered_commits)
            if len(filtered_commits) > max_commits:
                filtered_commits = filtered_commits[:max_commits]
                await ctx.info(f"Limited results to {max_commits} commits (filtered total: {original_count})")

            await ctx.debug("Analyzing commit patterns and statistics")

            # Analyze patterns
            authors_stats: dict[str, dict[str, int]] = {}
            daily_commits: dict[str, int] = {}
            message_patterns = {
                "fix": 0,
                "feat": 0,
                "docs": 0,
                "test": 0,
                "refactor": 0,
                "other": 0,
            }

            for commit in filtered_commits:
                # Author stats
                if commit.author not in authors_stats:
                    authors_stats[commit.author] = {
                        "commits": 0,
                        "insertions": 0,
                        "deletions": 0,
                    }
                authors_stats[commit.author]["commits"] += 1
                authors_stats[commit.author]["insertions"] += commit.insertions
                authors_stats[commit.author]["deletions"] += commit.deletions

                # Daily stats
                date_str = commit.date.strftime("%Y-%m-%d")
                daily_commits[date_str] = daily_commits.get(date_str, 0) + 1

                # Message pattern analysis - check for conventional commit prefixes first
                msg_lower = commit.message.lower()

                # Check for conventional commit format (prefix: message)
                if msg_lower.startswith("fix:") or msg_lower.startswith("fix("):
                    message_patterns["fix"] += 1
                elif msg_lower.startswith("feat:") or msg_lower.startswith("feat("):
                    message_patterns["feat"] += 1
                elif (
                    msg_lower.startswith("docs:")
                    or msg_lower.startswith("doc:")
                    or msg_lower.startswith("docs(")
                    or msg_lower.startswith("doc(")
                ):
                    message_patterns["docs"] += 1
                elif (
                    msg_lower.startswith("test:")
                    or msg_lower.startswith("tests:")
                    or msg_lower.startswith("test(")
                    or msg_lower.startswith("tests(")
                ):
                    message_patterns["test"] += 1
                elif msg_lower.startswith("refactor:") or msg_lower.startswith("refactor("):
                    message_patterns["refactor"] += 1
                # Fallback to keyword matching if not conventional commit format
                elif any(word in msg_lower for word in ["fix", "bug", "patch"]):
                    message_patterns["fix"] += 1
                elif any(word in msg_lower for word in ["feat", "add", "new"]):
                    message_patterns["feat"] += 1
                elif any(word in msg_lower for word in ["doc", "readme", "comment"]):
                    message_patterns["docs"] += 1
                elif any(word in msg_lower for word in ["test", "spec"]):
                    message_patterns["test"] += 1
                elif any(word in msg_lower for word in ["refactor", "clean", "improve"]):
                    message_patterns["refactor"] += 1
                else:
                    message_patterns["other"] += 1

            duration = time.time() - start_time
            await ctx.info(f"Commit history analysis completed in {duration:.2f} seconds")

            return {
                "repository_path": str(repo_path),
                "analysis_filters": {
                    "since": since,
                    "author": author,
                    "max_commits": max_commits,
                },
                "total_commits_found": len(all_commits),
                "commits_analyzed": len(filtered_commits),
                "statistics": {
                    "total_authors": len(authors_stats),
                    "total_insertions": sum(c.insertions for c in filtered_commits),
                    "total_deletions": sum(c.deletions for c in filtered_commits),
                    "average_changes_per_commit": (
                        sum(c.total_changes for c in filtered_commits) / len(filtered_commits)
                        if filtered_commits
                        else 0
                    ),
                },
                "authors": authors_stats,
                "daily_activity": daily_commits,
                "message_patterns": message_patterns,
                "recent_commits": [
                    {
                        "sha": c.short_sha,
                        "message": c.short_message,
                        "author": c.author,
                        "date": c.date.strftime("%Y-%m-%d %H:%M"),
                        "changes": c.total_changes,
                    }
                    for c in filtered_commits[:10]  # Show top 10
                ],
            }

        except Exception as e:
            duration = time.time() - start_time
            await ctx.error(f"Commit history analysis failed after {duration:.2f} seconds: {str(e)}")
            return {"error": f"Failed to analyze commit history: {str(e)}"}

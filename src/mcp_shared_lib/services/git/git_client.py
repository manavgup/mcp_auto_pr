"""Git command execution client with error handling."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp_shared_lib.config.git_analyzer import GitAnalyzerSettings
from mcp_shared_lib.utils import logging_service

if TYPE_CHECKING:
    from fastmcp import Context  # unused: keep for TYPE_CHECKING


class GitCommandError(Exception):
    """Exception raised when git command fails."""

    def __init__(self, command: list[str], return_code: int, stderr: str):
        """Initialize git command error with details."""
        self.command = command
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(f"Git command failed: {' '.join(command)}\nError: {stderr}")


class GitClient:
    """Git command execution client with error handling."""

    def __init__(self, settings: GitAnalyzerSettings):
        """Initialize git client with settings."""
        self.settings = settings
        self.logger = logging_service.get_logger(__name__)

    async def execute_command(
        self,
        repo_path: Path,
        command: list[str],
        check: bool = True,
        ctx: Context | None = None,
    ) -> str:
        """Execute a git command in the given repository."""
        full_command = ["git", "-C", str(repo_path)] + command

        if ctx:
            await ctx.debug(f"Executing git command: {' '.join(full_command)}")

        try:
            result = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path,
            )

            stdout, stderr = await result.communicate()
            stdout_str = stdout.decode("utf-8").strip()
            stderr_str = stderr.decode("utf-8").strip()

            if check and result.returncode != 0:
                if ctx:
                    await ctx.error(
                        f"Git command failed (exit {result.returncode}): {stderr_str}"
                    )
                raise GitCommandError(
                    full_command, result.returncode or 0, stderr_str
                ) from None

            if ctx and stdout_str:
                await ctx.debug(f"Git command output: {len(stdout_str)} characters")

            return stdout_str

        except FileNotFoundError as e:
            error_msg = "Git command not found - is git installed?"
            if ctx:
                await ctx.error(error_msg)
            raise GitCommandError(full_command, -1, error_msg) from e
        except Exception as e:
            if ctx:
                await ctx.error(f"Unexpected error executing git command: {str(e)}")
            raise GitCommandError(full_command, -1, str(e)) from e

    async def get_status(
        self, repo_path: Path, ctx: Context | None = None
    ) -> dict[str, Any]:
        """Get git status information."""
        if ctx:
            await ctx.debug("Getting git status (porcelain format)")

        # Get porcelain status for parsing - DON'T strip the output as leading spaces are significant
        full_command = ["git", "-C", str(repo_path), "status", "--porcelain=v1"]

        if ctx:
            await ctx.debug(f"Executing git command: {' '.join(full_command)}")

        try:
            result = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path,
            )

            stdout, stderr = await result.communicate()
            # Don't strip the output - leading spaces are significant for git status parsing
            status_output = stdout.decode("utf-8").rstrip(
                "\n"
            )  # Only remove trailing newlines
            stderr_str = stderr.decode("utf-8").strip()

            if result.returncode != 0:
                if ctx:
                    await ctx.error(
                        f"Git command failed (exit {result.returncode}): {stderr_str}"
                    )
                raise GitCommandError(full_command, result.returncode or 0, stderr_str)

            if ctx and status_output:
                await ctx.debug(f"Git command output: {len(status_output)} characters")

        except FileNotFoundError as e:
            error_msg = "Git command not found - is git installed?"
            if ctx:
                await ctx.error(error_msg)
            raise GitCommandError(full_command, -1, error_msg) from e
        except Exception as e:
            if ctx:
                await ctx.error(f"Unexpected error executing git command: {str(e)}")
            raise GitCommandError(full_command, -1, str(e)) from e

        files = []
        for line in status_output.split("\n"):
            if line.strip() and len(line) >= 2:
                # Git status porcelain format: XY filename
                # X = index status (staged), Y = working tree status (unstaged)
                # For unstaged files: " M filename" (space + M)
                # For staged files: "M  filename" (M + space)
                # For both: "MM filename" (M + M)

                # Handle different line lengths - some git versions may have different formats
                if len(line) >= 3 and line[2] == " ":
                    # Standard format: "XY filename" where position 2 is space
                    index_status = line[0] if line[0] != " " else None
                    working_status = line[1] if line[1] != " " else None
                    filename_start = 3
                elif len(line) >= 2:
                    # Compact format: "XYfilename" where there's no space separator
                    # This shouldn't happen with --porcelain=v1, but handle it just in case
                    index_status = line[0] if line[0] != " " else None
                    working_status = line[1] if line[1] != " " else None
                    filename_start = 2
                else:
                    continue

                # Handle rename case: status code 'R' has format "R  old -> new"
                if index_status == "R" or working_status == "R":
                    # For rename, filename is after '-> '
                    arrow_pos = line.find("->")
                    if arrow_pos != -1:
                        filename = line[arrow_pos + 3 :].strip()
                    else:
                        filename = line[filename_start:].strip()
                else:
                    filename = line[filename_start:].strip()

                files.append(
                    {
                        "filename": filename,
                        "index_status": index_status,
                        "working_status": working_status,
                        "status_code": line[
                            :2
                        ],  # Keep the full two-character status code
                    }
                )

        if ctx:
            await ctx.debug(f"Parsed {len(files)} file status entries")

        return {"files": files}

    async def get_diff(
        self,
        repo_path: Path,
        staged: bool = False,
        file_path: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Get diff output."""
        command = ["diff"]
        if staged:
            command.append("--cached")
        if file_path:
            command.extend(["--", file_path])

        if ctx:
            diff_type = "staged" if staged else "working tree"
            target = f" for {file_path}" if file_path else ""
            await ctx.debug(f"Getting {diff_type} diff{target}")

        diff_output = await self.execute_command(repo_path, command, ctx=ctx)

        if ctx:
            lines_count = len(diff_output.split("\n")) if diff_output else 0
            await ctx.debug(f"Retrieved diff with {lines_count} lines")

        return diff_output

    async def get_diff_stats(
        self,
        repo_path: Path,
        file_path: str,
        staged: bool | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get diff statistics for a specific file.

        Args:
            repo_path: Path to git repository
            file_path: Path to the file
            staged: If True, get staged diff stats. If False, get working diff stats. If None, detect automatically.
            ctx: Context for logging
        """
        if ctx:
            await ctx.debug(f"Getting diff stats for {file_path} (staged={staged})")

        try:
            # If staged is not specified, detect the file status first
            if staged is None:
                status_output = await self.execute_command(
                    repo_path, ["status", "--porcelain", "--", file_path], ctx=ctx
                )

                if not status_output.strip():
                    # No changes for this file
                    if ctx:
                        await ctx.debug(f"No changes detected for {file_path}")
                    return {"lines_added": 0, "lines_deleted": 0, "is_binary": False}

                # Parse the status to understand the file state
                line = status_output.strip()
                if len(line) >= 2:
                    index_status = line[0] if line[0] != " " else None
                    working_status = line[1] if line[1] != " " else None

                    # If file has index status, it's staged. If it has working status, check working tree.
                    # If it has both, prefer staged diff for getting the actual changes
                    if index_status and index_status != "?":
                        staged = True
                    elif working_status and working_status != "?":
                        staged = False
                    else:
                        staged = False

                    if ctx:
                        await ctx.debug(
                            f"Auto-detected file state for {file_path}: "
                            f"index='{index_status}', working='{working_status}', "
                            f"using staged={staged}"
                        )

            # Try to get numstat for the appropriate diff
            commands_to_try = []

            if staged:
                # For staged files, compare staged area with HEAD
                commands_to_try.append(
                    ["diff", "--cached", "--numstat", "--", file_path]
                )
            else:
                # For working directory files, compare working directory with staged/HEAD
                commands_to_try.append(["diff", "--numstat", "--", file_path])

            # If the first approach fails, try the other one as fallback
            if staged:
                commands_to_try.append(["diff", "--numstat", "--", file_path])
            else:
                commands_to_try.append(
                    ["diff", "--cached", "--numstat", "--", file_path]
                )

            numstat_output = None
            used_command = None

            for command in commands_to_try:
                try:
                    numstat_output = await self.execute_command(
                        repo_path, command, ctx=ctx
                    )
                    if numstat_output.strip():
                        used_command = command
                        break
                    elif ctx:
                        await ctx.debug(
                            f"Command {' '.join(command)} returned empty output"
                        )
                except GitCommandError as e:
                    if ctx:
                        await ctx.debug(f"Command {' '.join(command)} failed: {e}")
                    continue

            if not numstat_output or not numstat_output.strip():
                if ctx:
                    await ctx.warning(
                        f"No diff output found for {file_path} with any command"
                    )
                return {"lines_added": 0, "lines_deleted": 0, "is_binary": False}

            if ctx and used_command:
                await ctx.debug(
                    f"Successfully got diff stats using: {' '.join(used_command)}"
                )

            # Parse the numstat output
            lines = numstat_output.strip().split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        # parts[0] = additions, parts[1] = deletions, parts[2] = filename
                        additions_str = parts[0]
                        deletions_str = parts[1]
                        file_in_output = parts[2]

                        # Verify this is the correct file (git might return multiple files)
                        if file_in_output != file_path:
                            continue

                        # Check if binary file (git shows "-" for binary files)
                        if additions_str == "-" and deletions_str == "-":
                            if ctx:
                                await ctx.debug(f"Binary file detected: {file_path}")
                            return {
                                "lines_added": 0,
                                "lines_deleted": 0,
                                "is_binary": True,
                            }

                        try:
                            lines_added = int(additions_str)
                            lines_deleted = int(deletions_str)

                            if ctx:
                                await ctx.debug(
                                    f"Diff stats for {file_path}: +{lines_added}/-{lines_deleted}"
                                )

                            return {
                                "lines_added": lines_added,
                                "lines_deleted": lines_deleted,
                                "is_binary": False,
                            }
                        except ValueError:
                            if ctx:
                                await ctx.warning(
                                    f"Failed to parse numstat output: {line}"
                                )

            # Fallback - if we can't parse numstat, assume no changes
            if ctx:
                await ctx.warning(f"Could not parse diff stats for {file_path}")
            return {"lines_added": 0, "lines_deleted": 0, "is_binary": False}

        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to get diff stats for {file_path}: {e}")
            return {"lines_added": 0, "lines_deleted": 0, "is_binary": False}

    async def get_unpushed_commits(
        self, repo_path: Path, remote: str = "origin", ctx: Context | None = None
    ) -> list[dict[str, Any]]:
        """Get commits that haven't been pushed to remote."""
        if ctx:
            await ctx.debug(f"Getting unpushed commits for remote '{remote}'")

        try:
            # Get current branch
            current_branch = await self.execute_command(
                repo_path, ["branch", "--show-current"], ctx=ctx
            )

            if ctx:
                await ctx.debug(f"Current branch: {current_branch}")

            # Get unpushed commits
            log_format = '--pretty=format:{"sha":"%H","message":"%s","author":"%an","email":"%ae","date":"%ai"}'
            upstream = f"{remote}/{current_branch}"

            try:
                if ctx:
                    await ctx.debug(f"Checking for commits ahead of {upstream}")

                output = await self.execute_command(
                    repo_path, ["log", f"{upstream}..HEAD", log_format], ctx=ctx
                )
            except GitCommandError:
                # If upstream doesn't exist, get all commits (limited)
                if ctx:
                    await ctx.warning(
                        f"Upstream {upstream} not found, getting recent commits"
                    )

                output = await self.execute_command(
                    repo_path, ["log", log_format, "--max-count=10"], ctx=ctx
                )

            commits = []
            for line in output.split("\n"):
                if line.strip():
                    try:
                        commit_data = json.loads(line)
                        commits.append(commit_data)
                    except json.JSONDecodeError:
                        if ctx:
                            await ctx.warning(
                                f"Failed to parse commit JSON: {line[:50]}..."
                            )
                        continue

            if ctx:
                await ctx.debug(f"Found {len(commits)} unpushed commits")

            return commits

        except GitCommandError as e:
            if ctx:
                await ctx.warning(f"Failed to get unpushed commits: {e}")
            return []

    async def get_stash_list(
        self, repo_path: Path, ctx: Context | None = None
    ) -> list[dict[str, Any]]:
        """Get list of stashed changes."""
        if ctx:
            await ctx.debug("Getting git stash list")

        try:
            output = await self.execute_command(
                repo_path, ["stash", "list", "--pretty=format:%gd|%s|%cr"], ctx=ctx
            )

            stashes = []
            for i, line in enumerate(output.split("\n")):
                if line.strip():
                    parts = line.split("|", 2)
                    if len(parts) >= 2:
                        stashes.append(
                            {
                                "index": i,
                                "name": parts[0],
                                "message": parts[1],
                                "date": parts[2] if len(parts) > 2 else "",
                            }
                        )

            if ctx:
                await ctx.debug(f"Found {len(stashes)} stashed changes")

            return stashes

        except GitCommandError as e:
            if ctx:
                await ctx.warning(f"Failed to get stash list: {e}")
            return []

    async def get_branch_info(
        self, repo_path: Path, ctx: Context | None = None
    ) -> dict[str, Any]:
        """Get branch information."""
        if ctx:
            await ctx.debug("Getting branch information")

        try:
            # Get current branch
            current_branch = await self.execute_command(
                repo_path, ["branch", "--show-current"], ctx=ctx
            )

            if ctx:
                await ctx.debug(f"Current branch: {current_branch}")

            # Get upstream info
            upstream = None
            try:
                upstream = await self.execute_command(
                    repo_path, ["rev-parse", "--abbrev-ref", "@{upstream}"], ctx=ctx
                )
                if ctx:
                    await ctx.debug(f"Upstream branch: {upstream}")
            except GitCommandError:
                if ctx:
                    await ctx.debug("No upstream branch configured")

            # Get ahead/behind counts
            ahead, behind = 0, 0
            if upstream:
                try:
                    counts = await self.execute_command(
                        repo_path,
                        ["rev-list", "--left-right", "--count", f"{upstream}...HEAD"],
                        ctx=ctx,
                    )
                    behind, ahead = map(int, counts.split())

                    if ctx:
                        await ctx.debug(
                            f"Branch status: {ahead} ahead, {behind} behind"
                        )

                except (GitCommandError, ValueError) as e:
                    if ctx:
                        await ctx.warning(f"Failed to get ahead/behind counts: {e}")

            # Get HEAD commit SHA
            try:
                head_commit = await self.execute_command(
                    repo_path, ["rev-parse", "HEAD"], ctx=ctx
                )
                if ctx:
                    await ctx.debug(f"HEAD commit: {head_commit[:8]}...")
            except GitCommandError:
                head_commit = "unknown"
                if ctx:
                    await ctx.warning("Failed to get HEAD commit SHA")

            return {
                "current_branch": current_branch,
                "upstream": upstream,
                "ahead": ahead,
                "behind": behind,
                "head_commit": head_commit,
            }

        except GitCommandError as e:
            if ctx:
                await ctx.error(f"Failed to get branch info: {e}")
            return {
                "current_branch": "unknown",
                "upstream": None,
                "ahead": 0,
                "behind": 0,
                "head_commit": "unknown",
            }

    async def get_repository_info(
        self, repo_path: Path, ctx: Context | None = None
    ) -> dict[str, Any]:
        """Get general repository information."""
        if ctx:
            await ctx.debug("Getting repository information")

        try:
            # Check if it's a bare repository
            try:
                await self.execute_command(
                    repo_path, ["rev-parse", "--is-bare-repository"], ctx=ctx
                )
                is_bare = True
            except GitCommandError:
                is_bare = False

            # Get remote URLs
            remotes: dict[str, dict[str, str]] = {}
            try:
                remote_output = await self.execute_command(
                    repo_path, ["remote", "-v"], ctx=ctx
                )
                for line in remote_output.split("\n"):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            remote_name = parts[0]
                            remote_url = parts[1]
                            remote_type = parts[2].strip("()")

                            if remote_name not in remotes:
                                remotes[remote_name] = {}
                            remotes[remote_name][remote_type] = remote_url

            except GitCommandError:
                if ctx:
                    await ctx.debug("No remotes configured")

            # Check if repository is dirty (has uncommitted changes)
            try:
                status_output = await self.execute_command(
                    repo_path, ["status", "--porcelain"], ctx=ctx
                )
                is_dirty = bool(status_output.strip())
            except GitCommandError:
                is_dirty = False

            if ctx:
                await ctx.debug(
                    f"Repository info: bare={is_bare}, dirty={is_dirty}, remotes={len(remotes)}"
                )

            return {
                "is_bare": is_bare,
                "is_dirty": is_dirty,
                "remotes": remotes,
                "root_path": str(repo_path),
            }

        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to get repository info: {e}")
            return {
                "is_bare": False,
                "is_dirty": False,
                "remotes": {},
                "root_path": str(repo_path),
            }

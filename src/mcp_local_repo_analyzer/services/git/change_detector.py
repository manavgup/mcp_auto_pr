"""Service for detecting different types of git changes."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from shared.models import (
    FileStatus,
    LocalRepository,
    StagedChanges,
    StashedChanges,
    UnpushedCommit,
    WorkingDirectoryChanges,
)
from shared.services import GitClient
from shared.utils import logging_service

if TYPE_CHECKING:
    from fastmcp import Context


class ChangeDetector:
    """Service for detecting different types of git changes."""

    def __init__(self, git_client: GitClient):
        """Initialize change detector with git client."""
        self.git_client = git_client
        self.logger = logging_service.get_logger(__name__)

    async def detect_working_directory_changes(
        self, repo: LocalRepository, ctx: Optional["Context"] = None
    ) -> WorkingDirectoryChanges:
        """Detect uncommitted changes in working directory (changes NOT YET staged)."""
        if ctx:
            await ctx.debug("Detecting working directory changes (unstaged only)")

        try:
            status_info = await self.git_client.get_status(repo.path, ctx)
            if ctx:
                await ctx.debug(f"Raw git status info: {status_info}")

            modified_files = []
            added_files = []
            deleted_files = []
            renamed_files = []
            untracked_files = []

            if ctx:
                await ctx.debug(
                    f"Processing {len(status_info['files'])} file status entries for WD changes"
                )

            for file_info in status_info["files"]:
                index_status = file_info.get(
                    "index_status"
                )  # Left-hand side of status output (staged)
                working_status = file_info.get(
                    "working_status"
                )  # Right-hand side of status output (unstaged)
                status_code = file_info["status_code"]  # Combined status code

                # A file is an unstaged working directory change if:
                # 1. It has a 'working_status' (right-hand side of git status)
                # 2. It is NOT already entirely staged (index_status is empty or '?', meaning not yet added to index)
                #    OR, if it is staged, but it also has further unstaged modifications (e.g., 'MM' status)

                # Let's simplify: an unstaged change is indicated by a non-empty working_status (right column)
                # AND not being an untracked file, OR if it's untracked.

                # Handle untracked files explicitly first, as they are always unstaged
                if status_code == "?":
                    # Untracked files have no index_status or working_status beyond '?'
                    file_status = FileStatus(
                        path=file_info["filename"],
                        status_code="?",
                        working_tree_status="?",
                        index_status=None,  # Explicitly None for untracked in index
                        staged=False,
                        lines_added=0,  # Line counts for untracked are usually 0 until added.
                        lines_deleted=0,
                        is_binary=False,  # Default, can improve with file type detection
                        old_path=None,
                    )
                    untracked_files.append(file_status)
                    continue  # Move to next file_info

                # For tracked files, differentiate based on working_status
                # ' 'M' ' 'A' ' 'D' ' 'R' etc. where working_status (right) is not empty and index_status (left)
                # does not fully cover the changes (e.g., ' M' is unstaged modify, 'MM' is staged+unstaged modify)

                # Check if there are UNSTAGED changes in the working tree
                # This means working_status is not ' ' (space) and is not '?'
                if (
                    working_status and working_status.strip() != ""
                ):  # Check right-hand side of status (unstaged changes)
                    # For these files, diff_stats should be relative to the index (staged=False)
                    lines_added = 0
                    lines_deleted = 0
                    is_binary = False

                    try:
                        if ctx:
                            await ctx.debug(
                                f"Getting diff stats for unstaged WD file {file_info['filename']}"
                            )
                        diff_stats = await self.git_client.get_diff_stats(
                            repo.path,
                            file_info["filename"],
                            staged=False,  # Get diff between working tree and index (unstaged changes)
                            ctx=ctx,
                        )
                        lines_added = diff_stats.get("lines_added", 0)
                        lines_deleted = diff_stats.get("lines_deleted", 0)
                        is_binary = diff_stats.get("is_binary", False)
                        if ctx:
                            await ctx.debug(
                                f"Got diff stats for unstaged WD file {file_info['filename']}: +{lines_added}/-{lines_deleted}, binary={is_binary}"
                            )
                    except Exception as e:
                        if ctx:
                            await ctx.error(
                                f"Failed to get diff stats for unstaged WD file {file_info['filename']}: {str(e)}"
                            )
                        raise

                    file_status = FileStatus(
                        path=file_info["filename"],
                        status_code=working_status,  # The specific unstaged status
                        working_tree_status=working_status,
                        index_status=index_status,  # Can still have an index status (e.g. 'MM')
                        staged=False,  # Explicitly mark as unstaged for this tool
                        lines_added=lines_added,
                        lines_deleted=lines_deleted,
                        is_binary=is_binary,
                        old_path=file_info.get("old_filename")
                        if working_status == "R"
                        else None,  # For untracked renames
                    )

                    if working_status == "M":
                        modified_files.append(file_status)
                    elif (
                        working_status == "A"
                    ):  # Note: 'A ' is working tree add. 'A' is staged add.
                        added_files.append(file_status)
                    elif (
                        working_status == "D"
                    ):  # Note: ' D' is working tree delete. 'D' is staged delete.
                        deleted_files.append(file_status)
                    elif (
                        working_status == "R"
                    ):  # Note: ' R' is working tree rename. 'R' is staged rename.
                        renamed_files.append(file_status)
                    # For other composite states like 'UD' (unmerged), we'll categorize based on actual status_code
                    # or simply ignore for this tool if not 'M', 'A', 'D', 'R'.
                else:
                    if ctx:
                        await ctx.debug(
                            f"File {file_info['filename']} has no unstaged changes in working directory (status: {status_code})"
                        )

            changes = WorkingDirectoryChanges(
                modified_files=modified_files,
                added_files=added_files,
                deleted_files=deleted_files,
                renamed_files=renamed_files,
                untracked_files=untracked_files,
            )

            if ctx:
                total_files = (
                    changes.total_files
                )  # This property will now correctly reflect unstaged only
                await ctx.debug(
                    f"Detected working directory changes: {total_files} total files (unstaged)"
                )
                if total_files > 0:
                    await ctx.info(
                        f"Working directory summary: "
                        f"{len(modified_files)} modified, "
                        f"{len(added_files)} added, "
                        f"{len(deleted_files)} deleted, "
                        f"{len(renamed_files)} renamed, "
                        f"{len(untracked_files)} untracked (all unstaged)"
                    )

            return changes

        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to detect working directory changes: {str(e)}")
            raise

    async def detect_staged_changes(
        self, repo: LocalRepository, ctx: Optional["Context"] = None
    ) -> StagedChanges:
        """Detect changes staged for commit (changes IN THE INDEX)."""
        if ctx:
            await ctx.debug("Detecting staged changes (in index only)")

        try:
            status_info = await self.git_client.get_status(repo.path, ctx)

            staged_files = []

            if ctx:
                await ctx.debug(
                    f"Processing {len(status_info['files'])} file status entries for staged changes"
                )

            for file_info in status_info["files"]:
                index_status = file_info.get(
                    "index_status"
                )  # Left-hand side of status output (staged)
                working_status = file_info.get(
                    "working_status"
                )  # Right-hand side of status output (unstaged)
                status_code = file_info.get("status_code", "")  # Combined status code

                # A file is considered "staged" if its left-hand status code from `git status` is not ' ' or '?'
                # E.g., 'M ', 'A ', 'D ', 'R ', 'C ', 'U ' (unmerged conflict staged)
                if (
                    index_status and index_status.strip() != "" and index_status != "?"
                ):  # Filter for actual staged changes
                    lines_added = 0
                    lines_deleted = 0
                    is_binary = False

                    try:
                        if ctx:
                            await ctx.debug(
                                f"Getting diff stats for staged file {file_info['filename']}"
                            )

                        # For staged changes, get diff between index and HEAD (staged=True)
                        diff_stats = await self.git_client.get_diff_stats(
                            repo.path,
                            file_info["filename"],
                            staged=True,  # Always True for staged changes
                            ctx=ctx,
                        )
                        lines_added = diff_stats.get("lines_added", 0)
                        lines_deleted = diff_stats.get("lines_deleted", 0)
                        is_binary = diff_stats.get("is_binary", False)

                        if ctx:
                            await ctx.debug(
                                f"Got diff stats for staged file {file_info['filename']}: +{lines_added}/-{lines_deleted}, binary={is_binary}"
                            )

                    except Exception as e:
                        if ctx:
                            await ctx.error(
                                f"Failed to get diff stats for staged file {file_info['filename']}: {str(e)}"
                            )
                        raise

                    file_status = FileStatus(
                        path=file_info["filename"],
                        status_code=index_status,  # Use index_status for staged files
                        staged=True,  # Explicitly mark as staged
                        index_status=index_status,
                        working_tree_status=working_status,  # Can still have unstaged changes (e.g. 'M M')
                        lines_added=lines_added,
                        lines_deleted=lines_deleted,
                        is_binary=is_binary,
                        old_path=file_info.get("old_filename")
                        if index_status == "R"
                        else None,  # For staged renames
                    )
                    staged_files.append(file_status)
                else:
                    if ctx:
                        await ctx.debug(
                            f"File {file_info['filename']} has no staged changes (status: {status_code})"
                        )

            changes = StagedChanges(staged_files=staged_files)

            if ctx:
                if changes.ready_to_commit:
                    await ctx.info(
                        f"Found {changes.total_staged} staged files ready for commit"
                    )
                    await ctx.debug(
                        f"Staged changes summary: "
                        f"{changes.total_additions} additions, "
                        f"{changes.total_deletions} deletions"
                    )
                else:
                    await ctx.debug("No staged changes found")

            return changes

        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to detect staged changes: {str(e)}")
            raise

    async def detect_unpushed_commits(
        self, repo: LocalRepository, ctx: Optional["Context"] = None
    ) -> list[UnpushedCommit]:
        """Detect commits that haven't been pushed to remote."""
        if ctx:
            await ctx.debug("Detecting unpushed commits")

        try:
            commits_data = await self.git_client.get_unpushed_commits(
                repo.path, ctx=ctx
            )

            unpushed_commits = []

            if ctx:
                await ctx.debug(f"Processing {len(commits_data)} unpushed commits")

            for commit_data in commits_data:
                try:
                    # Parse the date string
                    date_str = commit_data["date"]
                    # Handle different date formats
                    try:
                        # Try ISO format with timezone
                        if "+" in date_str or "Z" in date_str:
                            commit_date = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        else:
                            # Try without timezone
                            commit_date = datetime.fromisoformat(date_str)
                    except ValueError:
                        # Fallback to current time if parsing fails
                        commit_date = datetime.now()
                        if ctx:
                            await ctx.warning(
                                f"Failed to parse commit date: {date_str}"
                            )

                    unpushed_commit = UnpushedCommit(
                        sha=commit_data["sha"],
                        message=commit_data["message"],
                        author=commit_data["author"],
                        author_email=commit_data["email"],
                        date=commit_date,
                        files_changed=[],  # TODO: Get changed files if needed
                        insertions=0,  # TODO: Get stats if needed
                        deletions=0,  # TODO: Get stats if needed
                    )
                    unpushed_commits.append(unpushed_commit)

                except (KeyError, ValueError) as e:
                    if ctx:
                        await ctx.warning(f"Failed to parse commit data: {e}")
                    continue

            if ctx:
                if unpushed_commits:
                    # Removed unused variable 'authors'
                    await ctx.info(f"Found {len(unpushed_commits)} unpushed commits")

                    # Log commit summary
                    recent_commits = unpushed_commits[:3]  # Show first 3
                    for commit in recent_commits:
                        await ctx.debug(
                            f"Unpushed: {commit.short_sha} - {commit.short_message}"
                        )
                else:
                    await ctx.debug("No unpushed commits found")

            return unpushed_commits

        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to detect unpushed commits: {str(e)}")
            raise

    async def detect_stashed_changes(
        self, repo: LocalRepository, ctx: Optional["Context"] = None
    ) -> list[StashedChanges]:
        """Detect stashed changes."""
        if ctx:
            await ctx.debug("Detecting stashed changes")

        try:
            stashes_data = await self.git_client.get_stash_list(repo.path, ctx)

            stashed_changes = []

            if ctx:
                await ctx.debug(f"Processing {len(stashes_data)} stashed changes")

            for stash_data in stashes_data:
                try:
                    # Parse stash creation date (approximate)
                    try:
                        # Try to parse relative date (e.g., "2 hours ago")
                        # For now, just use current time as approximation
                        stash_date = datetime.now()
                    except Exception:
                        stash_date = datetime.now()

                    stashed_change = StashedChanges(
                        stash_index=stash_data["index"],
                        message=stash_data["message"],
                        branch=repo.current_branch,  # Approximate - stash doesn't store original branch
                        date=stash_date,
                        files_affected=[],  # TODO: Get affected files if needed
                    )
                    stashed_changes.append(stashed_change)

                except (KeyError, ValueError) as e:
                    if ctx:
                        await ctx.warning(f"Failed to parse stash data: {e}")
                    continue

            if ctx:
                if stashed_changes:
                    await ctx.info(f"Found {len(stashed_changes)} stashed changes")
                    for stash in stashed_changes[:3]:  # Show first 3
                        await ctx.debug(f"Stash {stash.stash_index}: {stash.message}")
                else:
                    await ctx.debug("No stashed changes found")

            return stashed_changes

        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to detect stashed changes: {str(e)}")
            raise

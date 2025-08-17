"""Git-related test data factories.

This module provides factories for creating realistic git objects
including commits, branches, repository states, and diffs.
"""

from datetime import datetime, timedelta
from typing import Any, TypeVar

from .base import BaseFactory, Faker, SequenceMixin, TraitMixin

T = TypeVar("T")


class GitCommitFactory(BaseFactory, SequenceMixin, TraitMixin):
    """Factory for creating git commit objects."""

    @staticmethod
    def hash() -> str:
        """Generate commit hash."""
        return Faker.hex_string(40)

    @staticmethod
    def short_hash() -> str:
        """Generate short commit hash."""
        return Faker.hex_string(7)

    @staticmethod
    def message() -> str:
        """Generate commit message."""
        return Faker.sentence(nb_words=6)

    @staticmethod
    def author_name() -> str:
        """Generate author name."""
        return Faker.name()

    @staticmethod
    def author_email() -> str:
        """Generate author email."""
        return Faker.email()

    @staticmethod
    def timestamp() -> datetime:
        """Generate commit timestamp."""
        return Faker.date_time()

    @staticmethod
    def files_changed() -> int:
        """Generate number of files changed."""
        return Faker.random_int(1, 20)

    @staticmethod
    def lines_added() -> int:
        """Generate lines added."""
        return Faker.random_int(0, 200)

    @staticmethod
    def lines_removed() -> int:
        """Generate lines removed."""
        return Faker.random_int(0, 100)

    @classmethod
    def trait_feature(cls) -> dict[str, Any]:
        """Trait for feature commits."""
        return {
            "message": f"feat: {Faker.sentence(nb_words=4)}",
            "files_changed": Faker.random_int(3, 15),
            "lines_added": Faker.random_int(20, 150),
        }

    @classmethod
    def trait_bugfix(cls) -> dict[str, Any]:
        """Trait for bugfix commits."""
        return {
            "message": f"fix: {Faker.sentence(nb_words=4)}",
            "files_changed": Faker.random_int(1, 8),
            "lines_added": Faker.random_int(5, 50),
        }

    @classmethod
    def trait_docs(cls) -> dict[str, Any]:
        """Trait for documentation commits."""
        return {
            "message": f"docs: {Faker.sentence(nb_words=4)}",
            "files_changed": Faker.random_int(1, 5),
            "lines_added": Faker.random_int(10, 100),
        }

    @classmethod
    def trait_large(cls) -> dict[str, Any]:
        """Trait for large commits."""
        return {
            "files_changed": Faker.random_int(10, 30),
            "lines_added": Faker.random_int(100, 500),
            "lines_removed": Faker.random_int(20, 100),
        }

    @classmethod
    def trait_small(cls) -> dict[str, Any]:
        """Trait for small commits."""
        return {
            "files_changed": Faker.random_int(1, 3),
            "lines_added": Faker.random_int(1, 20),
            "lines_removed": Faker.random_int(0, 10),
        }

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create git commit with computed properties."""
        commit = super().create(**kwargs)

        # Add computed properties
        commit["short_hash"] = commit["hash"][:7]
        commit["author_date"] = commit["timestamp"]
        commit["committer_date"] = commit["timestamp"]
        commit["committer_name"] = commit["author_name"]
        commit["committer_email"] = commit["author_email"]

        # Add commit metadata
        commit["metadata"] = {
            "branch": Faker.random_element(["main", "develop", "feature/auth"]),
            "tags": [],
            "parents": [],
            "tree_hash": Faker.hex_string(40),
        }

        return commit


class GitBranchFactory(BaseFactory, TraitMixin):
    """Factory for creating git branch objects."""

    @staticmethod
    def name() -> str:
        """Generate branch name."""
        branch_types = [
            "main",
            "develop",
            "feature/user-auth",
            "feature/api-endpoints",
            "bugfix/login-issue",
            "hotfix/security-patch",
            "release/v1.2.0",
            "chore/dependency-update",
            "docs/api-reference",
            "test/coverage-improvement",
        ]
        return Faker.random_element(branch_types)

    @staticmethod
    def commit_hash() -> str:
        """Generate commit hash."""
        return Faker.hex_string(40)

    @staticmethod
    def is_remote() -> bool:
        """Generate remote flag."""
        return Faker.random_element([True, False])

    @staticmethod
    def ahead_by() -> int:
        """Generate ahead count."""
        return Faker.random_int(0, 20)

    @staticmethod
    def behind_by() -> int:
        """Generate behind count."""
        return Faker.random_int(0, 50)

    @staticmethod
    def last_commit_date() -> datetime:
        """Generate last commit date."""
        return Faker.date_time()

    @classmethod
    def trait_main_branch(cls) -> dict[str, Any]:
        """Trait for main branch."""
        return {
            "name": "main",
            "is_remote": False,
            "ahead_by": 0,
            "behind_by": 0,
        }

    @classmethod
    def trait_feature_branch(cls) -> dict[str, Any]:
        """Trait for feature branch."""
        return {
            "name": f"feature/{Faker.random_element(['auth', 'api', 'ui', 'db'])}-{Faker.random_element(['login', 'search', 'profile', 'settings'])}",
            "is_remote": True,
            "ahead_by": Faker.random_int(1, 15),
            "behind_by": Faker.random_int(0, 10),
        }

    @classmethod
    def trait_stale_branch(cls) -> dict[str, Any]:
        """Trait for stale branch."""
        return {
            "name": f"feature/old-{Faker.random_element(['feature', 'bugfix', 'chore'])}",
            "is_remote": True,
            "ahead_by": 0,
            "behind_by": Faker.random_int(20, 100),
        }

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create git branch with computed properties."""
        branch = super().create(**kwargs)

        # Add computed properties
        branch["is_current"] = Faker.random_element([True, False])
        branch["last_commit_message"] = Faker.sentence(nb_words=6)
        branch["last_commit_author"] = Faker.name()

        # Add branch metadata
        branch["metadata"] = {
            "created_at": branch["last_commit_date"]
            - timedelta(days=Faker.random_int(1, 365)),
            "upstream": None if not branch["is_remote"] else f"origin/{branch['name']}",
            "tracking": branch["is_remote"],
        }

        return branch


class GitRepositoryStateFactory(BaseFactory, TraitMixin):
    """Factory for creating git repository state objects."""

    @staticmethod
    def current_branch() -> str:
        """Generate current branch name."""
        return Faker.random_element(["main", "develop", "feature/user-auth"])

    @staticmethod
    def default_branch() -> str:
        """Generate default branch name."""
        return Faker.random_element(["main", "master"])

    @staticmethod
    def is_dirty() -> bool:
        """Generate dirty state."""
        return Faker.random_element([True, False])

    @staticmethod
    def total_commits() -> int:
        """Generate total commits."""
        return Faker.random_int(10, 1000)

    @staticmethod
    def total_branches() -> int:
        """Generate total branches."""
        return Faker.random_int(2, 20)

    @staticmethod
    def stash_count() -> int:
        """Generate stash count."""
        return Faker.random_int(0, 5)

    @staticmethod
    def ahead_by() -> int:
        """Generate ahead count."""
        return Faker.random_int(0, 10)

    @staticmethod
    def behind_by() -> int:
        """Generate behind count."""
        return Faker.random_int(0, 20)

    @staticmethod
    def remote_url() -> str:
        """Generate remote URL."""
        return f"https://github.com/{Faker.random_element(['user', 'org', 'company'])}/{Faker.random_element(['repo', 'project', 'app'])}.git"

    @staticmethod
    def last_commit_hash() -> str:
        """Generate last commit hash."""
        return Faker.hex_string(40)

    @staticmethod
    def last_commit_message() -> str:
        """Generate last commit message."""
        return Faker.sentence(nb_words=6)

    @staticmethod
    def last_commit_date() -> datetime:
        """Generate last commit date."""
        return Faker.date_time()

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create repository state with related objects."""
        state = super().create(**kwargs)

        # Generate related collections
        state["branches"] = [
            GitBranchFactory.create() for _ in range(state["total_branches"])
        ]

        # Generate recent commits
        commit_count = min(state["total_commits"], 20)
        state["recent_commits"] = [
            GitCommitFactory.create() for _ in range(commit_count)
        ]

        # Generate stash entries
        state["stash_entries"] = []
        for i in range(state["stash_count"]):
            state["stash_entries"].append(
                {
                    "index": i,
                    "message": f"WIP: {Faker.sentence(nb_words=4)}",
                    "timestamp": Faker.date_time(),
                    "files_count": Faker.random_int(1, 8),
                }
            )

        return state

    # Trait methods
    @classmethod
    def trait_clean(cls) -> dict[str, Any]:
        """Trait for clean repository (no uncommitted changes)."""
        return {"is_dirty": False, "ahead_by": 0, "behind_by": 0, "stash_count": 0}

    @classmethod
    def trait_dirty(cls) -> dict[str, Any]:
        """Trait for dirty repository (many changes)."""
        return {
            "is_dirty": True,
            "ahead_by": Faker.random_int(3, 10),
            "stash_count": Faker.random_int(1, 5),
        }

    @classmethod
    def trait_large(cls) -> dict[str, Any]:
        """Trait for large repository."""
        return {
            "total_commits": Faker.random_int(500, 5000),
            "total_branches": Faker.random_int(10, 50),
        }


class GitDiffFactory(BaseFactory):
    """Factory for creating git diff information."""

    @staticmethod
    def file_path() -> str:
        """File path for diff."""
        return Faker.file_path()

    @staticmethod
    def lines_added() -> int:
        """Lines added in diff."""
        return Faker.random_int(0, 100)

    @staticmethod
    def lines_removed() -> int:
        """Lines removed in diff."""
        return Faker.random_int(0, 50)

    @staticmethod
    def change_type() -> str:
        """Type of change."""
        return Faker.random_element(["modified", "added", "deleted", "renamed"])

    @staticmethod
    def similarity() -> float:
        """Similarity percentage for renames."""
        return Faker.pyfloat(0.0, 1.0)

    @staticmethod
    def is_binary() -> bool:
        """Whether file is binary."""
        return Faker.weighted_choice([False, True], [0.8, 0.2])

    @staticmethod
    def hunks() -> list[dict[str, Any]]:
        """Generate diff hunks."""
        hunk_count = Faker.random_int(1, 5)
        hunks = []

        for _ in range(hunk_count):
            hunks.append(
                {
                    "start_line": Faker.random_int(1, 100),
                    "lines_added": Faker.random_int(1, 10),
                    "lines_removed": Faker.random_int(0, 5),
                    "content": f"@@ -{Faker.random_int(1, 100)},{Faker.random_int(1, 10)} +\
                    {Faker.random_int(1, 100)},{Faker.random_int(1, 10)} @@",
                }
            )

        return hunks

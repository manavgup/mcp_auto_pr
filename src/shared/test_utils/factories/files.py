"""File-related test data factories.

This module provides factories for creating realistic file changes,
file metadata, and file-related objects.
"""

import random
from datetime import datetime, timedelta
from typing import Any, TypeVar

from .base import BaseFactory, Faker, TraitMixin

T = TypeVar("T")


class FileChangeFactory(BaseFactory, TraitMixin):
    """Factory for creating file change objects."""

    @staticmethod
    def file_path() -> str:
        """Generate realistic file path."""
        # Common file patterns
        patterns = [
            "src/{module}/{file}.py",
            "tests/{module}/test_{file}.py",
            "docs/{file}.md",
            "config/{file}.yaml",
            "scripts/{file}.sh",
            "data/{file}.json",
            "static/{type}/{file}.{ext}",
            "templates/{file}.html",
            "migrations/{timestamp}_{file}.py",
            "utils/{file}.py",
        ]

        pattern = random.choice(patterns)
        modules = ["auth", "api", "core", "models", "services", "utils", "handlers"]
        files = ["user", "config", "database", "validation", "helper", "manager"]
        types = ["css", "js", "img", "fonts"]
        exts = ["css", "js", "png", "jpg", "svg", "woff"]

        return pattern.format(
            module=random.choice(modules),
            file=random.choice(files),
            type=random.choice(types),
            ext=random.choice(exts),
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )

    @staticmethod
    def change_type() -> str:
        """Generate change type."""
        return Faker.random_element(["modified", "added", "deleted", "renamed"])

    @staticmethod
    def lines_added() -> int:
        """Generate lines added."""
        # Weighted distribution: most changes are small
        weights = [0.6, 0.25, 0.1, 0.05]
        ranges = [(1, 10), (11, 50), (51, 200), (201, 1000)]
        chosen_range = Faker.weighted_choice(ranges, weights)
        return Faker.random_int(chosen_range[0], chosen_range[1])

    @staticmethod
    def lines_removed() -> int:
        """Generate lines removed."""
        # For deletions, often remove fewer lines than added
        if random.random() < 0.3:  # 30% chance of deletion
            return Faker.random_int(1, 50)
        else:
            return Faker.random_int(0, 20)

    @staticmethod
    def risk_score() -> float:
        """Generate risk score (0.0 to 1.0)."""
        return Faker.pyfloat(0.0, 1.0)

    @staticmethod
    def complexity_change() -> int:
        """Generate complexity change score."""
        return Faker.random_int(-10, 20)

    @staticmethod
    def test_coverage() -> float:
        """Generate test coverage percentage."""
        return Faker.pyfloat(0.0, 1.0)

    @staticmethod
    def file_size_bytes() -> int:
        """Generate file size in bytes."""
        return Faker.random_int(100, 102400)  # 100B to 100KB

    @staticmethod
    def last_modified() -> datetime:
        """Generate last modified timestamp."""
        return Faker.date_time()

    @staticmethod
    def language() -> str:
        """Generate programming language."""
        languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "rust",
            "cpp",
            "csharp",
            "php",
            "ruby",
            "swift",
            "kotlin",
            "scala",
            "dart",
            "elixir",
            "clojure",
            "haskell",
            "ocaml",
            "fsharp",
            "nim",
        ]
        return Faker.random_element(languages)

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create file change with computed properties."""
        change = super().create(**kwargs)

        # Adjust lines based on change type
        if change["change_type"] == "added":
            change["lines_removed"] = 0
        elif change["change_type"] == "deleted":
            change["lines_added"] = 0

        # Calculate total lines changed
        change["total_lines_changed"] = change["lines_added"] + change["lines_removed"]

        # Determine file type from path
        path = change["file_path"]
        if path.endswith((".py", ".js", ".ts", ".java", ".go", ".rs")):
            change["file_type"] = "source"
        elif path.endswith((".md", ".txt", ".rst")):
            change["file_type"] = "documentation"
        elif path.endswith((".yml", ".yaml", ".json", ".toml", ".ini")):
            change["file_type"] = "configuration"
        elif path.endswith((".test.", ".spec.", "test_", "_test.")):
            change["file_type"] = "test"
        else:
            change["file_type"] = "other"

        return change

    # Trait methods for different risk levels
    @classmethod
    def trait_high_risk(cls) -> dict[str, Any]:
        """Trait for high-risk changes."""
        return {
            "risk_score": Faker.pyfloat(0.7, 1.0),
            "complexity_change": Faker.random_int(5, 20),
            "lines_added": Faker.random_int(50, 200),
            "file_type": "source",
        }

    @classmethod
    def trait_low_risk(cls) -> dict[str, Any]:
        """Trait for low-risk changes."""
        return {
            "risk_score": Faker.pyfloat(0.0, 0.3),
            "complexity_change": Faker.random_int(-5, 5),
            "lines_added": Faker.random_int(1, 20),
            "file_type": Faker.random_element(["documentation", "configuration"]),
        }

    # Trait methods for different file types
    @classmethod
    def trait_source_code(cls) -> dict[str, Any]:
        """Trait for source code files."""
        return {
            "file_path": f"src/{Faker.random_element(['auth', 'api', 'core'])}/{Faker.random_element(['user', 'config', 'database'])}.py",
            "language": "python",
            "file_type": "source",
            "complexity_change": Faker.random_int(0, 15),
        }

    @classmethod
    def trait_test_file(cls) -> dict[str, Any]:
        """Trait for test files."""
        return {
            "file_path": f"tests/{Faker.random_element(['unit', 'integration'])}/test_{Faker.random_element(['user', 'config', 'database'])}.py",
            "language": "python",
            "file_type": "test",
            "test_coverage": Faker.pyfloat(0.8, 1.0),
        }

    @classmethod
    def trait_documentation(cls) -> dict[str, Any]:
        """Trait for documentation files."""
        return {
            "file_path": f"docs/{Faker.random_element(['user_guide', 'api_reference', 'deployment'])}.md",
            "language": "markdown",
            "file_type": "documentation",
            "risk_score": Faker.pyfloat(0.0, 0.2),
        }

    @classmethod
    def trait_configuration(cls) -> dict[str, Any]:
        """Trait for configuration files."""
        return {
            "file_path": f"config/{Faker.random_element(['database', 'app', 'logging'])}.yaml",
            "language": "yaml",
            "file_type": "configuration",
            "risk_score": Faker.pyfloat(0.1, 0.4),
        }

    # Trait methods for change sizes
    @classmethod
    def trait_large_change(cls) -> dict[str, Any]:
        """Trait for large changes."""
        return {
            "lines_added": Faker.random_int(100, 500),
            "lines_removed": Faker.random_int(20, 100),
            "complexity_change": Faker.random_int(10, 30),
            "risk_score": Faker.pyfloat(0.5, 1.0),
        }

    @classmethod
    def trait_small_change(cls) -> dict[str, Any]:
        """Trait for small changes."""
        return {
            "lines_added": Faker.random_int(1, 10),
            "lines_removed": Faker.random_int(0, 5),
            "complexity_change": Faker.random_int(-2, 2),
            "risk_score": Faker.pyfloat(0.0, 0.3),
        }


class FileMetadataFactory(BaseFactory):
    """Factory for creating file metadata objects."""

    @staticmethod
    def file_path() -> str:
        """File path."""
        return FileChangeFactory.file_path()

    @staticmethod
    def size_bytes() -> int:
        """File size in bytes."""
        return Faker.random_int(100, 100000)

    @staticmethod
    def line_count() -> int:
        """Generate a random number of lines in a file."""
        return Faker.random_int(10, 1000)

    @staticmethod
    def language() -> str:
        """Programming language."""
        return FileChangeFactory.language()

    @staticmethod
    def encoding() -> str:
        """File encoding."""
        return Faker.weighted_choice(["utf-8", "ascii", "latin-1"], [90, 8, 2])

    @staticmethod
    def permissions() -> str:
        """Generate Unix-style file permissions string."""
        return random.choice(["644", "755", "600", "664"])

    @staticmethod
    def created_date() -> datetime:
        """File creation date."""
        return datetime.now() - timedelta(days=Faker.random_int(1, 365))

    @staticmethod
    def modified_date() -> datetime:
        """Last modified date."""
        return Faker.date_time()

    @staticmethod
    def checksum() -> str:
        """File checksum/hash."""
        return Faker.hex_string(32)  # MD5-style hash

    @staticmethod
    def mime_type() -> str:
        """MIME type."""
        mime_types = {
            "python": "text/x-python",
            "javascript": "application/javascript",
            "json": "application/json",
            "yaml": "application/x-yaml",
            "markdown": "text/markdown",
            "html": "text/html",
            "css": "text/css",
            "sql": "application/sql",
            "shell": "application/x-sh",
        }
        return random.choice(list(mime_types.values()))


# Convenience functions for creating file-related collections
def create_file_changes(
    count: int = 5,
    risk_distribution: str = "mixed",
    change_types: list[str] | None = None,
    **kwargs,
) -> list[dict[str, Any]]:
    """Create a list of realistic file changes.

    Args:
        count: Number of file changes to create
        risk_distribution: 'low', 'high', or 'mixed'
        change_types: List of allowed change types
        **kwargs: Additional arguments passed to factory

    Returns:
        List of file change dictionaries
    """
    if change_types is None:
        change_types = ["modified", "added", "deleted"]

    changes = []

    for _ in range(count):
        # Determine risk level
        if risk_distribution == "low":
            change = FileChangeFactory.with_traits("low_risk", **kwargs)
        elif risk_distribution == "high":
            change = FileChangeFactory.with_traits("high_risk", **kwargs)
        else:  # mixed
            risk_type = Faker.weighted_choice(
                ["low_risk", "medium", "high_risk"], [60, 30, 10]
            )
            if risk_type == "low_risk":
                change = FileChangeFactory.with_traits("low_risk", **kwargs)
            elif risk_type == "high_risk":
                change = FileChangeFactory.with_traits("high_risk", **kwargs)
            else:
                change = FileChangeFactory.create(**kwargs)

        # Override change type if specified
        if change_types:
            change["change_type"] = random.choice(change_types)

        changes.append(change)

    return changes


def create_file_tree(depth: int = 3, files_per_dir: int = 5) -> dict[str, Any]:
    """Create a realistic file tree structure."""

    def _create_directory(current_depth: int, max_depth: int) -> dict[str, Any]:
        if current_depth >= max_depth:
            return {}

        directory = {}

        # Add files to this directory
        for _ in range(random.randint(1, files_per_dir)):
            file_meta = FileMetadataFactory.create()
            filename = file_meta["file_path"].split("/")[-1]
            directory[filename] = file_meta

        # Add subdirectories
        subdir_count = random.randint(0, 3) if current_depth < max_depth - 1 else 0
        for i in range(subdir_count):
            subdir_name = f"subdir_{i}"
            directory[subdir_name] = _create_directory(current_depth + 1, max_depth)

        return directory

    return _create_directory(0, depth)


def create_diff_summary(file_changes: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a summary of file changes (like git diff --stat)."""
    total_files = len(file_changes)
    total_additions = sum(change.get("lines_added", 0) for change in file_changes)
    total_deletions = sum(change.get("lines_removed", 0) for change in file_changes)

    # Categorize changes by type
    change_types = {}
    for change in file_changes:
        change_type = change.get("change_type", "modified")
        change_types[change_type] = change_types.get(change_type, 0) + 1

    # Find largest changes
    largest_changes = sorted(
        file_changes,
        key=lambda c: c.get("lines_added", 0) + c.get("lines_removed", 0),
        reverse=True,
    )[:5]

    return {
        "total_files": total_files,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "net_change": total_additions - total_deletions,
        "change_types": change_types,
        "largest_changes": [
            {
                "file_path": change["file_path"],
                "total_lines": change.get("lines_added", 0)
                + change.get("lines_removed", 0),
            }
            for change in largest_changes
        ],
        "binary_files": [
            change["file_path"]
            for change in file_changes
            if change.get("file_path", "").endswith((".png", ".jpg", ".pdf", ".exe"))
        ],
    }


def create_file_changes_by_category() -> dict[str, list[dict[str, Any]]]:
    """Create file changes categorized by type."""
    categories: dict[str, list[dict[str, Any]]] = {
        "source": [],
        "test": [],
        "documentation": [],
        "configuration": [],
        "other": [],
    }

    # Create changes for each category
    for category in categories:
        if category == "source":
            changes = [
                FileChangeFactory.with_traits("source_code")
                for _ in range(random.randint(3, 8))
            ]
        elif category == "test":
            changes = [
                FileChangeFactory.with_traits("test_file")
                for _ in range(random.randint(2, 5))
            ]
        elif category == "documentation":
            changes = [
                FileChangeFactory.with_traits("documentation")
                for _ in range(random.randint(1, 4))
            ]
        elif category == "configuration":
            changes = [
                FileChangeFactory.with_traits("configuration")
                for _ in range(random.randint(1, 3))
            ]
        else:
            changes = [FileChangeFactory.create() for _ in range(random.randint(1, 3))]

        categories[category] = changes

    return categories

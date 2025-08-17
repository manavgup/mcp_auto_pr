"""Base factory classes and utilities for the MCP test ecosystem.

This module provides the foundation for all other factories, including
a simple Faker implementation and base factory class.
"""

import random
import uuid
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


class Faker:
    """Simple faker implementation for generating realistic test data.

    This provides basic data generation without external dependencies.
    Can be easily extended or replaced with factory_boy's Faker if needed.
    """

    @staticmethod
    def sentence(nb_words: int = 6) -> str:
        """Generate a realistic sentence."""
        words = [
            "implement",
            "refactor",
            "optimize",
            "enhance",
            "improve",
            "update",
            "authentication",
            "validation",
            "processing",
            "analysis",
            "monitoring",
            "user",
            "data",
            "system",
            "service",
            "feature",
            "functionality",
            "performance",
            "security",
            "reliability",
            "scalability",
            "maintainability",
        ]
        return " ".join(random.choices(words, k=nb_words)).capitalize()

    @staticmethod
    def name() -> str:
        """Generate a realistic person name."""
        first_names = [
            "Alex",
            "Jordan",
            "Taylor",
            "Casey",
            "Morgan",
            "Riley",
            "Avery",
            "Quinn",
            "Sam",
            "Charlie",
            "Dana",
            "Jesse",
            "Reese",
            "Blake",
            "Cameron",
            "Drew",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
            "Hernandez",
            "Lopez",
            "Gonzalez",
        ]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    @staticmethod
    def email() -> str:
        """Generate a realistic email address."""
        domains = ["example.com", "test.org", "sample.net", "demo.io", "mock.dev"]
        prefixes = ["user", "test", "demo", "sample", "dev", "team", "admin"]
        prefix = random.choice(prefixes)
        number = random.randint(1, 999)
        domain = random.choice(domains)
        return f"{prefix}{number}@{domain}"

    @staticmethod
    def file_path(depth: int = 2, extension: str = "py") -> str:
        """Generate a realistic file path."""
        directories = [
            "src",
            "tests",
            "docs",
            "config",
            "utils",
            "models",
            "services",
            "tools",
            "lib",
            "core",
            "api",
            "cli",
            "web",
            "db",
            "migrations",
        ]

        files = [
            "main",
            "utils",
            "config",
            "helpers",
            "models",
            "client",
            "server",
            "processor",
            "analyzer",
            "validator",
            "formatter",
            "parser",
            "handler",
            "manager",
            "controller",
            "service",
            "repository",
            "factory",
            "builder",
        ]

        # Build path with specified depth
        path_parts = [random.choice(directories) for _ in range(depth)]
        filename = f"{random.choice(files)}.{extension}"

        return str(Path(*path_parts, filename))

    @staticmethod
    def date_time() -> datetime:
        """Generate a realistic datetime."""
        base = datetime.now()
        # Random time within the last 30 days
        offset = timedelta(
            days=random.randint(-30, 0),
            hours=random.randint(-23, 23),
            minutes=random.randint(-59, 59),
        )
        return base + offset

    @staticmethod
    def random_int(min_val: int = 0, max_val: int = 100) -> int:
        """Generate a random integer."""
        return random.randint(min_val, max_val)

    @staticmethod
    def pyfloat(
        min_value: float = 0.0, max_value: float = 1.0, precision: int = 2
    ) -> float:
        """Generate a random float."""
        value = random.uniform(min_value, max_value)
        return round(value, precision)

    @staticmethod
    def text(max_nb_chars: int = 200) -> str:
        """Generate realistic text content."""
        sentences = [
            "This implementation provides comprehensive functionality for the system.",
            "The new feature enhances user experience and improves performance.",
            "Robust error handling ensures system reliability and stability.",
            "Optimized algorithms deliver better processing speed and efficiency.",
            "Enhanced security measures protect against common vulnerabilities.",
            "The modular design facilitates easier maintenance and extensibility.",
            "Comprehensive testing coverage ensures code quality and reliability.",
            "User-friendly interface simplifies complex operations and workflows.",
        ]

        text = ""
        while len(text) < max_nb_chars:
            sentence = random.choice(sentences)
            if len(text + sentence) <= max_nb_chars:
                text += sentence + " "
            else:
                break

        return text.strip()

    @staticmethod
    def url() -> str:
        """Generate a realistic repository URL."""
        platforms = ["github.com", "gitlab.com", "bitbucket.org"]
        organizations = ["company", "team", "project", "organization", "group"]
        repositories = [
            "web-app",
            "api-service",
            "data-processor",
            "ml-pipeline",
            "user-service",
            "auth-system",
            "monitoring-tool",
            "deployment-scripts",
        ]

        platform = random.choice(platforms)
        org = random.choice(organizations)
        repo = random.choice(repositories)

        return f"https://{platform}/{org}/{repo}.git"

    @staticmethod
    def uuid4() -> str:
        """Generate a UUID4 string."""
        return str(uuid.uuid4())

    @staticmethod
    def hex_string(length: int = 40) -> str:
        """Generate a hex string (useful for git hashes)."""
        return "".join(random.choices("0123456789abcdef", k=length))

    @staticmethod
    def random_element(elements: list[Any]) -> Any:
        """Choose a random element from a list."""
        return random.choice(elements)

    @staticmethod
    def weighted_choice(choices: list[Any], weights: list[float]) -> Any:
        """Choose a random element with weights."""
        return random.choices(choices, weights=weights)[0]


class BaseFactory:
    """Base factory class providing common functionality for all factories.

    This class provides the foundation for creating test objects with
    realistic defaults and easy customization.
    """

    # Override in subclasses to specify the model/type to create
    _model = dict

    @classmethod
    def create(cls, **kwargs: Any) -> Any:
        """Create an instance with optional overrides.

        Args:
            **kwargs: Override any default attributes

        Returns:
            Created instance (dict by default, or specified model)
        """
        # Get default values from class attributes
        defaults = cls._get_defaults()

        # Override with provided kwargs
        defaults.update(kwargs)

        # Create and return the object
        if cls._model is dict:
            return defaults
        else:
            return cls._model(**defaults)

    @classmethod
    def build(cls, **kwargs: Any) -> Any:
        """Alias for create method for factory_boy compatibility."""
        return cls.create(**kwargs)

    @classmethod
    def create_batch(cls, size: int, **kwargs: Any) -> list[Any]:
        """Create multiple instances."""
        return [cls.create(**kwargs) for _ in range(size)]

    @classmethod
    def _get_defaults(cls) -> dict[str, Any]:
        """Extract default values from class attributes."""
        defaults = {}

        for attr_name in dir(cls):
            # Skip private attributes and methods
            if attr_name.startswith("_") or attr_name in [
                "create",
                "build",
                "create_batch",
            ]:
                continue

            attr_value = getattr(cls, attr_name)

            # If it's a callable (like a Faker method), call it
            if callable(attr_value):
                with suppress(Exception):
                    defaults[attr_name] = attr_value()
            # If it's a regular value, use it directly
            elif not callable(attr_value):
                defaults[attr_name] = attr_value

        return defaults


class TraitMixin:
    """Mixin for adding trait support to factories.

    Traits allow for easy creation of variations of the same factory.
    """

    # Type hints for mypy - these should be overridden by concrete classes
    _model: type[Any] = dict

    @classmethod
    def _get_defaults(cls) -> dict[str, Any]:
        """Extract default values from class attributes. Must be implemented by concrete classes."""
        return {}

    @classmethod
    def with_traits(cls, *trait_names: str, **kwargs: Any) -> Any:
        """Create an instance with specified traits applied."""
        # Get base defaults
        defaults = cls._get_defaults()

        # Apply traits
        for trait_name in trait_names:
            trait_method = getattr(cls, f"trait_{trait_name}", None)
            if trait_method:
                trait_overrides = trait_method()
                defaults.update(trait_overrides)

        # Apply final overrides
        defaults.update(kwargs)

        # Create the object
        if cls._model is dict:
            return defaults
        else:
            return cls._model(**defaults)


class SequenceMixin:
    """Mixin for adding sequence support to factories.

    Sequences provide unique values across multiple instances.
    """

    _sequences: dict[str, int] = {}

    @classmethod
    def sequence(cls, name: str, template: str = "{n}") -> str:
        """Generate a sequence value."""
        if name not in cls._sequences:
            cls._sequences[name] = 0

        cls._sequences[name] += 1
        return template.format(n=cls._sequences[name])

    @classmethod
    def reset_sequences(cls) -> None:
        """Reset all sequences to 0."""
        cls._sequences.clear()


# Utility functions for common patterns
def create_realistic_timestamp(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    """Create a realistic timestamp relative to now."""
    base = datetime.now()
    offset = timedelta(days=-abs(days_ago), hours=-abs(hours_ago))
    return base + offset


def generate_commit_message(commit_type: str | None = None) -> str:
    """Generate a realistic commit message."""
    if commit_type is None:
        commit_type = random.choice(
            ["feat", "fix", "docs", "refactor", "test", "chore"]
        )

    scopes = ["auth", "api", "ui", "db", "core", "utils", "tests", "docs"]
    scope = random.choice(scopes)

    actions = {
        "feat": ["add", "implement", "create", "introduce"],
        "fix": ["resolve", "correct", "patch", "repair"],
        "docs": ["update", "improve", "add", "clarify"],
        "refactor": ["reorganize", "simplify", "optimize", "restructure"],
        "test": ["add", "improve", "update", "fix"],
        "chore": ["update", "maintain", "configure", "upgrade"],
    }

    subjects = [
        "user authentication",
        "data validation",
        "error handling",
        "API endpoints",
        "database queries",
        "configuration settings",
        "performance monitoring",
        "security checks",
        "test coverage",
    ]

    action = random.choice(actions[commit_type])
    subject = random.choice(subjects)

    return f"{commit_type}({scope}): {action} {subject}"


def create_realistic_file_content(file_type: str, lines: int = 50) -> str:
    """Generate realistic file content based on file type."""
    if file_type == "python":
        return _create_python_content(lines)
    elif file_type == "markdown":
        return _create_markdown_content(lines)
    elif file_type == "json":
        return _create_json_content()
    elif file_type == "yaml":
        return _create_yaml_content()
    else:
        return _create_generic_content(lines)


def _create_python_content(lines: int) -> str:
    """Create realistic Python file content."""
    content = [
        '"""Module for processing and analyzing data."""',
        "",
        "import os",
        "import sys",
        "from typing import Dict, Any, List, Optional",
        "",
        "",
        "class DataProcessor:",
        '    """Process and analyze data efficiently."""',
        "    ",
        "    def __init__(self, config: Optional[Dict[str, Any]] = None):",
        "        self.config = config or {}",
        "        self.results = {}",
        "    ",
        "    def process(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:",
        '        """Process the input data and return results."""',
        "        # Implementation here",
        '        return {"processed": len(data), "status": "success"}',
        "    ",
        "    def validate(self, data: Any) -> bool:",
        '        """Validate input data."""',
        "        return isinstance(data, (list, dict))",
        "",
        "",
        "def main():",
        '    """Main entry point."""',
        "    processor = DataProcessor()",
        '    print("Processing complete")',
        "",
        "",
        'if __name__ == "__main__":',
        "    main()",
    ]

    # Pad or trim to desired length
    while len(content) < lines:
        content.extend(["    # Additional processing logic", "    pass"])

    return "\n".join(content[:lines])


def _create_markdown_content(lines: int) -> str:
    """Create realistic Markdown content."""
    content = [
        "# Project Documentation",
        "",
        "This document provides comprehensive information about the project.",
        "",
        "## Overview",
        "",
        "The system provides advanced functionality for data processing and analysis.",
        "",
        "## Features",
        "",
        "- High-performance data processing",
        "- Comprehensive error handling",
        "- Flexible configuration options",
        "- Extensive test coverage",
        "",
        "## Installation",
        "",
        "```bash",
        "pip install package-name",
        "```",
        "",
        "## Usage",
        "",
        "Basic usage example:",
        "",
        "```python",
        "from package import DataProcessor",
        "processor = DataProcessor()",
        "result = processor.process(data)",
        "```",
    ]

    while len(content) < lines:
        content.extend(["", "Additional documentation content here."])

    return "\n".join(content[:lines])


def _create_json_content() -> str:
    """Create realistic JSON configuration."""
    config = {
        "version": "1.0.0",
        "debug": False,
        "database": {"host": "localhost", "port": 5432, "name": "app_db"},
        "features": {"advanced_processing": True, "monitoring": True, "caching": False},
        "thresholds": {"max_items": 1000, "timeout": 30, "retry_count": 3},
    }

    import json

    return json.dumps(config, indent=2)


def _create_yaml_content() -> str:
    """Create realistic YAML configuration."""
    return """version: "1.0.0"
debug: false

database:
  host: localhost
  port: 5432
  name: app_db

features:
  advanced_processing: true
  monitoring: true
  caching: false

thresholds:
  max_items: 1000
  timeout: 30
  retry_count: 3
"""


def _create_generic_content(lines: int) -> str:
    """Create generic text content."""
    content = []
    for i in range(lines):
        content.append(f"Line {i + 1}: This is sample content for testing purposes.")

    return "\n".join(content)

"""Recommendation-related test data factories.

This module provides factories for creating realistic PR recommendations
and recommendation-related objects.
"""

import random
from datetime import datetime
from typing import Any, TypeVar

from .base import BaseFactory, Faker, SequenceMixin, TraitMixin

T = TypeVar("T")


class PRRecommendationFactory(BaseFactory, SequenceMixin, TraitMixin):
    """Factory for creating PR recommendation objects."""

    @classmethod
    def id(cls) -> str:
        """Generate unique PR recommendation ID."""
        return cls.sequence("pr_rec", "pr_rec_{n:06d}")

    @staticmethod
    def title() -> str:
        """Generate PR title."""
        return Faker.sentence(nb_words=5)

    @staticmethod
    def description() -> str:
        """Generate PR description."""
        return Faker.text(max_nb_chars=200)

    @staticmethod
    def priority() -> str:
        """Generate priority level."""
        return Faker.random_element(["low", "medium", "high", "critical"])

    @staticmethod
    def estimated_effort() -> str:
        """Generate effort estimate."""
        return Faker.random_element(["small", "medium", "large"])

    @staticmethod
    def file_count() -> int:
        """Generate file count."""
        return Faker.random_int(1, 15)

    @staticmethod
    def total_lines_changed() -> int:
        """Generate total lines changed."""
        return Faker.random_int(10, 500)

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create PR recommendation with computed properties."""
        rec = super().create(**kwargs)

        # Determine PR type based on title
        title_lower = rec["title"].lower()
        if any(word in title_lower for word in ["feat", "feature", "add"]):
            rec["pr_type"] = "feature"
        elif any(word in title_lower for word in ["fix", "bug", "patch"]):
            rec["pr_type"] = "bugfix"
        elif any(word in title_lower for word in ["refactor", "improve", "optimize"]):
            rec["pr_type"] = "refactor"
        elif any(word in title_lower for word in ["doc", "readme", "guide"]):
            rec["pr_type"] = "documentation"
        elif any(word in title_lower for word in ["test", "spec", "coverage"]):
            rec["pr_type"] = "test"
        else:
            rec["pr_type"] = "other"

        # Generate rationale for this PR grouping
        rationales = {
            "feature": "Groups related feature development files together",
            "bugfix": "Isolates bug fix changes for focused review",
            "refactor": "Combines refactoring changes for consistency",
            "documentation": "Groups documentation updates separately",
            "test": "Isolates test changes for independent review",
            "other": "Groups related changes logically",
        }
        rec["rationale"] = rationales.get(
            rec["pr_type"], "Groups related changes together"
        )

        return rec

    # Trait methods for different PR types
    @classmethod
    def trait_feature_pr(cls) -> dict[str, Any]:
        """Trait for feature PRs."""
        return {
            "title": f"feat: {Faker.sentence(nb_words=4)}",
            "priority": Faker.random_element(["medium", "high"]),
            "estimated_effort": Faker.random_element(["medium", "large"]),
            "file_count": Faker.random_int(3, 12),
        }

    @classmethod
    def trait_bugfix_pr(cls) -> dict[str, Any]:
        """Trait for bugfix PRs."""
        return {
            "title": f"fix: {Faker.sentence(nb_words=4)}",
            "priority": Faker.random_element(["high", "critical"]),
            "estimated_effort": Faker.random_element(["small", "medium"]),
            "file_count": Faker.random_int(1, 5),
        }

    @classmethod
    def trait_docs_pr(cls) -> dict[str, Any]:
        """Trait for documentation PRs."""
        return {
            "title": f"docs: {Faker.sentence(nb_words=4)}",
            "priority": Faker.random_element(["low", "medium"]),
            "estimated_effort": Faker.random_element(["small", "medium"]),
            "file_count": Faker.random_int(1, 3),
        }

    @classmethod
    def trait_refactor_pr(cls) -> dict[str, Any]:
        """Trait for refactor PRs."""
        return {
            "title": f"refactor: {Faker.sentence(nb_words=4)}",
            "priority": Faker.random_element(["medium", "high"]),
            "estimated_effort": Faker.random_element(["medium", "large"]),
            "file_count": Faker.random_int(2, 8),
        }

    @classmethod
    def trait_test_pr(cls) -> dict[str, Any]:
        """Trait for test PRs."""
        return {
            "title": f"test: {Faker.sentence(nb_words=4)}",
            "priority": Faker.random_element(["low", "medium"]),
            "estimated_effort": Faker.random_element(["small", "medium"]),
            "file_count": Faker.random_int(1, 4),
        }


class RecommendationGroupFactory(BaseFactory):
    """Factory for creating groups of related recommendations."""

    @staticmethod
    def group_name() -> str:
        """Generate group name."""
        return Faker.random_element(
            [
                "Core Features",
                "Bug Fixes",
                "Documentation Updates",
                "Test Improvements",
                "Performance Optimizations",
                "Security Enhancements",
                "Configuration Changes",
            ]
        )

    @staticmethod
    def group_priority() -> str:
        """Generate group priority."""
        return Faker.random_element(["low", "medium", "high", "critical"])

    @staticmethod
    def estimated_completion_days() -> int:
        """Generate estimated completion time."""
        return Faker.random_int(1, 14)

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create recommendation group with computed properties."""
        group = super().create(**kwargs)

        # Add computed properties
        group["estimated_completion_hours"] = group["estimated_completion_days"] * 8
        group["complexity_score"] = Faker.pyfloat(0.1, 1.0)
        group["risk_level"] = Faker.random_element(["low", "medium", "high"])

        # Add group metadata
        group["metadata"] = {
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "assigned_team": Faker.random_element(
                ["frontend", "backend", "devops", "qa"]
            ),
            "dependencies": [],
            "blockers": [],
        }

        return group


# Convenience functions for creating recommendation collections
def create_pr_recommendation_set(
    count: int = 5, strategy: str = "mixed"
) -> list[dict[str, Any]]:
    """Create a realistic set of PR recommendations."""
    recommendations = []

    if strategy == "mixed":
        # Mix of different PR types
        pr_types = ["feature_pr", "bugfix_pr", "docs_pr", "refactor_pr", "test_pr"]

        for i in range(count):
            pr_type = pr_types[i % len(pr_types)] if i < len(pr_types) else None

            if pr_type:
                rec = PRRecommendationFactory.with_traits(pr_type)
            else:
                rec = PRRecommendationFactory.create()

            recommendations.append(rec)

    elif strategy == "feature_focused":
        # Mostly feature PRs
        for _ in range(count):
            if random.random() < 0.8:
                rec = PRRecommendationFactory.with_traits("feature_pr")
            else:
                rec = PRRecommendationFactory.with_traits("test_pr")
            recommendations.append(rec)

    elif strategy == "maintenance":
        # Bug fixes and refactoring
        for _ in range(count):
            if random.random() < 0.6:
                rec = PRRecommendationFactory.with_traits("bugfix_pr")
            else:
                rec = PRRecommendationFactory.with_traits("refactor_pr")
            recommendations.append(rec)

    else:
        # Default: create standard recommendations
        recommendations = [PRRecommendationFactory.create() for _ in range(count)]

    return recommendations


def create_recommendation_summary(
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a summary of PR recommendations."""
    if not recommendations:
        return {"total_prs": 0, "summary": "No recommendations available"}

    # Count by type
    type_counts: dict[str, int] = {}
    for rec in recommendations:
        pr_type = rec.get("pr_type", "other")
        type_counts[pr_type] = type_counts.get(pr_type, 0) + 1

    # Count by priority
    priority_counts: dict[str, int] = {}
    for rec in recommendations:
        priority = rec.get("priority", "medium")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    # Calculate totals
    total_files = sum(rec.get("file_count", 0) for rec in recommendations)
    total_lines = sum(rec.get("total_lines_changed", 0) for rec in recommendations)

    return {
        "total_prs": len(recommendations),
        "total_files": total_files,
        "total_lines_changed": total_lines,
        "type_distribution": type_counts,
        "priority_distribution": priority_counts,
        "average_files_per_pr": (
            total_files / len(recommendations) if recommendations else 0
        ),
        "average_lines_per_pr": (
            total_lines / len(recommendations) if recommendations else 0
        ),
        "complexity_score": _calculate_complexity_score(recommendations),
    }


def _calculate_complexity_score(recommendations: list[dict[str, Any]]) -> float:
    """Calculate complexity score for recommendations."""
    if not recommendations:
        return 0.0

    total_score = 0.0
    for rec in recommendations:
        # Base complexity on file count and lines changed
        file_score = min(rec.get("file_count", 0) / 10.0, 1.0)
        lines_score = min(rec.get("total_lines_changed", 0) / 500.0, 1.0)

        # Weight by priority
        priority_weights = {"low": 0.5, "medium": 0.7, "high": 0.9, "critical": 1.0}
        priority_weight = priority_weights.get(rec.get("priority", "medium"), 0.7)

        rec_score = (file_score + lines_score) / 2.0 * priority_weight
        total_score += rec_score

    return total_score / len(recommendations)


def create_recommendation_metrics() -> dict[str, Any]:
    """Create metrics for recommendation quality assessment."""
    return {
        "generated_at": datetime.now(),
        "algorithm_version": "1.0.0",
        "confidence_score": Faker.pyfloat(0.7, 1.0),
        "processing_time_ms": Faker.random_int(100, 5000),
        "recommendations_considered": Faker.random_int(10, 100),
        "recommendations_generated": Faker.random_int(3, 15),
        "quality_factors": {
            "file_grouping_coherence": Faker.pyfloat(0.6, 1.0),
            "risk_distribution_balance": Faker.pyfloat(0.5, 1.0),
            "size_optimization": Faker.pyfloat(0.7, 1.0),
            "dependency_awareness": Faker.pyfloat(0.6, 1.0),
        },
    }

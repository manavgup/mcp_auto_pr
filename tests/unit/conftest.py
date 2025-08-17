"""Test configuration and fixtures for mcp_pr_recommender.

This module provides PR recommender-specific fixtures while importing
shared fixtures from mcp_shared_lib.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from tests.utils.factories import FileChangeFactory, create_file_changes


@pytest.fixture
def sample_config():
    """Provide basic configuration for testing."""
    return {
        "git_client": {"timeout": 30},
        "analyzer": {"scan_depth": 10},
    }


@pytest.fixture
def temp_dir():
    """Temporary directory fixture."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def pr_recommender_config(sample_config):
    """Provide extended configuration specific to the PR recommender."""
    config = sample_config.copy()
    config.update(
        {
            "pr_recommender": {
                "max_files_per_pr": 15,
                "min_files_per_pr": 2,
                "similarity_threshold": 0.7,
                "max_prs_to_recommend": 5,
                "grouping_strategy": "semantic",  # semantic, size, risk, manual
                "risk_balance": True,
                "include_test_files": True,
            },
            "grouping": {
                "semantic_similarity": {
                    "enabled": True,
                    "threshold": 0.75,
                    "model": "text-similarity",
                },
                "file_path_similarity": {"enabled": True, "weight": 0.3},
                "change_type_grouping": {"enabled": True, "group_similar_types": True},
                "size_balancing": {
                    "enabled": True,
                    "target_size": "medium",
                    "max_deviation": 0.3,
                },
            },
            "recommendation_engine": {
                "scoring_weights": {
                    "cohesion": 0.4,
                    "size_balance": 0.3,
                    "risk_distribution": 0.3,
                },
                "filters": {
                    "exclude_low_impact": True,
                    "min_confidence": 0.6,
                    "require_tests": False,
                },
            },
        }
    )
    return config


@pytest.fixture
def mock_pr_grouper():
    """Mock PR grouper service for testing."""
    grouper = Mock()

    # Main grouping method
    grouper.group_files.return_value = [
        {
            "group_id": "auth_features",
            "files": ["src/auth/login.py", "src/auth/logout.py", "tests/test_auth.py"],
            "description": "Authentication feature updates",
            "cohesion_score": 0.85,
            "estimated_size": "medium",
            "risk_level": "medium",
        },
        {
            "group_id": "user_model",
            "files": [
                "src/models/user.py",
                "src/models/profile.py",
                "tests/test_user_model.py",
            ],
            "description": "User model enhancements",
            "cohesion_score": 0.92,
            "estimated_size": "small",
            "risk_level": "low",
        },
        {
            "group_id": "config_updates",
            "files": ["config/database.json", "config/auth.yaml"],
            "description": "Configuration updates",
            "cohesion_score": 0.78,
            "estimated_size": "small",
            "risk_level": "high",
        },
    ]

    # Similarity analysis
    grouper.calculate_file_similarity.return_value = 0.8
    grouper.analyze_change_patterns.return_value = {
        "dominant_pattern": "feature_addition",
        "pattern_confidence": 0.85,
        "suggested_grouping": "by_feature",
    }

    # Group optimization
    grouper.optimize_groups.return_value = {
        "optimized": True,
        "changes_made": 2,
        "final_score": 0.87,
        "improvements": ["Moved test files to feature groups", "Balanced group sizes"],
    }

    return grouper


@pytest.fixture
def mock_recommendation_engine():
    """Mock recommendation engine for testing."""
    engine = Mock()

    # Generate recommendations
    engine.generate_recommendations.return_value = [
        {
            "id": "pr_001",
            "title": "Add user authentication system",
            "description": "Implement comprehensive user authentication with login, logout, and session management.",
            "files": [
                "src/auth/login.py",
                "src/auth/logout.py",
                "src/auth/session.py",
                "tests/test_auth.py",
            ],
            "estimated_size": "large",
            "priority": "high",
            "risk_level": "medium",
            "confidence": 0.92,
            "labels": ["feature", "authentication", "security"],
            "reviewers": ["senior-dev", "security-team"],
            "estimated_review_time": "2-3 hours",
        },
        {
            "id": "pr_002",
            "title": "Update user and profile models",
            "description": "Enhance user model with new fields and improve profile management.",
            "files": [
                "src/models/user.py",
                "src/models/profile.py",
                "tests/test_user_model.py",
                "migrations/0002_user_updates.py",
            ],
            "estimated_size": "medium",
            "priority": "medium",
            "risk_level": "low",
            "confidence": 0.88,
            "labels": ["enhancement", "models"],
            "reviewers": ["backend-team"],
            "estimated_review_time": "1-2 hours",
        },
        {
            "id": "pr_003",
            "title": "Critical configuration updates",
            "description": "Update database and authentication configuration for production deployment.",
            "files": ["config/database.json", "config/auth.yaml", "docs/deployment.md"],
            "estimated_size": "small",
            "priority": "critical",
            "risk_level": "high",
            "confidence": 0.95,
            "labels": ["config", "deployment", "critical"],
            "reviewers": ["devops-team", "senior-dev"],
            "estimated_review_time": "30-60 minutes",
        },
    ]

    # Scoring and ranking
    engine.score_recommendation.return_value = {
        "overall_score": 0.85,
        "factors": {
            "cohesion": 0.9,
            "size_appropriateness": 0.8,
            "risk_balance": 0.85,
            "review_efficiency": 0.88,
        },
    }

    engine.rank_recommendations.return_value = [
        {"id": "pr_003", "rank": 1, "score": 0.95},
        {"id": "pr_001", "rank": 2, "score": 0.92},
        {"id": "pr_002", "rank": 3, "score": 0.88},
    ]

    # Optimization suggestions
    engine.suggest_optimizations.return_value = {
        "suggestions": [
            "Consider splitting large PR into smaller ones",
            "Add more test coverage for new features",
            "Include documentation updates",
        ],
        "confidence": 0.8,
    }

    return engine


@pytest.fixture
def sample_change_analysis():
    """Sample change analysis data for testing."""
    return {
        "timestamp": datetime.now(),
        "repository": {
            "path": "/test/repo",
            "name": "test-project",
            "branch": "feature/user-auth",
        },
        "changes": [
            {
                "file_path": "src/auth/login.py",
                "change_type": "added",
                "lines_added": 125,
                "lines_removed": 0,
                "risk_score": 0.6,
                "complexity_score": 8,
                "semantic_category": "authentication",
                "dependencies": ["src/models/user.py", "src/utils/crypto.py"],
            },
            {
                "file_path": "src/auth/logout.py",
                "change_type": "added",
                "lines_added": 45,
                "lines_removed": 0,
                "risk_score": 0.3,
                "complexity_score": 3,
                "semantic_category": "authentication",
                "dependencies": ["src/auth/session.py"],
            },
            {
                "file_path": "src/models/user.py",
                "change_type": "modified",
                "lines_added": 30,
                "lines_removed": 5,
                "risk_score": 0.4,
                "complexity_score": 5,
                "semantic_category": "data_model",
                "dependencies": [],
            },
            {
                "file_path": "tests/test_auth.py",
                "change_type": "added",
                "lines_added": 180,
                "lines_removed": 0,
                "risk_score": 0.1,
                "complexity_score": 6,
                "semantic_category": "testing",
                "dependencies": ["src/auth/login.py", "src/auth/logout.py"],
            },
            {
                "file_path": "config/auth.yaml",
                "change_type": "added",
                "lines_added": 25,
                "lines_removed": 0,
                "risk_score": 0.8,
                "complexity_score": 1,
                "semantic_category": "configuration",
                "dependencies": [],
            },
            {
                "file_path": "docs/authentication.md",
                "change_type": "added",
                "lines_added": 90,
                "lines_removed": 0,
                "risk_score": 0.0,
                "complexity_score": 0,
                "semantic_category": "documentation",
                "dependencies": [],
            },
        ],
        "summary": {
            "total_files": 6,
            "total_lines_added": 495,
            "total_lines_removed": 5,
            "average_risk_score": 0.37,
            "categories": {
                "authentication": 2,
                "data_model": 1,
                "testing": 1,
                "configuration": 1,
                "documentation": 1,
            },
        },
    }


@pytest.fixture
def expected_pr_recommendations():
    """Provide expected PR recommendations for testing."""
    return [
        {
            "title": "Add core authentication functionality",
            "description": "Implement login and logout functionality with session management and user model updates.",
            "files": [
                "src/auth/login.py",
                "src/auth/logout.py",
                "src/models/user.py",
                "tests/test_auth.py",
            ],
            "estimated_size": "large",
            "risk_level": "medium",
            "priority": "high",
            "confidence": 0.9,
            "labels": ["feature", "authentication"],
            "rationale": "Groups core authentication files with their tests and related model changes",
        },
        {
            "title": "Add authentication configuration",
            "description": "Add authentication configuration and documentation.",
            "files": ["config/auth.yaml", "docs/authentication.md"],
            "estimated_size": "small",
            "risk_level": "high",
            "priority": "critical",
            "confidence": 0.85,
            "labels": ["config", "documentation"],
            "rationale": "Separates high-risk configuration changes for focused review",
        },
    ]


@pytest.fixture
def mock_file_similarity_analyzer():
    """Mock file similarity analyzer."""
    analyzer = Mock()

    # Calculate similarity between files
    def mock_similarity(file1, file2):
        # Mock some realistic similarities
        similarity_map = {
            ("src/auth/login.py", "src/auth/logout.py"): 0.85,
            ("src/auth/login.py", "tests/test_auth.py"): 0.7,
            ("src/models/user.py", "src/models/profile.py"): 0.9,
            ("config/database.json", "config/auth.yaml"): 0.6,
        }
        key = (file1, file2) if file1 < file2 else (file2, file1)
        return similarity_map.get(key, 0.3)

    analyzer.calculate_similarity.side_effect = mock_similarity

    # Semantic categorization
    analyzer.categorize_file.return_value = {
        "category": "authentication",
        "subcategory": "core_logic",
        "confidence": 0.9,
    }

    # Dependency analysis
    analyzer.analyze_dependencies.return_value = {
        "imports": ["os", "json", "typing"],
        "internal_deps": ["src.models.user", "src.utils.crypto"],
        "dependency_score": 0.8,
    }

    return analyzer


@pytest.fixture
def grouping_test_scenarios():
    """Test scenarios for different grouping strategies."""
    return {
        "by_feature": {
            "description": "Group files by feature/functionality",
            "input_changes": [
                {"file": "src/auth/login.py", "category": "auth"},
                {"file": "src/auth/logout.py", "category": "auth"},
                {"file": "src/user/profile.py", "category": "user"},
                {"file": "src/user/settings.py", "category": "user"},
                {"file": "tests/test_auth.py", "category": "auth"},
                {"file": "tests/test_user.py", "category": "user"},
            ],
            "expected_groups": [
                {
                    "name": "Authentication features",
                    "files": [
                        "src/auth/login.py",
                        "src/auth/logout.py",
                        "tests/test_auth.py",
                    ],
                },
                {
                    "name": "User management features",
                    "files": [
                        "src/user/profile.py",
                        "src/user/settings.py",
                        "tests/test_user.py",
                    ],
                },
            ],
        },
        "by_risk": {
            "description": "Group files by risk level",
            "input_changes": [
                {"file": "config/production.json", "risk": 0.95},
                {"file": "src/core/auth.py", "risk": 0.8},
                {"file": "src/utils/helper.py", "risk": 0.3},
                {"file": "tests/test_helper.py", "risk": 0.1},
                {"file": "docs/readme.md", "risk": 0.05},
            ],
            "expected_groups": [
                {"name": "Critical risk changes", "files": ["config/production.json"]},
                {"name": "High risk changes", "files": ["src/core/auth.py"]},
                {
                    "name": "Low risk changes",
                    "files": [
                        "src/utils/helper.py",
                        "tests/test_helper.py",
                        "docs/readme.md",
                    ],
                },
            ],
        },
        "by_size": {
            "description": "Group files to balance PR sizes",
            "input_changes": [
                {"file": "src/large_file.py", "size": 500},
                {"file": "src/medium1.py", "size": 150},
                {"file": "src/medium2.py", "size": 120},
                {"file": "src/small1.py", "size": 30},
                {"file": "src/small2.py", "size": 25},
                {"file": "src/small3.py", "size": 20},
            ],
            "expected_groups": [
                {
                    "name": "Large changes",
                    "files": ["src/large_file.py"],
                    "total_size": 500,
                },
                {
                    "name": "Medium changes",
                    "files": ["src/medium1.py", "src/medium2.py"],
                    "total_size": 270,
                },
                {
                    "name": "Small changes",
                    "files": ["src/small1.py", "src/small2.py", "src/small3.py"],
                    "total_size": 75,
                },
            ],
        },
    }


@pytest.fixture
def mock_pr_template_generator():
    """Mock PR template generator."""
    generator = Mock()

    generator.generate_title.return_value = "Add user authentication system"
    generator.generate_description.return_value = """
## Summary
This PR implements a comprehensive user authentication system including:
- Login/logout functionality
- Session management
- User model updates
- Comprehensive test coverage

## Changes
- Added `src/auth/login.py` - Core login logic
- Added `src/auth/logout.py` - Logout functionality
- Modified `src/models/user.py` - User model enhancements
- Added `tests/test_auth.py` - Authentication tests

## Testing
- All existing tests pass
- New authentication tests added
- Manual testing completed

## Risk Assessment
- Medium risk due to new authentication logic
- Comprehensive test coverage mitigates risk
- No breaking changes to existing API
    """.strip()

    generator.suggest_labels.return_value = ["feature", "authentication", "backend"]
    generator.suggest_reviewers.return_value = ["backend-team", "security-reviewer"]

    return generator


@pytest.fixture
def recommendation_validation_rules():
    """Provide validation rules for PR recommendations."""
    return {
        "max_files_per_pr": 15,
        "min_files_per_pr": 1,
        "max_total_changes": 1000,
        "required_fields": ["title", "description", "files", "estimated_size"],
        "valid_sizes": ["small", "medium", "large"],
        "valid_priorities": ["low", "medium", "high", "critical"],
        "valid_risk_levels": ["low", "medium", "high", "critical"],
        "file_patterns": {
            "must_include_tests": True,
            "config_files_separate": True,
            "documentation_with_features": False,
        },
    }


@pytest.fixture
def pr_recommender_integration_data():
    """Integration test data combining analyzer output with recommender input."""
    return {
        "analyzer_output": {
            "status": "success",
            "changes": create_file_changes(count=8),
            "risk_assessment": {
                "overall_risk": 0.6,
                "high_risk_files": ["config/database.json"],
            },
            "summary": {
                "total_files": 8,
                "categories": ["authentication", "models", "configuration", "testing"],
            },
        },
        "expected_recommendations": [
            {
                "id": "pr_001",
                "title": "Add user authentication system",
                "description": "Implement comprehensive user authentication with login, logout, and session management.",
                "files": [
                    "src/auth/login.py",
                    "src/auth/logout.py",
                    "src/auth/session.py",
                    "tests/test_auth.py",
                ],
                "estimated_size": "large",
                "priority": "high",
                "risk_level": "medium",
                "confidence": 0.92,
                "labels": ["feature", "authentication", "security"],
                "reviewers": ["senior-dev", "security-team"],
                "estimated_review_time": "2-3 hours",
            },
            {
                "id": "pr_002",
                "title": "Update user and profile models",
                "description": "Enhance user model with new fields and improve profile management.",
                "files": [
                    "src/models/user.py",
                    "src/models/profile.py",
                    "tests/test_user_model.py",
                    "migrations/0002_user_updates.py",
                ],
                "estimated_size": "medium",
                "priority": "medium",
                "risk_level": "low",
                "confidence": 0.88,
                "labels": ["enhancement", "models"],
                "reviewers": ["backend-team"],
                "estimated_review_time": "1-2 hours",
            },
            {
                "id": "pr_003",
                "title": "Critical configuration updates",
                "description": "Update database and authentication configuration for production deployment.",
                "files": [
                    "config/database.json",
                    "config/auth.yaml",
                    "docs/deployment.md",
                ],
                "estimated_size": "small",
                "priority": "critical",
                "risk_level": "high",
                "confidence": 0.95,
                "labels": ["config", "deployment", "critical"],
                "reviewers": ["devops-team", "senior-dev"],
                "estimated_review_time": "30-60 minutes",
            },
        ],
        "validation_results": {
            "all_valid": True,
            "warnings": ["Large changeset detected"],
            "errors": [],
        },
    }


@pytest.fixture
def mock_analyzer_client():
    """Mock analyzer client for testing integration."""
    client = Mock()

    # Mock analyzer responses
    client.analyze_repository.return_value = {
        "status": "success",
        "timestamp": datetime.now(),
        "changes": {
            "modified": ["src/auth.py", "src/user.py"],
            "untracked": ["src/new_feature.py"],
            "staged": ["tests/test_auth.py"],
        },
        "risk_assessment": {"overall_risk": 0.5, "high_risk_files": ["src/auth.py"]},
        "file_analysis": [
            {
                "file_path": "src/auth.py",
                "change_type": "modified",
                "risk_score": 0.8,
                "complexity": 12,
                "semantic_category": "authentication",
            },
            {
                "file_path": "src/user.py",
                "change_type": "modified",
                "risk_score": 0.4,
                "complexity": 6,
                "semantic_category": "models",
            },
        ],
    }

    client.get_detailed_changes.return_value = [
        FileChangeFactory.create(
            file_path="src/auth.py", change_type="modified", risk_score=0.8
        ),
        FileChangeFactory.create(
            file_path="src/user.py", change_type="modified", risk_score=0.4
        ),
    ]

    return client


@pytest.fixture
def mock_semantic_analyzer():
    """Mock semantic analyzer for understanding file content."""
    analyzer = Mock()

    # Semantic similarity
    def mock_semantic_similarity(content1, content2):
        # Mock realistic semantic similarities
        if "auth" in content1.lower() and "auth" in content2.lower():
            return 0.9
        elif "model" in content1.lower() and "model" in content2.lower():
            return 0.85
        elif "test" in content1.lower() and "test" in content2.lower():
            return 0.7
        else:
            return 0.3

    analyzer.calculate_semantic_similarity.side_effect = mock_semantic_similarity

    # Content categorization
    analyzer.categorize_content.return_value = {
        "primary_category": "business_logic",
        "secondary_categories": ["authentication", "validation"],
        "confidence": 0.85,
        "keywords": ["login", "user", "session", "validate"],
    }

    # Impact analysis
    analyzer.analyze_impact.return_value = {
        "scope": "module",
        "affected_components": ["auth_service", "user_controller"],
        "breaking_changes": False,
        "api_changes": True,
    }

    return analyzer


@pytest.fixture
def edge_case_scenarios():
    """Edge case scenarios for testing."""
    return {
        "empty_changes": {
            "description": "No changes detected",
            "input": {"changes": [], "repository_state": "clean"},
            "expected_behavior": "return_empty_recommendations",
        },
        "single_file": {
            "description": "Only one file changed",
            "input": {"changes": [FileChangeFactory.create()]},
            "expected_behavior": "single_recommendation",
        },
        "too_many_files": {
            "description": "More files than max PR limit",
            "input": {"changes": [FileChangeFactory.create() for _ in range(50)]},
            "expected_behavior": "split_into_multiple_prs",
        },
        "all_high_risk": {
            "description": "All files are high risk",
            "input": {
                "changes": [FileChangeFactory.create(risk_score=0.9) for _ in range(5)]
            },
            "expected_behavior": "recommend_small_prs",
        },
        "no_tests": {
            "description": "Changes without any test files",
            "input": {
                "changes": [
                    FileChangeFactory.create(file_path="src/feature.py"),
                    FileChangeFactory.create(file_path="src/utils.py"),
                ]
            },
            "expected_behavior": "flag_missing_tests",
        },
        "only_config": {
            "description": "Only configuration files changed",
            "input": {
                "changes": [
                    FileChangeFactory.create(
                        file_path="config/production.json", risk_score=0.95
                    ),
                    FileChangeFactory.create(
                        file_path="config/staging.json", risk_score=0.9
                    ),
                ]
            },
            "expected_behavior": "separate_config_pr",
        },
    }


@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing."""
    return {
        "large_changeset": {
            "file_count": 100,
            "changes": [
                FileChangeFactory.create(file_path=f"src/module_{i:03d}.py")
                for i in range(100)
            ],
        },
        "complex_dependencies": {
            "file_count": 20,
            "changes": [
                FileChangeFactory.create(file_path=f"src/interconnected_{i}.py")
                for i in range(20)
            ],
            "dependency_matrix": {
                # Mock complex dependency relationships
                f"src/interconnected_{i}.py": [
                    f"src/interconnected_{j}.py"
                    for j in range(max(0, i - 3), min(20, i + 3))
                    if j != i
                ]
                for i in range(20)
            },
        },
    }


@pytest.fixture
def integration_test_workflows():
    """Complete workflow scenarios for integration testing."""
    return {
        "full_feature_workflow": {
            "description": "Complete feature development workflow",
            "steps": [
                {
                    "step": "analyze_changes",
                    "input": {"repo_path": "/test/repo"},
                    "expected_output": "successful_analysis",
                },
                {
                    "step": "group_files",
                    "input": "analysis_result",
                    "expected_output": "file_groups",
                },
                {
                    "step": "generate_recommendations",
                    "input": "file_groups",
                    "expected_output": "pr_recommendations",
                },
                {
                    "step": "validate_recommendations",
                    "input": "pr_recommendations",
                    "expected_output": "validation_results",
                },
            ],
        },
        "error_recovery_workflow": {
            "description": "Workflow with error scenarios",
            "steps": [
                {
                    "step": "analyze_changes",
                    "input": {"repo_path": "/invalid/path"},
                    "expected_output": "error_response",
                },
                {
                    "step": "fallback_analysis",
                    "input": "error_response",
                    "expected_output": "fallback_recommendations",
                },
            ],
        },
    }


# Utility functions for PR recommender testing
def create_test_file_group(
    name: str, files: list[str], **kwargs: Any
) -> dict[str, Any]:
    """Create a test file group."""
    defaults: dict[str, Any] = {
        "group_id": name.lower().replace(" ", "_"),
        "name": name,
        "files": files,
        "cohesion_score": 0.8,
        "estimated_size": "medium",
        "risk_level": "medium",
        "description": f"{name} related changes",
    }
    defaults.update(kwargs)
    return defaults


def create_recommendation_test_case(
    title: str, files: list[str], **kwargs: Any
) -> dict[str, Any]:
    """Create a recommendation test case."""
    defaults: dict[str, Any] = {
        "title": title,
        "files": files,
        "estimated_size": "medium",
        "priority": "medium",
        "risk_level": "medium",
        "confidence": 0.8,
        "description": f"Implements {title.lower()}",
        "labels": ["feature"],
    }
    defaults.update(kwargs)
    return defaults


def assert_recommendation_valid(recommendation: dict[str, Any], rules: dict[str, Any]):
    """Assert that a recommendation meets validation rules."""
    # Check required fields
    for field in rules.get("required_fields", []):
        assert field in recommendation, f"Missing required field: {field}"

    # Check file count limits
    file_count = len(recommendation.get("files", []))
    assert file_count >= rules.get(
        "min_files_per_pr", 1
    ), f"Too few files: {file_count}"
    assert file_count <= rules.get(
        "max_files_per_pr", 100
    ), f"Too many files: {file_count}"

    # Check valid enum values
    if "estimated_size" in recommendation:
        valid_sizes = rules.get("valid_sizes", [])
        if valid_sizes:
            assert (
                recommendation["estimated_size"] in valid_sizes
            ), f"Invalid size: {recommendation['estimated_size']}"

    if "priority" in recommendation:
        valid_priorities = rules.get("valid_priorities", [])
        if valid_priorities:
            assert (
                recommendation["priority"] in valid_priorities
            ), f"Invalid priority: {recommendation['priority']}"


@pytest.fixture
def recommendation_validator():
    """Provide validator function for recommendations."""
    return assert_recommendation_valid


@pytest.fixture
def file_group_factory():
    """Create factory function for creating file groups."""
    return create_test_file_group


@pytest.fixture
def recommendation_factory():
    """Create factory function for creating recommendation test cases."""
    return create_recommendation_test_case


# Make all fixtures available for import
__all__ = [
    # Configuration fixtures
    "pr_recommender_config",
    # Service mocks
    "mock_pr_grouper",
    "mock_recommendation_engine",
    "mock_file_similarity_analyzer",
    "mock_pr_template_generator",
    "mock_analyzer_client",
    "mock_semantic_analyzer",
    # Test data fixtures
    "sample_change_analysis",
    "expected_pr_recommendations",
    "grouping_test_scenarios",
    "recommendation_validation_rules",
    "pr_recommender_integration_data",
    "edge_case_scenarios",
    "performance_test_data",
    "integration_test_workflows",
    # Utility fixtures
    "recommendation_validator",
    "file_group_factory",
    "recommendation_factory",
]

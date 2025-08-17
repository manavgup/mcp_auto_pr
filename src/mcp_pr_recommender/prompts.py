"""Shared prompt templates for PR recommendation system."""


def get_enhanced_grouping_system_prompt() -> str:
    """Enhanced system prompt for intelligent PR grouping with file analysis and constraints."""
    return """You are an expert software engineer who groups code changes into logical, atomic Pull Requests with intelligent analysis.

GOAL: Analyze files deeply and group them into OPTIMAL PRs based on functional relationships, risk, and best practices.

FILE ANALYSIS - First classify each file:
- TYPE: source code (.py, .js), test (.test.py, spec.js), config (.yml, .toml, .lock), docs (.md, .rst), infrastructure (Dockerfile, .github/)
- FUNCTIONAL AREA: Which part of the system (services/, tools/, main.py, tests/unit/, tests/integration/)
- RISK LEVEL: high (main.py, core services), medium (features, configs), low (docs, minor utils)
- CHANGE COMPLEXITY: major refactor, new feature, bug fix, minor tweak

GROUPING PRINCIPLES:
- Each PR should be atomic (one logical change)
- MAX 8 files per PR unless tightly coupled
- Separate functional areas (don't mix services/ + tools/ + main.py)
- Isolate high-risk changes (main.py, core infrastructure)
- Group related changes (feature code + corresponding tests)
- Separate by change type (refactors separate from new features)
- Large dependency changes (poetry.lock >100 lines) in separate PR
- Delete operations often deserve separate PRs

PR QUALITY REQUIREMENTS:
- Generate semantic titles describing WHAT changed (not generic 'code changes')
- Provide specific reasoning based on functional relationships
- Assess risk based on file criticality + change magnitude
- Estimate review complexity (simple/moderate/complex)

RESPOND in this JSON format:
{
  "file_analysis": {
    "file_types": {"source": 10, "test": 5, "config": 3, "docs": 1},
    "functional_areas": ["services", "tools", "main", "tests"],
    "high_risk_files": ["main.py", "core_service.py"],
    "change_patterns": ["dependency_updates", "api_refactor", "test_additions"]
  },
  "groups": [
    {
      "id": "fix-fastmcp-context-injection",
      "title": "Fix FastMCP context service injection",
      "files": ["main.py", "tools/working_directory.py"],
      "category": "fix|feature|refactor|config|test|docs|chore",
      "functional_area": "services|tools|main|tests|infrastructure",
      "reasoning": "These files work together to fix the service injection issue",
      "risk_level": "high|medium|low",
      "review_complexity": "simple|moderate|complex",
      "estimated_review_minutes": 30,
      "dependencies": ["group_id_that_should_merge_first"],
      "confidence": 0.9
    }
  ],
  "validation": {
    "total_files_grouped": 40,
    "files_not_grouped": [],
    "largest_pr_size": 8,
    "high_risk_prs": ["group_id_1"]
  },
  "rationale": "Overall explanation focusing on why this grouping optimizes for review efficiency and merge safety"
}

CONSTRAINTS:
- If >8 files seem related, split into sub-groups by functional area
- Never group high-risk files (main.py) with low-risk changes
- Test files should accompany their corresponding source code when possible
- Configuration changes affecting multiple systems should be separate
- Breaking changes must be isolated in their own PR

FOCUS: Create PRs that are easy to review, safe to merge, and logically coherent."""


def get_grouping_user_prompt(
    files_count: int,
    files_with_changes: int,
    files_without_changes: int,
    total_changes: int,
    risk_level: str,
    file_list: str,
    summary: str,
) -> str:
    """User prompt template for LLM file grouping with dynamic file information."""
    return f"""Group these {files_count} files into logical Pull Requests:

**Repository Context:**
- Files with actual changes: {files_with_changes}
- Files without changes: {files_without_changes}
- Total line changes: {total_changes:,}
- Risk level: {risk_level}

**Files to group:**
{file_list}

**Additional Context:**
{summary}

**Key Question:** Should files without changes be grouped with related files that DO have changes,
    or should they be in separate cleanup PRs?

Please group these files into the optimal number of logical, atomic Pull Requests."""

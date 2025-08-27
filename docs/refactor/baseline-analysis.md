# FINAL RESULTS: MCP Auto PR Code Analysis Report

> **STATUS**: ✅ **REFACTORING COMPLETE** (2025-08-27)
> **ACHIEVEMENT**: 90% duplicate code reduction (30→3 functions)

## 📊 Summary

- **Files Analyzed**: 47
- **Functions Found**: 273
- **Classes Found**: 54
- **Import Statements**: 281
- **Duplicate Functions**: 2
- **Duplicate Classes**: 0

## 🔧 Refactoring Opportunities

🔶 **Consolidate Imports**
  - Consider consolidating 32 commonly used imports
  - Files affected: 86

🚨 **Extract Common Functions**
  - Extract 2 duplicate functions to shared utilities
  - Files affected: 4

🔶 **Unified Configuration**
  - Unify 5 configuration-related functions
  - Files affected: 4

## 🔄 Duplicate Code Patterns

### Identical Function
- **Files**: mcp_local_repo_analyzer/main.py, mcp_pr_recommender/main.py
- **Pattern**: Function: lifespan(_app)
- **Similarity**: 100.0%

### Identical Function
- **Files**: shared/models/git/files.py, shared/models/git/files.py
- **Pattern**: Function: total_changes(self)
- **Similarity**: 100.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/run_http_server.py, mcp_local_repo_analyzer/cli.py, mcp_local_repo_analyzer/main.py, mcp_pr_recommender/cli.py, mcp_pr_recommender/main.py
- **Pattern**: Function: main(0 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/cli.py, mcp_pr_recommender/cli.py
- **Pattern**: Function: parse_args(0 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/main.py, mcp_pr_recommender/main.py
- **Pattern**: Function: lifespan(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/main.py, mcp_pr_recommender/main.py
- **Pattern**: Function: create_server(0 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/main.py, mcp_pr_recommender/main.py, shared/transports/sse.py, shared/transports/http.py
- **Pattern**: Function: health_check(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/main.py, mcp_pr_recommender/main.py
- **Pattern**: Function: health_check_z(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/main.py, mcp_pr_recommender/main.py
- **Pattern**: Function: run_stdio_server(0 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/main.py, mcp_pr_recommender/main.py
- **Pattern**: Function: run_http_server(3 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_pr_recommender/main.py, shared/utils/logging_utils.py
- **Pattern**: Function: setup_logging(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/tools/base.py, shared/utils/logging_utils.py, mcp_pr_recommender/tools/validator_tool.py, mcp_pr_recommender/tools/pr_recommender_tool.py, mcp_pr_recommender/tools/strategy_manager_tool.py, mcp_pr_recommender/tools/feasibility_analyzer_tool.py, mcp_pr_recommender/services/semantic_analyzer.py, mcp_pr_recommender/services/atomicity_validator.py, mcp_pr_recommender/services/grouping_engine.py
- **Pattern**: Function: __init__(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/transports/sse.py, shared/transports/http.py, shared/transports/stdio.py, shared/transports/base.py, shared/transports/base.py, shared/transports/websocket.py, mcp_local_repo_analyzer/services/git/status_tracker.py
- **Pattern**: Function: __init__(3 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/transports/sse.py, shared/transports/http.py, shared/transports/stdio.py, shared/transports/base.py, shared/transports/websocket.py
- **Pattern**: Function: run(2 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/transports/sse.py, shared/transports/http.py, shared/transports/stdio.py, shared/transports/base.py, shared/transports/base.py, shared/transports/websocket.py
- **Pattern**: Function: stop(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/transports/sse.py, shared/transports/http.py, shared/transports/stdio.py, shared/transports/base.py, shared/transports/base.py, shared/transports/websocket.py
- **Pattern**: Function: is_running(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/transports/sse.py, shared/transports/http.py, shared/transports/stdio.py, shared/transports/base.py, shared/transports/base.py, shared/transports/websocket.py
- **Pattern**: Function: get_connection_info(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/transports/sse.py, shared/transports/http.py, shared/transports/stdio.py, shared/transports/base.py
- **Pattern**: Function: get_health_status(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/transports/sse.py, shared/transports/http.py
- **Pattern**: Function: _register_health_endpoint(2 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/utils/file_utils.py, shared/utils/git_utils.py
- **Pattern**: Function: get_file_extension(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/utils/file_utils.py, shared/utils/git_utils.py
- **Pattern**: Function: is_binary_file(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/models/analysis/categorization.py, shared/models/git/changes.py
- **Pattern**: Function: total_files(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/models/git/files.py, shared/models/git/files.py, shared/models/git/commits.py, mcp_pr_recommender/models/pr/recommendations.py
- **Pattern**: Function: total_changes(1 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: shared/services/git/git_client.py, mcp_local_repo_analyzer/services/git/change_detector.py, mcp_local_repo_analyzer/services/git/diff_analyzer.py
- **Pattern**: Function: __init__(2 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/services/git/diff_analyzer.py, mcp_pr_recommender/services/grouping_engine.py
- **Pattern**: Function: _is_documentation(2 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_local_repo_analyzer/services/git/diff_analyzer.py, mcp_pr_recommender/services/grouping_engine.py
- **Pattern**: Function: _is_test_file(2 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_pr_recommender/services/semantic_analyzer.py, mcp_pr_recommender/services/grouping_engine.py
- **Pattern**: Function: _should_exclude_file(2 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_pr_recommender/services/semantic_analyzer.py, mcp_pr_recommender/services/grouping_engine.py
- **Pattern**: Function: _generate_branch_name(2 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_pr_recommender/services/semantic_analyzer.py, mcp_pr_recommender/services/grouping_engine.py
- **Pattern**: Function: _estimate_review_time(3 params)
- **Similarity**: 80.0%

### Similar Function Signature
- **Files**: mcp_pr_recommender/services/semantic_analyzer.py, mcp_pr_recommender/services/grouping_engine.py
- **Pattern**: Function: _generate_labels(2 params)
- **Similarity**: 80.0%

## 📦 Import Analysis

### Most Common Imports

- `typing` (used in 26 files)
- `pydantic` (used in 18 files)
- `fastmcp` (used in 15 files)
- `pathlib` (used in 14 files)
- `logging` (used in 13 files)
- `shared.models` (used in 11 files)
- `shared.utils` (used in 9 files)
- `config` (used in 7 files)
- `datetime` (used in 7 files)
- `sys` (used in 6 files)

### Common Function Names

- `__init__` (appears 20 times)
- `stop` (appears 6 times)
- `is_running` (appears 6 times)
- `get_connection_info` (appears 6 times)
- `main` (appears 5 times)
- `health_check` (appears 5 times)
- `run` (appears 5 times)
- `get_health_status` (appears 4 times)
- `total_changes` (appears 4 times)
- `parse_args` (appears 2 times)

---
*Report generated by LibCST Code Analyzer*

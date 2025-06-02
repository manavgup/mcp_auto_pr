# TASK.md

## Purpose
This document outlines current tasks, backlog items, sub-tasks, and provides a framework for progress tracking for the modular MCP servers solution.

## Active Work Items and Progress

### mcp_shared_lib (Shared Library)
*   **Progress:** This library appears to be well-structured with foundational components.
    *   **Models:** `analysis_models.py`, `base_models.py`, `batching_models.py`, `directory_models.py`, `git_models.py`, `grouping_models.py`, `pr_suggestion_models.py`, `tool_models.py`, `utility_models.py` are defined, suggesting a comprehensive data structure for the entire system.
    *   **Tools:** `git_operations.py`, `directory_analyzer_tool.py`, `file_grouper_tool.py`, `batch_processor_tool.py`, `batch_splitter_tool.py`, `group_merging_tool.py`, `group_refiner_tool.py`, `group_validator_tool.py`, `grouping_strategy_selector_tool.py` are present, indicating that core functionalities for Git interaction, directory analysis, and file grouping/processing are being developed as reusable tools.
    *   **Utilities:** `file_utils.py`, `git_utils.py`, `logging_utils.py` are in place, providing common helper functions.
    *   **State/Telemetry/Error Handling:** `state/manager.py`, `telemetry/monitor.py`, `error/handler.py` suggest robust system management and observability features are being built.
*   **Outstanding Tasks:**
    *   Ensure all defined models are fully implemented and validated.
    *   Complete the implementation and testing of all shared tools.
    *   Verify cross-server compatibility and reusability of shared components.

### mcp_change_analyzer (Change Analysis Server)
*   **Progress:** This server is focused on identifying outstanding changes.
    *   **Services:** `analysis_service.py` and `git_service.py` are present, indicating the core logic for analyzing changes and interacting with Git is being developed.
    *   **Tools:** `directory_analyzer.py`, `metrics_collector.py`, `repo_analyzer.py` suggest specific tools for detailed analysis are in progress.
    *   **Server Setup:** `src/server.py` and `config/server.yaml` are present, indicating the FastMCP server structure is initiated.
*   **Outstanding Tasks:**
    *   Implement the full logic for identifying all types of outstanding changes (staged, unstaged, untracked).
    *   Integrate `git_operations` from `mcp_shared_lib` for robust Git interactions.
    *   Develop comprehensive metrics collection for change analysis.
    *   Ensure the server can expose tools for external consumption (e.g., by `mcp_pr_recommender`).
    *   Implement error handling and logging specific to change analysis.

### mcp_pr_recommender (PR Recommendation Server)
*   **Progress:** This server is geared towards generating PR suggestions.
    *   **Services:** `grouping_service.py` and `validation_service.py` are present, suggesting work on grouping related changes and validating them for PRs.
    *   **Tools:** `batch_processor_tool.py`, `batch_splitter_tool.py`, `file_grouper_tool.py`, `group_validator_tool.py` are present, indicating the use of shared tools for processing and validating file groups.
    *   **Models:** `agent_models.py`, `batching_models.py`, `recommender_models.py` are defined, suggesting specific models for recommendation logic.
    *   **Server Setup:** `src/server.py` and `config/server.yaml` are present, indicating the FastMCP server structure is initiated.
*   **Outstanding Tasks:**
    *   Develop the core recommendation engine logic, leveraging analysis from `mcp_change_analyzer`.
    *   Refine grouping strategies to create coherent PR suggestions.
    *   Implement validation rules for PR content.
    *   Ensure the server can consume analysis data from `mcp_change_analyzer`.
    *   Develop mechanisms for generating actionable PR descriptions and content.

## Milestones and Deadlines (Proposed)

*   **Phase 1: Core Analysis & Shared Library (Target: Q3 2025)**
    *   Complete `mcp_shared_lib` core models, utilities, and base tools.
    *   Implement `mcp_change_analyzer` to accurately identify and report outstanding changes.
    *   Establish basic communication between `mcp_change_analyzer` and `mcp_shared_lib`.
    *   Initial unit tests for both projects.
*   **Phase 2: PR Recommendation & Integration (Target: Q4 2025)**
    *   Implement `mcp_pr_recommender` with initial recommendation logic.
    *   Integrate `mcp_change_analyzer` and `mcp_pr_recommender` for end-to-end flow.
    *   Develop comprehensive integration tests.
    *   Basic documentation for server setup and usage.
*   **Phase 3: Refinement & Advanced Features (Target: Q1 2026)**
    *   Enhance recommendation intelligence (e.g., context-aware suggestions).
    *   Improve error handling, logging, and telemetry across all servers.
    *   Performance optimization.
    *   Comprehensive documentation and examples.

## Discovered Tasks During Development

*   **Inter-server Communication Protocol:** Define and implement a clear communication protocol between `mcp_change_analyzer` and `mcp_pr_recommender` (e.g., via MCP tool calls, shared data structures).
*   **FastMCP Server Configuration:** Ensure `server.py` and `config/server.yaml` in both `mcp_change_analyzer` and `mcp_pr_recommender` are fully configured to expose the necessary tools and resources.
*   **Comprehensive Testing:** Develop a robust testing strategy including unit, integration, and end-to-end tests for the entire solution.
*   **Deployment Strategy:** Plan for how these modular servers will be deployed and managed in a production environment (e.g., Docker containers, Kubernetes).
*   **User Interface/Integration:** Consider how developers will interact with these servers (e.g., VSCode extension, CLI tool).
*   **VSCode Multi-root Workspace Repository:**
    *   **Recommendation:** Yes, it is highly recommended to create a separate GitHub repository for the VSCode multi-root workspace configuration itself.
    *   **Rationale:** This repository would contain the `.vscode/` directory with `settings.json`, `launch.json`, `tasks.json`, and importantly, `*.code-workspace` files. This allows for version control of the workspace setup, making it easy for other developers to clone the repository and immediately have the correct multi-root workspace configuration, including paths to the `mcp_shared_lib`, `mcp_change_analyzer`, and `mcp_pr_recommender` repositories. It centralizes the development environment setup.
    *   **Action:** Create a new repository (e.g., `mcp_repo_analysis_workspace`) and commit the `.vscode/` directory and `.code-workspace` file(s) there.

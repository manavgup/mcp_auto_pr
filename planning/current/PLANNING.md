# PLANNING.md

## Purpose
This document defines the epic, user stories, and acceptance criteria for the modular MCP servers solution for GitHub repo analysis and PR recommendation.

## Project Scope and Objectives

### Epic
Modular MCP Servers for GitHub Repo Analysis and PR Recommendation

### Project Objectives
*   To develop a modular solution using FastMCP servers for analyzing outstanding changes in a local GitHub repository.
*   To generate intelligent Pull Request (PR) recommendations based on the analyzed changes.
*   To establish a shared library (`mcp_shared_lib`) for common functionalities across all MCP servers.
*   To ensure the solution is easily deployable and manageable within a multi-root VSCode workspace.

### User Stories
*   **As a developer,** I want to analyze outstanding changes in my local repository so I can understand what modifications have not yet been committed to source control.
*   **As a developer,** I want to receive intelligent recommendations for Pull Requests based on my outstanding changes so I can streamline the PR creation process and ensure comprehensive changes are included.
*   **As a system administrator,** I want to easily integrate and manage modular MCP servers for code analysis and PR recommendation within my development environment.
*   **As a system administrator,** I want the MCP servers to be built on a robust and scalable framework (FastMCP).

### Acceptance Criteria
*   The `mcp_change_analyzer` server successfully identifies and reports uncommitted changes (e.g., new files, modified files, deleted files) in a specified Git repository.
*   The `mcp_pr_recommender` server generates relevant and actionable PR suggestions based on the analysis provided by `mcp_change_analyzer` and other contextual information.
*   The `mcp_shared_lib` effectively provides common models, utilities, and base tool functionalities that are utilized by both `mcp_change_analyzer` and `mcp_pr_recommender`.
*   All MCP servers are implemented using the FastMCP framework and adhere to its best practices.
*   The solution can be run and tested within the existing multi-root VSCode workspace.

## Detailed Implementation Plan

### Phase 1: Refactor `mcp_change_analyzer` to use `FastMCP`

1.  **Modify `src/server.py`:**
    *   Import `FastMCP` and the `mcp.tool` decorator from `fastmcp`.
    *   Replace the `FastAPI` app instantiation with `FastMCP` server instantiation.
    *   Migrate existing tools (e.g., `directory_analyzer`, `repo_analyzer`, `metrics_collector`) to be registered with the `FastMCP` server using the `@mcp.tool()` decorator. This will involve importing the tool classes and decorating their `execute` methods or the classes themselves if they are callable.
    *   Remove the manual FastAPI routes for `/tools` and `/tools/{tool_name}` as `FastMCP` handles tool exposure automatically.
    *   Adjust the `if __name__ == "__main__":` block to run the `FastMCP` server.
    *   Integrate `Telemetry` and `StateManager` with `FastMCP`'s lifecycle hooks (e.g., using the `lifespan` argument in the `FastMCP` constructor) or adapt them to work within the `FastMCP` context.
    *   Review and adapt error handling and CORS middleware to `FastMCP`'s structure, as `FastMCP` is built on FastAPI and should largely be compatible.

2.  **Review and update tool implementations:**
    *   Ensure that the `execute` methods of the tools (`directory_analyzer`, `repo_analyzer`, `metrics_collector`) are compatible with how `FastMCP` expects tools to be defined, particularly regarding type hints for argument validation.

### Phase 2: Testing the FastMCP-based server

1.  **Unit Tests:**
    *   Ensure existing unit tests for individual tools still pass after the refactoring.
    *   Add new unit tests for the `FastMCP` server's startup and shutdown logic if custom lifespan functions are implemented.

2.  **Integration Tests (MCP Client Interaction):**
    *   Create a new test file (e.g., `tests/integration/test_fastmcp_server.py`).
    *   Use `pytest` with `httpx` (already a dependency in `pyproject.toml`) to send HTTP requests to the running `FastMCP` server.
    *   Test the `/health` endpoint to confirm the server is running.
    *   Test the `/tools` endpoint (provided by `FastMCP`) to verify that all expected tools are listed with their correct schemas.
    *   Test the execution of each tool (e.g., `directory_analyzer`, `repo_analyzer`, `metrics_collector`) by sending POST requests to the `FastMCP`'s tool execution endpoint (typically `/tools/{tool_name}`).
    *   Verify the responses, including the `result` and `metadata`.
    *   Consider using `pytest-asyncio` for asynchronous tests if the tool execution involves `await` calls.

## Technology Decisions

*   **Framework:** FastMCP (Python-based) for building modular servers.
*   **Programming Language:** Python (evident from `pyproject.toml`, `poetry.lock`, and `.py` files).
*   **Version Control:** Git/GitHub for repository operations and analysis.
*   **Shared Library:** `mcp_shared_lib` for common data models, utility functions, and base classes for tools and services.
*   **Dependency Management:** Poetry (indicated by `poetry.lock` and `pyproject.toml`).

## Architecture Patterns and Constraints

### Architecture Patterns
*   **Modular Microservices:** Each core functionality (change analysis, PR recommendation) is encapsulated within its own independent MCP server, promoting loose coupling and scalability.
*   **Shared Library:** A dedicated shared library (`mcp_shared_lib`) acts as a central repository for common code, ensuring consistency and reducing redundancy across servers.
*   **API-driven Communication:** MCP servers will expose well-defined APIs for inter-server communication and external integration.
*   **Event-Driven (Potential):** Consider an event-driven approach for triggering analysis or recommendations based on file system changes or Git events.

### Constraints
*   **Existing Workspace:** The solution must integrate seamlessly into the current VSCode multi-root workspace.
*   **Outstanding Changes Focus:** The primary analysis focus is on changes not yet committed to source control.
*   **FastMCP Adherence:** All servers must strictly follow the FastMCP server architecture and conventions.
*   **Python Ecosystem:** Development must remain within the Python ecosystem, leveraging existing libraries and tools.

## Security Requirements and Standards

*   **Least Privilege:** MCP servers should operate with the minimum necessary permissions to perform their functions.
*   **Secure Configuration:** Configuration files (e.g., `server.yaml`) must be handled securely, avoiding hardcoded sensitive information.
*   **Input Validation:** All inputs to server APIs and tools must be rigorously validated to prevent injection attacks or unexpected behavior.
*   **Dependency Security:** Regularly audit and update third-party dependencies to mitigate known vulnerabilities.
*   **Data Handling:** Sensitive repository data (if any) should be handled and stored securely, potentially with encryption.
*   **Authentication/Authorization (Future Consideration):** For production deployments, implement robust authentication and authorization mechanisms for server access.

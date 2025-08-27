#!/usr/bin/env python3
"""Local Repository Analyzer entry point."""

from mcp_local_repo_analyzer.server import LocalRepoAnalyzerServer


def main() -> None:
    """Run the Local Repository Analyzer."""
    server = LocalRepoAnalyzerServer()
    server.main()


if __name__ == "__main__":
    main()

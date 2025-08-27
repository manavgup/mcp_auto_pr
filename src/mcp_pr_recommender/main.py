#!/usr/bin/env python3
"""PR Recommender entry point."""

from mcp_pr_recommender.server import PRRecommenderServer


def main() -> None:
    """Run the PR Recommender."""
    server = PRRecommenderServer()
    server.main()


if __name__ == "__main__":
    main()

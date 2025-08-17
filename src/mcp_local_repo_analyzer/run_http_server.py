#!/usr/bin/env python3
"""HTTP Server Runner for Git Analyzer.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Author: Manav Gupta <manavg@gmail.com>

Run the git analyzer as an HTTP server for testing purposes.
"""

import sys
from pathlib import Path

from mcp_local_repo_analyzer.main import create_server, register_tools

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Run server in HTTP mode."""
    # Create and configure server
    server, services = create_server()
    register_tools(server, services)

    # Run in HTTP mode
    print("🚀 Starting HTTP server on http://localhost:8000/mcp")
    server.run(transport="streamable-http", host="localhost", port=8000)


if __name__ == "__main__":
    main()

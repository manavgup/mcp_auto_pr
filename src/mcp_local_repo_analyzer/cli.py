#!/usr/bin/env python3
"""CLI module for mcp_local_repo_analyzer - simplified to match main.py pattern."""

import argparse
import logging
import sys

from mcp_local_repo_analyzer.main import main as run_main
from shared.utils import logging_service

logger = logging_service.get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Local Repository Analyzer Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport protocol to use",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (HTTP mode only)"
    )
    parser.add_argument(
        "--port", type=int, default=9070, help="Port to bind to (HTTP mode only)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    parser.add_argument(
        "--work-dir", help="Default working directory for Git operations"
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point - delegates to main.py with CLI arguments."""
    args = parse_args()

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Convert CLI args to sys.argv format that main.py expects
    old_argv = sys.argv[:]

    try:
        # Build argv for main.py
        sys.argv = ["main.py"]
        sys.argv.extend(["--transport", args.transport])
        sys.argv.extend(["--host", args.host])
        sys.argv.extend(["--port", str(args.port)])
        sys.argv.extend(["--log-level", args.log_level])
        if args.work_dir:
            sys.argv.extend(["--work-dir", args.work_dir])

        # Call main.py's main function directly
        logger.info("Delegating to main.py with CLI arguments")
        run_main()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        # Restore original argv
        sys.argv = old_argv


if __name__ == "__main__":
    main()

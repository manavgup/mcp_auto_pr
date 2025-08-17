#!/usr/bin/env python3
"""CLI module for mcp_pr_recommender - simplified to match main.py pattern."""
import argparse
import logging
import os
import sys

from mcp_shared_lib.utils import logging_service

from mcp_pr_recommender.main import main as run_main

logger = logging_service.get_logger(__name__)


def check_environment() -> None:
    """Check if required environment variables are set."""
    required_env = {"OPENAI_API_KEY": "OpenAI API key for LLM operations"}

    missing = []
    for var, description in required_env.items():
        if not os.getenv(var):
            missing.append(f"  {var}: {description}")

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(var)
        print("\nPlease set these variables and try again.")
        print("Example:")
        print("  export OPENAI_API_KEY=your_api_key_here")
        print("  pr-recommender")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP PR Recommender Server",
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
        "--port", type=int, default=9071, help="Port to bind to (HTTP mode only)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    return parser.parse_args()


def main() -> None:
    """CLI entry point - delegates to main.py with CLI arguments."""
    args = parse_args()

    # Check environment first
    check_environment()

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

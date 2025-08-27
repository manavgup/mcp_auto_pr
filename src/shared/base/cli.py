#!/usr/bin/env python3
"""Base CLI functionality shared across MCP servers."""

import argparse
import os
import sys
from abc import ABC, abstractmethod

from shared.utils.logging import logging_service

logger = logging_service.get_logger(__name__)


class BaseMCPCLI(ABC):
    """Base class for MCP server CLI interfaces."""

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return the service name for help text."""
        pass

    @property
    @abstractmethod
    def default_port(self) -> int:
        """Return the default port for this service."""
        pass

    @property
    def required_env_vars(self) -> dict[str, str]:
        """Return required environment variables and their descriptions."""
        return {}

    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with common options."""
        parser = argparse.ArgumentParser(
            description=f"{self.service_name} Server",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        # Transport options
        parser.add_argument(
            "--transport",
            choices=["stdio", "streamable-http", "sse"],
            default="stdio",
            help="Transport protocol to use",
        )

        # Server options
        parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (HTTP mode only)")
        parser.add_argument(
            "--port",
            type=int,
            default=self.default_port,
            help="Port to bind to (HTTP mode only)",
        )

        # Common options
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="Logging level",
        )
        parser.add_argument("--work-dir", help="Default working directory for operations")

        return parser

    def check_environment(self) -> None:
        """Check if required environment variables are set."""
        required_env = self.required_env_vars
        if not required_env:
            return

        missing = []
        for var, description in required_env.items():
            if not os.getenv(var):
                missing.append(f"  {var}: {description}")

        if missing:
            print(f"❌ Missing required environment variables for {self.service_name}:")
            for var in missing:
                print(var)
            print("\nPlease set these variables and try again.")
            print("Example:")
            for var in required_env:
                print(f"  export {var}=your_value_here")
            sys.exit(1)

    def parse_args(self, args: list[str] | None = None) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = self.create_parser()
        return parser.parse_args(args)

    def setup_logging(self, args: argparse.Namespace) -> None:
        """Configure logging for the CLI."""
        # Logging is handled by the logging service
        logger.debug(f"Logging setup called with level: {args.log_level}")

    @abstractmethod
    async def run_server(self, args: argparse.Namespace) -> None:
        """Run the server with parsed arguments."""
        pass

    async def main(self, args: list[str] | None = None) -> None:
        """Run the CLI with parsed arguments."""
        try:
            self.check_environment()
            parsed_args = self.parse_args(args)
            self.setup_logging(parsed_args)
            await self.run_server(parsed_args)
        except KeyboardInterrupt:
            logger.info(f"{self.service_name} stopped by user")
        except Exception as e:
            logger.error(f"Error running {self.service_name}: {e}")
            sys.exit(1)

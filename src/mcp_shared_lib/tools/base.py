"""Base tool functionality for FastMCP tools."""

from abc import ABC, abstractmethod
from typing import Any

from mcp_shared_lib.utils import logging_service


class BaseMCPTool(ABC):
    """Base class for MCP tools with common functionality."""

    def __init__(self) -> None:
        """Initialize the base tool with logging."""
        self.logger = logging_service.get_logger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool's main functionality."""
        pass

    def _log_execution_start(self, operation: str, **params: Any) -> None:
        """Log the start of an operation."""
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        self.logger.info(f"Starting {operation} with parameters: {param_str}")

    def _log_execution_end(
        self, operation: str, success: bool = True, **results: Any
    ) -> None:
        """Log the end of an operation."""
        status = "completed" if success else "failed"
        result_str = ", ".join(f"{k}={v}" for k, v in results.items())
        self.logger.info(f"Operation {operation} {status}: {result_str}")

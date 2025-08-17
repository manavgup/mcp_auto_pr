"""Factory classes for creating MCP tool-related test data.

This module provides factories for creating realistic tool execution results,
server configurations, client sessions, and transaction data.
"""

import random
from datetime import datetime, timedelta
from typing import Any, TypeVar

from .base import BaseFactory, Faker, SequenceMixin

T = TypeVar("T")


class MCPToolResultFactory(BaseFactory, SequenceMixin):
    """Factory for creating MCP tool execution results."""

    @classmethod
    def tool_id(cls) -> str:
        """Generate unique tool execution ID."""
        return cls.sequence("tool_exec", "tool_exec_{n:08d}")

    @staticmethod
    def tool_name() -> str:
        """Generate tool name."""
        return Faker.random_element(
            [
                "analyze_repository",
                "get_changes",
                "assess_risk",
                "check_push_readiness",
                "get_commit_history",
                "analyze_diff",
                "recommend_prs",
                "validate_changes",
                "get_file_metadata",
                "calculate_metrics",
            ]
        )

    @staticmethod
    def status() -> str:
        """Generate execution status."""
        return Faker.weighted_choice(
            ["success", "error", "timeout", "cancelled"], [85, 10, 3, 2]
        )

    @staticmethod
    def execution_time_ms() -> int:
        """Generate execution time."""
        return Faker.random_int(50, 30000)

    @staticmethod
    def timestamp() -> datetime:
        """Generate execution timestamp."""
        return Faker.date_time()

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create tool result with status-specific data."""
        result = super().create(**kwargs)

        # Add status-specific data
        if result["status"] == "success":
            result.update(cls._create_success_result(result["tool_name"]))
        elif result["status"] == "error":
            result.update(cls._create_error_result())
        elif result["status"] == "timeout":
            result.update(cls._create_timeout_result())
        elif result["status"] == "cancelled":
            result.update(cls._create_cancelled_result())

        return result

    @classmethod
    def _create_success_result(cls, tool_name: str) -> dict[str, Any]:
        """Create success result data based on tool type."""
        base_result = {
            "success": True,
            "message": f"{tool_name} completed successfully",
        }

        # Tool-specific result data
        if tool_name == "analyze_repository":
            base_result["data"] = {
                "files_analyzed": Faker.random_int(10, 200),
                "total_lines": Faker.random_int(1000, 50000),
                "risk_score": Faker.pyfloat(0.0, 1.0),
                "complexity_score": Faker.pyfloat(0.0, 1.0),
                "issues_found": Faker.random_int(0, 20),
            }
        elif tool_name == "get_changes":
            base_result["data"] = {
                "modified_files": Faker.random_int(0, 15),
                "added_files": Faker.random_int(0, 8),
                "deleted_files": Faker.random_int(0, 3),
                "total_changes": Faker.random_int(5, 25),
            }
        elif tool_name == "assess_risk":
            base_result["data"] = {
                "overall_risk": Faker.random_element(["low", "medium", "high"]),
                "risk_score": Faker.pyfloat(0.0, 1.0),
                "risk_factors": Faker.random_int(0, 8),
                "mitigation_suggestions": Faker.random_int(1, 6),
            }
        elif tool_name == "recommend_prs":
            base_result["data"] = {
                "recommendations_count": Faker.random_int(1, 10),
                "total_files_grouped": Faker.random_int(5, 50),
                "grouping_strategy": Faker.random_element(
                    ["by_feature", "by_risk", "by_type"]
                ),
                "confidence_score": Faker.pyfloat(0.6, 1.0),
            }
        else:
            # Generic success data
            base_result["data"] = {
                "items_processed": Faker.random_int(1, 100),
                "processing_time_ms": Faker.random_int(100, 5000),
            }

        return base_result

    @classmethod
    def _create_error_result(cls) -> dict[str, Any]:
        """Create error result data."""
        error_types = [
            "ValidationError",
            "FileNotFoundError",
            "GitCommandError",
            "AnalysisError",
            "NetworkError",
            "TimeoutError",
            "ConfigurationError",
        ]

        error_messages = {
            "ValidationError": "Invalid input parameters provided",
            "FileNotFoundError": "Required file or directory not found",
            "GitCommandError": "Git operation failed",
            "AnalysisError": "Analysis process encountered an error",
            "NetworkError": "Network connection failed",
            "TimeoutError": "Operation timed out",
            "ConfigurationError": "Invalid configuration detected",
        }

        error_type = Faker.random_element(error_types)

        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_messages.get(error_type, "An unknown error occurred"),
                "code": Faker.random_int(1000, 9999),
                "details": {
                    "stacktrace": f'Error in {Faker.random_element(["analyzer.py", "processor.py", "git_service.py"])} line {Faker.random_int(10, 500)}',
                    "context": f'Processing {Faker.random_element(["file", "repository", "request"])} {Faker.random_int(1, 100)}',
                },
            },
        }

    @classmethod
    def _create_timeout_result(cls) -> dict[str, Any]:
        """Create timeout result data."""
        return {
            "success": False,
            "error": {
                "type": "TimeoutError",
                "message": "Operation exceeded maximum allowed time",
                "timeout_seconds": Faker.random_int(30, 300),
                "partial_results": {
                    "completed_steps": Faker.random_int(1, 5),
                    "total_steps": Faker.random_int(6, 10),
                },
            },
        }

    @classmethod
    def _create_cancelled_result(cls) -> dict[str, Any]:
        """Create cancelled result data."""
        return {
            "success": False,
            "error": {
                "type": "OperationCancelled",
                "message": "Operation was cancelled by user or system",
                "cancellation_reason": Faker.random_element(
                    [
                        "user_request",
                        "system_shutdown",
                        "resource_limit",
                        "priority_override",
                    ]
                ),
            },
        }


class MCPServerFactory(BaseFactory):
    """Factory for creating MCP server configurations."""

    @staticmethod
    def name() -> str:
        """Generate server name."""
        return Faker.random_element(
            [
                "LocalRepoAnalyzer",
                "PRRecommender",
                "GitAnalysisServer",
                "CodeQualityChecker",
                "RepositoryInsights",
                "DevelopmentAssistant",
            ]
        )

    @staticmethod
    def version() -> str:
        """Generate server version."""
        major = Faker.random_int(1, 3)
        minor = Faker.random_int(0, 9)
        patch = Faker.random_int(0, 9)
        return f"{major}.{minor}.{patch}"

    @staticmethod
    def description() -> str:
        """Generate server description."""
        return Faker.text(max_nb_chars=150)

    @staticmethod
    def port() -> int:
        """Generate server port."""
        return Faker.random_int(8000, 9999)

    @staticmethod
    def max_concurrent_requests() -> int:
        """Generate max concurrent requests."""
        return Faker.random_int(10, 1000)

    @staticmethod
    def timeout_seconds() -> int:
        """Generate request timeout."""
        return Faker.random_int(30, 300)

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create server configuration with computed properties."""
        server = super().create(**kwargs)

        # Add computed properties
        server["health_status"] = Faker.random_element(
            ["healthy", "degraded", "unhealthy"]
        )
        server["uptime_percent"] = Faker.pyfloat(95.0, 99.9)
        server["last_restart"] = Faker.date_time()

        # Generate available tools
        tool_count = Faker.random_int(5, 20)
        server["available_tools"] = [
            MCPToolResultFactory.tool_name() for _ in range(tool_count)
        ]

        # Add performance metrics
        server["performance_metrics"] = {
            "avg_response_time_ms": Faker.random_int(50, 500),
            "requests_per_second": Faker.random_int(10, 100),
            "error_rate_percent": Faker.pyfloat(0.0, 2.0),
            "memory_usage_mb": Faker.random_int(100, 2048),
            "cpu_usage_percent": Faker.random_int(10, 80),
        }

        return server


class MCPClientFactory(BaseFactory):
    """Factory for creating MCP client configurations."""

    @staticmethod
    def client_id() -> str:
        """Generate client ID."""
        return Faker.uuid4()

    @staticmethod
    def client_name() -> str:
        """Generate client name."""
        return Faker.random_element(
            [
                "IDE Extension",
                "CLI Tool",
                "Web Dashboard",
                "CI/CD Pipeline",
                "Development Workflow",
                "Code Review Bot",
            ]
        )

    @staticmethod
    def user_agent() -> str:
        """Generate user agent string."""
        client_name = Faker.random_element(
            ["mcp-client", "repo-analyzer", "dev-assistant"]
        )
        version = f"{Faker.random_int(1, 3)}.{Faker.random_int(0, 9)}.{Faker.random_int(0, 9)}"
        return f"{client_name}/{version}"

    @staticmethod
    def connection_timeout_seconds() -> int:
        """Generate connection timeout."""
        return Faker.random_int(5, 60)

    @staticmethod
    def retry_attempts() -> int:
        """Generate retry attempts."""
        return Faker.random_int(1, 5)

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create client configuration with computed properties."""
        client = super().create(**kwargs)

        # Add computed properties
        client["connection_status"] = Faker.random_element(
            ["connected", "disconnected", "reconnecting"]
        )
        client["last_activity"] = Faker.date_time()
        client["session_duration_minutes"] = Faker.random_int(1, 480)

        # Add client capabilities
        client["capabilities"] = {
            "supports_streaming": Faker.random_element([True, False]),
            "supports_batch_operations": Faker.random_element([True, False]),
            "max_concurrent_requests": Faker.random_int(1, 10),
            "preferred_transport": Faker.random_element(["http", "websocket", "stdio"]),
        }

        # Add usage statistics
        client["usage_stats"] = {
            "total_requests": Faker.random_int(10, 10000),
            "successful_requests": Faker.random_int(8, 9500),
            "failed_requests": Faker.random_int(0, 500),
            "average_response_time_ms": Faker.random_int(100, 2000),
        }

        return client


class MCPTransactionFactory(BaseFactory, SequenceMixin):
    """Factory for creating MCP client-server transaction records."""

    @classmethod
    def transaction_id(cls) -> str:
        """Generate unique transaction ID."""
        return cls.sequence("txn", "txn_{n:010d}")

    @staticmethod
    def request_timestamp() -> datetime:
        """Generate request timestamp."""
        return Faker.date_time()

    @staticmethod
    def response_timestamp() -> datetime:
        """Generate response timestamp."""
        base_time = Faker.date_time()
        response_delay = timedelta(milliseconds=Faker.random_int(50, 5000))
        return base_time + response_delay

    @staticmethod
    def tool_name() -> str:
        """Generate tool name for transaction."""
        return MCPToolResultFactory.tool_name()

    @staticmethod
    def request_size_bytes() -> int:
        """Generate request size."""
        return Faker.random_int(100, 10240)  # 100B to 10KB

    @staticmethod
    def response_size_bytes() -> int:
        """Generate response size."""
        return Faker.random_int(500, 51200)  # 500B to 50KB

    @classmethod
    def create(cls, **kwargs: Any) -> dict[str, Any]:
        """Create transaction record with computed metrics."""
        transaction = super().create(**kwargs)

        # Calculate duration
        request_time = transaction["request_timestamp"]
        response_time = transaction["response_timestamp"]
        transaction["duration_ms"] = int(
            (response_time - request_time).total_seconds() * 1000
        )

        # Add request/response metadata
        transaction["request"] = {
            "method": "POST",
            "path": f'/tools/{transaction["tool_name"]}',
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": f"mcp-client/{Faker.random_int(1, 3)}.{Faker.random_int(0, 9)}.{Faker.random_int(0, 9)}",
                "X-Request-ID": transaction["transaction_id"],
            },
            "size_bytes": transaction["request_size_bytes"],
        }

        transaction["response"] = {
            "status_code": Faker.weighted_choice([200, 400, 500, 503], [90, 5, 3, 2]),
            "headers": {
                "Content-Type": "application/json",
                "X-Response-Time": f"{transaction['duration_ms']}ms",
                "X-Request-ID": transaction["transaction_id"],
            },
            "size_bytes": transaction["response_size_bytes"],
        }

        # Add performance metrics
        transaction["metrics"] = {
            "processing_time_ms": max(
                0, transaction["duration_ms"] - Faker.random_int(10, 100)
            ),
            "queue_time_ms": Faker.random_int(0, 50),
            "network_time_ms": Faker.random_int(10, 100),
            "cache_hit": Faker.random_element([True, False]),
            "memory_used_mb": Faker.random_int(10, 500),
        }

        return transaction


# Convenience functions for creating tool-related collections
def create_tool_execution_batch(
    tool_names: list[str] | None = None, count: int = 5, success_rate: float = 0.9
) -> list[dict[str, Any]]:
    """Create a batch of tool execution results."""
    if tool_names is None:
        tool_names = [
            "analyze_repository",
            "get_changes",
            "assess_risk",
            "recommend_prs",
        ]

    results = []
    for _ in range(count):
        # Determine status based on success rate
        if random.random() < success_rate:
            status = "success"
        else:
            status = Faker.random_element(["error", "timeout"])

        result = MCPToolResultFactory.create(
            tool_name=random.choice(tool_names), status=status
        )
        results.append(result)

    return results


def create_server_farm(server_count: int = 3) -> dict[str, Any]:
    """Create a collection of MCP servers for load balancing."""
    servers = []

    for i in range(server_count):
        server = MCPServerFactory.create(name=f"Server-{i+1:02d}", port=8000 + i)
        servers.append(server)

    return {
        "servers": servers,
        "load_balancer": {
            "strategy": Faker.random_element(
                ["round_robin", "least_connections", "weighted"]
            ),
            "health_check_enabled": True,
            "health_check_interval_seconds": 30,
            "failover_enabled": True,
            "sticky_sessions": Faker.random_element([True, False]),
        },
        "total_capacity": {
            "max_concurrent_requests": sum(
                s["max_concurrent_requests"] for s in servers
            ),
            "total_tools": len(
                {tool for s in servers for tool in s["available_tools"]}
            ),
            "average_response_time_ms": Faker.random_int(100, 1000),
        },
    }


def create_client_session_history(
    session_duration_hours: int = 8, requests_per_hour: int = 10
) -> dict[str, Any]:
    """Create a client session with request history."""
    total_requests = session_duration_hours * requests_per_hour

    # Generate transaction history
    transactions = []
    base_time = datetime.now() - timedelta(hours=session_duration_hours)

    for i in range(total_requests):
        # Spread requests across the session duration
        request_time = base_time + timedelta(
            minutes=i * (session_duration_hours * 60) / total_requests
        )

        transaction = MCPTransactionFactory.create(request_timestamp=request_time)
        transactions.append(transaction)

    # Calculate session statistics
    successful_requests = len(
        [t for t in transactions if t["response"]["status_code"] == 200]
    )
    total_bytes_transferred = sum(
        t["request"]["size_bytes"] + t["response"]["size_bytes"] for t in transactions
    )
    average_response_time = sum(t["duration_ms"] for t in transactions) / len(
        transactions
    )

    return {
        "session_info": MCPClientFactory.create(),
        "transactions": transactions,
        "statistics": {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests,
            "total_bytes_transferred": total_bytes_transferred,
            "average_response_time_ms": average_response_time,
            "session_duration_hours": session_duration_hours,
            "requests_per_hour": len(transactions) / session_duration_hours,
        },
    }


def create_performance_benchmark_data(
    duration_minutes: int = 30, concurrent_clients: int = 10
) -> dict[str, Any]:
    """Create performance benchmark data for load testing."""
    # Generate per-minute metrics
    metrics_per_minute = []
    base_time = datetime.now() - timedelta(minutes=duration_minutes)

    for minute in range(duration_minutes):
        timestamp = base_time + timedelta(minutes=minute)

        # Simulate varying load
        load_factor = 0.5 + 0.5 * random.random()  # 50-100% load
        requests_this_minute = int(
            concurrent_clients * 6 * load_factor
        )  # ~6 req/min per client

        minute_metrics = {
            "timestamp": timestamp,
            "requests_count": requests_this_minute,
            "response_time_p50": Faker.random_int(100, 500),
            "response_time_p95": Faker.random_int(500, 2000),
            "response_time_p99": Faker.random_int(1000, 5000),
            "error_rate_percent": Faker.pyfloat(0.0, 5.0),
            "throughput_rps": requests_this_minute / 60,
            "active_connections": int(concurrent_clients * load_factor),
            "memory_usage_mb": Faker.random_int(200, 1024),
            "cpu_usage_percent": Faker.random_int(10, 80),
        }
        metrics_per_minute.append(minute_metrics)

    # Calculate overall statistics
    total_requests = sum(m["requests_count"] for m in metrics_per_minute)
    avg_response_time = sum(m["response_time_p50"] for m in metrics_per_minute) / len(
        metrics_per_minute
    )
    max_response_time = max(m["response_time_p99"] for m in metrics_per_minute)
    avg_error_rate = sum(m["error_rate_percent"] for m in metrics_per_minute) / len(
        metrics_per_minute
    )

    return {
        "benchmark_config": {
            "duration_minutes": duration_minutes,
            "concurrent_clients": concurrent_clients,
            "started_at": base_time,
            "completed_at": base_time + timedelta(minutes=duration_minutes),
        },
        "metrics_timeline": metrics_per_minute,
        "summary_statistics": {
            "total_requests": total_requests,
            "average_rps": total_requests / (duration_minutes * 60),
            "average_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "average_error_rate_percent": avg_error_rate,
            "peak_memory_usage_mb": max(
                m["memory_usage_mb"] for m in metrics_per_minute
            ),
            "peak_cpu_usage_percent": max(
                m["cpu_usage_percent"] for m in metrics_per_minute
            ),
        },
        "performance_grade": _calculate_performance_grade(
            avg_response_time, avg_error_rate
        ),
    }


def _calculate_performance_grade(
    avg_response_time: float, avg_error_rate: float
) -> str:
    """Calculate performance grade based on metrics."""
    if avg_response_time < 200 and avg_error_rate < 0.1:
        return "A"
    elif avg_response_time < 500 and avg_error_rate < 0.5:
        return "B"
    elif avg_response_time < 1000 and avg_error_rate < 1.0:
        return "C"
    elif avg_response_time < 2000 and avg_error_rate < 2.0:
        return "D"
    else:
        return "F"

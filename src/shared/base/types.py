"""Base types for the shared modules."""

from enum import IntEnum


class LogLevel(IntEnum):
    """Log levels following RFC 5424."""

    EMERGENCY = 0
    ALERT = 1
    CRITICAL = 2
    ERROR = 3
    WARNING = 4
    NOTICE = 5
    INFO = 6
    DEBUG = 7

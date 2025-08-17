"""Common types and enums for MCP models.

Copyright 2025
SPDX-License-Identifier: Apache-2.0
Authors: Manav Gupta

This module defines shared types and enums used across MCP components.
"""

from enum import Enum


class LogLevel(str, Enum):
    """Enumeration of available logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"
    EMERGENCY = "EMERGENCY"

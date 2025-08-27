"""Base configuration for all MCP components."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseMCPSettings(BaseSettings):
    """Base settings for all MCP components."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow",  # Allow extra fields in subclasses
    )

    log_level: str = Field(default="INFO", description="Logging level")
    max_diff_lines: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum lines to include in diff output",
    )

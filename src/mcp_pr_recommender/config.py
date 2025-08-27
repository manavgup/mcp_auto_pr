"""Configuration for PR recommender."""

from pydantic import Field

from shared.base.config import BaseMCPSettings


class PRRecommenderSettings(BaseMCPSettings):
    """PR recommender configuration."""

    # Environment variables that may be set in .env
    workspace_dir: str = Field(
        default="",
        description="Workspace directory path",
    )
    python_env: str = Field(
        default="development",
        description="Python environment (development, production, etc.)",
    )

    # LLM Settings
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    max_tokens_per_request: int = Field(default=2000, description="Max tokens per LLM request")

    # Grouping Settings
    max_files_per_pr: int = Field(default=8, ge=1, le=20, description="Max files per PR")
    min_files_per_pr: int = Field(default=1, ge=1, description="Min files per PR")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")

    # Strategy Settings
    default_strategy: str = Field(default="semantic", description="Default grouping strategy")
    enable_llm_analysis: bool = Field(default=True, description="Enable LLM-powered analysis")

    # Server Settings
    server_host: str = Field(default="localhost", description="Server host")
    server_port: int = Field(default=8002, description="Server port")
    log_level: str = Field(default="INFO", description="Log level")


# Global settings instance - lazy loaded to avoid requiring API key at import time
_settings_instance = None


def get_settings() -> PRRecommenderSettings:
    """Get the global settings instance, creating it if necessary."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = PRRecommenderSettings()
    return _settings_instance


# For backward compatibility
class PRRecommenderConfig:
    """Compatibility class for accessing settings."""

    @staticmethod
    def get_settings() -> PRRecommenderSettings:
        """Get settings instance."""
        return get_settings()


# Export settings getter for convenience
settings = get_settings

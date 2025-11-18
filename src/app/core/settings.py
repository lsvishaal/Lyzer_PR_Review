"""Application settings and configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Lyzer PR Review Agent"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "info"
    log_format: str = "json"  # json or console

    # GitHub
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"

    # LLM / AI
    # Ollama (local, default)
    llm_base_url: str = "http://ollama:11434"
    llm_model_name: str = "qwen2.5-coder:3b"
    llm_timeout: float = 60.0
    # Cloud LLMs (optional, for comparison)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Agent Configuration
    max_chunk_size: int = 1000
    reasoning_depth: int = 3
    enable_parallel_agents: bool = True

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

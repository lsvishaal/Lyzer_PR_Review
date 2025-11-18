"""Dependency injection providers."""

from functools import lru_cache

from src.app.core.settings import get_settings
from src.app.llm import LLMClient, LLMConfig


@lru_cache
def get_llm_client() -> LLMClient:
    """Get cached LLM client instance.

    Returns:
        Configured LLM client
    """
    settings = get_settings()
    config = LLMConfig(
        base_url=settings.llm_base_url,
        model=settings.llm_model_name,
        timeout=settings.llm_timeout,
    )
    return LLMClient(config=config)

"""Dependency injection providers."""

from collections.abc import AsyncIterator
from functools import lru_cache

from src.app.agents.logic import LogicAgent
from src.app.agents.manager import AgentOrchestrator
from src.app.agents.performance import PerformanceAgent
from src.app.agents.readability import ReadabilityAgent
from src.app.agents.security import SecurityAgent
from src.app.core.settings import get_settings
from src.app.github.client import GitHubClient
from src.app.llm import LLMClient, LLMConfig


@lru_cache
def get_llm_client() -> LLMClient:
    """Get cached LLM client instance."""

    settings = get_settings()
    config = LLMConfig(
        base_url=settings.llm_base_url,
        model=settings.llm_model_name,
        timeout=settings.llm_timeout,
    )
    return LLMClient(config=config)


async def get_github_client() -> AsyncIterator[GitHubClient]:
    """Provide a configured GitHub client for request scope."""

    settings = get_settings()
    client = GitHubClient(
        token=settings.github_token,
        base_url=settings.github_api_url,
        timeout=settings.github_timeout,
        user_agent=settings.github_user_agent,
    )
    try:
        yield client
    finally:
        await client.aclose()


def get_agent_orchestrator() -> AgentOrchestrator:
    """Construct an orchestrator wired with the default agent set."""

    llm_client = get_llm_client()
    agents = [
        LogicAgent(llm=llm_client),
        ReadabilityAgent(llm=llm_client),
        PerformanceAgent(llm=llm_client),
        SecurityAgent(llm=llm_client),
    ]
    return AgentOrchestrator(agents)

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Sequence

from src.app.agents.base import BaseAgent
from src.app.models.code import CodeChunk
from src.app.models.review import ReviewComment


class AgentOrchestrator:
    """Runs multiple agents over code chunks and aggregates their comments."""

    def __init__(self, agents: Sequence[BaseAgent]) -> None:
        self._agents = list(agents)

    async def review(self, chunks: Iterable[CodeChunk]) -> list[ReviewComment]:
        tasks: list[asyncio.Task[list[ReviewComment]]] = []

        for chunk in chunks:
            for agent in self._agents:
                tasks.append(asyncio.create_task(agent.analyze(chunk)))

        results: list[list[ReviewComment]] = []
        if tasks:
            results = await asyncio.gather(*tasks)

        all_comments: list[ReviewComment] = [comment for batch in results for comment in batch]

        # Deduplicate comments by hash/equality
        unique: dict[ReviewComment, ReviewComment] = {}
        for comment in all_comments:
            unique[comment] = comment

        return list(unique.values())

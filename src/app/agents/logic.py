from __future__ import annotations

from src.app.agents.base import BaseAgent
from src.app.models.code import CodeChunk
from src.app.models.review import ReviewComment


class LogicAgent(BaseAgent):
    """Agent focused on logical flaws and edge cases."""

    def __init__(self, llm: object) -> None:
        super().__init__(name="logic")
        # Accepts any object with an async .generate(...) method (LLMClient or FakeLLMClient)
        self._llm = llm

    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Placeholder implementation; returns no comments for now.

        The real implementation will use the LLM client to analyze the chunk.
        """
        return []


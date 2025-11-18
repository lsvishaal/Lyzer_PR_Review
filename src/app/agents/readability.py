from __future__ import annotations

from src.app.agents.base import BaseAgent
from src.app.models.code import CodeChunk
from src.app.models.review import ReviewComment


class ReadabilityAgent(BaseAgent):
    """Agent focusing on naming, structure, and documentation."""

    def __init__(self, llm: object) -> None:
        super().__init__(name="readability")
        self._llm = llm

    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Placeholder implementation; returns no comments for now."""
        return []


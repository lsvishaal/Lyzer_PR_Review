from __future__ import annotations

from src.app.agents.base import BaseAgent
from src.app.models.code import CodeChunk
from src.app.models.review import ReviewComment


class SecurityAgent(BaseAgent):
    """Agent detecting security issues and vulnerabilities."""

    def __init__(self, llm: object) -> None:
        super().__init__(name="security")
        self._llm = llm

    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Placeholder implementation; returns no comments for now."""
        return []


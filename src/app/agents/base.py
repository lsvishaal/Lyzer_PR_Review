from __future__ import annotations

from abc import ABC, abstractmethod

from src.app.models.code import CodeChunk
from src.app.models.review import ReviewComment


class BaseAgent(ABC):
    """Abstract base class for all review agents.

    Contract:
    - Input: CodeChunk (single chunk of changed code)
    - Output: list[ReviewComment]
    """

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Analyze a single code chunk and return review comments."""

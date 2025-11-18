from __future__ import annotations

import pytest

from src.app.agents import (
    AgentOrchestrator,
    BaseAgent,
    LogicAgent,
    PerformanceAgent,
    ReadabilityAgent,
    SecurityAgent,
)
from src.app.llm.client import FakeLLMClient
from src.app.models.code import CodeChunk
from src.app.models.base import Language
from src.app.models.review import ReviewCategory, ReviewComment, Severity


class DummyAgent(BaseAgent):
    """Simple concrete agent for contract testing."""

    def __init__(self, name: str, label: str) -> None:
        super().__init__(name=name)
        self._label = label

    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        return [
            ReviewComment(
                file_path=chunk.file_path,
                line_number=chunk.start_line,
                severity=Severity.WARNING,
                category=ReviewCategory.LOGIC,
                message=f"{self._label} issue in {chunk.file_path}",
                suggestion=None,
                agent_name=self.name,
            )
        ]


class TestBaseAgent:
    def test_base_agent_name(self) -> None:
        agent = DummyAgent(name="dummy", label="test")
        assert agent.name == "dummy"


class TestAgentOrchestrator:
    @pytest.mark.asyncio
    async def test_orchestrator_aggregates_comments(self) -> None:
        chunk = CodeChunk(
            file_path="src/app/example.py",
            language=Language.PYTHON,
            original_lines=["old"],
            new_lines=["new"],
            start_line=10,
            end_line=11,
        )

        agents: list[BaseAgent] = [
            DummyAgent(name="a1", label="first"),
            DummyAgent(name="a2", label="second"),
        ]

        orchestrator = AgentOrchestrator(agents)
        comments = await orchestrator.review([chunk])

        assert len(comments) == 2
        messages = {c.message for c in comments}
        assert "first issue in src/app/example.py" in messages
        assert "second issue in src/app/example.py" in messages

    @pytest.mark.asyncio
    async def test_orchestrator_handles_empty_chunks(self) -> None:
        orchestrator = AgentOrchestrator([])
        comments = await orchestrator.review([])
        assert comments == []


class TestConcreteAgents:
    @pytest.fixture()
    def fake_llm(self) -> FakeLLMClient:
        return FakeLLMClient(responses={})

    @pytest.fixture()
    def chunk(self) -> CodeChunk:
        return CodeChunk(
            file_path="src/app/example.py",
            language=Language.PYTHON,
            original_lines=["old"],
            new_lines=["new"],
            start_line=1,
            end_line=2,
        )

    @pytest.mark.asyncio
    async def test_logic_agent_runs_with_fake_llm(self, fake_llm: FakeLLMClient, chunk: CodeChunk) -> None:
        agent = LogicAgent(llm=fake_llm)
        comments = await agent.analyze(chunk)
        assert isinstance(comments, list)

    @pytest.mark.asyncio
    async def test_readability_agent_runs_with_fake_llm(self, fake_llm: FakeLLMClient, chunk: CodeChunk) -> None:
        agent = ReadabilityAgent(llm=fake_llm)
        comments = await agent.analyze(chunk)
        assert isinstance(comments, list)

    @pytest.mark.asyncio
    async def test_performance_agent_runs_with_fake_llm(self, fake_llm: FakeLLMClient, chunk: CodeChunk) -> None:
        agent = PerformanceAgent(llm=fake_llm)
        comments = await agent.analyze(chunk)
        assert isinstance(comments, list)

    @pytest.mark.asyncio
    async def test_security_agent_runs_with_fake_llm(self, fake_llm: FakeLLMClient, chunk: CodeChunk) -> None:
        agent = SecurityAgent(llm=fake_llm)
        comments = await agent.analyze(chunk)
        assert isinstance(comments, list)

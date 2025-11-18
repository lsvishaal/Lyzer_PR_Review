from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.app.core import dependencies
from src.app.main import app
from src.app.models.code import CodeChunk
from src.app.models.review import ReviewCategory, ReviewComment, Severity


class _TestOrchestrator:
    def __init__(self, comments: Iterable[ReviewComment]) -> None:
        self._comments = list(comments)
        self.last_chunks: list[CodeChunk] = []

    async def review(self, chunks: Iterable[CodeChunk]) -> list[ReviewComment]:
        self.last_chunks = list(chunks)
        return list(self._comments)


class _TestGitHubClient:
    def __init__(self, diff: str) -> None:
        self._diff = diff
        self.calls: list[tuple[str, str, int]] = []

    async def get_pull_request_diff(self, owner: str, repo: str, number: int) -> str:
        self.calls.append((owner, repo, number))
        return self._diff


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _make_comment() -> ReviewComment:
    return ReviewComment(
        file_path="src/app/example.py",
        line_number=3,
        severity=Severity.WARNING,
        category=ReviewCategory.LOGIC,
        message="Potential bug detected",
        suggestion="Add error handling",
        agent_name="logic",
    )


def _diff_payload() -> str:
    return """diff --git a/src/app/example.py b/src/app/example.py
index 123..456 100644
--- a/src/app/example.py
+++ b/src/app/example.py
@@ -1,2 +1,2 @@
-old_line
+new_line
"""


def _override_dependencies(orchestrator: Any, github_client: Any) -> None:
    dependencies_overrides = app.dependency_overrides
    dependencies_overrides[dependencies.get_agent_orchestrator] = lambda: orchestrator
    dependencies_overrides[dependencies.get_github_client] = lambda: github_client


def _clear_dependency_overrides() -> None:
    app.dependency_overrides.pop(dependencies.get_agent_orchestrator, None)
    app.dependency_overrides.pop(dependencies.get_github_client, None)


def test_review_endpoint_with_manual_diff(client: TestClient) -> None:
    orchestrator = _TestOrchestrator([_make_comment()])
    _override_dependencies(orchestrator, None)

    try:
        response = client.post("/review/pr", json={"diff": _diff_payload()})
    finally:
        _clear_dependency_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["total_issues"] == 1
    assert data["comments"][0]["message"] == "Potential bug detected"
    assert orchestrator.last_chunks  # Ensure diff was parsed into chunks


def test_review_endpoint_requires_input(client: TestClient) -> None:
    """Test that endpoint returns 422 for invalid input (Pydantic validation)."""
    _override_dependencies(_TestOrchestrator([]), None)

    try:
        response = client.post("/review/pr", json={})
    finally:
        _clear_dependency_overrides()

    assert response.status_code == 422  # Pydantic validation error
    data = response.json()
    assert "detail" in data


def test_review_endpoint_fetches_github_diff(client: TestClient) -> None:
    orchestrator = _TestOrchestrator([_make_comment()])
    github_client = _TestGitHubClient(diff=_diff_payload())
    _override_dependencies(orchestrator, github_client)

    try:
        response = client.post(
            "/review/pr",
            json={"pr_id": 42, "repo": "octocat/hello-world"},
        )
    finally:
        _clear_dependency_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["total_issues"] == 1
    assert github_client.calls == [("octocat", "hello-world", 42)]

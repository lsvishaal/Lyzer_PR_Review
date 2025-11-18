from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from src.app.github.client import GitHubClient, GitHubClientError


def _build_transport(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_get_pull_request_diff_success() -> None:
    expected_diff = "diff --git a/src/app/example.py b/src/app/example.py"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("accept") == "application/vnd.github.v3.diff"
        assert request.headers.get("authorization") == "Bearer test-token"
        assert request.url.path == "/repos/octocat/hello-world/pulls/42"
        return httpx.Response(status_code=200, text=expected_diff)

    client = GitHubClient(
        token="test-token",
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    async with client:
        diff = await client.get_pull_request_diff("octocat", "hello-world", 42)

    assert diff == expected_diff


@pytest.mark.asyncio
async def test_get_pull_request_diff_raises_for_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, json={"message": "Not Found"})

    client = GitHubClient(
        token="test-token",
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    with pytest.raises(GitHubClientError) as exc_info:
        async with client:
            await client.get_pull_request_diff("octocat", "hello-world", 99)

    assert exc_info.value.status_code == 404
    assert "Not Found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_pull_request_metadata_success() -> None:
    payload = {"number": 42, "title": "Add feature"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("accept") == "application/vnd.github+json"
        return httpx.Response(status_code=200, json=payload)

    client = GitHubClient(
        token=None,
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    async with client:
        data = await client.get_pull_request("octocat", "hello-world", 42)

    assert data == payload


@pytest.mark.asyncio
async def test_list_pull_requests_success() -> None:
    payload = [
        {"number": 1, "title": "First"},
        {"number": 2, "title": "Second"},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("accept") == "application/vnd.github+json"
        assert request.url.path == "/repos/octocat/hello-world/pulls"
        # Query params are strings in the URL
        assert request.url.params["state"] == "closed"
        assert request.url.params["per_page"] == "10"
        assert request.url.params["page"] == "2"
        return httpx.Response(status_code=200, json=payload)

    client = GitHubClient(
        token="abc123",
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    async with client:
        data = await client.list_pull_requests(
            "octocat",
            "hello-world",
            state="closed",
            per_page=10,
            page=2,
        )

    assert data == payload


@pytest.mark.asyncio
async def test_list_pull_requests_handles_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=403, json={"message": "Forbidden"})

    client = GitHubClient(
        token="bad-token",
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    with pytest.raises(GitHubClientError) as exc_info:
        async with client:
            await client.list_pull_requests("octocat", "hello-world")

    assert exc_info.value.status_code == 403
    assert "Forbidden" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_pull_request_files_success() -> None:
    payload: list[dict[str, Any]] = [
        {
            "filename": "src/app/example.py",
            "status": "modified",
            "additions": 3,
            "deletions": 1,
            "changes": 4,
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("accept") == "application/vnd.github+json"
        assert request.url.path == "/repos/octocat/hello-world/pulls/7/files"
        return httpx.Response(status_code=200, json=payload)

    client = GitHubClient(
        token="abc123",
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    async with client:
        files = await client.get_pull_request_files("octocat", "hello-world", 7)

    assert files == payload


@pytest.mark.asyncio
async def test_get_pull_request_commits_success() -> None:
    payload = [
        {
            "sha": "abc",
            "commit": {"message": "Initial"},
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("accept") == "application/vnd.github+json"
        assert request.url.path == "/repos/octocat/hello-world/pulls/7/commits"
        return httpx.Response(status_code=200, json=payload)

    client = GitHubClient(
        token="abc123",
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    async with client:
        commits = await client.get_pull_request_commits("octocat", "hello-world", 7)

    assert commits == payload


@pytest.mark.asyncio
async def test_get_pull_request_patch_success() -> None:
    expected_patch = "diff --git a/foo b/foo"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("accept") == "application/vnd.github.v3.patch"
        assert request.url.path == "/repos/octocat/hello-world/pulls/5"
        return httpx.Response(status_code=200, text=expected_patch)

    client = GitHubClient(
        token="abc123",
        base_url="https://api.github.com",
        timeout=5.0,
        transport=_build_transport(handler),
    )

    async with client:
        patch = await client.get_pull_request_patch("octocat", "hello-world", 5)

    assert patch == expected_patch

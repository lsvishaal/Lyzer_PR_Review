"""Review endpoints for orchestrating PR analysis."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.app.agents.manager import AgentOrchestrator
from src.app.core.dependencies import get_agent_orchestrator, get_github_client
from src.app.core.logging_config import get_logger, log_pr_event
from src.app.diff.parser import parse_unified_diff
from src.app.github.client import GitHubClient, GitHubClientError
from src.app.models.review import ReviewRequest, ReviewResponse

router = APIRouter(prefix="/review", tags=["review"])

logger = get_logger(__name__)


def _parse_repo_slug(slug: str) -> tuple[str, str]:
    owner, _, repo = slug.partition("/")
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Repository must be in owner/repo format")
    return owner, repo


@router.post("/pr", response_model=ReviewResponse)
async def review_pull_request(
    request: ReviewRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
    github_client: GitHubClient | None = Depends(get_github_client),
) -> ReviewResponse:
    """Review a pull request by PR identifier or raw diff input."""

    if not request.validate_input():
        raise HTTPException(status_code=400, detail="Provide either pr_id+repo or diff")

    diff_source: str
    repo_owner: str | None = None
    repo_name: str | None = None

    if request.diff:
        diff_source = request.diff
    else:
        assert request.pr_id is not None  # mypy appeasement
        assert request.repo is not None
        repo_owner, repo_name = _parse_repo_slug(request.repo)
        if github_client is None:
            raise HTTPException(status_code=500, detail="GitHub client not configured")

        try:
            diff_source = await github_client.get_pull_request_diff(
                repo_owner, repo_name, request.pr_id
            )
        except GitHubClientError as exc:
            logger.error(
                "github_diff_fetch_failed",
                status_code=exc.status_code,
                pr_id=request.pr_id,
                repo=request.repo,
            )
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    file_diffs = parse_unified_diff(diff_source)
    chunks = [chunk for file_diff in file_diffs for chunk in file_diff.chunks]

    if request.pr_id and repo_owner and repo_name:
        log_pr_event(request.pr_id, "review_requested", repo=request.repo, chunks=len(chunks))

    comments = await orchestrator.review(chunks)

    return ReviewResponse(pr_id=request.pr_id, repo=request.repo, comments=comments)

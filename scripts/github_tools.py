#!/usr/bin/env python3
"""Utility CLI for interacting with GitHub pull requests.

This script provides a lightweight wrapper around the asynchronous GitHub client
so that engineers can quickly list pull requests, view metadata, inspect the
diff/patch, or examine the changed files from the command line.

Example usages:

    # List open pull requests (defaults to settings from .env)
    python scripts/github_tools.py list octocat/Hello-World --state open

    # Download the diff for PR #123
    python scripts/github_tools.py diff octocat/Hello-World 123 --output pr123.diff

    # Print changed files for PR #42
    python scripts/github_tools.py files octocat/Hello-World 42

The token can be supplied via --token or by configuring GITHUB_TOKEN in .env.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from src.app.core.settings import Settings
from src.app.github.client import GitHubClient


def _load_settings() -> Settings:
    return Settings()


def _resolve_token(explicit: str | None, settings: Settings) -> str | None:
    if explicit:
        return explicit
    return settings.github_token


async def _run_list(client: GitHubClient, args: argparse.Namespace) -> None:
    pull_requests = await client.list_pull_requests(
        args.owner,
        args.repo,
        state=args.state,
        per_page=args.per_page,
        page=args.page,
    )
    _print_json(pull_requests)


async def _run_metadata(client: GitHubClient, args: argparse.Namespace) -> None:
    pr = await client.get_pull_request(args.owner, args.repo, args.number)
    _print_json(pr)


async def _run_diff(client: GitHubClient, args: argparse.Namespace) -> None:
    diff_text = await client.get_pull_request_diff(args.owner, args.repo, args.number)
    _output_text(diff_text, args.output)


async def _run_patch(client: GitHubClient, args: argparse.Namespace) -> None:
    patch_text = await client.get_pull_request_patch(args.owner, args.repo, args.number)
    _output_text(patch_text, args.output)


async def _run_files(client: GitHubClient, args: argparse.Namespace) -> None:
    files = await client.get_pull_request_files(
        args.owner,
        args.repo,
        args.number,
        per_page=args.per_page,
        page=args.page,
    )
    _print_json(files)


async def _run_commits(client: GitHubClient, args: argparse.Namespace) -> None:
    commits = await client.get_pull_request_commits(
        args.owner,
        args.repo,
        args.number,
        per_page=args.per_page,
        page=args.page,
    )
    _print_json(commits)


def _print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _output_text(content: str, destination: str | None) -> None:
    if destination:
        output_path = Path(destination)
        output_path.write_text(content, encoding="utf-8")
        print(f"Wrote output to {output_path}")
    else:
        print(content)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub PR helper utilities")
    parser.add_argument("command", choices=["list", "metadata", "diff", "patch", "files", "commits"])
    parser.add_argument("repo_slug", help="Repository in owner/repo format")
    parser.add_argument("number", nargs="?", type=int, help="Pull request number where required")
    parser.add_argument("--token", dest="token", help="GitHub personal access token")
    parser.add_argument("--state", default="open", help="Filter pull requests by state (list command)")
    parser.add_argument("--per-page", dest="per_page", type=int, default=30, help="Items per page for list endpoints")
    parser.add_argument("--page", type=int, default=1, help="Result page to fetch")
    parser.add_argument("--output", help="File path to write diff/patch output")
    return parser


def _parse_repo(slug: str) -> tuple[str, str]:
    owner, _, repo = slug.partition("/")
    if not owner or not repo:
        raise SystemExit("Repository must be in owner/repo format")
    return owner, repo


async def _dispatch(args: argparse.Namespace) -> None:
    settings = _load_settings()
    owner, repo = _parse_repo(args.repo_slug)
    token = _resolve_token(args.token, settings)

    if token is None:
        raise SystemExit("GitHub token is required; provide via --token or GITHUB_TOKEN in .env")

    client = GitHubClient(
        token=token,
        base_url=settings.github_api_url,
        timeout=settings.github_timeout,
        user_agent=settings.github_user_agent,
    )

    async with client:
        if args.command == "list":
            args.owner, args.repo = owner, repo
            await _run_list(client, args)
        elif args.command == "metadata":
            _ensure_number(args)
            args.owner, args.repo = owner, repo
            await _run_metadata(client, args)
        elif args.command == "diff":
            _ensure_number(args)
            args.owner, args.repo = owner, repo
            await _run_diff(client, args)
        elif args.command == "patch":
            _ensure_number(args)
            args.owner, args.repo = owner, repo
            await _run_patch(client, args)
        elif args.command == "files":
            _ensure_number(args)
            args.owner, args.repo = owner, repo
            await _run_files(client, args)
        elif args.command == "commits":
            _ensure_number(args)
            args.owner, args.repo = owner, repo
            await _run_commits(client, args)


def _ensure_number(args: argparse.Namespace) -> None:
    if args.number is None:
        raise SystemExit("This command requires a pull request number")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    asyncio.run(_dispatch(args))


if __name__ == "__main__":
    main()

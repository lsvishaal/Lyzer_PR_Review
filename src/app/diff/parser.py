"""Utilities for parsing unified diffs into Pydantic models.

This module is intentionally small and focused: it converts a raw unified diff
string into a list of FileDiff/CodeChunk models that the agent layer can
consume. It does not know anything about GitHub or HTTP.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from src.app.core.settings import get_settings
from src.app.models.base import Language
from src.app.models.code import CodeChunk, FileDiff

_LANGUAGE_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".java": Language.JAVA,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".c": Language.C,
    ".h": Language.C,
    ".hpp": Language.CPP,
    ".rb": Language.RUBY,
    ".php": Language.PHP,
}


def _normalize_diff_path(path: str | None) -> str | None:
    if path is None:
        return None
    trimmed = path.strip()
    if trimmed in {"/dev/null", "dev/null"}:
        return "/dev/null"
    if trimmed.startswith("a/") or trimmed.startswith("b/"):
        return trimmed[2:]
    return trimmed


def _detect_language(path: str | None) -> Language:
    if not path or path == "/dev/null":
        return Language.UNKNOWN
    ext = Path(path).suffix.lower()
    return _LANGUAGE_MAP.get(ext, Language.UNKNOWN)


def parse_unified_diff(raw_diff: str) -> list[FileDiff]:
    """Parse a unified diff string into a list of FileDiff models.

    The parser supports standard unified diff output, such as that produced by
    ``git diff --unified`` or GitHub's pull request diff APIs. It focuses on
    changed hunks and maps them into CodeChunk instances.

    This implementation is intentionally conservative: it handles the common
    patterns we care about for PR review (file headers, hunk headers, and line
    prefixes ``+``, ``-``, and space). It does not attempt to be a fully
    general diff parser.
    """

    if not raw_diff.strip():
        return []

    file_diffs: list[FileDiff] = []

    current_file: FileDiff | None = None
    original_lines: list[str] = []
    new_lines: list[str] = []
    hunk_start_line_new: int | None = None
    current_additions = 0
    current_deletions = 0
    old_path: str | None = None
    new_path: str | None = None
    file_lines: list[str] | None = None

    def _flush_chunk() -> None:
        nonlocal original_lines, new_lines, hunk_start_line_new, current_file
        if current_file is None or hunk_start_line_new is None:
            return
        if not original_lines and not new_lines:
            return

        line_span = max(len(original_lines), len(new_lines))
        end_line = hunk_start_line_new + line_span - 1
        chunk = CodeChunk(
            file_path=current_file.file_path,
            language=current_file.language,
            original_lines=list(original_lines),
            new_lines=list(new_lines),
            start_line=hunk_start_line_new,
            end_line=end_line,
        )
        current_file.chunks.append(chunk)

        original_lines = []
        new_lines = []
        hunk_start_line_new = None

    def _finalize_file() -> None:
        nonlocal current_file, current_additions, current_deletions, file_lines, old_path, new_path
        _flush_chunk()
        if current_file is None:
            file_lines = None
            old_path = None
            new_path = None
            return

        current_file.additions = current_additions
        current_file.deletions = current_deletions
        if file_lines:
            current_file.raw_diff = "\n".join(file_lines)
        file_diffs.append(current_file)

        current_file = None
        current_additions = 0
        current_deletions = 0
        file_lines = None
        old_path = None
        new_path = None

    lines: Iterable[str] = raw_diff.splitlines()
    for line in lines:
        if line.startswith("diff --git "):
            _finalize_file()
            file_lines = [line]
            continue

        if file_lines is not None:
            file_lines.append(line)

        if line.startswith("--- "):
            old_path = _normalize_diff_path(line[4:])
            continue

        if line.startswith("+++ "):
            new_path = _normalize_diff_path(line[4:])

            normalized_old = old_path
            normalized_new = new_path

            if normalized_old == "/dev/null":
                file_path = normalized_new or ""
                status = "added"
            elif normalized_new == "/dev/null":
                file_path = normalized_old or ""
                status = "deleted"
            else:
                file_path = normalized_new or normalized_old or ""
                if normalized_old and normalized_new and normalized_old != normalized_new:
                    status = "renamed"
                else:
                    status = "modified"

            language = _detect_language(file_path)
            current_file = FileDiff(
                file_path=file_path,
                language=language,
                status=status,
                additions=0,
                deletions=0,
                chunks=[],
                raw_diff="",
            )
            current_additions = 0
            current_deletions = 0
            continue

        if line.startswith("@@ ") and current_file is not None:
            _flush_chunk()
            try:
                header = line.split("@@")[1].strip()
                parts = header.split()
                new_part = next(p for p in parts if p.startswith("+"))
                plus_range = new_part[1:]
                if "," in plus_range:
                    start_str, _ = plus_range.split(",", 1)
                else:
                    start_str = plus_range
                parsed_line = int(start_str) if start_str else 0
                hunk_start_line_new = parsed_line if parsed_line > 0 else 1
            except Exception:
                hunk_start_line_new = None
            original_lines = []
            new_lines = []
            continue

        if current_file is None or hunk_start_line_new is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            new_lines.append(line[1:])
            current_additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            original_lines.append(line[1:])
            current_deletions += 1
        elif line.startswith(" "):
            text = line[1:]
            original_lines.append(text)
            new_lines.append(text)

    _finalize_file()

    return file_diffs


def filter_supported_files(
    file_diffs: list[FileDiff],
) -> tuple[list[FileDiff], list[str]]:
    """Filter files to only supported languages and detect binary files.

    Returns:
        Tuple of (supported_files, ignored_files)
    """
    settings = get_settings()
    supported = []
    ignored = []

    for file_diff in file_diffs:
        # Check for binary files (common markers)
        if file_diff.file_path.endswith(
            (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".ico",
                ".pdf",
                ".zip",
                ".tar",
                ".gz",
                ".exe",
                ".dll",
                ".so",
                ".dylib",
            )
        ):
            ignored.append(f"{file_diff.file_path} (binary)")
            continue

        # Check extension
        ext = Path(file_diff.file_path).suffix.lower()
        if ext and ext not in settings.supported_extensions:
            ignored.append(f"{file_diff.file_path} (unsupported: {ext})")
            continue

        # Check if file has actual code changes
        if file_diff.status == "deleted":
            ignored.append(f"{file_diff.file_path} (deleted)")
            continue

        if len(file_diff.chunks) == 0:
            ignored.append(f"{file_diff.file_path} (no code changes)")
            continue

        supported.append(file_diff)

    return supported, ignored

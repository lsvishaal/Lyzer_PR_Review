"""Tests for unified diff parsing utilities."""

from pathlib import Path

import pytest

from src.app.diff.parser import parse_unified_diff
from src.app.models.base import Language

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


class TestParseUnifiedDiff:
    """Behavioral tests for ``parse_unified_diff``."""

    def test_modified_file_reports_counts_and_chunks(self) -> None:
        """Modified files should track additions/deletions and chunk metadata."""

        diff = """diff --git a/src/app/example.py b/src/app/example.py
index 1111111..2222222 100644
--- a/src/app/example.py
+++ b/src/app/example.py
@@ -1,3 +1,4 @@
 def foo():
-    return 1
+    return 2

"""

        file_diffs = parse_unified_diff(diff)

        assert len(file_diffs) == 1
        file_diff = file_diffs[0]
        assert file_diff.status == "modified"
        assert file_diff.additions == 1
        assert file_diff.deletions == 1
        assert file_diff.file_path == "src/app/example.py"
        assert file_diff.language == Language.PYTHON
        assert len(file_diff.chunks) == 1
        chunk = file_diff.chunks[0]
        assert chunk.start_line == 1
        assert "    return 2" in chunk.new_lines
        assert "    return 1" in chunk.original_lines

    def test_added_file_detected(self) -> None:
        """A diff against ``/dev/null`` should be flagged as an added file."""

        diff = """diff --git a/src/app/new_file.py b/src/app/new_file.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/src/app/new_file.py
@@ -0,0 +1,2 @@
+def added():
+    return True
"""

        file_diffs = parse_unified_diff(diff)

        assert len(file_diffs) == 1
        file_diff = file_diffs[0]
        assert file_diff.status == "added"
        assert file_diff.file_path == "src/app/new_file.py"
        assert file_diff.language == Language.PYTHON
        assert file_diff.additions == 2
        assert file_diff.deletions == 0
        assert len(file_diff.chunks) == 1
        chunk = file_diff.chunks[0]
        assert chunk.start_line == 1
        assert chunk.is_addition is True

    def test_deleted_file_detected(self) -> None:
        """When the new path is ``/dev/null`` the file should be marked deleted."""

        diff = """diff --git a/src/app/old_file.py b/src/app/old_file.py
deleted file mode 100644
index 4444444..0000000
--- a/src/app/old_file.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def removed():
-    pass
"""

        file_diffs = parse_unified_diff(diff)

        assert len(file_diffs) == 1
        file_diff = file_diffs[0]
        assert file_diff.status == "deleted"
        assert file_diff.file_path == "src/app/old_file.py"
        assert file_diff.additions == 0
        assert file_diff.deletions == 2
        assert len(file_diff.chunks) == 1
        chunk = file_diff.chunks[0]
        assert chunk.is_deletion is True

    def test_rename_reports_new_path(self) -> None:
        """Renames should record the new path and report renamed status."""

        diff = """diff --git a/src/app/old_name.py b/src/app/new_name.py
similarity index 100%
rename from src/app/old_name.py
rename to src/app/new_name.py
--- a/src/app/old_name.py
+++ b/src/app/new_name.py
@@ -1,2 +1,2 @@
-def foo():
-    return 1
+def bar():
+    return 1
"""

        file_diffs = parse_unified_diff(diff)

        assert len(file_diffs) == 1
        file_diff = file_diffs[0]
        assert file_diff.status == "renamed"
        assert file_diff.file_path == "src/app/new_name.py"
        assert file_diff.additions == 2
        assert file_diff.deletions == 2
        assert file_diff.language == Language.PYTHON
        assert file_diff.chunks[0].start_line == 1


@pytest.mark.parametrize(
    "raw_diff",
    [
        "",
        "\n\n",
    ],
)
def test_empty_input_returns_empty_list(raw_diff: str) -> None:
    """Whitespace-only diffs should return an empty result."""

    assert parse_unified_diff(raw_diff) == []


def test_real_world_fixture_parses_multiple_files() -> None:
    """Parsing should succeed on the multi-file fixture diff."""

    fixture_path = FIXTURE_DIR / "real_world_pr.diff"
    diff_text = fixture_path.read_text(encoding="utf-8")

    file_diffs = parse_unified_diff(diff_text)

    assert len(file_diffs) == 2
    paths = {file_diff.file_path for file_diff in file_diffs}
    assert "src/app/utils.py" in paths
    assert "src/app/services/cache.py" in paths

    utils_diff = next(fd for fd in file_diffs if fd.file_path == "src/app/utils.py")
    assert utils_diff.status == "modified"
    assert utils_diff.language == Language.PYTHON
    assert utils_diff.chunks

    cache_diff = next(fd for fd in file_diffs if fd.file_path == "src/app/services/cache.py")
    assert cache_diff.status == "modified"
    assert cache_diff.additions >= 0

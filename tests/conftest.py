"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.app.core import Settings
from src.app.main import app


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        debug=True,
        log_level="debug",
        log_format="console",
        github_token="test_token",
        openai_api_key="test_key",
    )


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_code_chunk_data():
    """Sample code chunk data for testing."""
    return {
        "file_path": "src/main.py",
        "language": "python",
        "original_lines": ["def old_function():", "    pass"],
        "new_lines": ["def new_function():", "    return True"],
        "start_line": 10,
    }


@pytest.fixture
def sample_diff():
    """Sample unified diff for testing."""
    return """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,5 +10,5 @@ def example():
-def old_function():
-    pass
+def new_function():
+    return True
"""


@pytest.fixture
def sample_review_comment_data():
    """Sample review comment data."""
    return {
        "file_path": "src/main.py",
        "line_number": 10,
        "severity": "warning",
        "category": "readability",
        "message": "Function name should be more descriptive",
        "suggestion": "Consider renaming to describe what the function does",
    }

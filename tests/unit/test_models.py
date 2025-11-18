"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.app.models import (
    CodeChunk,
    FileDiff,
    Language,
    ReviewCategory,
    ReviewComment,
    ReviewRequest,
    ReviewResponse,
    Severity,
)


class TestCodeChunk:
    """Tests for CodeChunk model."""

    def test_code_chunk_creation_success(self, sample_code_chunk_data):
        """Test successful CodeChunk creation."""
        chunk = CodeChunk(**sample_code_chunk_data)
        assert chunk.file_path == "src/main.py"
        assert chunk.language == Language.PYTHON
        assert len(chunk.new_lines) == 2
        assert chunk.start_line == 10

    def test_code_chunk_line_count(self, sample_code_chunk_data):
        """Test line_count property."""
        chunk = CodeChunk(**sample_code_chunk_data)
        assert chunk.line_count == 2

    def test_code_chunk_is_addition(self):
        """Test is_addition property."""
        chunk = CodeChunk(
            file_path="test.py",
            original_lines=[],
            new_lines=["new code"],
            start_line=1,
        )
        assert chunk.is_addition is True
        assert chunk.is_deletion is False
        assert chunk.is_modification is False

    def test_code_chunk_is_deletion(self):
        """Test is_deletion property."""
        chunk = CodeChunk(
            file_path="test.py",
            original_lines=["old code"],
            new_lines=[],
            start_line=1,
        )
        assert chunk.is_deletion is True
        assert chunk.is_addition is False
        assert chunk.is_modification is False

    def test_code_chunk_is_modification(self, sample_code_chunk_data):
        """Test is_modification property."""
        chunk = CodeChunk(**sample_code_chunk_data)
        assert chunk.is_modification is True
        assert chunk.is_addition is False
        assert chunk.is_deletion is False

    def test_code_chunk_validation_fails_missing_required(self):
        """Test CodeChunk validation fails with missing required fields."""
        with pytest.raises(ValidationError):
            CodeChunk(new_lines=["code"])  # Missing file_path and start_line


class TestFileDiff:
    """Tests for FileDiff model."""

    def test_file_diff_creation_success(self):
        """Test successful FileDiff creation."""
        diff = FileDiff(
            file_path="src/main.py",
            language=Language.PYTHON,
            status="modified",
            additions=5,
            deletions=3,
        )
        assert diff.file_path == "src/main.py"
        assert diff.status == "modified"
        assert diff.total_changes == 8

    def test_file_diff_total_changes(self):
        """Test total_changes property."""
        diff = FileDiff(
            file_path="test.py",
            status="modified",
            additions=10,
            deletions=5,
        )
        assert diff.total_changes == 15

    def test_file_diff_with_chunks(self, sample_code_chunk_data):
        """Test FileDiff with code chunks."""
        chunk = CodeChunk(**sample_code_chunk_data)
        diff = FileDiff(
            file_path="src/main.py",
            status="modified",
            chunks=[chunk],
        )
        assert len(diff.chunks) == 1
        assert diff.chunks[0].file_path == "src/main.py"


class TestReviewComment:
    """Tests for ReviewComment model."""

    def test_review_comment_creation_success(self, sample_review_comment_data):
        """Test successful ReviewComment creation."""
        comment = ReviewComment(**sample_review_comment_data)
        assert comment.file_path == "src/main.py"
        assert comment.severity == Severity.WARNING
        assert comment.category == ReviewCategory.READABILITY

    def test_review_comment_equality(self, sample_review_comment_data):
        """Test ReviewComment equality for deduplication."""
        comment1 = ReviewComment(**sample_review_comment_data)
        comment2 = ReviewComment(**sample_review_comment_data)
        assert comment1 == comment2
        assert hash(comment1) == hash(comment2)

    def test_review_comment_inequality_different_line(self, sample_review_comment_data):
        """Test ReviewComment inequality with different line numbers."""
        comment1 = ReviewComment(**sample_review_comment_data)
        data2 = sample_review_comment_data.copy()
        data2["line_number"] = 20
        comment2 = ReviewComment(**data2)
        assert comment1 != comment2

    def test_review_comment_with_agent_name(self, sample_review_comment_data):
        """Test ReviewComment with agent_name."""
        data = sample_review_comment_data.copy()
        data["agent_name"] = "LogicAgent"
        comment = ReviewComment(**data)
        assert comment.agent_name == "LogicAgent"


class TestReviewRequest:
    """Tests for ReviewRequest model."""

    def test_review_request_with_pr_id(self):
        """Test ReviewRequest with PR ID."""
        request = ReviewRequest(pr_id=123, repo="owner/repo")
        assert request.pr_id == 123
        assert request.repo == "owner/repo"
        assert request.validate_input() is True

    def test_review_request_with_diff(self):
        """Test ReviewRequest with manual diff."""
        request = ReviewRequest(diff="sample diff content")
        assert request.diff == "sample diff content"
        assert request.validate_input() is True

    def test_review_request_validation_fails_no_input(self):
        """Test ReviewRequest validation fails with no input."""
        request = ReviewRequest()
        assert request.validate_input() is False

    def test_review_request_validation_fails_incomplete_pr(self):
        """Test ReviewRequest validation fails with incomplete PR info."""
        request = ReviewRequest(pr_id=123)  # Missing repo
        assert request.validate_input() is False


class TestReviewResponse:
    """Tests for ReviewResponse model."""

    def test_review_response_empty(self):
        """Test ReviewResponse with no comments."""
        response = ReviewResponse()
        assert response.total_issues == 0
        assert response.critical_count == 0
        assert response.warning_count == 0
        assert response.info_count == 0

    def test_review_response_with_comments(self, sample_review_comment_data):
        """Test ReviewResponse calculates counts correctly."""
        comments = [
            ReviewComment(**{**sample_review_comment_data, "severity": "critical"}),
            ReviewComment(
                **{**sample_review_comment_data, "severity": "warning", "line_number": 20}
            ),
            ReviewComment(**{**sample_review_comment_data, "severity": "info", "line_number": 30}),
        ]
        response = ReviewResponse(comments=comments)
        assert response.total_issues == 3
        assert response.critical_count == 1
        assert response.warning_count == 1
        assert response.info_count == 1

    def test_review_response_with_pr_info(self, sample_review_comment_data):
        """Test ReviewResponse with PR information."""
        comment = ReviewComment(**sample_review_comment_data)
        response = ReviewResponse(
            pr_id=123,
            repo="owner/repo",
            comments=[comment],
        )
        assert response.pr_id == 123
        assert response.repo == "owner/repo"
        assert response.total_issues == 1


class TestEnums:
    """Tests for enum values."""

    def test_severity_enum_values(self):
        """Test Severity enum has expected values."""
        assert Severity.CRITICAL == "critical"
        assert Severity.WARNING == "warning"
        assert Severity.INFO == "info"

    def test_review_category_enum_values(self):
        """Test ReviewCategory enum has expected values."""
        assert ReviewCategory.LOGIC == "logic"
        assert ReviewCategory.READABILITY == "readability"
        assert ReviewCategory.PERFORMANCE == "performance"
        assert ReviewCategory.SECURITY == "security"

    def test_language_enum_values(self):
        """Test Language enum has expected values."""
        assert Language.PYTHON == "python"
        assert Language.JAVASCRIPT == "javascript"
        assert Language.UNKNOWN == "unknown"

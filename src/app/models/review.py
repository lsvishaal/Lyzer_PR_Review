"""Review-related models for comments and responses."""

from pydantic import BaseModel, Field

from .base import ReviewCategory, Severity


class ReviewComment(BaseModel):
    """A single code review comment from an agent."""

    file_path: str = Field(..., description="Path to the file")
    line_number: int = Field(..., description="Line number in the file")
    severity: Severity = Field(default=Severity.WARNING, description="Severity level")
    category: ReviewCategory = Field(..., description="Review category")
    message: str = Field(..., description="Review message")
    suggestion: str | None = Field(None, description="Suggested fix or improvement")
    agent_name: str | None = Field(None, description="Name of the agent that generated this")

    def __hash__(self) -> int:
        """Make comment hashable for deduplication."""
        return hash((self.file_path, self.line_number, self.message))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ReviewComment):
            return False
        return (
            self.file_path == other.file_path
            and self.line_number == other.line_number
            and self.message == other.message
        )


class ReviewRequest(BaseModel):
    """API request for PR review."""

    pr_id: int | None = Field(None, description="GitHub PR ID")
    repo: str | None = Field(None, description="Repository in format owner/repo")
    diff: str | None = Field(None, description="Raw diff string (for manual input)")

    def validate_input(self) -> bool:
        """Validate that either pr_id+repo or diff is provided."""
        has_pr = self.pr_id is not None and self.repo is not None
        has_diff = self.diff is not None and len(self.diff.strip()) > 0
        return has_pr or has_diff


class ReviewResponse(BaseModel):
    """API response with review results."""

    pr_id: int | None = Field(None, description="GitHub PR ID")
    repo: str | None = Field(None, description="Repository name")
    comments: list[ReviewComment] = Field(default_factory=list, description="Review comments")
    total_issues: int = Field(default=0, description="Total number of issues found")
    critical_count: int = Field(default=0, description="Number of critical issues")
    warning_count: int = Field(default=0, description="Number of warnings")
    info_count: int = Field(default=0, description="Number of info items")

    def __init__(self, **data):
        """Initialize and calculate counts."""
        super().__init__(**data)
        if self.comments:
            self.total_issues = len(self.comments)
            self.critical_count = sum(1 for c in self.comments if c.severity == Severity.CRITICAL)
            self.warning_count = sum(1 for c in self.comments if c.severity == Severity.WARNING)
            self.info_count = sum(1 for c in self.comments if c.severity == Severity.INFO)

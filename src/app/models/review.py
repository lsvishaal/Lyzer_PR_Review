"""Review-related models for comments and responses."""

from pydantic import BaseModel, Field, field_validator, model_validator

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
    """API request for PR review.

    Must provide EITHER:
    - pr_id + repo (for GitHub PR review)
    - diff (for manual diff review)
    """

    pr_id: int | None = Field(None, description="GitHub PR ID", gt=0)
    repo: str | None = Field(
        None,
        description="Repository in format owner/repo",
        pattern=r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$",
    )
    diff: str | None = Field(
        None, description="Raw diff string (for manual input)", max_length=500000
    )  # 500KB limit

    @field_validator("diff")
    @classmethod
    def validate_diff_not_empty(cls, v: str | None) -> str | None:
        """Ensure diff is not just whitespace."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Diff cannot be empty or only whitespace")
        return v

    @field_validator("repo")
    @classmethod
    def validate_repo_format(cls, v: str | None) -> str | None:
        """Validate repository format."""
        if v is not None:
            if "/" not in v:
                raise ValueError("Repository must be in format 'owner/repo'")
            owner, repo = v.split("/", 1)
            if not owner or not repo:
                raise ValueError("Repository must have both owner and repo name")
        return v

    @model_validator(mode="after")
    def validate_input_combination(self) -> "ReviewRequest":
        """Validate that either pr_id+repo or diff is provided, but not both."""
        has_pr = self.pr_id is not None and self.repo is not None
        has_diff = self.diff is not None

        if has_pr and has_diff:
            raise ValueError("Provide either 'pr_id' + 'repo' OR 'diff', not both")

        if not has_pr and not has_diff:
            raise ValueError(
                "Must provide either 'pr_id' + 'repo' for GitHub PR review, "
                "or 'diff' for manual diff review"
            )

        if self.pr_id is not None and self.repo is None:
            raise ValueError("'pr_id' requires 'repo' to be specified")

        if self.repo is not None and self.pr_id is None:
            raise ValueError("'repo' requires 'pr_id' to be specified")

        return self

    def validate_input(self) -> bool:
        """Legacy method for backwards compatibility."""
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
    ignored_files: list[str] = Field(
        default_factory=list, description="Files ignored (binary or unsupported language)"
    )

    def __init__(self, **data):
        """Initialize and calculate counts."""
        super().__init__(**data)
        if self.comments:
            self.total_issues = len(self.comments)
            self.critical_count = sum(1 for c in self.comments if c.severity == Severity.CRITICAL)
            self.warning_count = sum(1 for c in self.comments if c.severity == Severity.WARNING)
            self.info_count = sum(1 for c in self.comments if c.severity == Severity.INFO)

"""Code-related models for diff parsing and code chunks."""

from pydantic import BaseModel, Field

from .base import Language


class CodeChunk(BaseModel):
    """A section of code that changed in a PR."""

    file_path: str = Field(..., description="Path to the file")
    language: Language = Field(default=Language.UNKNOWN, description="Programming language")
    original_lines: list[str] = Field(default_factory=list, description="Original code lines")
    new_lines: list[str] = Field(default_factory=list, description="New code lines")
    start_line: int = Field(..., description="Starting line number")
    end_line: int | None = Field(None, description="Ending line number")

    @property
    def line_count(self) -> int:
        """Number of new lines in this chunk."""
        return len(self.new_lines)

    @property
    def is_addition(self) -> bool:
        """Check if this chunk is a pure addition."""
        return len(self.original_lines) == 0 and len(self.new_lines) > 0

    @property
    def is_deletion(self) -> bool:
        """Check if this chunk is a pure deletion."""
        return len(self.original_lines) > 0 and len(self.new_lines) == 0

    @property
    def is_modification(self) -> bool:
        """Check if this chunk is a modification."""
        return len(self.original_lines) > 0 and len(self.new_lines) > 0


class FileDiff(BaseModel):
    """Represents changes to a single file in a PR."""

    file_path: str = Field(..., description="Path to the file")
    language: Language = Field(default=Language.UNKNOWN, description="Programming language")
    status: str = Field(..., description="File status: added, modified, deleted")
    additions: int = Field(default=0, description="Number of lines added")
    deletions: int = Field(default=0, description="Number of lines deleted")
    chunks: list[CodeChunk] = Field(default_factory=list, description="Code chunks that changed")
    raw_diff: str = Field(default="", description="Raw diff string")

    @property
    def total_changes(self) -> int:
        """Total number of changes (additions + deletions)."""
        return self.additions + self.deletions

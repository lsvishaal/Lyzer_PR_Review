"""Base models and enums for the PR review system."""

from enum import Enum


class Severity(str, Enum):
    """Severity levels for review comments."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ReviewCategory(str, Enum):
    """Categories of code review feedback."""

    LOGIC = "logic"
    READABILITY = "readability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    BEST_PRACTICES = "best_practices"


class Language(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    RUBY = "ruby"
    PHP = "php"
    UNKNOWN = "unknown"

from __future__ import annotations

import json

from src.app.agents.base import BaseAgent
from src.app.core.logging_config import get_logger
from src.app.models.base import Severity
from src.app.models.code import CodeChunk
from src.app.models.review import ReviewComment

logger = get_logger(__name__)


class ReadabilityAgent(BaseAgent):
    """Agent focusing on naming, structure, and documentation."""

    def __init__(self, llm: object) -> None:
        super().__init__(name="readability")
        self._llm = llm

    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Analyze code chunk for readability and maintainability issues."""
        if not chunk.new_lines or len(chunk.new_lines) == 0:
            return []

        prompt = self._build_prompt(chunk)

        try:
            response = await self._llm.generate(prompt, temperature=0.2, max_tokens=800)
            return self._parse_response(response, chunk)
        except Exception as e:
            logger.error("readability_agent_error", error=str(e), file=chunk.file_path)
            return []

    def _build_prompt(self, chunk: CodeChunk) -> str:
        """Build readability analysis prompt."""
        code_context = "\n".join(chunk.new_lines)

        prompt = f"""You are an expert code reviewer specializing in readability and maintainability. Analyze the following code for clarity, naming, and structure.

FILE: {chunk.file_path}
LANGUAGE: {chunk.language.value if chunk.language else "unknown"}
LINES: {chunk.start_line} - {chunk.start_line + len(chunk.new_lines) - 1}

CODE TO REVIEW:
```
{code_context}
```

Focus on:
1. **Naming** - unclear variable/function names, inconsistent naming conventions
2. **Function length** - functions that are too long or do too many things
3. **Complexity** - deeply nested code, complex conditionals
4. **Comments** - missing docstrings, outdated comments, over-commenting
5. **Code organization** - poor structure, duplicate code
6. **Magic numbers** - hardcoded values without explanation

For each issue found, return a JSON array with this exact structure:
[
  {{
    "line": <line_number_relative_to_chunk>,
    "severity": "warning" | "info",
    "message": "<clear description of the readability issue>",
    "suggestion": "<specific improvement recommendation>"
  }}
]

If no issues found, return: []

IMPORTANT: Return ONLY valid JSON, no markdown, no explanations."""

        return prompt

    def _parse_response(self, response: str, chunk: CodeChunk) -> list[ReviewComment]:
        """Parse LLM JSON response into ReviewComment objects."""
        if not response or not response.strip():
            return []

        # Clean up response
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(line for line in lines if not line.strip().startswith("```"))

        try:
            issues = json.loads(cleaned.strip())
            if not isinstance(issues, list):
                logger.warning("readability_agent_invalid_format", file=chunk.file_path)
                return []

            comments = []
            for issue in issues:
                try:
                    relative_line = issue.get("line", 0)
                    absolute_line = chunk.start_line + relative_line - 1

                    severity_str = issue.get("severity", "info").lower()
                    severity = (
                        Severity(severity_str)
                        if severity_str in ["warning", "info"]
                        else Severity.INFO
                    )

                    comment = ReviewComment(
                        file_path=chunk.file_path,
                        line_number=absolute_line,
                        severity=severity,
                        category="readability",  # type: ignore[arg-type]
                        message=issue.get("message", "Readability issue detected"),
                        suggestion=issue.get("suggestion"),
                        agent_name=self.name,
                    )
                    comments.append(comment)
                except (ValueError, KeyError) as e:
                    logger.warning("readability_agent_parse_issue", error=str(e), issue=issue)
                    continue

            return comments

        except json.JSONDecodeError as e:
            logger.warning("readability_agent_json_error", error=str(e), response=response[:200])
            return []

from __future__ import annotations

import json

from src.app.agents.base import BaseAgent
from src.app.core.logging_config import get_logger
from src.app.models.base import Severity
from src.app.models.code import CodeChunk
from src.app.models.review import ReviewComment

logger = get_logger(__name__)


class SecurityAgent(BaseAgent):
    """Agent detecting security issues and vulnerabilities."""

    def __init__(self, llm: object) -> None:
        super().__init__(name="security")
        self._llm = llm

    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Analyze code chunk for security vulnerabilities."""
        if not chunk.new_lines or len(chunk.new_lines) == 0:
            return []

        prompt = self._build_prompt(chunk)

        try:
            response = await self._llm.generate(prompt, temperature=0.1, max_tokens=800)
            return self._parse_response(response, chunk)
        except Exception as e:
            logger.error("security_agent_error", error=str(e), file=chunk.file_path)
            return []

    def _build_prompt(self, chunk: CodeChunk) -> str:
        """Build security analysis prompt with OWASP and CWE references."""
        code_context = "\n".join(chunk.new_lines)

        prompt = f"""You are an expert security code reviewer. Analyze the following code for security vulnerabilities using OWASP Top 10 and CWE standards.

FILE: {chunk.file_path}
LANGUAGE: {chunk.language.value if chunk.language else "unknown"}
LINES: {chunk.start_line} - {chunk.start_line + len(chunk.new_lines) - 1}

CODE TO REVIEW:
```
{code_context}
```

Focus on:
1. **Injection** - SQL injection, command injection, code injection (OWASP A03)
2. **Authentication** - weak auth, missing verification, password issues (OWASP A07)
3. **Sensitive data** - hardcoded secrets, exposed credentials, logging sensitive info (OWASP A02)
4. **Access control** - missing authorization checks, privilege escalation (OWASP A01)
5. **Cryptography** - weak algorithms, poor key management, insecure random (OWASP A02)
6. **Input validation** - unvalidated input, missing sanitization (CWE-20)
7. **XSS/CSRF** - cross-site scripting, cross-site request forgery (OWASP A03)

For each security issue found, return a JSON array with this exact structure:
[
  {{
    "line": <line_number_relative_to_chunk>,
    "severity": "critical" | "warning",
    "message": "<clear description of the security vulnerability>",
    "suggestion": "<specific remediation recommendation>"
  }}
]

If no issues found, return: []

IMPORTANT: Return ONLY valid JSON, no markdown, no explanations."""

        return prompt

    def _parse_response(self, response: str, chunk: CodeChunk) -> list[ReviewComment]:
        """Parse LLM JSON response into ReviewComment objects."""
        if not response or not response.strip():
            return []

        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(line for line in lines if not line.strip().startswith("```"))

        try:
            issues = json.loads(cleaned.strip())
            if not isinstance(issues, list):
                logger.warning("security_agent_invalid_format", file=chunk.file_path)
                return []

            comments = []
            for issue in issues:
                try:
                    relative_line = issue.get("line", 0)
                    absolute_line = chunk.start_line + relative_line - 1

                    severity_str = issue.get("severity", "warning").lower()
                    severity = (
                        Severity(severity_str)
                        if severity_str in ["critical", "warning"]
                        else Severity.WARNING
                    )

                    comment = ReviewComment(
                        file_path=chunk.file_path,
                        line_number=absolute_line,
                        severity=severity,
                        category="security",  # type: ignore[arg-type]
                        message=issue.get("message", "Security issue detected"),
                        suggestion=issue.get("suggestion"),
                        agent_name=self.name,
                    )
                    comments.append(comment)
                except (ValueError, KeyError) as e:
                    logger.warning("security_agent_parse_issue", error=str(e), issue=issue)
                    continue

            return comments

        except json.JSONDecodeError as e:
            logger.warning("security_agent_json_error", error=str(e), response=response[:200])
            return []

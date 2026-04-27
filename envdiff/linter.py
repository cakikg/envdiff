"""Lint .env files for common style and correctness issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class LintIssue:
    line: int
    key: str | None
    message: str
    severity: str  # 'error' | 'warning'

    def __str__(self) -> str:
        location = f"line {self.line}" + (f" ({self.key})" if self.key else "")
        return f"[{self.severity.upper()}] {location}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)


def lint_env_file(path: str) -> LintResult:
    """Lint a single .env file and return a LintResult."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        if not line or line.lstrip().startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(
                LintIssue(lineno, None, "Line is not a valid KEY=VALUE pair", "error")
            )
            continue

        key, _, value = line.partition("=")

        if key != key.strip():
            result.issues.append(
                LintIssue(lineno, key.strip(), "Key has leading or trailing whitespace", "warning")
            )
            key = key.strip()

        if not key:
            result.issues.append(
                LintIssue(lineno, None, "Empty key detected", "error")
            )
            continue

        if not key.replace("_", "").isalnum() or key[0].isdigit():
            result.issues.append(
                LintIssue(lineno, key, "Key contains invalid characters or starts with a digit", "warning")
            )

        if key in seen_keys:
            result.issues.append(
                LintIssue(
                    lineno, key,
                    f"Duplicate key (first seen on line {seen_keys[key]})",
                    "error",
                )
            )
        else:
            seen_keys[key] = lineno

        if value != value.strip() and not (value.startswith('"') or value.startswith("'")):
            result.issues.append(
                LintIssue(lineno, key, "Value has unquoted leading or trailing whitespace", "warning")
            )

    return result

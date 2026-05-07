"""Block deployment when required keys are absent or values match forbidden patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.core import parse_env_file


@dataclass
class BlockRule:
    key: str
    required: bool = True
    forbidden_pattern: Optional[str] = None  # regex applied to value


@dataclass
class BlockViolation:
    key: str
    reason: str

    def to_dict(self) -> dict:
        return {"key": self.key, "reason": self.reason}


@dataclass
class BlockReport:
    file: str
    violations: List[BlockViolation] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "clean": self.clean,
            "violations": [v.to_dict() for v in self.violations],
        }


def check_env_file(
    path: Path,
    rules: List[BlockRule],
    env: Optional[Dict[str, str]] = None,
) -> BlockReport:
    """Evaluate *rules* against the .env file at *path*.

    *env* may supply additional key/value pairs (e.g. from the process
    environment) that are merged with the file contents before checking.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    parsed: Dict[str, str] = parse_env_file(path)
    if env:
        parsed = {**env, **parsed}

    violations: List[BlockViolation] = []

    for rule in rules:
        value = parsed.get(rule.key)

        if rule.required and value is None:
            violations.append(
                BlockViolation(key=rule.key, reason="required key is missing")
            )
            continue

        if rule.forbidden_pattern and value is not None:
            if re.search(rule.forbidden_pattern, value):
                violations.append(
                    BlockViolation(
                        key=rule.key,
                        reason=f"value matches forbidden pattern '{rule.forbidden_pattern}'",
                    )
                )

    return BlockReport(file=str(path), violations=violations)

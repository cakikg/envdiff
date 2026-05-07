"""sanitizer.py – strip or replace sensitive values in .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.redactor import Redactor

_PLACEHOLDER = "REDACTED"


@dataclass
class SanitizeResult:
    file: str
    sanitized_keys: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.sanitized_keys) > 0

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "changed": self.changed,
            "sanitized_keys": self.sanitized_keys,
        }

    def content(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines else "")


def sanitize_env_file(
    path: Path,
    placeholder: str = _PLACEHOLDER,
    extra_patterns: Optional[List[str]] = None,
    write: bool = False,
) -> SanitizeResult:
    """Replace sensitive values with *placeholder* in *path*.

    Args:
        path: Path to the .env file.
        placeholder: Replacement string for sensitive values.
        extra_patterns: Additional key-name substrings to treat as sensitive.
        write: If True, overwrite the file with sanitized content.

    Returns:
        A :class:`SanitizeResult` describing what changed.
    """
    redactor = Redactor(extra_patterns=extra_patterns or [])
    result = SanitizeResult(file=str(path))

    raw = Path(path).read_text(encoding="utf-8")
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            result.lines.append(line)
            continue
        if "=" not in stripped:
            result.lines.append(line)
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if redactor.is_sensitive(key) and value:
            result.lines.append(f"{key}={placeholder}")
            result.sanitized_keys.append(key)
        else:
            result.lines.append(line)

    if write and result.changed:
        Path(path).write_text(result.content(), encoding="utf-8")

    return result

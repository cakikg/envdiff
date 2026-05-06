"""Normalize .env file values: strip quotes, fix spacing, unify booleans."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from envdiff.tokenizer import tokenize_lines, TokenKind

_BOOL_TRUE = {"true", "yes", "1", "on"}
_BOOL_FALSE = {"false", "no", "0", "off"}


@dataclass
class NormalizeResult:
    path: Path
    original_lines: List[str]
    normalized_lines: List[str]
    changes: List[Tuple[int, str, str]] = field(default_factory=list)  # (lineno, before, after)

    @property
    def changed(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "changed": self.changed,
            "changes": [
                {"line": lineno, "before": before, "after": after}
                for lineno, before, after in self.changes
            ],
        }


def _normalize_value(raw: str) -> str:
    """Strip surrounding quotes and normalize boolean literals."""
    stripped = raw.strip()
    # Remove surrounding single or double quotes
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ('"', "'"):
        stripped = stripped[1:-1]
    # Normalize boolean
    lower = stripped.lower()
    if lower in _BOOL_TRUE:
        return "true"
    if lower in _BOOL_FALSE:
        return "false"
    return stripped


def _normalize_line(line: str) -> str:
    """Return a normalized version of an assignment line, or the original."""
    tokens = tokenize_lines([line])
    if not tokens or tokens[0].kind != TokenKind.ASSIGNMENT:
        return line
    token = tokens[0]
    key = token.key.strip()
    value = _normalize_value(token.value)
    return f"{key}={value}\n" if line.endswith("\n") else f"{key}={value}"


def normalize_env_file(path: Path, *, write: bool = False) -> NormalizeResult:
    """Normalize all assignment lines in *path*.

    Parameters
    ----------
    path:
        The .env file to normalize.
    write:
        When *True* the file is overwritten with the normalized content.
    """
    original_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    normalized_lines: List[str] = []
    changes: List[Tuple[int, str, str]] = []

    for i, line in enumerate(original_lines, start=1):
        normalized = _normalize_line(line)
        normalized_lines.append(normalized)
        if normalized != line:
            changes.append((i, line.rstrip("\n"), normalized.rstrip("\n")))

    result = NormalizeResult(
        path=path,
        original_lines=original_lines,
        normalized_lines=normalized_lines,
        changes=changes,
    )

    if write and result.changed:
        path.write_text("".join(normalized_lines), encoding="utf-8")

    return result

"""masker.py – selectively mask values in a .env file for safe sharing.

Replaces values of sensitive keys with a configurable mask string while
leaving non-sensitive keys untouched.  The result can be written back to
disk or returned as a string for display purposes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.redactor import Redactor
from envdiff.tokenizer import tokenize_line, TokenKind

_DEFAULT_MASK = "***"


@dataclass
class MaskResult:
    file: str
    masked_keys: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.masked_keys) > 0

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "masked_keys": self.masked_keys,
            "changed": self.changed,
        }

    def content(self) -> str:
        return "\n".join(self.lines)


def mask_env_file(
    path: Path,
    *,
    mask: str = _DEFAULT_MASK,
    extra_patterns: Optional[List[str]] = None,
    write: bool = False,
) -> MaskResult:
    """Read *path*, mask sensitive values, and optionally write it back.

    Parameters
    ----------
    path:
        The .env file to process.
    mask:
        Replacement string for sensitive values (default ``"***"``).
    extra_patterns:
        Additional glob-style key patterns treated as sensitive.
    write:
        When *True* the masked content is written back to *path*.
    """
    redactor = Redactor(extra_patterns=extra_patterns or [])
    raw_lines = Path(path).read_text().splitlines()
    out_lines: List[str] = []
    masked_keys: List[str] = []

    for raw in raw_lines:
        token = tokenize_line(raw)
        if token.kind is TokenKind.ASSIGNMENT and redactor.is_sensitive(token.key):  # type: ignore[arg-type]
            # Preserve any inline comment after the value
            comment_part = ""
            if token.comment:  # type: ignore[attr-defined]
                comment_part = f"  # {token.comment}"  # type: ignore[attr-defined]
            out_lines.append(f"{token.key}={mask}{comment_part}")  # type: ignore[attr-defined]
            masked_keys.append(token.key)  # type: ignore[attr-defined]
        else:
            out_lines.append(raw)

    result = MaskResult(file=str(path), masked_keys=masked_keys, lines=out_lines)

    if write:
        Path(path).write_text(result.content() + "\n")

    return result

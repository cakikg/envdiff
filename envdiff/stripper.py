"""Strip comments and blank lines from .env files, optionally in-place."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


@dataclass
class StripResult:
    file: str
    original_lines: int
    stripped_lines: int
    removed_comments: int
    removed_blanks: int
    content: str

    @property
    def changed(self) -> bool:
        return self.original_lines != self.stripped_lines

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "original_lines": self.original_lines,
            "stripped_lines": self.stripped_lines,
            "removed_comments": self.removed_comments,
            "removed_blanks": self.removed_blanks,
            "changed": self.changed,
        }


def _classify_line(line: str) -> str:
    """Return 'comment', 'blank', or 'keep'."""
    stripped = line.strip()
    if not stripped:
        return "blank"
    if stripped.startswith("#"):
        return "comment"
    return "keep"


def strip_env_file(
    path: Path,
    *,
    remove_comments: bool = True,
    remove_blanks: bool = True,
    write: bool = False,
) -> StripResult:
    """Strip comments and/or blank lines from *path*.

    Parameters
    ----------
    path:
        Path to the .env file.
    remove_comments:
        When *True* (default) lines that are pure comments are removed.
    remove_blanks:
        When *True* (default) blank / whitespace-only lines are removed.
    write:
        When *True* the result is written back to *path* in-place.
    """
    raw = Path(path).read_text(encoding="utf-8")
    lines: List[str] = raw.splitlines(keepends=True)

    kept: List[str] = []
    n_comments = 0
    n_blanks = 0

    for line in lines:
        kind = _classify_line(line)
        if kind == "comment" and remove_comments:
            n_comments += 1
        elif kind == "blank" and remove_blanks:
            n_blanks += 1
        else:
            kept.append(line)

    content = "".join(kept)

    if write:
        Path(path).write_text(content, encoding="utf-8")

    return StripResult(
        file=str(path),
        original_lines=len(lines),
        stripped_lines=len(kept),
        removed_comments=n_comments,
        removed_blanks=n_blanks,
        content=content,
    )

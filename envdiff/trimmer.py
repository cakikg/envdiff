"""trimmer.py – strip trailing whitespace and normalize quoting in .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

_QUOTED_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)=([\'"])(.*)(\2)\s*$')
_PLAIN_RE  = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$')


@dataclass
class TrimResult:
    path: str
    original_lines: List[str]
    trimmed_lines: List[str]
    changes: List[Tuple[int, str, str]] = field(default_factory=list)  # (lineno, before, after)

    @property
    def changed(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "changed": self.changed,
            "change_count": len(self.changes),
            "changes": [
                {"line": lineno, "before": before, "after": after}
                for lineno, before, after in self.changes
            ],
        }


def _trim_line(line: str) -> str:
    """Return line with trailing whitespace removed from value portion."""
    # Preserve newline character if present
    nl = "\n" if line.endswith("\n") else ""
    raw = line.rstrip("\n")

    m_quoted = _QUOTED_RE.match(raw)
    if m_quoted:
        key, quote, value, _ = m_quoted.groups()
        return f"{key}={quote}{value.rstrip()}{quote}{nl}"

    m_plain = _PLAIN_RE.match(raw)
    if m_plain:
        key, value = m_plain.groups()
        return f"{key}={value.rstrip()}{nl}"

    # Comment or blank line – just strip trailing whitespace
    return raw.rstrip() + nl


def trim_env_file(path: str | Path, *, dry_run: bool = False) -> TrimResult:
    """Trim trailing whitespace from every value in *path*.

    Parameters
    ----------
    path:
        Path to the .env file.
    dry_run:
        When *True* the file is not written; only the diff is returned.
    """
    p = Path(path)
    original_lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    trimmed_lines: List[str] = []
    changes: List[Tuple[int, str, str]] = []

    for i, line in enumerate(original_lines, start=1):
        trimmed = _trim_line(line)
        trimmed_lines.append(trimmed)
        if trimmed != line:
            changes.append((i, line, trimmed))

    result = TrimResult(
        path=str(p),
        original_lines=original_lines,
        trimmed_lines=trimmed_lines,
        changes=changes,
    )

    if not dry_run and result.changed:
        p.write_text("".join(trimmed_lines), encoding="utf-8")

    return result

"""Remove duplicate keys from a .env file, keeping the last occurrence."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


@dataclass
class DeduplicateResult:
    file: str
    removed: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.removed) > 0

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "changed": self.changed,
            "removed_keys": self.removed,
        }


def _parse_key(line: str) -> str | None:
    """Return the key name if *line* is an assignment, else None."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        return None
    return stripped.split("=", 1)[0].strip()


def deduplicate_env_file(
    path: str | Path,
    *,
    keep: str = "last",
    dry_run: bool = False,
) -> DeduplicateResult:
    """Deduplicate keys in *path*.

    Parameters
    ----------
    keep:
        ``'last'`` (default) keeps the final assignment; ``'first'`` keeps the
        first assignment and discards later duplicates.
    dry_run:
        When *True* the file is not written.
    """
    if keep not in {"first", "last"}:
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    path = Path(path)
    raw_lines: List[str] = path.read_text(encoding="utf-8").splitlines(keepends=True)

    # Collect (line_index, key) for every assignment line
    assignments: List[Tuple[int, str]] = []
    for idx, line in enumerate(raw_lines):
        key = _parse_key(line)
        if key is not None:
            assignments.append((idx, key))

    # Determine which indices to drop
    seen: dict[str, int] = {}  # key -> index to keep
    for idx, key in assignments:
        if keep == "last":
            seen[key] = idx  # overwrite — last wins
        else:  # first
            seen.setdefault(key, idx)

    keep_indices = set(seen.values())
    dropped_keys: List[str] = []
    out_lines: List[str] = []

    for idx, line in enumerate(raw_lines):
        key = _parse_key(line)
        if key is not None and idx not in keep_indices:
            dropped_keys.append(key)
        else:
            out_lines.append(line)

    if not dry_run and dropped_keys:
        path.write_text("".join(out_lines), encoding="utf-8")

    return DeduplicateResult(file=str(path), removed=dropped_keys, lines=out_lines)

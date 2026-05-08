"""Highlight changed keys between two env file snapshots or versions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.core import parse_env_file


@dataclass
class HighlightEntry:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    status: str  # 'added' | 'removed' | 'changed' | 'unchanged'

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "status": self.status,
        }


@dataclass
class HighlightReport:
    file_a: str
    file_b: str
    entries: List[HighlightEntry] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(e.status != "unchanged" for e in self.entries)

    @property
    def added(self) -> List[HighlightEntry]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[HighlightEntry]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def modified(self) -> List[HighlightEntry]:
        return [e for e in self.entries if e.status == "changed"]

    def to_dict(self) -> dict:
        return {
            "file_a": self.file_a,
            "file_b": self.file_b,
            "changed": self.changed,
            "added": len(self.added),
            "removed": len(self.removed),
            "modified": len(self.modified),
            "entries": [e.to_dict() for e in self.entries],
        }


def highlight_env_files(
    path_a: Path,
    path_b: Path,
    include_unchanged: bool = False,
) -> HighlightReport:
    """Compare two env files and return a HighlightReport."""
    env_a: Dict[str, str] = parse_env_file(path_a)
    env_b: Dict[str, str] = parse_env_file(path_b)
    all_keys = sorted(set(env_a) | set(env_b))

    entries: List[HighlightEntry] = []
    for key in all_keys:
        in_a = key in env_a
        in_b = key in env_b
        if in_a and in_b:
            if env_a[key] == env_b[key]:
                if include_unchanged:
                    entries.append(HighlightEntry(key, env_a[key], env_b[key], "unchanged"))
            else:
                entries.append(HighlightEntry(key, env_a[key], env_b[key], "changed"))
        elif in_a:
            entries.append(HighlightEntry(key, env_a[key], None, "removed"))
        else:
            entries.append(HighlightEntry(key, None, env_b[key], "added"))

    return HighlightReport(
        file_a=str(path_a),
        file_b=str(path_b),
        entries=entries,
    )

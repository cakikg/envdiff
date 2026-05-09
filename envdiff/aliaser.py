"""aliaser.py – manage key aliases across .env files.

An alias maps an old key name to a new canonical key name so that
legacy keys can be detected and reported without breaking anything.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class AliasEntry:
    old_key: str
    new_key: str
    files_affected: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "old_key": self.old_key,
            "new_key": self.new_key,
            "files_affected": self.files_affected,
        }


@dataclass
class AliasReport:
    hits: List[AliasEntry] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.hits) == 0

    def to_dict(self) -> dict:
        return {
            "clean": self.clean,
            "hits": [h.to_dict() for h in self.hits],
        }


def load_aliases(alias_file: str | Path) -> Dict[str, str]:
    """Load alias mapping from a JSON file {old_key: new_key}."""
    path = Path(alias_file)
    if not path.exists():
        raise FileNotFoundError(f"Alias file not found: {path}")
    with path.open() as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Alias file must be a JSON object mapping old keys to new keys.")
    return {str(k): str(v) for k, v in data.items()}


def check_aliases(
    env_files: List[str | Path],
    aliases: Dict[str, str],
) -> AliasReport:
    """Scan env_files for deprecated alias keys and return a report."""
    from envdiff.core import parse_env_file

    # Build a reverse index: old_key -> entry
    entries: Dict[str, AliasEntry] = {
        old: AliasEntry(old_key=old, new_key=new)
        for old, new in aliases.items()
    }

    for env_path in env_files:
        parsed = parse_env_file(str(env_path))
        for old_key, entry in entries.items():
            if old_key in parsed:
                entry.files_affected.append(str(env_path))

    hits = [e for e in entries.values() if e.files_affected]
    return AliasReport(hits=hits)

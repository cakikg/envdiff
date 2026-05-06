"""Tag keys in a .env file with arbitrary labels stored in a sidecar JSON file."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _tag_path(env_path: Path) -> Path:
    return env_path.with_suffix(".tags.json")


@dataclass
class TagResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)

    def to_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "unchanged": self.unchanged,
            "changed": self.changed,
        }


def load_tags(env_path: Path) -> Dict[str, List[str]]:
    """Load the tag map for *env_path*. Returns {} when no sidecar exists."""
    tag_file = _tag_path(env_path)
    if not tag_file.exists():
        return {}
    data = json.loads(tag_file.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{tag_file} must contain a JSON object")
    return {k: list(v) for k, v in data.items()}


def save_tags(env_path: Path, tags: Dict[str, List[str]]) -> None:
    """Persist *tags* to the sidecar file next to *env_path*."""
    _tag_path(env_path).write_text(json.dumps(tags, indent=2) + "\n")


def tag_key(
    env_path: Path,
    key: str,
    label: str,
    *,
    dry_run: bool = False,
) -> TagResult:
    """Add *label* to *key*. Returns a TagResult describing what changed."""
    tags = load_tags(env_path)
    existing = tags.get(key, [])
    if label in existing:
        return TagResult(unchanged=[key])
    updated = existing + [label]
    tags[key] = updated
    if not dry_run:
        save_tags(env_path, tags)
    return TagResult(added=[key])


def untag_key(
    env_path: Path,
    key: str,
    label: Optional[str] = None,
    *,
    dry_run: bool = False,
) -> TagResult:
    """Remove *label* from *key*, or all labels when *label* is None."""
    tags = load_tags(env_path)
    if key not in tags:
        return TagResult(unchanged=[key])
    if label is None:
        del tags[key]
    else:
        remaining = [t for t in tags[key] if t != label]
        if remaining:
            tags[key] = remaining
        else:
            del tags[key]
    if not dry_run:
        save_tags(env_path, tags)
    return TagResult(removed=[key])


def keys_with_label(env_path: Path, label: str) -> List[str]:
    """Return every key that carries *label*."""
    return [k for k, labels in load_tags(env_path).items() if label in labels]

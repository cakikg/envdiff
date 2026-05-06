"""Detect and report deprecated keys in .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.core import parse_env_file


@dataclass
class DeprecationEntry:
    key: str
    reason: str
    replacement: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "reason": self.reason,
            "replacement": self.replacement,
        }


@dataclass
class DeprecationReport:
    file: str
    hits: List[DeprecationEntry] = field(default_factory=list)
    total_keys: int = 0

    @property
    def clean(self) -> bool:
        return len(self.hits) == 0

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "clean": self.clean,
            "total_keys": self.total_keys,
            "hits": [h.to_dict() for h in self.hits],
        }


def check_deprecations(
    env_path: Path,
    deprecated: Dict[str, Dict[str, str]],
) -> DeprecationReport:
    """Scan *env_path* for keys listed in *deprecated*.

    *deprecated* maps key names to dicts with at least a ``reason`` field and
    an optional ``replacement`` field, e.g.::

        {
            "OLD_API_KEY": {"reason": "renamed", "replacement": "API_KEY"},
            "LEGACY_MODE": {"reason": "feature removed"},
        }
    """
    env = parse_env_file(env_path)
    report = DeprecationReport(file=str(env_path), total_keys=len(env))
    for key, meta in deprecated.items():
        if key in env:
            report.hits.append(
                DeprecationEntry(
                    key=key,
                    reason=meta.get("reason", "deprecated"),
                    replacement=meta.get("replacement"),
                )
            )
    return report

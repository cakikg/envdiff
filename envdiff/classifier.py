"""Classify .env keys by inferred value type and sensitivity tier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.core import parse_env_file
from envdiff.redactor import Redactor

_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "on", "off"}
_URL_SCHEMES = ("http://", "https://", "ftp://", "redis://", "postgres://",
                "postgresql://", "mysql://", "mongodb://", "amqp://")


def _infer_type(value: str) -> str:
    if value.lower() in _BOOL_VALUES:
        return "bool"
    try:
        int(value)
        return "int"
    except ValueError:
        pass
    try:
        float(value)
        return "float"
    except ValueError:
        pass
    low = value.lower()
    if any(low.startswith(s) for s in _URL_SCHEMES):
        return "url"
    if not value:
        return "empty"
    return "string"


@dataclass
class ClassifyReport:
    file: str
    by_type: Dict[str, List[str]] = field(default_factory=dict)
    by_tier: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "by_type": self.by_type,
            "by_tier": self.by_tier,
        }


def classify_env_file(path: str) -> ClassifyReport:
    """Parse *path* and classify every key by type and sensitivity tier."""
    env = parse_env_file(path)
    redactor = Redactor()

    by_type: Dict[str, List[str]] = {}
    by_tier: Dict[str, List[str]] = {}

    for key, value in env.items():
        # --- type bucket ---
        t = _infer_type(value)
        by_type.setdefault(t, []).append(key)

        # --- sensitivity tier ---
        if redactor.is_sensitive(key):
            tier = "sensitive"
        elif t in ("url",):
            tier = "connection"
        elif t in ("int", "float", "bool"):
            tier = "config"
        else:
            tier = "general"
        by_tier.setdefault(tier, []).append(key)

    # sort lists for deterministic output
    for bucket in (by_type, by_tier):
        for lst in bucket.values():
            lst.sort()

    return ClassifyReport(file=path, by_type=by_type, by_tier=by_tier)

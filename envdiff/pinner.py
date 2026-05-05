"""Pin current .env values to a lock file for drift detection."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

DEFAULT_LOCK_NAME = ".env.lock"


@dataclass
class PinEntry:
    key: str
    checksum: str  # sha256 of value

    def to_dict(self) -> dict:
        return {"key": self.key, "checksum": self.checksum}

    @staticmethod
    def from_dict(d: dict) -> "PinEntry":
        return PinEntry(key=d["key"], checksum=d["checksum"])


@dataclass
class DriftReport:
    added: List[str] = field(default_factory=list)    # in env, not in lock
    removed: List[str] = field(default_factory=list)  # in lock, not in env
    changed: List[str] = field(default_factory=list)  # checksum mismatch

    @property
    def clean(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def to_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "clean": self.clean,
        }


def _checksum(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def pin_env(env: Dict[str, str], lock_path: Path) -> None:
    """Write a lock file capturing checksums of all env values."""
    entries = [
        PinEntry(key=k, checksum=_checksum(v)).to_dict()
        for k, v in sorted(env.items())
    ]
    lock_path.write_text(json.dumps({"pins": entries}, indent=2))


def load_pins(lock_path: Path) -> Dict[str, str]:
    """Return {key: checksum} from an existing lock file."""
    if not lock_path.exists():
        raise FileNotFoundError(f"Lock file not found: {lock_path}")
    data = json.loads(lock_path.read_text())
    return {e["key"]: e["checksum"] for e in data.get("pins", [])}


def detect_drift(env: Dict[str, str], lock_path: Path) -> DriftReport:
    """Compare current env against pinned checksums and return a DriftReport."""
    pinned = load_pins(lock_path)
    current = {k: _checksum(v) for k, v in env.items()}

    report = DriftReport()
    for key in current:
        if key not in pinned:
            report.added.append(key)
        elif current[key] != pinned[key]:
            report.changed.append(key)
    for key in pinned:
        if key not in current:
            report.removed.append(key)

    report.added.sort()
    report.removed.sort()
    report.changed.sort()
    return report

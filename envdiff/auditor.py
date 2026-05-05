"""Audit trail: record and replay env diff operations."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_AUDIT_DIR = Path(".envdiff_audit")


@dataclass
class AuditEntry:
    operation: str
    files: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user: str = field(default_factory=lambda: os.environ.get("USER", "unknown"))
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        return cls(
            operation=data["operation"],
            files=data["files"],
            timestamp=data.get("timestamp", ""),
            user=data.get("user", "unknown"),
            details=data.get("details", {}),
        )


def _audit_path(audit_dir: Path, operation: str, timestamp: str) -> Path:
    safe_ts = timestamp.replace(":", "-").replace("+", "Z")
    return audit_dir / f"{operation}_{safe_ts}.json"


def record(entry: AuditEntry, audit_dir: Path = _DEFAULT_AUDIT_DIR) -> Path:
    """Persist an audit entry to disk; returns the path written."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    path = _audit_path(audit_dir, entry.operation, entry.timestamp)
    path.write_text(json.dumps(entry.to_dict(), indent=2))
    return path


def load_entry(path: Path) -> AuditEntry:
    """Load a single audit entry from a JSON file."""
    data = json.loads(path.read_text())
    return AuditEntry.from_dict(data)


def list_entries(audit_dir: Path = _DEFAULT_AUDIT_DIR) -> list[AuditEntry]:
    """Return all audit entries sorted by timestamp ascending."""
    if not audit_dir.exists():
        return []
    entries = []
    for p in sorted(audit_dir.glob("*.json")):
        try:
            entries.append(load_entry(p))
        except (json.JSONDecodeError, KeyError):
            continue
    return entries


def clear_audit_log(audit_dir: Path = _DEFAULT_AUDIT_DIR) -> int:
    """Delete all audit entries; returns count removed."""
    if not audit_dir.exists():
        return 0
    removed = 0
    for p in audit_dir.glob("*.json"):
        p.unlink()
        removed += 1
    return removed

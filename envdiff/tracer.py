"""Trace where a key's value originates across a cascade of .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envdiff.core import parse_env_file


@dataclass
class TraceEntry:
    file: str
    value: Optional[str]  # None means key is absent in this file
    is_origin: bool = False  # True for the first file that defines the key

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "value": self.value,
            "is_origin": self.is_origin,
        }


@dataclass
class TraceReport:
    key: str
    entries: List[TraceEntry] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return any(e.value is not None for e in self.entries)

    @property
    def origin(self) -> Optional[TraceEntry]:
        return next((e for e in self.entries if e.is_origin), None)

    @property
    def effective_value(self) -> Optional[str]:
        """Last defined value wins (cascade semantics)."""
        last = None
        for e in self.entries:
            if e.value is not None:
                last = e.value
        return last

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "found": self.found,
            "effective_value": self.effective_value,
            "origin": self.origin.file if self.origin else None,
            "entries": [e.to_dict() for e in self.entries],
        }


def trace_key(key: str, files: List[str]) -> TraceReport:
    """Trace *key* through each file in order and record where it appears."""
    report = TraceReport(key=key)
    origin_found = False
    for path in files:
        env = parse_env_file(Path(path))
        value = env.get(key)
        is_origin = value is not None and not origin_found
        if is_origin:
            origin_found = True
        report.entries.append(
            TraceEntry(file=path, value=value, is_origin=is_origin)
        )
    return report

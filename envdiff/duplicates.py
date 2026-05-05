"""Detect and report duplicate keys across multiple .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.core import parse_env_file


@dataclass
class DuplicateReport:
    """Result of scanning one or more env files for duplicate keys."""

    # key -> list of files that define it (only keys appearing in >1 file)
    cross_file: Dict[str, List[str]] = field(default_factory=dict)
    # file -> list of keys that appear more than once inside that file
    within_file: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def has_cross_file(self) -> bool:
        return bool(self.cross_file)

    @property
    def has_within_file(self) -> bool:
        return bool(self.within_file)

    @property
    def clean(self) -> bool:
        return not self.has_cross_file and not self.has_within_file

    def to_dict(self) -> dict:
        return {
            "cross_file": self.cross_file,
            "within_file": self.within_file,
        }


def _parse_raw_keys(path: Path) -> List[str]:
    """Return every key occurrence in *path*, preserving duplicates."""
    keys: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            keys.append(stripped.split("=", 1)[0].strip())
    return keys


def find_duplicates(paths: List[Path]) -> DuplicateReport:
    """Scan *paths* for duplicate keys within and across files."""
    report = DuplicateReport()

    key_to_files: Dict[str, List[str]] = {}

    for path in paths:
        raw_keys = _parse_raw_keys(path)
        seen: Dict[str, int] = {}
        for key in raw_keys:
            seen[key] = seen.get(key, 0) + 1
        within = [k for k, count in seen.items() if count > 1]
        if within:
            report.within_file[str(path)] = within

        # cross-file tracking (use deduplicated keys per file)
        for key in set(raw_keys):
            key_to_files.setdefault(key, []).append(str(path))

    report.cross_file = {
        k: files for k, files in key_to_files.items() if len(files) > 1
    }
    return report

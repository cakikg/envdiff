"""Key-frequency analyzer: counts how often each key appears across many .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.core import parse_env_file


@dataclass
class FrequencyReport:
    files: List[str]
    counts: Dict[str, int] = field(default_factory=dict)
    total_files: int = 0

    # ------------------------------------------------------------------
    def coverage(self, key: str) -> float:
        """Return fraction of files that contain *key* (0.0 – 1.0)."""
        if self.total_files == 0:
            return 0.0
        return self.counts.get(key, 0) / self.total_files

    def common_keys(self, threshold: float = 1.0) -> List[str]:
        """Keys whose coverage is >= *threshold*."""
        return sorted(k for k in self.counts if self.coverage(k) >= threshold)

    def rare_keys(self, threshold: float = 0.5) -> List[str]:
        """Keys whose coverage is < *threshold*."""
        return sorted(k for k in self.counts if self.coverage(k) < threshold)

    def to_dict(self) -> dict:
        return {
            "files": self.files,
            "total_files": self.total_files,
            "counts": self.counts,
            "coverage": {k: round(self.coverage(k), 4) for k in self.counts},
        }


def analyze_frequency(paths: List[str | Path]) -> FrequencyReport:
    """Count how many files each key appears in."""
    str_paths = [str(p) for p in paths]
    counts: Dict[str, int] = {}
    for p in paths:
        env = parse_env_file(str(p))
        for key in env:
            counts[key] = counts.get(key, 0) + 1
    return FrequencyReport(
        files=str_paths,
        counts=counts,
        total_files=len(str_paths),
    )

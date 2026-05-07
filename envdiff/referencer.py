"""referencer.py – find all files that reference a given key."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict

from envdiff.core import parse_env_file


@dataclass
class ReferenceReport:
    key: str
    found_in: List[str] = field(default_factory=list)   # file paths where key exists
    missing_in: List[str] = field(default_factory=list) # file paths where key is absent

    @property
    def clean(self) -> bool:
        """True when the key is present in every supplied file."""
        return len(self.missing_in) == 0

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "found_in": self.found_in,
            "missing_in": self.missing_in,
            "clean": self.clean,
        }


def find_key_references(
    key: str,
    files: List[str | Path],
) -> ReferenceReport:
    """Search *files* for *key* and return a :class:`ReferenceReport`.

    Parameters
    ----------
    key:
        The environment variable name to look up (case-sensitive).
    files:
        Ordered list of ``.env`` file paths to inspect.
    """
    report = ReferenceReport(key=key)

    for path in files:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        env = parse_env_file(path)
        target = str(path)
        if key in env:
            report.found_in.append(target)
        else:
            report.missing_in.append(target)

    return report

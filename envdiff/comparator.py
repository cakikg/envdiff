"""Cross-environment key presence and value comparison report."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.core import parse_env_file


@dataclass
class KeyStatus:
    key: str
    # mapping of env_name -> value (None means key is absent)
    values: Dict[str, Optional[str]] = field(default_factory=dict)

    @property
    def is_consistent(self) -> bool:
        """True when every env that has the key shares the same value."""
        present = [v for v in self.values.values() if v is not None]
        return len(set(present)) <= 1

    @property
    def missing_in(self) -> List[str]:
        return [env for env, v in self.values.items() if v is None]

    @property
    def present_in(self) -> List[str]:
        return [env for env, v in self.values.items() if v is not None]

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "consistent": self.is_consistent,
            "missing_in": self.missing_in,
            "values": self.values,
        }


@dataclass
class CompareReport:
    env_names: List[str]
    statuses: List[KeyStatus] = field(default_factory=list)

    @property
    def inconsistent_keys(self) -> List[KeyStatus]:
        return [s for s in self.statuses if not s.is_consistent]

    @property
    def missing_keys(self) -> List[KeyStatus]:
        return [s for s in self.statuses if s.missing_in]

    @property
    def all_ok(self) -> bool:
        return not self.inconsistent_keys and not self.missing_keys

    def to_dict(self) -> dict:
        return {
            "envs": self.env_names,
            "all_ok": self.all_ok,
            "keys": [s.to_dict() for s in self.statuses],
        }


def compare_envs(
    files: List[Path],
    names: Optional[List[str]] = None,
) -> CompareReport:
    """Parse each file and build a unified CompareReport."""
    if names is None:
        names = [p.name for p in files]
    if len(names) != len(files):
        raise ValueError("Length of names must match length of files.")

    parsed = {name: parse_env_file(path) for name, path in zip(names, files)}
    all_keys: List[str] = sorted({k for env in parsed.values() for k in env})

    statuses: List[KeyStatus] = []
    for key in all_keys:
        values = {name: parsed[name].get(key) for name in names}
        statuses.append(KeyStatus(key=key, values=values))

    return CompareReport(env_names=names, statuses=statuses)

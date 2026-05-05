"""Group .env keys by prefix or custom delimiter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.core import parse_env_file


@dataclass
class GroupReport:
    groups: Dict[str, List[str]] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "groups": {k: sorted(v) for k, v in sorted(self.groups.items())},
            "ungrouped": sorted(self.ungrouped),
        }

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def keys_in(self, group: str) -> List[str]:
        return sorted(self.groups.get(group, []))


def group_env_file(
    path: str,
    delimiter: str = "_",
    min_prefix_length: int = 1,
    max_depth: int = 1,
) -> GroupReport:
    """Parse *path* and bucket every key by its prefix.

    Parameters
    ----------
    path:
        Path to the .env file.
    delimiter:
        Character used to split key segments (default ``_``).
    min_prefix_length:
        Minimum number of characters a prefix must have to form a group.
    max_depth:
        How many delimiter-separated segments to use as the group key.
    """
    env = parse_env_file(path)
    report = GroupReport()

    for key in env:
        parts = key.split(delimiter)
        if len(parts) > max_depth:
            prefix = delimiter.join(parts[:max_depth])
            if len(prefix) >= min_prefix_length:
                report.groups.setdefault(prefix, []).append(key)
                continue
        report.ungrouped.append(key)

    return report


def common_prefixes(report: GroupReport, min_keys: int = 2) -> List[str]:
    """Return group names that contain at least *min_keys* keys."""
    return [
        name
        for name, keys in report.groups.items()
        if len(keys) >= min_keys
    ]

"""Low-level value diffing utilities used across envdiff commands."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class ValueDiff:
    key: str
    old_value: Optional[str]  # None  => key was added
    new_value: Optional[str]  # None  => key was removed

    def is_added(self) -> bool:
        return self.old_value is None and self.new_value is not None

    def is_removed(self) -> bool:
        return self.old_value is not None and self.new_value is None

    def is_changed(self) -> bool:
        return (
            self.old_value is not None
            and self.new_value is not None
            and self.old_value != self.new_value
        )


def is_added(vd: ValueDiff) -> bool:
    return vd.is_added()


def is_removed(vd: ValueDiff) -> bool:
    return vd.is_removed()


def is_changed(vd: ValueDiff) -> bool:
    return vd.is_changed()


def _unified_value_diff(
    old: Dict[str, str],
    new: Dict[str, str],
    *,
    include_unchanged: bool = False,
) -> Dict[str, ValueDiff]:
    """Return a mapping of key -> ValueDiff for every key that differs."""
    result: Dict[str, ValueDiff] = {}
    all_keys = old.keys() | new.keys()
    for key in sorted(all_keys):
        ov = old.get(key)
        nv = new.get(key)
        if ov == nv and not include_unchanged:
            continue
        result[key] = ValueDiff(key=key, old_value=ov, new_value=nv)
    return result


# Public alias used by snapshot_cmd and other modules
unified_value_diff = _unified_value_diff


def diff_summary(diffs: Dict[str, ValueDiff]) -> Tuple[int, int, int]:
    """Return (added, removed, changed) counts."""
    added = sum(1 for d in diffs.values() if d.is_added())
    removed = sum(1 for d in diffs.values() if d.is_removed())
    changed = sum(1 for d in diffs.values() if d.is_changed())
    return added, removed, changed

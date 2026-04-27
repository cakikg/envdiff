"""Diff utilities for generating unified-style diffs between .env file values."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValueDiff:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    unified_lines: List[str] = field(default_factory=list)

    @property
    def is_added(self) -> bool:
        return self.old_value is None and self.new_value is not None

    @property
    def is_removed(self) -> bool:
        return self.old_value is not None and self.new_value is None

    @property
    def is_changed(self) -> bool:
        return (
            self.old_value is not None
            and self.new_value is not None
            and self.old_value != self.new_value
        )


def _unified_value_diff(key: str, old: str, new: str) -> List[str]:
    """Return unified diff lines for two values of the same key."""
    old_lines = [f"{key}={old}\n"]
    new_lines = [f"{key}={new}\n"]
    return list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )


def build_value_diffs(
    env_a: Dict[str, str],
    env_b: Dict[str, str],
    show_values: bool = False,
) -> List[ValueDiff]:
    """Compare two parsed env dicts and return a list of ValueDiff objects."""
    all_keys = sorted(set(env_a) | set(env_b))
    diffs: List[ValueDiff] = []

    for key in all_keys:
        old_val = env_a.get(key)
        new_val = env_b.get(key)

        if old_val == new_val:
            continue

        unified: List[str] = []
        if show_values and old_val is not None and new_val is not None:
            unified = _unified_value_diff(key, old_val, new_val)

        diffs.append(
            ValueDiff(
                key=key,
                old_value=old_val if show_values else ("***" if old_val is not None else None),
                new_value=new_val if show_values else ("***" if new_val is not None else None),
                unified_lines=unified,
            )
        )

    return diffs


def summarise_value_diffs(diffs: List[ValueDiff]) -> Dict[str, int]:
    """Return counts of added, removed, and changed keys."""
    return {
        "added": sum(1 for d in diffs if d.is_added),
        "removed": sum(1 for d in diffs if d.is_removed),
        "changed": sum(1 for d in diffs if d.is_changed),
    }

"""Merge multiple .env files into a single unified output."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# (key, value, source_file)
MergeEntry = Tuple[str, Optional[str], str]


def merge_env_files(
    envs: Dict[str, Dict[str, str]],
    strategy: str = "first",
) -> Dict[str, str]:
    """Merge multiple parsed env dicts into one.

    Args:
        envs: Mapping of filename -> {key: value}.
        strategy: Resolution strategy for conflicting keys.
            - "first": keep value from the first file that defines the key.
            - "last":  keep value from the last file that defines the key.
            - "error": raise ValueError on any conflict.

    Returns:
        A single merged dict of key -> value.
    """
    if strategy not in ("first", "last", "error"):
        raise ValueError(f"Unknown merge strategy: {strategy!r}")

    merged: Dict[str, str] = {}
    origins: Dict[str, str] = {}  # key -> first source filename

    for filename, env in envs.items():
        for key, value in env.items():
            if key in merged:
                if strategy == "error":
                    raise ValueError(
                        f"Conflict: key {key!r} defined in both "
                        f"{origins[key]!r} and {filename!r}"
                    )
                if strategy == "last":
                    merged[key] = value
                    origins[key] = filename
                # strategy == "first": do nothing, keep existing
            else:
                merged[key] = value
                origins[key] = filename

    return merged


def merge_conflicts(
    envs: Dict[str, Dict[str, str]],
) -> Dict[str, List[MergeEntry]]:
    """Return only keys that have conflicting values across files.

    Returns:
        Mapping of key -> list of (key, value, source) for each file
        that defines that key with a differing value.
    """
    all_keys: set = set()
    for env in envs.values():
        all_keys.update(env.keys())

    conflicts: Dict[str, List[MergeEntry]] = {}
    for key in sorted(all_keys):
        entries: List[MergeEntry] = [
            (key, env.get(key), fname)
            for fname, env in envs.items()
            if key in env
        ]
        values = {v for _, v, _ in entries}
        if len(values) > 1:
            conflicts[key] = entries

    return conflicts

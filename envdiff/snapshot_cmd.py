"""CLI command handlers for snapshot sub-commands."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from envdiff.core import parse_env_file
from envdiff.differ import unified_value_diff
from envdiff.snapshotter import (
    DEFAULT_SNAPSHOT_DIR,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


def run_snapshot_save(
    env_file: str,
    name: str,
    label: Optional[str] = None,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> int:
    """Parse *env_file* and save it as snapshot *name*.  Returns exit code."""
    try:
        env_data = parse_env_file(env_file)
    except FileNotFoundError:
        print(f"error: file not found: {env_file}", file=sys.stderr)
        return 1
    dest = save_snapshot(env_data, name, snapshot_dir=snapshot_dir, label=label)
    print(f"Snapshot '{name}' saved to {dest}")
    return 0


def run_snapshot_list(snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> int:
    """Print all saved snapshots."""
    snapshots = list_snapshots(snapshot_dir)
    if not snapshots:
        print("No snapshots found.")
        return 0
    for s in snapshots:
        print(f"{s['name']:20s}  {s['label']:20s}  {s['created_at']}")
    return 0


def run_snapshot_diff(
    name: str,
    env_file: str,
    show_values: bool = False,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> int:
    """Diff snapshot *name* against *env_file*.  Returns exit code."""
    try:
        snap = load_snapshot(name, snapshot_dir)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    try:
        current = parse_env_file(env_file)
    except FileNotFoundError:
        print(f"error: file not found: {env_file}", file=sys.stderr)
        return 1

    diffs = unified_value_diff(snap["env"], current)
    if not diffs:
        print("No differences found.")
        return 0
    for key, vd in diffs.items():
        old = vd.old_value if show_values else "***"
        new = vd.new_value if show_values else "***"
        print(f"  {key}: {old!r} -> {new!r}")
    return 1


def run_snapshot_delete(
    name: str,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> int:
    """Delete snapshot *name*.  Returns exit code."""
    removed = delete_snapshot(name, snapshot_dir)
    if removed:
        print(f"Snapshot '{name}' deleted.")
        return 0
    print(f"error: snapshot '{name}' not found.", file=sys.stderr)
    return 1

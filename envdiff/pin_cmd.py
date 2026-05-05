"""CLI commands for env pinning and drift detection."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from envdiff.core import parse_env_file
from envdiff.pinner import DEFAULT_LOCK_NAME, detect_drift, pin_env


def _render_text(report, file: str) -> str:
    lines = [f"Drift report for {file}"]
    if report.clean:
        lines.append("  No drift detected — environment matches lock file.")
        return "\n".join(lines)
    for key in report.added:
        lines.append(f"  + {key}  (new key, not in lock)")
    for key in report.removed:
        lines.append(f"  - {key}  (removed key, was in lock)")
    for key in report.changed:
        lines.append(f"  ~ {key}  (value changed since last pin)")
    return "\n".join(lines)


def _render_json(report) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_pin(args) -> int:
    """Pin current .env values to a lock file."""
    env_path = Path(args.file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 1

    lock_path = Path(args.lock) if args.lock else env_path.parent / DEFAULT_LOCK_NAME
    env = parse_env_file(env_path)
    pin_env(env, lock_path)
    print(f"Pinned {len(env)} key(s) to {lock_path}")
    return 0


def run_drift(args) -> int:
    """Detect drift between current .env and its lock file."""
    env_path = Path(args.file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 1

    lock_path = Path(args.lock) if args.lock else env_path.parent / DEFAULT_LOCK_NAME
    if not lock_path.exists():
        print(f"error: lock file not found: {lock_path}", file=sys.stderr)
        return 1

    env = parse_env_file(env_path)
    report = detect_drift(env, lock_path)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(_render_json(report))
    else:
        print(_render_text(report, str(env_path)))

    return 0 if report.clean else 1

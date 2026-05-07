"""reference_cmd.py – CLI entry-point for the `reference` sub-command."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.referencer import find_key_references


def _render_text(report, *, use_color: bool = False) -> str:
    lines: list[str] = [f"Key: {report.key}"]

    if report.found_in:
        lines.append("  Found in:")
        for f in report.found_in:
            lines.append(f"    + {f}")

    if report.missing_in:
        lines.append("  Missing in:")
        for f in report.missing_in:
            lines.append(f"    - {f}")

    status = "OK" if report.clean else "MISSING"
    lines.append(f"  Status: {status}")
    return "\n".join(lines)


def _render_json(report) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_reference(args: Namespace) -> int:
    """Execute the reference command; returns an exit code."""
    files = [Path(p) for p in args.files]

    for p in files:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 1

    report = find_key_references(args.key, files)

    if getattr(args, "format", "text") == "json":
        print(_render_json(report))
    else:
        print(_render_text(report))

    return 0 if report.clean else 1

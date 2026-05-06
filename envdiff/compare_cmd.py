"""CLI command: envdiff compare — compare keys across multiple env files."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from envdiff.comparator import CompareReport, KeyStatus, compare_envs


def _status_label(status: KeyStatus) -> str:
    if status.missing_in:
        return "MISSING"
    if not status.is_consistent:
        return "MISMATCH"
    return "OK"


def _render_text(report: CompareReport, show_values: bool = False) -> str:
    lines: List[str] = []
    col = max((len(k.key) for k in report.statuses), default=10)
    header = f"{'KEY':<{col}}  STATUS    MISSING IN"
    lines.append(header)
    lines.append("-" * len(header))
    for status in report.statuses:
        label = _status_label(status)
        missing = ", ".join(status.missing_in) if status.missing_in else ""
        row = f"{status.key:<{col}}  {label:<8}  {missing}"
        if show_values and not status.is_consistent:
            for env, val in status.values.items():
                row += f"\n    {env}: {val!r}"
        lines.append(row)
    lines.append("")
    if report.all_ok:
        lines.append("All environments are consistent.")
    else:
        lines.append(
            f"{len(report.inconsistent_keys)} inconsistent, "
            f"{len(report.missing_keys)} with missing keys."
        )
    return "\n".join(lines)


def _render_json(report: CompareReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_compare(args) -> int:  # noqa: ANN001
    files = [Path(f) for f in args.files]
    names = args.names.split(",") if getattr(args, "names", None) else None

    for f in files:
        if not f.exists():
            print(f"error: file not found: {f}", file=sys.stderr)
            return 1

    try:
        report = compare_envs(files, names)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fmt = getattr(args, "format", "text")
    show_values = getattr(args, "show_values", False)

    if fmt == "json":
        print(_render_json(report))
    else:
        print(_render_text(report, show_values=show_values))

    return 0 if report.all_ok else 1

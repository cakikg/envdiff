"""CLI command: highlight differences between two env files."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from envdiff.highlighter import HighlightReport, highlight_env_files

_STATUS_COLOR = {
    "added": "\033[32m",   # green
    "removed": "\033[31m",  # red
    "changed": "\033[33m",  # yellow
    "unchanged": "\033[0m",
}
_RESET = "\033[0m"


def _render_text(report: HighlightReport, *, color: bool = True) -> str:
    lines = [
        f"Highlighting: {report.file_a}  →  {report.file_b}",
        f"  added={len(report.added)}  removed={len(report.removed)}  modified={len(report.modified)}",
        "",
    ]
    if not report.entries:
        lines.append("  (no differences)")
        return "\n".join(lines)

    for entry in report.entries:
        prefix = {
            "added": "+ ",
            "removed": "- ",
            "changed": "~ ",
            "unchanged": "  ",
        }[entry.status]
        col = _STATUS_COLOR.get(entry.status, "") if color else ""
        rst = _RESET if color else ""
        if entry.status == "changed":
            lines.append(f"{col}{prefix}{entry.key}{rst}")
            lines.append(f"    old: {entry.old_value}")
            lines.append(f"    new: {entry.new_value}")
        elif entry.status == "added":
            lines.append(f"{col}{prefix}{entry.key}={entry.new_value}{rst}")
        elif entry.status == "removed":
            lines.append(f"{col}{prefix}{entry.key}={entry.old_value}{rst}")
        else:
            lines.append(f"{prefix}{entry.key}={entry.old_value}")
    return "\n".join(lines)


def _render_json(report: HighlightReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_highlight(args: SimpleNamespace) -> int:
    path_a = Path(args.file_a)
    path_b = Path(args.file_b)
    for p in (path_a, path_b):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 1

    report = highlight_env_files(
        path_a,
        path_b,
        include_unchanged=getattr(args, "unchanged", False),
    )

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(_render_json(report))
    else:
        use_color = getattr(args, "color", True)
        print(_render_text(report, color=use_color))

    return 1 if report.changed else 0

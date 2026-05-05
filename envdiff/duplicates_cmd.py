"""CLI command: envdiff duplicates — find duplicate keys in env files."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from envdiff.duplicates import find_duplicates


def _render_text(report, files: List[str]) -> str:
    lines: List[str] = []
    if report.has_cross_file:
        lines.append("Cross-file duplicates (key defined in multiple files):")
        for key, paths in sorted(report.cross_file.items()):
            lines.append(f"  {key}")
            for p in paths:
                lines.append(f"    - {p}")
    if report.has_within_file:
        lines.append("Within-file duplicates (key repeated inside same file):")
        for path, keys in sorted(report.within_file.items()):
            lines.append(f"  {path}")
            for k in sorted(keys):
                lines.append(f"    - {k}")
    if report.clean:
        lines.append("No duplicate keys found.")
    return "\n".join(lines)


def _render_json(report) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_duplicates(args) -> int:
    paths = [Path(f) for f in args.files]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        for m in missing:
            print(f"error: file not found: {m}", file=sys.stderr)
        return 1

    report = find_duplicates(paths)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(_render_json(report))
    else:
        print(_render_text(report, args.files))

    return 0 if report.clean else 1

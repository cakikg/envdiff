"""CLI command: trace a key across multiple .env files."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.tracer import trace_key, TraceReport


def _render_text(report: TraceReport) -> str:
    lines = [f"Tracing key: {report.key}"]
    if not report.found:
        lines.append("  (not found in any file)")
        return "\n".join(lines)
    for entry in report.entries:
        if entry.value is None:
            status = "absent"
        elif entry.is_origin:
            status = f"ORIGIN  -> {entry.value!r}"
        else:
            status = f"override-> {entry.value!r}"
        lines.append(f"  {entry.file}: {status}")
    lines.append(f"Effective value: {report.effective_value!r}")
    return "\n".join(lines)


def _render_json(report: TraceReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_trace(args: Namespace) -> int:
    for f in args.files:
        if not Path(f).exists():
            print(f"error: file not found: {f}", file=sys.stderr)
            return 1

    report = trace_key(key=args.key, files=args.files)

    if args.format == "json":
        print(_render_json(report))
    else:
        print(_render_text(report))

    return 0 if report.found else 1

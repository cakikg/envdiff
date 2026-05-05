"""CLI command: envdiff profile — show a statistical profile of an .env file."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.profiler import ProfileReport, profile_env_file
from envdiff.redactor import Redactor


def _render_text(report: ProfileReport) -> str:
    lines = [
        f"Profile: {report.path}",
        f"  Total keys      : {report.total_keys}",
        f"  Empty values    : {len(report.empty_keys)}",
        f"  Sensitive keys  : {len(report.sensitive_keys)}",
        f"  URL values      : {len(report.url_keys)}",
        f"  Integer values  : {len(report.int_keys)}",
        f"  Boolean values  : {len(report.bool_keys)}",
        f"  String values   : {len(report.string_keys)}",
    ]
    if report.empty_keys:
        lines.append("  Empty keys      : " + ", ".join(report.empty_keys))
    if report.sensitive_keys:
        lines.append("  Sensitive keys  : " + ", ".join(report.sensitive_keys))
    return "\n".join(lines)


def _render_json(report: ProfileReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_profile(args: Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    extra_patterns = list(args.sensitive_pattern) if getattr(args, "sensitive_pattern", None) else []
    redactor = Redactor(extra_patterns=extra_patterns)

    report = profile_env_file(path, redactor=redactor)

    fmt = getattr(args, "format", "text")
    output = _render_json(report) if fmt == "json" else _render_text(report)
    print(output)
    return 0

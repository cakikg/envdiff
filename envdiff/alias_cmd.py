"""alias_cmd.py – CLI entry point for the alias-check command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.aliaser import AliasReport, check_aliases, load_aliases


def _render_text(report: AliasReport) -> str:
    if report.clean:
        return "No deprecated alias keys found."
    lines = ["Deprecated alias keys detected:"]
    for hit in report.hits:
        files = ", ".join(hit.files_affected)
        lines.append(f"  {hit.old_key!r} -> {hit.new_key!r}  (in: {files})")
    return "\n".join(lines)


def _render_json(report: AliasReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_alias(args: argparse.Namespace) -> int:
    alias_path = Path(args.alias_file)
    try:
        aliases = load_aliases(alias_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        for m in missing:
            print(f"error: file not found: {m}", file=sys.stderr)
        return 1

    report = check_aliases(args.files, aliases)

    if args.format == "json":
        print(_render_json(report))
    else:
        print(_render_text(report))

    return 0 if report.clean else 1

"""CLI command: envdiff split — split a .env file by prefix group."""
from __future__ import annotations

import json
import sys
from argparse import Namespace

from envdiff.splitter import split_env_file


def _render_text(result) -> str:
    if not result.changed:
        return "No groups found — nothing written."
    lines = [f"Source : {result.source}"]
    if result.dry_run:
        lines.append("Mode   : dry-run (no files written)")
    for group, path in sorted(result.outputs.items()):
        keys = result.keys_written.get(group, [])
        lines.append(f"  [{group}] -> {path}  ({len(keys)} keys)")
    return "\n".join(lines)


def _render_json(result) -> str:
    return json.dumps(result.to_dict(), indent=2)


def run_split(args: Namespace) -> int:
    try:
        result = split_env_file(
            source=args.file,
            output_dir=args.output_dir,
            prefix=getattr(args, "prefix", None),
            dry_run=getattr(args, "dry_run", False),
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fmt = getattr(args, "format", "text")
    output = _render_json(result) if fmt == "json" else _render_text(result)
    print(output)
    return 0 if result.changed else 0

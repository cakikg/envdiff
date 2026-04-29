"""CLI entry-point for the ``rename`` sub-command."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import List

from .renamer import RenameResult, rename_key_in_many


def _render_text(results: List[RenameResult], *, verbose: bool = False) -> str:
    lines: List[str] = []
    for r in results:
        status = "renamed" if r.changed else "not found"
        dry = " (dry-run)" if r.dry_run else ""
        lines.append(f"{r.path}: {r.old_key} -> {r.new_key}: {status}{dry}")
        if verbose and r.changed:
            for orig, new in zip(r.original_lines, r.patched_lines):
                if orig != new:
                    lines.append(f"  - {orig.rstrip()}")
                    lines.append(f"  + {new.rstrip()}")
    return "\n".join(lines)


def _render_json(results: List[RenameResult]) -> str:
    payload = [
        {
            "path": str(r.path),
            "old_key": r.old_key,
            "new_key": r.new_key,
            "changed": r.changed,
            "dry_run": r.dry_run,
        }
        for r in results
    ]
    return json.dumps(payload, indent=2)


def run_rename(args: Namespace) -> int:  # pragma: no branch
    paths = [Path(p) for p in args.files]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"error: file not found: {p}", file=sys.stderr)
        return 1

    results = rename_key_in_many(
        paths,
        args.old_key,
        args.new_key,
        dry_run=getattr(args, "dry_run", False),
    )

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(_render_json(results))
    else:
        print(_render_text(results, verbose=getattr(args, "verbose", False)))

    any_changed = any(r.changed for r in results)
    return 0 if any_changed else 2

"""CLI command: normalize one or more .env files."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.normalizer import normalize_env_file


def _render_text(result, *, verbose: bool) -> None:
    label = str(result.path)
    if not result.changed:
        if verbose:
            print(f"{label}: already normalized")
        return
    print(f"{label}: {len(result.changes)} change(s)")
    for lineno, before, after in result.changes:
        print(f"  line {lineno}:")
        print(f"    - {before}")
        print(f"    + {after}")


def _render_json(results: list) -> None:
    print(json.dumps([r.to_dict() for r in results], indent=2))


def run_normalize(args: Namespace) -> int:
    """Entry point for the *normalize* sub-command.

    Returns an exit code (0 = success, 1 = error).
    """
    paths = [Path(p) for p in args.files]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"error: file not found: {p}", file=sys.stderr)
        return 1

    write = not getattr(args, "dry_run", False)
    results = []
    for path in paths:
        try:
            result = normalize_env_file(path, write=write)
            results.append(result)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if getattr(args, "format", "text") == "json":
        _render_json(results)
    else:
        verbose = getattr(args, "verbose", False)
        for result in results:
            _render_text(result, verbose=verbose)

    return 0

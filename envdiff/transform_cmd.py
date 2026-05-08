"""CLI command: transform — replace specific key values across .env files."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import Dict

from envdiff.renamer2 import transform_many


def _parse_mapping(pairs: list[str]) -> Dict[str, str]:
    """Parse KEY=VALUE strings into a dict."""
    mapping: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            print(f"[error] invalid mapping '{pair}' — expected KEY=VALUE", file=sys.stderr)
            sys.exit(1)
        k, _, v = pair.partition("=")
        mapping[k.strip()] = v
    return mapping


def _render_text(results: list, dry_run: bool) -> None:
    tag = "[dry-run] " if dry_run else ""
    for r in results:
        if r.changed:
            for key, val in r.replacements.items():
                print(f"{tag}{r.file}: {key} -> {val}")
        else:
            print(f"{r.file}: no changes")


def _render_json(results: list, dry_run: bool) -> None:
    out = [r.to_dict() for r in results]
    for item in out:
        item["dry_run"] = dry_run
    print(json.dumps(out, indent=2))


def run_transform(args: Namespace) -> int:
    paths = [Path(f) for f in args.files]
    for p in paths:
        if not p.exists():
            print(f"[error] file not found: {p}", file=sys.stderr)
            return 1

    mapping = _parse_mapping(args.set or [])
    if not mapping:
        print("[error] provide at least one --set KEY=VALUE", file=sys.stderr)
        return 1

    results = transform_many(paths, mapping, dry_run=getattr(args, "dry_run", False))

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        _render_json(results, getattr(args, "dry_run", False))
    else:
        _render_text(results, getattr(args, "dry_run", False))

    any_changed = any(r.changed for r in results)
    return 0 if any_changed or not any(True for _ in results) else 0

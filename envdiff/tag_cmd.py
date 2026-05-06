"""CLI command handlers for the 'tag' sub-command group."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.tagger import (
    keys_with_label,
    load_tags,
    tag_key,
    untag_key,
)


def _render_text(result: dict) -> str:
    lines = []
    if result.get("added"):
        lines.append(f"  tagged:   {', '.join(result['added'])}")
    if result.get("removed"):
        lines.append(f"  untagged: {', '.join(result['removed'])}")
    if result.get("unchanged"):
        lines.append(f"  unchanged: {', '.join(result['unchanged'])}")
    return "\n".join(lines)


def run_tag_add(args: Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    result = tag_key(path, args.key, args.label, dry_run=getattr(args, "dry_run", False))
    if getattr(args, "format", "text") == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(_render_text(result.to_dict()))
    return 0


def run_tag_remove(args: Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    label = getattr(args, "label", None)
    result = untag_key(path, args.key, label, dry_run=getattr(args, "dry_run", False))
    if getattr(args, "format", "text") == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(_render_text(result.to_dict()))
    return 0


def run_tag_list(args: Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    label = getattr(args, "label", None)
    if label:
        keys = keys_with_label(path, label)
        if getattr(args, "format", "text") == "json":
            print(json.dumps({"label": label, "keys": keys}, indent=2))
        else:
            for k in keys:
                print(f"  {k}")
    else:
        tags = load_tags(path)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(tags, indent=2))
        else:
            for k, labels in sorted(tags.items()):
                print(f"  {k}: {', '.join(labels)}")
    return 0

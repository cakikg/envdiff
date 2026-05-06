"""mask_cmd.py – CLI entry-point for the `envdiff mask` sub-command."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.masker import mask_env_file


def _render_text(result, *, show_content: bool) -> None:
    if result.changed:
        print(f"Masked {len(result.masked_keys)} key(s) in {result.file}:")
        for key in result.masked_keys:
            print(f"  - {key}")
    else:
        print(f"No sensitive keys found in {result.file}.")

    if show_content:
        print()
        print(result.content())


def _render_json(result, *, show_content: bool) -> None:
    data = result.to_dict()
    if show_content:
        data["content"] = result.content()
    print(json.dumps(data, indent=2))


def run_mask(args: Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    extra = list(args.pattern) if getattr(args, "pattern", None) else []
    mask_str = getattr(args, "mask", "***") or "***"
    write = getattr(args, "write", False)
    fmt = getattr(args, "format", "text")
    show_content = getattr(args, "show_content", False)

    result = mask_env_file(
        path,
        mask=mask_str,
        extra_patterns=extra,
        write=write,
    )

    if fmt == "json":
        _render_json(result, show_content=show_content)
    else:
        _render_text(result, show_content=show_content)

    return 0

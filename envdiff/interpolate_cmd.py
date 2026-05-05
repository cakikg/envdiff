"""CLI command: envdiff interpolate — resolve variable references in a .env file."""
from __future__ import annotations

import json
import os
import sys
from argparse import Namespace
from typing import List

from envdiff.core import parse_env_file
from envdiff.interpolator import interpolate_env


def _render_text(result, show_values: bool) -> List[str]:
    lines: List[str] = []
    if result.cycles:
        lines.append("CYCLES detected in: " + ", ".join(result.cycles))
    if result.unresolved:
        lines.append("Unresolved references:")
        for key, refs in result.unresolved.items():
            lines.append(f"  {key} -> missing: {', '.join(refs)}")
    if result.resolved:
        lines.append("Resolved keys:")
        for key, value in result.resolved.items():
            display = value if show_values else "***"
            lines.append(f"  {key}={display}")
    return lines


def _render_json(result, show_values: bool) -> str:
    data = {
        "resolved": {
            k: (v if show_values else "***") for k, v in result.resolved.items()
        },
        "unresolved": result.unresolved,
        "cycles": result.cycles,
        "ok": result.ok,
    }
    return json.dumps(data, indent=2)


def run_interpolate(args: Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    external = dict(os.environ) if getattr(args, "use_os_env", False) else None
    result = interpolate_env(env, external=external)

    if getattr(args, "format", "text") == "json":
        print(_render_json(result, show_values=getattr(args, "show_values", False)))
    else:
        for line in _render_text(result, show_values=getattr(args, "show_values", False)):
            print(line)

    return 0 if result.ok else 1

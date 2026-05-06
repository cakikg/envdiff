"""CLI command: envdiff deprecate — check for deprecated keys."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict

from envdiff.deprecator import check_deprecations
from envdiff.schema import load_schema


def _render_text(report: Any, *, show_replacement: bool = True) -> str:
    lines = [f"File : {report.file}"]
    lines.append(f"Keys : {report.total_keys}")
    if report.clean:
        lines.append("Status: no deprecated keys found")
        return "\n".join(lines)
    lines.append(f"Status: {len(report.hits)} deprecated key(s) found")
    for hit in report.hits:
        tag = f"[{hit.key}]"
        msg = f"  {tag} {hit.reason}"
        if show_replacement and hit.replacement:
            msg += f" → use {hit.replacement}"
        lines.append(msg)
    return "\n".join(lines)


def _render_json(report: Any) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_deprecate(args: Namespace) -> int:
    env_path = Path(args.file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 1

    # Load deprecated key definitions from a schema/json file
    try:
        raw: Dict = load_schema(Path(args.deprecated))
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    deprecated = raw.get("deprecated", {})
    if not isinstance(deprecated, dict):
        print("error: schema must have a top-level 'deprecated' object", file=sys.stderr)
        return 1

    report = check_deprecations(env_path, deprecated)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(_render_json(report))
    else:
        print(_render_text(report))

    return 0 if report.clean else 1

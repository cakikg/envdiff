"""CLI command: cascade multiple .env files and report the result."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from typing import List

from envdiff.cascader import cascade_env_files, override_summary


def _render_text(result, *, verbose: bool) -> str:
    lines: List[str] = []

    if result.changed():
        lines.append(f"Overrides detected ({len(result.overrides)} key(s)):")
        for line in override_summary(result):
            lines.append(f"  {line}")
    else:
        lines.append("No overrides — all keys are unique across files.")

    if verbose:
        lines.append("")
        lines.append("Resolved environment:")
        for key, (value, source) in sorted(result.provenance.items()):
            lines.append(f"  {key}={value}  [{source}]")

    return "\n".join(lines)


def _render_json(result) -> str:
    return json.dumps(result.to_dict(), indent=2)


def run_cascade(args: Namespace) -> int:
    """Entry point for the *cascade* sub-command.

    Returns an exit code: 0 = success, 1 = error, 2 = overrides found
    (only when ``--strict`` is requested).
    """
    if len(args.files) < 2:
        print("error: cascade requires at least two .env files", file=sys.stderr)
        return 1

    try:
        result = cascade_env_files(
            args.files,
            show_values=getattr(args, "show_values", False),
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(_render_json(result))
    else:
        print(_render_text(result, verbose=getattr(args, "verbose", False)))

    if getattr(args, "strict", False) and result.changed():
        return 2

    return 0

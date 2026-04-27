"""CLI command handler for the `envdiff diff` sub-command (value-level diff)."""

from __future__ import annotations

import json
import sys
from typing import List

from envdiff.core import parse_env_file
from envdiff.differ import ValueDiff, build_value_diffs, summarise_value_diffs


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def _render_text(diffs: List[ValueDiff], use_color: bool) -> str:
    if not diffs:
        return "No value-level differences found.\n"

    lines: List[str] = []
    for d in diffs:
        if d.is_added:
            line = f"+ {d.key} = {d.new_value}"
            lines.append(_colorize(line, ANSI_GREEN, use_color))
        elif d.is_removed:
            line = f"- {d.key} = {d.old_value}"
            lines.append(_colorize(line, ANSI_RED, use_color))
        elif d.is_changed:
            lines.append(_colorize(f"~ {d.key}", ANSI_YELLOW, use_color))
            if d.unified_lines:
                for ul in d.unified_lines:
                    if ul.startswith("-"):
                        lines.append(_colorize(f"  {ul}", ANSI_RED, use_color))
                    elif ul.startswith("+"):
                        lines.append(_colorize(f"  {ul}", ANSI_GREEN, use_color))
                    else:
                        lines.append(f"  {ul}")
            else:
                lines.append(f"  before: {d.old_value}")
                lines.append(f"  after:  {d.new_value}")
    return "\n".join(lines) + "\n"


def _render_json(diffs: List[ValueDiff]) -> str:
    payload = []
    for d in diffs:
        payload.append(
            {
                "key": d.key,
                "status": "added" if d.is_added else "removed" if d.is_removed else "changed",
                "old_value": d.old_value,
                "new_value": d.new_value,
            }
        )
    return json.dumps(payload, indent=2) + "\n"


def run_diff(args) -> int:  # noqa: ANN001
    """Entry point for the diff sub-command. Returns exit code."""
    try:
        env_a = parse_env_file(args.file_a)
        env_b = parse_env_file(args.file_b)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    diffs = build_value_diffs(env_a, env_b, show_values=args.show_values)
    summary = summarise_value_diffs(diffs)

    use_color = getattr(args, "color", True) and sys.stdout.isatty()

    if getattr(args, "format", "text") == "json":
        sys.stdout.write(_render_json(diffs))
    else:
        sys.stdout.write(_render_text(diffs, use_color))
        print(
            f"Summary: {summary['added']} added, "
            f"{summary['removed']} removed, "
            f"{summary['changed']} changed."
        )

    return 1 if diffs else 0

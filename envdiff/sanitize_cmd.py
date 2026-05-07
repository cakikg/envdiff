"""sanitize_cmd.py – CLI entry-point for the sanitize sub-command."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from envdiff.sanitizer import sanitize_env_file


def _render_text(result) -> str:
    lines = [f"File : {result.file}"]
    if not result.changed:
        lines.append("No sensitive keys found – nothing to sanitize.")
    else:
        lines.append(f"Sanitized {len(result.sanitized_keys)} key(s):")
        for key in result.sanitized_keys:
            lines.append(f"  - {key}")
    return "\n".join(lines)


def _render_json(result) -> str:
    return json.dumps(result.to_dict(), indent=2)


def run_sanitize(args: SimpleNamespace) -> int:
    """Run the sanitize command; returns an exit code."""
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    extra = list(args.extra_patterns) if getattr(args, "extra_patterns", None) else []
    placeholder = getattr(args, "placeholder", "REDACTED") or "REDACTED"
    write = getattr(args, "write", False)
    dry_run = getattr(args, "dry_run", False)

    result = sanitize_env_file(
        path,
        placeholder=placeholder,
        extra_patterns=extra,
        write=(write and not dry_run),
    )

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(_render_json(result))
    else:
        print(_render_text(result))
        if dry_run and result.changed:
            print("\n--- dry-run output ---")
            print(result.content())

    return 0

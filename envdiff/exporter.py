"""Export diff results to various file formats (dotenv template, markdown)."""
from __future__ import annotations

from typing import Any


def export_dotenv_template(diff: dict[str, Any], include_values: bool = False) -> str:
    """Generate a .env.template file from diff results.

    Outputs all keys found across compared files. Keys missing in at least
    one environment are marked with a comment. Values are redacted unless
    *include_values* is True.
    """
    lines: list[str] = []
    for key, info in sorted(diff.items()):
        status = info.get("status", "ok")
        if status == "missing":
            lines.append(f"# MISSING in some environments")
        elif status == "mismatch":
            lines.append(f"# MISMATCH across environments")

        if include_values:
            # Use first non-None value available
            value = next(
                (v for v in info.get("values", {}).values() if v is not None),
                "",
            )
            lines.append(f"{key}={value}")
        else:
            lines.append(f"{key}=")

        lines.append("")  # blank line between entries

    return "\n".join(lines).rstrip("\n") + "\n"


def export_markdown(diff: dict[str, Any], env_names: list[str]) -> str:
    """Generate a Markdown table summarising the diff."""
    headers = ["Key", "Status"] + env_names
    separator = ["---"] * len(headers)

    rows: list[list[str]] = []
    for key, info in sorted(diff.items()):
        status = info.get("status", "ok")
        values = info.get("values", {})
        row = [f"`{key}`", status]
        for env in env_names:
            val = values.get(env)
            row.append("*(missing)*" if val is None else "✓")
        rows.append(row)

    def _row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    lines = [
        _row(headers),
        _row(separator),
        *[_row(r) for r in rows],
    ]
    return "\n".join(lines) + "\n"

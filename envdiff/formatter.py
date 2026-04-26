"""Output formatters for envdiff results."""

from typing import Dict, List, Optional
from envdiff.core import compare_env_files


def format_table(diff: Dict, file_a: str, file_b: str, show_values: bool = False) -> str:
    """Format a diff result as an ASCII table."""
    lines = []
    col_width = max(len(file_a), len(file_b), 20)
    key_width = 30

    header = f"{'KEY':<{key_width}}  {'STATUS':<12}  {file_a:<{col_width}}  {file_b:<{col_width}}"
    lines.append(header)
    lines.append("-" * len(header))

    missing_in_b = diff.get("missing_in_b", [])
    missing_in_a = diff.get("missing_in_a", [])
    mismatched = diff.get("mismatched", {})

    for key in sorted(missing_in_b):
        val = diff.get("values_a", {}).get(key, "") if show_values else "***"
        lines.append(f"{key:<{key_width}}  {'MISSING':<12}  {val:<{col_width}}  {'<absent>':<{col_width}}")

    for key in sorted(missing_in_a):
        val = diff.get("values_b", {}).get(key, "") if show_values else "***"
        lines.append(f"{key:<{key_width}}  {'ADDED':<12}  {'<absent>':<{col_width}}  {val:<{col_width}}")

    for key in sorted(mismatched):
        if show_values:
            val_a = mismatched[key]["a"]
            val_b = mismatched[key]["b"]
        else:
            val_a = val_b = "***"
        lines.append(f"{key:<{key_width}}  {'MISMATCH':<12}  {val_a:<{col_width}}  {val_b:<{col_width}}")

    if not missing_in_a and not missing_in_b and not mismatched:
        lines.append("No differences found.")

    return "\n".join(lines)


def format_json(diff: Dict, file_a: str, file_b: str, show_values: bool = False) -> str:
    """Format a diff result as JSON string."""
    import json

    output = {
        "files": {"a": file_a, "b": file_b},
        "missing_in_b": sorted(diff.get("missing_in_b", [])),
        "missing_in_a": sorted(diff.get("missing_in_a", [])),
        "mismatched": {},
    }

    for key, vals in sorted(diff.get("mismatched", {}).items()):
        if show_values:
            output["mismatched"][key] = vals
        else:
            output["mismatched"][key] = {"a": "***", "b": "***"}

    return json.dumps(output, indent=2)


def format_summary(diff: Dict) -> str:
    """Return a one-line summary of the diff."""
    n_missing_b = len(diff.get("missing_in_b", []))
    n_missing_a = len(diff.get("missing_in_a", []))
    n_mismatch = len(diff.get("mismatched", {}))
    total = n_missing_a + n_missing_b + n_mismatch
    if total == 0:
        return "Files are identical."
    return (
        f"{total} difference(s): "
        f"{n_missing_b} missing in B, "
        f"{n_missing_a} missing in A, "
        f"{n_mismatch} mismatched."
    )

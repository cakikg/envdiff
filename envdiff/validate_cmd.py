"""CLI helpers for the `envdiff validate` sub-command."""

from __future__ import annotations

import sys
from typing import List, Optional

from envdiff.core import parse_env_file
from envdiff.schema import load_schema
from envdiff.validator import ValidationResult, validate_env


def _result_lines(result: ValidationResult, show_warnings: bool = True) -> List[str]:
    """Format a ValidationResult into human-readable lines."""
    lines: List[str] = [f"Validating: {result.file_path}"]

    if result.is_valid and not (show_warnings and result.has_warnings):
        lines.append("  ✓ All checks passed.")
        return lines

    if result.missing_required:
        lines.append("  ERRORS — missing required keys:")
        for key in sorted(result.missing_required):
            lines.append(f"    - {key}")

    if result.type_mismatches:
        lines.append("  ERRORS — type mismatches:")
        for key, expected in sorted(result.type_mismatches.items()):
            lines.append(f"    - {key}: expected {expected}")

    if show_warnings and result.unknown_keys:
        lines.append("  WARNINGS — unknown keys (not in schema):")
        for key in sorted(result.unknown_keys):
            lines.append(f"    ? {key}")

    return lines


def run_validate(
    env_files: List[str],
    schema_path: str,
    strict: bool = False,
    show_warnings: bool = True,
    output=None,
) -> int:
    """Validate one or more env files against a schema file.

    Returns:
        0 if all files are valid, 1 otherwise.
    """
    if output is None:
        output = sys.stdout

    try:
        schema = load_schema(schema_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 1

    all_valid = True
    for env_path in env_files:
        try:
            env = parse_env_file(env_path)
        except FileNotFoundError:
            print(f"Error: env file not found: {env_path}", file=sys.stderr)
            all_valid = False
            continue

        result = validate_env(env, schema, file_path=env_path, strict=strict)
        for line in _result_lines(result, show_warnings=show_warnings):
            print(line, file=output)

        if not result.is_valid:
            all_valid = False

    return 0 if all_valid else 1

"""Validation module for envdiff: check env files against a schema/required keys list."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationResult:
    """Result of validating an env file against a schema."""

    file_path: str
    missing_required: List[str] = field(default_factory=list)
    type_mismatches: Dict[str, str] = field(default_factory=dict)  # key -> expected type
    unknown_keys: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.missing_required and not self.type_mismatches

    @property
    def has_warnings(self) -> bool:
        return bool(self.unknown_keys)


def _check_type(value: str, expected_type: str) -> bool:
    """Return True if value matches the expected type string."""
    expected_type = expected_type.lower()
    if expected_type == "int":
        try:
            int(value)
            return True
        except ValueError:
            return False
    if expected_type == "bool":
        return value.lower() in ("true", "false", "1", "0", "yes", "no")
    if expected_type == "url":
        return value.startswith(("http://", "https://"))
    if expected_type == "str":
        return True
    return True  # unknown types pass through


def validate_env(
    env: Dict[str, str],
    schema: Dict[str, dict],
    file_path: str = "<env>",
    strict: bool = False,
) -> ValidationResult:
    """Validate an env dict against a schema.

    Schema format::

        {
            "PORT": {"required": True, "type": "int"},
            "DEBUG": {"required": False, "type": "bool"},
        }

    Args:
        env: Parsed environment variables.
        schema: Mapping of key names to their constraints.
        file_path: Label used in the result (e.g. the file name).
        strict: If True, keys not present in schema are reported as unknown.

    Returns:
        A :class:`ValidationResult` instance.
    """
    result = ValidationResult(file_path=file_path)

    for key, constraints in schema.items():
        required: bool = constraints.get("required", True)
        expected_type: Optional[str] = constraints.get("type")

        if key not in env:
            if required:
                result.missing_required.append(key)
        elif expected_type:
            if not _check_type(env[key], expected_type):
                result.type_mismatches[key] = expected_type

    if strict:
        schema_keys = set(schema.keys())
        result.unknown_keys = [k for k in env if k not in schema_keys]

    return result

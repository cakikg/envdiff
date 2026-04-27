"""Schema loading utilities for envdiff."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


SCHEMA_TYPE = Dict[str, dict]


def load_schema(path: str | Path) -> SCHEMA_TYPE:
    """Load a validation schema from a JSON or TOML file.

    Args:
        path: Path to a ``.json`` or ``.toml`` schema file.

    Returns:
        A dict mapping key names to constraint dicts.

    Raises:
        ValueError: If the file extension is unsupported or TOML support is missing.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    elif suffix == ".toml":
        if tomllib is None:
            raise ValueError(
                "TOML support requires Python 3.11+ or 'tomli' package. "
                "Install it with: pip install tomli"
            )
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    else:
        raise ValueError(f"Unsupported schema format: '{suffix}'. Use .json or .toml")

    if not isinstance(data, dict):
        raise ValueError("Schema must be a top-level object/table.")

    return data  # type: ignore[return-value]


def schema_from_env_file(env: Dict[str, str]) -> SCHEMA_TYPE:
    """Generate a minimal schema from an existing env dict (all keys required, type str)."""
    return {key: {"required": True, "type": "str"} for key in env}

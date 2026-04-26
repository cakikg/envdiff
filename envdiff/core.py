"""Core logic for comparing .env files across environments."""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def parse_env_file(filepath: str | Path) -> Dict[str, str]:
    """
    Parse a .env file and return a dictionary of key-value pairs.

    Handles:
    - KEY=VALUE pairs
    - Quoted values (single and double quotes)
    - Inline comments
    - Empty lines and comment-only lines
    """
    env_vars: Dict[str, str] = {}
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Handle lines with '=' separator
            if "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip()

            # Strip inline comments from value
            value = value.strip()
            if " #" in value:
                value = value[:value.index(" #")].strip()

            # Strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]

            if key:
                env_vars[key] = value

    return env_vars


def compare_env_files(
    base: Dict[str, str],
    other: Dict[str, str],
) -> Dict[str, object]:
    """
    Compare two parsed .env dictionaries and return a diff report.

    Returns a dict with:
    - missing_in_other: keys present in base but not in other
    - missing_in_base: keys present in other but not in base
    - mismatched: keys present in both but with different values
    - matching: keys with identical values in both files
    """
    base_keys: Set[str] = set(base.keys())
    other_keys: Set[str] = set(other.keys())

    missing_in_other: List[str] = sorted(base_keys - other_keys)
    missing_in_base: List[str] = sorted(other_keys - base_keys)

    mismatched: Dict[str, Tuple[str, str]] = {}
    matching: List[str] = []

    for key in sorted(base_keys & other_keys):
        if base[key] != other[key]:
            mismatched[key] = (base[key], other[key])
        else:
            matching.append(key)

    return {
        "missing_in_other": missing_in_other,
        "missing_in_base": missing_in_base,
        "mismatched": mismatched,
        "matching": matching,
    }


def compare_multiple(
    files: List[str | Path],
    labels: Optional[List[str]] = None,
) -> Dict[str, Dict[str, object]]:
    """
    Compare multiple .env files against the first file as the base.

    Returns a dict mapping each comparison label to its diff report.
    """
    if len(files) < 2:
        raise ValueError("At least two .env files are required for comparison.")

    if labels is None:
        labels = [str(f) for f in files]

    base_label = labels[0]
    base_env = parse_env_file(files[0])

    results: Dict[str, Dict[str, object]] = {}

    for filepath, label in zip(files[1:], labels[1:]):
        other_env = parse_env_file(filepath)
        diff = compare_env_files(base_env, other_env)
        comparison_key = f"{base_label} vs {label}"
        results[comparison_key] = diff

    return results

"""Cascade multiple .env files in priority order.

Later files override earlier ones; the result is a merged dict
with provenance tracking so callers know which file supplied each key.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envdiff.core import parse_env_file


@dataclass
class CascadeResult:
    """Resolved environment after cascading all layers."""

    resolved: Dict[str, str] = field(default_factory=dict)
    # key -> (value, source_path)
    provenance: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    # keys overridden at least once: key -> list of (value, source)
    overrides: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)

    def changed(self) -> bool:
        return bool(self.overrides)

    def to_dict(self) -> dict:
        return {
            "resolved": self.resolved,
            "provenance": {
                k: {"value": v, "source": s}
                for k, (v, s) in self.provenance.items()
            },
            "overrides": {
                k: [{"value": v, "source": s} for v, s in entries]
                for k, entries in self.overrides.items()
            },
        }


def cascade_env_files(
    paths: List[str],
    *,
    show_values: bool = True,
) -> CascadeResult:
    """Merge *paths* left-to-right; later files win on conflict.

    Parameters
    ----------
    paths:
        Ordered list of .env file paths. Index 0 is lowest priority.
    show_values:
        When *False* values in provenance/overrides are redacted.
    """
    result = CascadeResult()

    for raw_path in paths:
        source = str(Path(raw_path))
        env = parse_env_file(raw_path)

        for key, value in env.items():
            display_value = value if show_values else "***"

            if key in result.resolved:
                # Record the override history
                prev_val, prev_src = result.provenance[key]
                if key not in result.overrides:
                    result.overrides[key] = [(prev_val, prev_src)]
                result.overrides[key].append((display_value, source))

            result.resolved[key] = value
            result.provenance[key] = (display_value, source)

    return result


def override_summary(result: CascadeResult) -> List[str]:
    """Return human-readable lines describing every override."""
    lines: List[str] = []
    for key, history in result.overrides.items():
        final_val, final_src = result.provenance[key]
        chain = " -> ".join(f"{src}({val})" for val, src in history)
        lines.append(f"{key}: {chain} -> {final_src}({final_val})")
    return lines

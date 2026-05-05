"""Resolve variable interpolation in .env files (e.g. ${VAR} or $VAR)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: Dict[str, List[str]] = field(default_factory=dict)  # key -> missing refs
    cycles: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unresolved and not self.cycles


def _refs_in(value: str) -> List[str]:
    """Return all variable names referenced inside *value*."""
    return [m.group(1) or m.group(2) for m in _REF_RE.finditer(value)]


def _substitute(value: str, env: Dict[str, str]) -> str:
    def _replace(m: re.Match) -> str:
        name = m.group(1) or m.group(2)
        return env.get(name, m.group(0))

    return _REF_RE.sub(_replace, value)


def interpolate_env(
    env: Dict[str, str],
    external: Optional[Dict[str, str]] = None,
    max_passes: int = 10,
) -> InterpolationResult:
    """Resolve all ``${VAR}`` / ``$VAR`` references in *env*.

    Parameters
    ----------
    env:
        The parsed key/value mapping to resolve in-place.
    external:
        Optional extra variables (e.g. OS environment) used as fallback.
    max_passes:
        Safety limit to break out of circular references.
    """
    result = InterpolationResult()
    combined: Dict[str, str] = {**(external or {}), **env}
    resolved = dict(combined)

    for _ in range(max_passes):
        changed = False
        for key, value in list(resolved.items()):
            if key not in env:
                continue  # don't mutate external
            new_value = _substitute(value, resolved)
            if new_value != value:
                resolved[key] = new_value
                changed = True
        if not changed:
            break
    else:
        # Detect remaining cycles
        for key in env:
            refs = _refs_in(resolved[key])
            if refs:
                result.cycles.append(key)

    for key in env:
        remaining = _refs_in(resolved[key])
        if remaining:
            result.unresolved[key] = remaining
        else:
            result.resolved[key] = resolved[key]

    return result

"""redactor.py — utilities for redacting sensitive values in .env output.

Provides pattern-based redaction so that secret keys, tokens, and passwords
are never accidentally printed to the terminal or written to reports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# Default patterns whose *keys* suggest the value is sensitive.
_DEFAULT_SENSITIVE_PATTERNS: list[str] = [
    r"(?i)secret",
    r"(?i)password",
    r"(?i)passwd",
    r"(?i)token",
    r"(?i)api[_\-]?key",
    r"(?i)private[_\-]?key",
    r"(?i)auth",
    r"(?i)credential",
    r"(?i)access[_\-]?key",
    r"(?i)signing[_\-]?key",
]

REDACTED_PLACEHOLDER = "***REDACTED***"


@dataclass
class Redactor:
    """Decides whether a key's value should be hidden and performs the masking.

    Parameters
    ----------
    patterns:
        List of regex patterns matched against *key names*.  If any pattern
        matches the key, the value is considered sensitive.
    placeholder:
        String substituted in place of a sensitive value.
    extra_keys:
        Explicit set of key names (case-insensitive) that are always redacted,
        regardless of pattern matching.
    """

    patterns: list[str] = field(default_factory=lambda: list(_DEFAULT_SENSITIVE_PATTERNS))
    placeholder: str = REDACTED_PLACEHOLDER
    extra_keys: set[str] = field(default_factory=set)

    # compiled regexes — built lazily on first use
    _compiled: list[re.Pattern[str]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._compile()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_sensitive(self, key: str) -> bool:
        """Return True if *key* matches any sensitive pattern or extra_keys."""
        if key.upper() in {k.upper() for k in self.extra_keys}:
            return True
        return any(rx.search(key) for rx in self._compiled)

    def redact(self, key: str, value: str) -> str:
        """Return *value* unchanged, or the placeholder if the key is sensitive."""
        return self.placeholder if self.is_sensitive(key) else value

    def redact_dict(self, env: dict[str, str]) -> dict[str, str]:
        """Return a copy of *env* with sensitive values replaced."""
        return {k: self.redact(k, v) for k, v in env.items()}

    def add_pattern(self, pattern: str) -> None:
        """Append a new regex pattern and recompile."""
        self.patterns.append(pattern)
        self._compile()

    def add_key(self, key: str) -> None:
        """Mark an explicit key name as sensitive."""
        self.extra_keys.add(key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compile(self) -> None:
        self._compiled = [re.compile(p) for p in self.patterns]


# ---------------------------------------------------------------------------
# Module-level convenience helpers
# ---------------------------------------------------------------------------

_default_redactor = Redactor()


def is_sensitive(key: str) -> bool:
    """Return True if *key* looks sensitive using the default pattern set."""
    return _default_redactor.is_sensitive(key)


def redact_dict(
    env: dict[str, str],
    *,
    extra_keys: Iterable[str] = (),
    placeholder: str = REDACTED_PLACEHOLDER,
) -> dict[str, str]:
    """Convenience wrapper: redact sensitive values in *env* and return a new dict.

    Parameters
    ----------
    env:
        Mapping of key → value (as returned by ``parse_env_file``).
    extra_keys:
        Additional key names to treat as sensitive for this call only.
    placeholder:
        Override the default redaction placeholder.
    """
    r = Redactor(
        patterns=list(_DEFAULT_SENSITIVE_PATTERNS),
        placeholder=placeholder,
        extra_keys=set(extra_keys),
    )
    return r.redact_dict(env)

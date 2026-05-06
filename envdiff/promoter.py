"""Promote keys from one environment file to another.

Copies keys (and optionally their values) from a source .env file into a
target .env file, skipping keys that already exist in the target unless
``overwrite=True`` is requested.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.core import parse_env_file


@dataclass
class PromoteResult:
    added: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.added or self.overwritten)

    def to_dict(self) -> Dict:
        return {
            "added": self.added,
            "skipped": self.skipped,
            "overwritten": self.overwritten,
        }


def promote_env_file(
    source: Path,
    target: Path,
    keys: List[str] | None = None,
    overwrite: bool = False,
    redact_values: bool = False,
    dry_run: bool = False,
) -> PromoteResult:
    """Promote *keys* from *source* into *target*.

    Parameters
    ----------
    source:
        The .env file to read values from.
    target:
        The .env file to write promoted keys into.  It is created if it does
        not exist.
    keys:
        Explicit list of keys to promote.  When ``None`` all keys from
        *source* are candidates.
    overwrite:
        When ``True``, existing keys in *target* are updated to the source
        value.
    redact_values:
        When ``True``, promoted keys are written with an empty value instead
        of the actual value from *source*.
    dry_run:
        When ``True``, no files are written; the result still reflects what
        *would* change.
    """
    src_env: Dict[str, str] = parse_env_file(source)
    tgt_env: Dict[str, str] = parse_env_file(target) if target.exists() else {}

    candidates = keys if keys is not None else list(src_env.keys())

    result = PromoteResult()
    new_lines: List[str] = []

    for key in candidates:
        if key not in src_env:
            continue
        value = "" if redact_values else src_env[key]
        if key in tgt_env:
            if overwrite:
                result.overwritten.append(key)
                tgt_env[key] = value
            else:
                result.skipped.append(key)
        else:
            result.added.append(key)
            tgt_env[key] = value

    if not dry_run and result.changed:
        # Preserve existing lines and append / update in place.
        existing_lines: List[str] = []
        if target.exists():
            existing_lines = target.read_text().splitlines(keepends=True)

        updated_keys: set = set(result.overwritten)
        out_lines: List[str] = []
        for line in existing_lines:
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                k = stripped.split("=", 1)[0].strip()
                if k in updated_keys:
                    out_lines.append(f"{k}={tgt_env[k]}\n")
                    updated_keys.discard(k)
                    continue
            out_lines.append(line)

        for key in result.added:
            out_lines.append(f"{key}={tgt_env[key]}\n")

        target.write_text("".join(out_lines))

    return result

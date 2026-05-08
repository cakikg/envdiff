"""Key-value transformer: apply a mapping of old->new values across one or more .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.core import parse_env_file


@dataclass
class TransformResult:
    file: str
    changed: bool
    replacements: Dict[str, str] = field(default_factory=dict)  # key -> new_value
    lines: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "changed": self.changed,
            "replacements": self.replacements,
        }


def _transform_line(line: str, mapping: Dict[str, str]) -> tuple[str, Optional[str]]:
    """Return (new_line, key_if_replaced | None)."""
    stripped = line.rstrip("\n")
    if "=" not in stripped or stripped.lstrip().startswith("#"):
        return line, None
    key, _, _val = stripped.partition("=")
    key_clean = key.strip()
    if key_clean in mapping:
        new_val = mapping[key_clean]
        new_line = f"{key}={new_val}\n"
        return new_line, key_clean
    return line, None


def transform_env_file(
    path: Path,
    mapping: Dict[str, str],
    *,
    dry_run: bool = False,
) -> TransformResult:
    """Replace values for keys listed in *mapping* inside *path*."""
    raw_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines: List[str] = []
    replacements: Dict[str, str] = {}

    for line in raw_lines:
        new_line, key = _transform_line(line, mapping)
        new_lines.append(new_line)
        if key is not None:
            replacements[key] = mapping[key]

    changed = bool(replacements)
    if changed and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")

    return TransformResult(
        file=str(path),
        changed=changed,
        replacements=replacements,
        lines=new_lines,
    )


def transform_many(
    paths: List[Path],
    mapping: Dict[str, str],
    *,
    dry_run: bool = False,
) -> List[TransformResult]:
    return [transform_env_file(p, mapping, dry_run=dry_run) for p in paths]

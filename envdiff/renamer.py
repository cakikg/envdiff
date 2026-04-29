"""Rename a key across one or more .env files, preserving formatting."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


@dataclass
class RenameResult:
    path: Path
    old_key: str
    new_key: str
    replaced: bool = False
    dry_run: bool = False
    original_lines: List[str] = field(default_factory=list, repr=False)
    patched_lines: List[str] = field(default_factory=list, repr=False)

    @property
    def changed(self) -> bool:
        return self.replaced


def _rename_in_lines(
    lines: List[str], old_key: str, new_key: str
) -> Tuple[List[str], bool]:
    """Return (new_lines, was_replaced)."""
    pattern = re.compile(r"^(\s*)" + re.escape(old_key) + r"(\s*=)")
    result: List[str] = []
    replaced = False
    for line in lines:
        m = pattern.match(line)
        if m:
            line = pattern.sub(rf"\g<1>{new_key}\g<2>", line)
            replaced = True
        result.append(line)
    return result, replaced


def rename_key(
    path: Path,
    old_key: str,
    new_key: str,
    *,
    dry_run: bool = False,
) -> RenameResult:
    """Rename *old_key* to *new_key* inside *path*.

    Returns a :class:`RenameResult` describing what happened.
    When *dry_run* is ``True`` the file is never written.
    """
    original = path.read_text(encoding="utf-8").splitlines(keepends=True)
    patched, replaced = _rename_in_lines(original, old_key, new_key)

    result = RenameResult(
        path=path,
        old_key=old_key,
        new_key=new_key,
        replaced=replaced,
        dry_run=dry_run,
        original_lines=original,
        patched_lines=patched,
    )

    if replaced and not dry_run:
        path.write_text("".join(patched), encoding="utf-8")

    return result


def rename_key_in_many(
    paths: List[Path],
    old_key: str,
    new_key: str,
    *,
    dry_run: bool = False,
) -> List[RenameResult]:
    """Apply :func:`rename_key` to every path in *paths*."""
    return [rename_key(p, old_key, new_key, dry_run=dry_run) for p in paths]

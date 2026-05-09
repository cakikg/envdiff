"""Split a .env file into multiple files based on key prefixes or groups."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.grouper import group_env_file


@dataclass
class SplitResult:
    source: str
    outputs: Dict[str, str] = field(default_factory=dict)   # group -> file path
    keys_written: Dict[str, List[str]] = field(default_factory=dict)
    dry_run: bool = False

    @property
    def changed(self) -> bool:
        return bool(self.outputs)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "dry_run": self.dry_run,
            "outputs": self.outputs,
            "keys_written": self.keys_written,
        }


def split_env_file(
    source: str,
    output_dir: str,
    prefix: Optional[str] = None,
    dry_run: bool = False,
) -> SplitResult:
    """Split *source* into one file per prefix-group inside *output_dir*.

    If *prefix* is given only that group is written; otherwise every group
    discovered by :func:`~envdiff.grouper.group_env_file` is written.
    """
    report = group_env_file(source)
    result = SplitResult(source=source, dry_run=dry_run)

    groups = [prefix] if prefix else report.group_names()
    if not groups:
        return result

    os.makedirs(output_dir, exist_ok=True)

    for group in groups:
        keys = report.keys_in(group)
        if not keys:
            continue

        out_path = str(Path(output_dir) / f"{group.lower()}.env")
        lines: List[str] = []
        raw = report.to_dict()["groups"].get(group, {})
        for key in keys:
            value = raw.get(key, "")
            lines.append(f"{key}={value}\n")

        if not dry_run:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.writelines(lines)

        result.outputs[group] = out_path
        result.keys_written[group] = list(keys)

    return result

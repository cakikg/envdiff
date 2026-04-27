"""Apply a diff to a .env file, adding missing keys and optionally updating changed ones."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from envdiff.differ import ValueDiff, is_added, is_removed, is_changed


def _read_lines(path: Path) -> List[str]:
    """Return raw lines from *path*, or empty list if the file does not exist."""
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def _build_patch_block(diffs: Dict[str, ValueDiff], update_changed: bool) -> List[str]:
    """Return lines to append for keys that are missing or (optionally) changed."""
    lines: List[str] = []
    for key, vd in sorted(diffs.items()):
        if is_added(vd):
            # Key exists in source but not in target — add it.
            lines.append(f"{key}={vd.source_value}\n")
        elif is_changed(vd) and update_changed:
            # Key exists in both but values differ — overwrite handled below.
            pass  # changed keys are handled in-place by patch_env_file
    return lines


def patch_env_file(
    target_path: Path,
    diffs: Dict[str, ValueDiff],
    *,
    update_changed: bool = False,
    dry_run: bool = False,
) -> Dict[str, str]:
    """Patch *target_path* according to *diffs*.

    Parameters
    ----------
    target_path:
        The .env file to update.
    diffs:
        Mapping returned by :func:`envdiff.differ.unified_value_diff`.
    update_changed:
        When *True*, lines whose keys appear as *changed* in *diffs* are
        rewritten with the source value.
    dry_run:
        When *True*, return the would-be content without writing anything.

    Returns
    -------
    dict mapping action -> list-of-keys that were affected, plus
    a special ``"content"`` key holding the final file text.
    """
    lines = _read_lines(target_path)
    report: Dict[str, list] = {"added": [], "updated": [], "removed": [], "skipped": []}

    # Rewrite existing lines for *changed* keys when requested.
    new_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in diffs and is_changed(diffs[key]) and update_changed:
            new_lines.append(f"{key}={diffs[key].source_value}\n")
            report["updated"].append(key)
        elif key in diffs and is_removed(diffs[key]):
            report["skipped"].append(key)  # we never delete keys automatically
            new_lines.append(line)
        else:
            new_lines.append(line)

    # Append genuinely missing keys.
    added_keys = [k for k, v in diffs.items() if is_added(v)]
    if added_keys:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append("# patched by envdiff\n")
        for key in sorted(added_keys):
            new_lines.append(f"{key}={diffs[key].source_value}\n")
            report["added"].append(key)

    content = "".join(new_lines)
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")

    report["content"] = content  # type: ignore[assignment]
    return report

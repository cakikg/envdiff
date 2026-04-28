"""Sort and reorder keys in a .env file."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Tuple

# A parsed line is either (key, raw_line) or (None, raw_line) for comments/blanks
_KV_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=')


def _parse_lines(lines: List[str]) -> List[Tuple[Optional[str], str]]:
    """Return list of (key_or_None, raw_line) pairs."""
    result = []
    for line in lines:
        stripped = line.rstrip("\n")
        m = _KV_RE.match(stripped)
        result.append((m.group(1) if m else None, line))
    return result


def sort_env_file(
    path: str | Path,
    *,
    reverse: bool = False,
    group_comments: bool = True,
    dry_run: bool = False,
) -> str:
    """Sort keys in *path* alphabetically and return the resulting text.

    Parameters
    ----------
    path:
        Path to the .env file to sort.
    reverse:
        Sort in descending order when True.
    group_comments:
        When True, a comment line immediately preceding a key line is kept
        attached to that key during sorting.
    dry_run:
        When True the file is not written; only the sorted text is returned.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)

    parsed = _parse_lines(lines)

    # Build blocks: list of (key_or_None, [lines])
    # A block is a key line optionally preceded by its comment lines.
    blocks: List[Tuple[Optional[str], List[str]]] = []
    pending_comments: List[str] = []

    for key, line in parsed:
        if key is None:
            if group_comments and line.lstrip().startswith("#"):
                pending_comments.append(line)
            else:
                # blank line — flush pending comments as standalone block
                for c in pending_comments:
                    blocks.append((None, [c]))
                pending_comments = []
                blocks.append((None, [line]))
        else:
            block_lines = pending_comments + [line]
            pending_comments = []
            blocks.append((key, block_lines))

    # Flush any trailing comments
    for c in pending_comments:
        blocks.append((None, [c]))

    # Separate key blocks from non-key blocks (blanks / standalone comments)
    key_blocks = [(k, ls) for k, ls in blocks if k is not None]
    other_blocks = [(k, ls) for k, ls in blocks if k is None]

    key_blocks.sort(key=lambda t: t[0].lower(), reverse=reverse)  # type: ignore[arg-type]

    # Reassemble: other (leading blanks/comments) first, then sorted keys
    # Preserve leading non-key lines in their original positions is complex;
    # simplest useful behaviour: leading blanks/comments stay at top.
    leading = []
    trailing_others = list(other_blocks)
    # Heuristic: blanks/comments before the first key stay leading
    first_key_index = next((i for i, (k, _) in enumerate(blocks) if k is not None), None)
    if first_key_index is not None:
        leading = [ls for _, ls in blocks[:first_key_index] if _ is None]
        trailing_others = []

    result_lines: List[str] = []
    for ls in leading:
        result_lines.extend(ls)
    for _, ls in key_blocks:
        result_lines.extend(ls)
    for _, ls in trailing_others:
        result_lines.extend(ls)

    output = "".join(result_lines)
    if not dry_run:
        path.write_text(output, encoding="utf-8")
    return output

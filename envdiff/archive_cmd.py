"""CLI command handlers for the archive sub-command."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from envdiff.archiver import ArchiveResult, archive_env_files, extract_archive, list_archive


def _render_text(result: ArchiveResult) -> None:
    print(f"Archive created: {result.archive_path}")
    print(f"Files bundled : {len(result.files_added)}")
    for name in result.files_added:
        print(f"  - {name}")
    print(f"Size           : {result.size_bytes} bytes")


def _render_json(result: ArchiveResult) -> None:
    print(json.dumps(result.to_dict(), indent=2))


def run_archive_create(args) -> int:  # noqa: ANN001
    paths: List[Path] = []
    for raw in args.files:
        p = Path(raw)
        if not p.exists():
            print(f"error: file not found: {raw}", file=sys.stderr)
            return 1
        paths.append(p)

    dest = Path(args.output)
    try:
        result = archive_env_files(
            paths,
            dest,
            redact=not args.no_redact,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "format", "text") == "json":
        _render_json(result)
    else:
        _render_text(result)
    return 0


def run_archive_list(args) -> int:  # noqa: ANN001
    path = Path(args.archive)
    if not path.exists():
        print(f"error: archive not found: {args.archive}", file=sys.stderr)
        return 1
    names = list_archive(path)
    if getattr(args, "format", "text") == "json":
        print(json.dumps(names, indent=2))
    else:
        for name in names:
            print(name)
    return 0


def run_archive_extract(args) -> int:  # noqa: ANN001
    path = Path(args.archive)
    if not path.exists():
        print(f"error: archive not found: {args.archive}", file=sys.stderr)
        return 1
    dest_dir = Path(args.dest)
    extracted = extract_archive(path, dest_dir)
    if getattr(args, "format", "text") == "json":
        print(json.dumps([str(p) for p in extracted], indent=2))
    else:
        print(f"Extracted {len(extracted)} file(s) to {dest_dir}")
        for p in extracted:
            print(f"  - {p}")
    return 0

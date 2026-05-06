"""CLI command: envdiff frequency — show key-frequency report across .env files."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.differ2 import analyze_frequency


def _render_text(report, show_rare: bool, threshold: float) -> str:
    lines = [f"Analyzed {report.total_files} file(s)\n"]
    lines.append(f"{'KEY':<40} {'COUNT':>6}  {'COVERAGE':>8}")
    lines.append("-" * 58)
    for key in sorted(report.counts):
        cov = report.coverage(key)
        marker = "" if cov >= threshold else "  [rare]"
        lines.append(f"{key:<40} {report.counts[key]:>6}  {cov:>7.1%}{marker}")
    if show_rare:
        rare = report.rare_keys(threshold)
        lines.append(f"\nRare keys (< {threshold:.0%} coverage): {len(rare)}")
        for k in rare:
            lines.append(f"  - {k}")
    return "\n".join(lines)


def _render_json(report) -> str:
    return json.dumps(report.to_dict(), indent=2)


def run_frequency(args: Namespace) -> int:
    paths = [Path(f) for f in args.files]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for m in missing:
            print(f"error: file not found: {m}", file=sys.stderr)
        return 1

    report = analyze_frequency(paths)
    threshold = getattr(args, "threshold", 1.0)
    show_rare = getattr(args, "show_rare", False)

    if getattr(args, "format", "text") == "json":
        print(_render_json(report))
    else:
        print(_render_text(report, show_rare=show_rare, threshold=threshold))

    return 0

"""CLI command: envdiff score — report quality score for one or more .env files."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from typing import List

from envdiff.scorer import ScoreReport, score_env_file


def _render_text(reports: List[ScoreReport]) -> str:
    lines = []
    for r in reports:
        lines.append(f"{r.file}  score={r.score}/{r.max_score}  grade={r.grade}")
        for p in r.penalties:
            lines.append(f"  - {p}")
        if not r.penalties:
            lines.append("  (no issues found)")
    return "\n".join(lines)


def _render_json(reports: List[ScoreReport]) -> str:
    return json.dumps([r.to_dict() for r in reports], indent=2)


def run_score(args: Namespace) -> int:
    reports: List[ScoreReport] = []
    exit_code = 0

    for path in args.files:
        try:
            report = score_env_file(path)
            reports.append(report)
            if report.score < (args.min_score or 0):
                exit_code = 1
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1

    if getattr(args, "format", "text") == "json":
        print(_render_json(reports))
    else:
        print(_render_text(reports))

    return exit_code

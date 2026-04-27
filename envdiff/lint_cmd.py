"""CLI command handler for the 'lint' subcommand."""
from __future__ import annotations

import json
import sys
from typing import List

from envdiff.linter import LintIssue, LintResult, lint_env_file


def _severity_prefix(issue: LintIssue, use_color: bool) -> str:
    if not use_color:
        return f"[{issue.severity.upper()}]"
    color = "\033[31m" if issue.severity == "error" else "\033[33m"
    return f"{color}[{issue.severity.upper()}]\033[0m"


def _render_text(path: str, result: LintResult, use_color: bool) -> List[str]:
    lines = [f"Linting: {path}"]
    if not result.issues:
        ok = "\033[32mOK\033[0m" if use_color else "OK"
        lines.append(f"  {ok} — no issues found")
    else:
        for issue in result.issues:
            prefix = _severity_prefix(issue, use_color)
            key_part = f" ({issue.key})" if issue.key else ""
            lines.append(f"  {prefix} line {issue.line}{key_part}: {issue.message}")
    return lines


def _render_json(path: str, result: LintResult) -> dict:
    return {
        "file": path,
        "ok": result.ok(),
        "issues": [
            {
                "line": i.line,
                "key": i.key,
                "severity": i.severity,
                "message": i.message,
            }
            for i in result.issues
        ],
    }


def run_lint(args) -> int:
    """Run lint for one or more .env files. Returns exit code."""
    use_color = getattr(args, "color", True)
    as_json = getattr(args, "format", "text") == "json"

    all_results = []
    exit_code = 0

    for path in args.files:
        try:
            result = lint_env_file(path)
        except FileNotFoundError:
            msg = {"file": path, "ok": False, "issues": [{"line": 0, "key": None, "severity": "error", "message": "File not found"}]}
            if as_json:
                all_results.append(msg)
            else:
                print(f"ERROR: File not found: {path}", file=sys.stderr)
            exit_code = 1
            continue

        if not result.ok():
            exit_code = 1

        if as_json:
            all_results.append(_render_json(path, result))
        else:
            for line in _render_text(path, result, use_color):
                print(line)

    if as_json:
        print(json.dumps(all_results, indent=2))

    return exit_code

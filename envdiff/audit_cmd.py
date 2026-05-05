"""CLI command handlers for the audit subcommand."""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from envdiff.auditor import (
    AuditEntry,
    _DEFAULT_AUDIT_DIR,
    clear_audit_log,
    list_entries,
    record,
)


def _entry_text(entry: AuditEntry) -> str:
    files = ", ".join(entry.files) if entry.files else "(none)"
    return f"[{entry.timestamp}] {entry.user} {entry.operation}: {files}"


def run_audit_list(args: Namespace) -> int:
    audit_dir = Path(getattr(args, "audit_dir", _DEFAULT_AUDIT_DIR))
    entries = list_entries(audit_dir)
    if not entries:
        print("No audit entries found.")
        return 0
    if getattr(args, "format", "text") == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            print(_entry_text(e))
            if getattr(args, "verbose", False) and e.details:
                for k, v in e.details.items():
                    print(f"  {k}: {v}")
    return 0


def run_audit_record(args: Namespace) -> int:
    """Manually record an audit entry (useful for scripting)."""
    audit_dir = Path(getattr(args, "audit_dir", _DEFAULT_AUDIT_DIR))
    entry = AuditEntry(
        operation=args.operation,
        files=args.files or [],
        details={"note": args.note} if getattr(args, "note", None) else {},
    )
    path = record(entry, audit_dir=audit_dir)
    print(f"Recorded audit entry: {path}")
    return 0


def run_audit_clear(args: Namespace) -> int:
    audit_dir = Path(getattr(args, "audit_dir", _DEFAULT_AUDIT_DIR))
    if not getattr(args, "yes", False):
        confirm = input("Delete all audit entries? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 1
    removed = clear_audit_log(audit_dir)
    print(f"Removed {removed} audit entries.")
    return 0

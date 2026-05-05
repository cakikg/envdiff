"""Tests for envdiff.audit_cmd."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.auditor import AuditEntry, record
from envdiff.audit_cmd import run_audit_clear, run_audit_list, run_audit_record


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def _args(**kwargs) -> Namespace:
    defaults = {"format": "text", "verbose": False, "audit_dir": None}
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_list_empty_exits_zero(audit_dir: Path, capsys) -> None:
    rc = run_audit_list(_args(audit_dir=audit_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit entries" in out


def test_list_shows_entries(audit_dir: Path, capsys) -> None:
    record(AuditEntry(operation="diff", files=[".env"]), audit_dir=audit_dir)
    rc = run_audit_list(_args(audit_dir=audit_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "diff" in out
    assert ".env" in out


def test_list_json_format(audit_dir: Path, capsys) -> None:
    record(AuditEntry(operation="lint", files=[".env"]), audit_dir=audit_dir)
    rc = run_audit_list(_args(audit_dir=audit_dir, format="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["operation"] == "lint"


def test_list_verbose_shows_details(audit_dir: Path, capsys) -> None:
    record(
        AuditEntry(operation="merge", files=[], details={"strategy": "last"}),
        audit_dir=audit_dir,
    )
    rc = run_audit_list(_args(audit_dir=audit_dir, verbose=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "strategy" in out


def test_record_cmd_creates_entry(audit_dir: Path, capsys) -> None:
    args = _args(audit_dir=audit_dir, operation="diff", files=[".env"], note=None)
    rc = run_audit_record(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Recorded" in out


def test_clear_with_yes_flag(audit_dir: Path, capsys) -> None:
    record(AuditEntry(operation="diff", files=[]), audit_dir=audit_dir)
    rc = run_audit_clear(_args(audit_dir=audit_dir, yes=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Removed 1" in out


def test_clear_aborted_without_confirmation(audit_dir: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")
    rc = run_audit_clear(_args(audit_dir=audit_dir, yes=False))
    assert rc == 1
    out = capsys.readouterr().out
    assert "Aborted" in out

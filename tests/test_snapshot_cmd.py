"""Integration tests for envdiff.snapshot_cmd."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.snapshot_cmd import (
    run_snapshot_delete,
    run_snapshot_diff,
    run_snapshot_list,
    run_snapshot_save,
)
from envdiff.snapshotter import save_snapshot


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snaps"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


def test_save_exits_zero(env_file: Path, snap_dir: Path) -> None:
    code = run_snapshot_save(str(env_file), "snap1", snapshot_dir=snap_dir)
    assert code == 0


def test_save_missing_file_exits_one(snap_dir: Path) -> None:
    code = run_snapshot_save("/no/such/.env", "x", snapshot_dir=snap_dir)
    assert code == 1


def test_list_exits_zero_empty(snap_dir: Path, capsys) -> None:
    code = run_snapshot_list(snapshot_dir=snap_dir)
    assert code == 0
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_list_shows_saved_name(env_file: Path, snap_dir: Path, capsys) -> None:
    run_snapshot_save(str(env_file), "mysnap", snapshot_dir=snap_dir)
    run_snapshot_list(snapshot_dir=snap_dir)
    out = capsys.readouterr().out
    assert "mysnap" in out


def test_diff_no_change_exits_zero(env_file: Path, snap_dir: Path) -> None:
    run_snapshot_save(str(env_file), "same", snapshot_dir=snap_dir)
    code = run_snapshot_diff("same", str(env_file), snapshot_dir=snap_dir)
    assert code == 0


def test_diff_with_change_exits_one(tmp_path: Path, snap_dir: Path) -> None:
    old = tmp_path / "old.env"
    old.write_text("FOO=old\n")
    new = tmp_path / "new.env"
    new.write_text("FOO=new\n")
    run_snapshot_save(str(old), "chg", snapshot_dir=snap_dir)
    code = run_snapshot_diff("chg", str(new), snapshot_dir=snap_dir)
    assert code == 1


def test_diff_missing_snapshot_exits_one(env_file: Path, snap_dir: Path) -> None:
    code = run_snapshot_diff("ghost", str(env_file), snapshot_dir=snap_dir)
    assert code == 1


def test_delete_exits_zero(snap_dir: Path) -> None:
    save_snapshot({}, "todel", snapshot_dir=snap_dir)
    code = run_snapshot_delete("todel", snapshot_dir=snap_dir)
    assert code == 0


def test_delete_missing_exits_one(snap_dir: Path) -> None:
    code = run_snapshot_delete("nope", snapshot_dir=snap_dir)
    assert code == 1

"""Integration tests: tagger + tag_cmd working end-to-end."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.tag_cmd import run_tag_add, run_tag_list, run_tag_remove
from envdiff.tagger import keys_with_label, load_tags


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "API_KEY=secret\n"
        "LOG_LEVEL=debug\n"
    )
    return p


def _args(**kw) -> Namespace:
    base = {"format": "text", "dry_run": False, "label": None}
    base.update(kw)
    return Namespace(**base)


def test_full_tag_lifecycle(env_file: Path) -> None:
    """Add, verify, then remove a label; check state at each step."""
    run_tag_add(_args(file=str(env_file), key="DB_HOST", label="infra"))
    run_tag_add(_args(file=str(env_file), key="DB_PORT", label="infra"))
    run_tag_add(_args(file=str(env_file), key="API_KEY", label="sensitive"))

    assert set(keys_with_label(env_file, "infra")) == {"DB_HOST", "DB_PORT"}
    assert keys_with_label(env_file, "sensitive") == ["API_KEY"]

    run_tag_remove(_args(file=str(env_file), key="DB_HOST", label="infra"))
    assert keys_with_label(env_file, "infra") == ["DB_PORT"]


def test_list_all_tags_json(env_file: Path, capsys) -> None:
    run_tag_add(_args(file=str(env_file), key="API_KEY", label="sensitive"))
    run_tag_add(_args(file=str(env_file), key="API_KEY", label="required"))
    run_tag_list(_args(file=str(env_file), format="json"))
    data = json.loads(capsys.readouterr().out)
    assert "sensitive" in data["API_KEY"]
    assert "required" in data["API_KEY"]


def test_duplicate_tag_not_doubled(env_file: Path) -> None:
    run_tag_add(_args(file=str(env_file), key="LOG_LEVEL", label="debug"))
    run_tag_add(_args(file=str(env_file), key="LOG_LEVEL", label="debug"))
    tags = load_tags(env_file)
    assert tags["LOG_LEVEL"].count("debug") == 1


def test_remove_all_labels_clears_key(env_file: Path) -> None:
    run_tag_add(_args(file=str(env_file), key="DB_HOST", label="infra"))
    run_tag_remove(_args(file=str(env_file), key="DB_HOST", label=None))
    assert "DB_HOST" not in load_tags(env_file)

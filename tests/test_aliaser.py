"""Tests for envdiff.aliaser and envdiff.alias_cmd."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

import pytest

from envdiff.aliaser import AliasEntry, AliasReport, check_aliases, load_aliases
from envdiff.alias_cmd import run_alias


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _alias_file(directory: Path, mapping: dict) -> Path:
    p = directory / "aliases.json"
    p.write_text(json.dumps(mapping))
    return p


# --- load_aliases ---

def test_load_aliases_returns_mapping(tmp_env):
    af = _alias_file(tmp_env, {"OLD_KEY": "NEW_KEY"})
    aliases = load_aliases(af)
    assert aliases == {"OLD_KEY": "NEW_KEY"}


def test_load_aliases_missing_file_raises(tmp_env):
    with pytest.raises(FileNotFoundError):
        load_aliases(tmp_env / "nonexistent.json")


def test_load_aliases_non_object_raises(tmp_env):
    p = tmp_env / "bad.json"
    p.write_text(json.dumps(["OLD_KEY"]))
    with pytest.raises(ValueError):
        load_aliases(p)


# --- check_aliases ---

def test_clean_file_returns_empty_report(tmp_env):
    env = _write(tmp_env, ".env", "NEW_KEY=value\n")
    af = _alias_file(tmp_env, {"OLD_KEY": "NEW_KEY"})
    aliases = load_aliases(af)
    report = check_aliases([env], aliases)
    assert report.clean is True
    assert report.hits == []


def test_deprecated_key_detected(tmp_env):
    env = _write(tmp_env, ".env", "OLD_KEY=value\n")
    af = _alias_file(tmp_env, {"OLD_KEY": "NEW_KEY"})
    aliases = load_aliases(af)
    report = check_aliases([env], aliases)
    assert not report.clean
    assert len(report.hits) == 1
    assert report.hits[0].old_key == "OLD_KEY"
    assert report.hits[0].new_key == "NEW_KEY"


def test_files_affected_lists_correct_paths(tmp_env):
    env1 = _write(tmp_env, ".env.dev", "OLD_KEY=a\n")
    env2 = _write(tmp_env, ".env.prod", "NEW_KEY=b\n")
    aliases = {"OLD_KEY": "NEW_KEY"}
    report = check_aliases([env1, env2], aliases)
    assert str(env1) in report.hits[0].files_affected
    assert str(env2) not in report.hits[0].files_affected


def test_to_dict_structure(tmp_env):
    env = _write(tmp_env, ".env", "OLD_KEY=1\n")
    aliases = {"OLD_KEY": "NEW_KEY"}
    report = check_aliases([env], aliases)
    d = report.to_dict()
    assert "clean" in d
    assert "hits" in d
    assert d["hits"][0]["old_key"] == "OLD_KEY"


# --- run_alias ---

def _args(alias_file, files, fmt="text"):
    ns = argparse.Namespace()
    ns.alias_file = str(alias_file)
    ns.files = [str(f) for f in files]
    ns.format = fmt
    return ns


def test_clean_file_exits_zero(tmp_env):
    env = _write(tmp_env, ".env", "NEW_KEY=ok\n")
    af = _alias_file(tmp_env, {"OLD_KEY": "NEW_KEY"})
    assert run_alias(_args(af, [env])) == 0


def test_deprecated_key_exits_one(tmp_env):
    env = _write(tmp_env, ".env", "OLD_KEY=legacy\n")
    af = _alias_file(tmp_env, {"OLD_KEY": "NEW_KEY"})
    assert run_alias(_args(af, [env])) == 1


def test_missing_alias_file_exits_one(tmp_env):
    env = _write(tmp_env, ".env", "KEY=val\n")
    assert run_alias(_args(tmp_env / "nope.json", [env])) == 1


def test_missing_env_file_exits_one(tmp_env):
    af = _alias_file(tmp_env, {"OLD": "NEW"})
    assert run_alias(_args(af, [tmp_env / "missing.env"])) == 1


def test_json_format_output(tmp_env, capsys):
    env = _write(tmp_env, ".env", "OLD_KEY=x\n")
    af = _alias_file(tmp_env, {"OLD_KEY": "NEW_KEY"})
    run_alias(_args(af, [env], fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "hits" in data
    assert data["clean"] is False

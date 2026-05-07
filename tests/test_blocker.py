"""Tests for envdiff.blocker."""
from pathlib import Path

import pytest

from envdiff.blocker import BlockRule, BlockReport, BlockViolation, check_env_file


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p

    return _write


def test_clean_file_returns_no_violations(tmp_env):
    p = tmp_env("DB_HOST=localhost\nDB_PASS=s3cr3t\n")
    rules = [BlockRule(key="DB_HOST"), BlockRule(key="DB_PASS")]
    report = check_env_file(p, rules)
    assert report.clean
    assert report.violations == []


def test_missing_required_key_is_violation(tmp_env):
    p = tmp_env("DB_HOST=localhost\n")
    rules = [BlockRule(key="DB_HOST"), BlockRule(key="DB_PASS")]
    report = check_env_file(p, rules)
    assert not report.clean
    assert len(report.violations) == 1
    assert report.violations[0].key == "DB_PASS"
    assert "missing" in report.violations[0].reason


def test_forbidden_pattern_triggers_violation(tmp_env):
    p = tmp_env("SECRET_KEY=changeme\n")
    rules = [BlockRule(key="SECRET_KEY", forbidden_pattern=r"^changeme$")]
    report = check_env_file(p, rules)
    assert not report.clean
    assert report.violations[0].key == "SECRET_KEY"
    assert "forbidden pattern" in report.violations[0].reason


def test_value_not_matching_pattern_is_ok(tmp_env):
    p = tmp_env("SECRET_KEY=xK9#mQ2!\n")
    rules = [BlockRule(key="SECRET_KEY", forbidden_pattern=r"^changeme$")]
    report = check_env_file(p, rules)
    assert report.clean


def test_optional_key_missing_is_not_violation(tmp_env):
    p = tmp_env("DB_HOST=localhost\n")
    rules = [BlockRule(key="OPTIONAL_KEY", required=False)]
    report = check_env_file(p, rules)
    assert report.clean


def test_multiple_violations_collected(tmp_env):
    p = tmp_env("DB_URL=postgres://user:pass@localhost/db\n")
    rules = [
        BlockRule(key="SECRET_KEY"),
        BlockRule(key="API_TOKEN"),
        BlockRule(key="DB_URL", forbidden_pattern=r"localhost"),
    ]
    report = check_env_file(p, rules)
    assert len(report.violations) == 3


def test_to_dict_structure(tmp_env):
    p = tmp_env("A=1\n")
    rules = [BlockRule(key="MISSING")]
    report = check_env_file(p, rules)
    d = report.to_dict()
    assert d["clean"] is False
    assert d["file"] == str(p)
    assert isinstance(d["violations"], list)
    assert d["violations"][0]["key"] == "MISSING"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        check_env_file(tmp_path / "nonexistent.env", [])


def test_env_overlay_provides_missing_key(tmp_env):
    """Keys from the *env* overlay should satisfy required rules."""
    p = tmp_env("DB_HOST=localhost\n")
    rules = [BlockRule(key="SECRET_KEY")]
    report = check_env_file(p, rules, env={"SECRET_KEY": "from-ci"})
    assert report.clean

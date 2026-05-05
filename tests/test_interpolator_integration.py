"""Integration tests combining parse_env_file + interpolate_env."""
from pathlib import Path

import pytest

from envdiff.core import parse_env_file
from envdiff.interpolator import interpolate_env


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "APP_ROOT=/srv/app\n"
        "LOG_DIR=${APP_ROOT}/logs\n"
        "DB_HOST=db.internal\n"
        "DB_URL=postgres://${DB_HOST}/mydb\n"
        "FULL_LOG=${LOG_DIR}/app.log\n"
    )
    return p


def test_all_keys_resolved(env_file):
    env = parse_env_file(str(env_file))
    result = interpolate_env(env)
    assert result.ok
    assert set(result.resolved.keys()) == set(env.keys())


def test_nested_chain_fully_resolved(env_file):
    env = parse_env_file(str(env_file))
    result = interpolate_env(env)
    assert result.resolved["FULL_LOG"] == "/srv/app/logs/app.log"


def test_db_url_resolved(env_file):
    env = parse_env_file(str(env_file))
    result = interpolate_env(env)
    assert result.resolved["DB_URL"] == "postgres://db.internal/mydb"


def test_partial_env_has_unresolved(tmp_path):
    p = tmp_path / ".env"
    p.write_text("GREETING=${SALUTATION} world\n")
    env = parse_env_file(str(p))
    result = interpolate_env(env)
    assert not result.ok
    assert "SALUTATION" in result.unresolved["GREETING"]

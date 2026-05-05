"""Tests for envdiff.grouper."""
from __future__ import annotations

import os
import textwrap

import pytest

from envdiff.grouper import GroupReport, common_prefixes, group_env_file


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


def test_groups_by_prefix(tmp_env):
    path = tmp_env("""
        DB_HOST=localhost
        DB_PORT=5432
        DB_NAME=mydb
        APP_DEBUG=true
        APP_ENV=production
        SECRET_KEY=abc
    """)
    report = group_env_file(path)
    assert "DB" in report.group_names
    assert "APP" in report.group_names
    assert set(report.keys_in("DB")) == {"DB_HOST", "DB_PORT", "DB_NAME"}
    assert set(report.keys_in("APP")) == {"APP_DEBUG", "APP_ENV"}


def test_ungrouped_single_segment_key(tmp_env):
    path = tmp_env("""
        PORT=8080
        HOST=0.0.0.0
        DB_URL=postgres://localhost/db
    """)
    report = group_env_file(path)
    assert "PORT" in report.ungrouped
    assert "HOST" in report.ungrouped
    assert "DB" in report.group_names


def test_to_dict_structure(tmp_env):
    path = tmp_env("""
        AWS_KEY=key
        AWS_SECRET=secret
        LONE=value
    """)
    report = group_env_file(path)
    d = report.to_dict()
    assert "groups" in d
    assert "ungrouped" in d
    assert "AWS" in d["groups"]
    assert "LONE" in d["ungrouped"]


def test_max_depth_two(tmp_env):
    path = tmp_env("""
        AWS_S3_BUCKET=my-bucket
        AWS_S3_REGION=us-east-1
        AWS_EC2_AMI=ami-123
    """)
    report = group_env_file(path, max_depth=2)
    assert "AWS_S3" in report.group_names
    assert "AWS_EC2" in report.group_names


def test_common_prefixes_filters_by_min_keys(tmp_env):
    path = tmp_env("""
        DB_HOST=localhost
        DB_PORT=5432
        APP_ENV=prod
    """)
    report = group_env_file(path)
    result = common_prefixes(report, min_keys=2)
    assert "DB" in result
    assert "APP" not in result


def test_empty_file_returns_empty_report(tmp_env):
    path = tmp_env("")
    report = group_env_file(path)
    assert report.groups == {}
    assert report.ungrouped == []


def test_min_prefix_length_respected(tmp_env):
    path = tmp_env("""
        A_VALUE=1
        A_OTHER=2
        DB_HOST=localhost
    """)
    report = group_env_file(path, min_prefix_length=2)
    assert "A" not in report.group_names
    assert "DB" in report.group_names
    assert "A_VALUE" in report.ungrouped
    assert "A_OTHER" in report.ungrouped

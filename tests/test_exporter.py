"""Tests for envdiff.exporter module."""
import pytest

from envdiff.exporter import export_dotenv_template, export_markdown


SAMPLE_DIFF = {
    "DB_HOST": {"status": "ok", "values": {"dev": "localhost", "prod": "localhost"}},
    "DB_PASS": {"status": "mismatch", "values": {"dev": "secret", "prod": "hunter2"}},
    "NEW_KEY": {"status": "missing", "values": {"dev": "value", "prod": None}},
}


class TestExportDotenvTemplate:
    def test_contains_all_keys(self):
        output = export_dotenv_template(SAMPLE_DIFF)
        assert "DB_HOST=" in output
        assert "DB_PASS=" in output
        assert "NEW_KEY=" in output

    def test_values_redacted_by_default(self):
        output = export_dotenv_template(SAMPLE_DIFF)
        assert "localhost" not in output
        assert "secret" not in output

    def test_values_included_when_requested(self):
        output = export_dotenv_template(SAMPLE_DIFF, include_values=True)
        assert "localhost" in output
        # mismatch: first non-None value should appear
        assert "secret" in output or "hunter2" in output

    def test_missing_key_has_comment(self):
        output = export_dotenv_template(SAMPLE_DIFF)
        lines = output.splitlines()
        new_key_idx = next(i for i, l in enumerate(lines) if "NEW_KEY=" in l)
        assert "MISSING" in lines[new_key_idx - 1]

    def test_mismatch_key_has_comment(self):
        output = export_dotenv_template(SAMPLE_DIFF)
        lines = output.splitlines()
        pass_idx = next(i for i, l in enumerate(lines) if "DB_PASS=" in l)
        assert "MISMATCH" in lines[pass_idx - 1]

    def test_output_ends_with_newline(self):
        output = export_dotenv_template(SAMPLE_DIFF)
        assert output.endswith("\n")

    def test_empty_diff(self):
        output = export_dotenv_template({})
        assert output.strip() == ""


class TestExportMarkdown:
    ENV_NAMES = ["dev", "prod"]

    def test_header_row_contains_env_names(self):
        output = export_markdown(SAMPLE_DIFF, self.ENV_NAMES)
        assert "dev" in output
        assert "prod" in output

    def test_contains_all_keys(self):
        output = export_markdown(SAMPLE_DIFF, self.ENV_NAMES)
        assert "DB_HOST" in output
        assert "NEW_KEY" in output

    def test_missing_shown_as_missing_label(self):
        output = export_markdown(SAMPLE_DIFF, self.ENV_NAMES)
        assert "*(missing)*" in output

    def test_present_key_shows_checkmark(self):
        output = export_markdown(SAMPLE_DIFF, self.ENV_NAMES)
        assert "✓" in output

    def test_output_is_valid_markdown_table(self):
        output = export_markdown(SAMPLE_DIFF, self.ENV_NAMES)
        lines = [l for l in output.splitlines() if l.strip()]
        # Every line should be a table row
        for line in lines:
            assert line.startswith("|") and line.endswith("|")

    def test_output_ends_with_newline(self):
        output = export_markdown(SAMPLE_DIFF, self.ENV_NAMES)
        assert output.endswith("\n")

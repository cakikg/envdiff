"""Tests for envdiff.tokenizer."""
import pytest
from envdiff.tokenizer import Token, TokenKind, tokenize_line, tokenize_lines


# ---------------------------------------------------------------------------
# tokenize_line
# ---------------------------------------------------------------------------

def test_blank_line():
    tok = tokenize_line("\n")
    assert tok.kind == TokenKind.BLANK


def test_whitespace_only_line():
    tok = tokenize_line("   ")
    assert tok.kind == TokenKind.BLANK


def test_comment_hash():
    tok = tokenize_line("# this is a comment")
    assert tok.kind == TokenKind.COMMENT
    assert tok.comment == "this is a comment"


def test_comment_semicolon():
    tok = tokenize_line("; another comment")
    assert tok.kind == TokenKind.COMMENT


def test_simple_key_value():
    tok = tokenize_line("FOO=bar")
    assert tok.kind == TokenKind.KEY
    assert tok.key == "FOO"
    assert tok.value == "bar"


def test_key_with_spaces_around_equals():
    tok = tokenize_line("FOO = bar")
    assert tok.key == "FOO"
    assert tok.value == "bar"


def test_quoted_value_double():
    tok = tokenize_line('DATABASE_URL="postgres://localhost/db"')
    assert tok.key == "DATABASE_URL"
    assert tok.value == "postgres://localhost/db"


def test_quoted_value_single():
    tok = tokenize_line("SECRET='my secret'")
    assert tok.value == "my secret"


def test_inline_comment_stripped():
    tok = tokenize_line("PORT=8080 # default port")
    assert tok.value == "8080"


def test_empty_value_returns_value_kind():
    tok = tokenize_line("EMPTY=")
    assert tok.kind == TokenKind.VALUE
    assert tok.key == "EMPTY"
    assert tok.value == ""


def test_invalid_line_no_equals():
    tok = tokenize_line("NOTANASSIGNMENT")
    assert tok.kind == TokenKind.INVALID


def test_invalid_line_no_key():
    tok = tokenize_line("=value_only")
    assert tok.kind == TokenKind.INVALID


def test_raw_preserved():
    raw = "MY_KEY=hello world"
    tok = tokenize_line(raw)
    assert tok.raw == raw


def test_is_assignment_true():
    tok = tokenize_line("A=1")
    assert tok.is_assignment() is True


def test_is_assignment_false_for_comment():
    tok = tokenize_line("# nope")
    assert tok.is_assignment() is False


# ---------------------------------------------------------------------------
# tokenize_lines
# ---------------------------------------------------------------------------

def test_tokenize_lines_returns_correct_count():
    lines = ["A=1\n", "# comment\n", "\n", "B=2\n"]
    tokens = tokenize_lines(lines)
    assert len(tokens) == 4


def test_tokenize_lines_kinds():
    lines = ["KEY=val", "# comment", "", "BAD"]
    kinds = [t.kind for t in tokenize_lines(lines)]
    assert kinds == [
        TokenKind.KEY,
        TokenKind.COMMENT,
        TokenKind.BLANK,
        TokenKind.INVALID,
    ]

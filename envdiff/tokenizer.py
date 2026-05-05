"""Tokenizer: break a raw .env line into structured tokens."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TokenKind(Enum):
    KEY = auto()
    VALUE = auto()
    COMMENT = auto()
    BLANK = auto()
    INVALID = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    raw: str
    key: Optional[str] = None
    value: Optional[str] = None
    comment: Optional[str] = None

    def is_assignment(self) -> bool:
        return self.kind in (TokenKind.KEY, TokenKind.VALUE)


_COMMENT_CHARS = ("#", ";")


def tokenize_line(line: str) -> Token:
    """Return a Token describing the structure of *line*.

    Rules (in priority order):
    1. Blank / whitespace-only  -> BLANK
    2. Starts with # or ;       -> COMMENT
    3. Contains '='             -> KEY/VALUE pair (inline comment stripped)
    4. Anything else            -> INVALID
    """
    stripped = line.rstrip("\n")

    if not stripped.strip():
        return Token(kind=TokenKind.BLANK, raw=stripped)

    lstripped = stripped.lstrip()
    if lstripped and lstripped[0] in _COMMENT_CHARS:
        return Token(kind=TokenKind.COMMENT, raw=stripped, comment=lstripped[1:].strip())

    if "=" not in stripped:
        return Token(kind=TokenKind.INVALID, raw=stripped)

    key_part, _, rest = stripped.partition("=")
    key = key_part.strip()

    # Strip inline comment
    value_raw = rest
    if not (value_raw.startswith('"') or value_raw.startswith("'")):
        for ch in _COMMENT_CHARS:
            idx = value_raw.find(f" {ch}")
            if idx != -1:
                value_raw = value_raw[:idx]
                break

    value = value_raw.strip().strip('"').strip("'")

    if not key:
        return Token(kind=TokenKind.INVALID, raw=stripped)

    return Token(
        kind=TokenKind.KEY if value else TokenKind.VALUE,
        raw=stripped,
        key=key,
        value=value or "",
    )


def tokenize_lines(lines: list[str]) -> list[Token]:
    """Tokenize a sequence of raw lines."""
    return [tokenize_line(line) for line in lines]

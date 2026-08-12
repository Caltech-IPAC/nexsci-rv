"""Hygiene check: VCR cassette files must not contain auth material.

This test runs even before any cassettes exist — the assertion is "if there
are cassettes, none of them leak credentials." It guards against accidental
re-recording without proper redaction filters in place.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CASSETTES_DIR = Path(__file__).parents[1] / "cassettes"

# Forbidden patterns — case-insensitive substring matches against the raw
# YAML content. Add more sentinel strings here if they crop up.
_FORBIDDEN: list[re.Pattern[str]] = [
    re.compile(r"\bpassword\s*[:=]\s*\S", re.IGNORECASE),
    re.compile(r"\bset-cookie\b", re.IGNORECASE),  # session cookies leak via Set-Cookie
    re.compile(r"\bcookie\s*[:=]\s*['\"]?\S+", re.IGNORECASE),
    re.compile(r"\buserid\s*=\s*[^&\s]+\s*&\s*password=", re.IGNORECASE),
    re.compile(r"\btoken\s*[:=]\s*[A-Za-z0-9+/=]{16,}", re.IGNORECASE),
]


def _cassette_files() -> list[Path]:
    if not CASSETTES_DIR.exists():
        return []
    return sorted(p for p in CASSETTES_DIR.rglob("*.y*ml") if p.is_file())


@pytest.mark.parametrize("cassette", _cassette_files(), ids=lambda p: p.name)
def test_cassette_has_no_secrets(cassette: Path):
    content = cassette.read_text(encoding="utf-8", errors="replace")
    for pattern in _FORBIDDEN:
        match = pattern.search(content)
        if match:
            raise AssertionError(
                f"{cassette} contains forbidden pattern {pattern.pattern!r}: "
                f"matched {match.group(0)!r}. Re-record with redaction filter."
            )


def test_cassette_directory_existence_documented():
    """Sanity: directory exists so VCR can write into it on record runs."""
    assert CASSETTES_DIR.exists(), (
        f"cassettes directory missing at {CASSETTES_DIR}; "
        "create it so VCR can write cassettes during recorded test runs"
    )

"""_types.py — import-time coverage for TYPE_CHECKING-only module."""

from __future__ import annotations

from nexsci_rv import _types


def test_date_range_alias_exists():
    """Asserts DateRange type alias is accessible from _types."""
    assert _types.DateRange is not None


def test_date_input_alias_exists():
    """Asserts DateInput type alias is accessible from _types."""
    assert _types.DateInput is not None


def test_all_exports_present():
    """Asserts __all__ lists the expected public names."""
    assert "DateRange" in _types.__all__
    assert "DateInput" in _types.__all__

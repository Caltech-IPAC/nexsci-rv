"""Shared pytest fixtures.

Keep this file minimal — package-wide knobs only. Test modules add their own
fixtures locally.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_cookie_root(tmp_path: Path) -> Path:
    """A per-test cookie root so tests never touch the real ~/.config tree."""
    root = tmp_path / "cookies"
    root.mkdir()
    return root

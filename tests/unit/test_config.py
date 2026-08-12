"""Conf — env-var resolution and default cookie root."""

from __future__ import annotations

from pathlib import Path

from nexsci_rv.config import Conf


def test_defaults_are_sensible():
    c = Conf()
    assert c.timeout > 0
    assert c.download_workers >= 1
    assert c.download_retries >= 0
    assert isinstance(c.cookie_root, Path)


def test_from_env_reads_all_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXSCI_RV_TIMEOUT", "5.5")
    monkeypatch.setenv("NEXSCI_RV_DOWNLOAD_WORKERS", "8")
    monkeypatch.setenv("NEXSCI_RV_DOWNLOAD_RETRIES", "10")
    monkeypatch.setenv("NEXSCI_RV_COOKIE_ROOT", str(tmp_path))

    c = Conf.from_env()
    assert c.timeout == 5.5
    assert c.download_workers == 8
    assert c.download_retries == 10
    assert c.cookie_root == tmp_path


def test_from_env_falls_back_when_unset(monkeypatch):
    for name in (
        "NEXSCI_RV_TIMEOUT",
        "NEXSCI_RV_DOWNLOAD_WORKERS",
        "NEXSCI_RV_DOWNLOAD_RETRIES",
        "NEXSCI_RV_COOKIE_ROOT",
    ):
        monkeypatch.delenv(name, raising=False)
    c = Conf.from_env()
    assert c == Conf()


def test_conf_is_frozen():
    """Conf is immutable; users should construct a new one to change values."""
    c = Conf()
    import dataclasses

    assert dataclasses.is_dataclass(c)
    try:
        c.timeout = 999  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("Conf should be frozen")

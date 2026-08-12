"""Exception-hierarchy invariants."""

from __future__ import annotations

import pytest

from nexsci_rv import exceptions as exc


def test_root_catches_everything():
    """All package exceptions are catchable as NexsciRVError."""
    targets = [
        exc.ConfigError,
        exc.AuthError,
        exc.LoginFailed,
        exc.AuthExpired,
        exc.NotAuthenticated,
        exc.QueryError,
        exc.UnknownDataLevel,
        exc.UnknownColumn,
        exc.NotApplicable,
        exc.TapServerError,
        exc.AsyncJobError,
    ]
    for cls in targets:
        with pytest.raises(exc.NexsciRVError):
            raise cls("boom")


def test_download_error_carries_failures():
    """DownloadError preserves per-file failure info."""
    failures = [("a.fits", RuntimeError("connection reset")), ("b.fits", OSError("disk full"))]
    err = exc.DownloadError("2 files failed", failures)
    assert err.failures == failures
    assert isinstance(err, exc.NexsciRVError)


def test_auth_subclasses_isolation():
    """LoginFailed / AuthExpired / NotAuthenticated all subclass AuthError."""
    for cls in (exc.LoginFailed, exc.AuthExpired, exc.NotAuthenticated):
        assert issubclass(cls, exc.AuthError)
        assert issubclass(cls, exc.NexsciRVError)

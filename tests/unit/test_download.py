"""download.parallel_download — filename sanitization, retries, error aggregation.

No network; we mock the HTTP session.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests
from astropy.table import Table

from nexsci_rv.config import Conf
from nexsci_rv.download import _sanitize_filename, parallel_download
from nexsci_rv.exceptions import AuthExpired, DownloadError


def _row_to_url(row):
    return row["filename"], f"https://example/{row['filename']}"


def _mock_stream_response(status_code=200, content=b"FITSdata"):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.iter_content.return_value = [content]
    resp.raise_for_status.side_effect = (
        None if status_code < 400 else requests.HTTPError(f"HTTP {status_code}")
    )
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)
    return resp


# ---- sanitization ----------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "../etc/passwd",
        "/etc/passwd",
        "foo/../bar",
        "..",
        ".",
        "",
        "foo\x00bar",
        "a\\b",
    ],
)
def test_sanitize_rejects_path_traversal(bad):
    with pytest.raises(ValueError):
        _sanitize_filename(bad)


def test_sanitize_accepts_plain_name():
    assert _sanitize_filename("neidL2_20240101T010101.fits") == "neidL2_20240101T010101.fits"


# ---- parallel_download -----------------------------------------------------


def _table_with_rows(n):
    return Table({"filename": [f"file_{i}.fits" for i in range(n)]})


def test_all_succeed(tmp_path):
    session = MagicMock(spec=requests.Session)
    session.get.return_value = _mock_stream_response()
    session.head.return_value = MagicMock(status_code=404, headers={})
    rows = _table_with_rows(3)
    out = parallel_download(rows, _row_to_url, tmp_path, session, workers=2, progress=False)
    assert len(out) == 3
    for p in out:
        assert p.exists()
        assert p.read_bytes() == b"FITSdata"


def test_auth_expired_propagates(tmp_path):
    session = MagicMock(spec=requests.Session)
    session.get.return_value = _mock_stream_response(status_code=401)
    session.head.return_value = MagicMock(status_code=404, headers={})
    rows = _table_with_rows(2)
    with pytest.raises(AuthExpired):
        parallel_download(rows, _row_to_url, tmp_path, session, workers=1, progress=False)


def test_partial_failure_collects_into_download_error(tmp_path):
    session = MagicMock(spec=requests.Session)

    call_log: list[str] = []

    def fake_get(url, **kwargs):
        call_log.append(url)
        if "file_1" in url:
            r = _mock_stream_response(status_code=500)
            return r
        return _mock_stream_response()

    session.get.side_effect = fake_get
    session.head.return_value = MagicMock(status_code=404, headers={})
    rows = _table_with_rows(3)
    with pytest.raises(DownloadError) as excinfo:
        parallel_download(
            rows,
            _row_to_url,
            tmp_path,
            session,
            workers=1,
            progress=False,
            conf=Conf(download_retries=0),
        )
    assert len(excinfo.value.failures) == 1
    assert excinfo.value.failures[0][0] == "file_1.fits"


def test_resume_skips_if_remote_size_matches(tmp_path):
    (tmp_path / "file_0.fits").write_bytes(b"FITSdata")
    session = MagicMock(spec=requests.Session)
    session.head.return_value = MagicMock(
        status_code=200, headers={"Content-Length": str(len(b"FITSdata"))}
    )
    session.get.return_value = _mock_stream_response()
    rows = _table_with_rows(1)
    out = parallel_download(rows, _row_to_url, tmp_path, session, workers=1, progress=False)
    assert out[0].exists()
    # GET should NOT have been called because resume detected an existing file
    session.get.assert_not_called()


def test_retries_then_succeeds(tmp_path):
    session = MagicMock(spec=requests.Session)
    session.head.return_value = MagicMock(status_code=404, headers={})

    # First call fails (5xx), second succeeds.
    fail = _mock_stream_response(status_code=500)
    ok = _mock_stream_response()
    session.get.side_effect = [fail, ok]
    rows = _table_with_rows(1)
    # With retries enabled, no DownloadError.
    out = parallel_download(
        rows,
        _row_to_url,
        tmp_path,
        session,
        workers=1,
        progress=False,
        conf=Conf(download_retries=1),
    )
    assert len(out) == 1


def test_filename_with_traversal_in_url_callback_raises(tmp_path):
    session = MagicMock(spec=requests.Session)
    session.head.return_value = MagicMock(status_code=404, headers={})
    session.get.return_value = _mock_stream_response()

    def bad_row_to_url(row):
        return "../escape.fits", "https://example/x"

    rows = _table_with_rows(1)
    with pytest.raises(DownloadError) as excinfo:
        parallel_download(
            rows,
            bad_row_to_url,
            tmp_path,
            session,
            workers=1,
            progress=False,
            conf=Conf(download_retries=0),
        )
    # Should be a ValueError (from sanitization) wrapped into the DownloadError list
    assert any(isinstance(exc, ValueError) for _, exc in excinfo.value.failures)

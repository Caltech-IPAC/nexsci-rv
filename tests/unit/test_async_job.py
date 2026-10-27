"""AsyncJob — UWS async TAP state machine.

Tests inject HTTP responses via a mocked requests.Session. No network.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from nexsci_rv.async_job import AsyncJob
from nexsci_rv.config import Conf
from nexsci_rv.exceptions import AsyncJobError, AuthExpired, TapServerError

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _mock_response(status_code: int = 200, body: str = "") -> MagicMock:
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.text = body
    r.raise_for_status.side_effect = (
        None if status_code < 400 else requests.HTTPError(f"HTTP {status_code}")
    )
    return r


def _make_uws_xml(
    phase: str = "COMPLETED",
    job_id: str = "abc123",
    result_href: str | None = "https://tap.example/job/abc123/result",
    error_message: str | None = None,
    start_time: str | None = "2026-01-01T00:00:00Z",
    end_time: str | None = "2026-01-01T00:05:00Z",
) -> str:
    """Build a minimal valid UWS job XML document."""
    result_block = ""
    if result_href is not None:
        result_block = (
            f'<uws:results><uws:result id="result" xlink:href="{result_href}"/></uws:results>'
        )

    error_block = ""
    if error_message is not None:
        error_block = (
            f"<uws:errorSummary><uws:message>{error_message}</uws:message></uws:errorSummary>"
        )

    start_block = f"<uws:startTime>{start_time}</uws:startTime>" if start_time else ""
    end_block = f"<uws:endTime>{end_time}</uws:endTime>" if end_time else ""

    return (
        '<uws:job xmlns:uws="http://www.ivoa.net/xml/UWS/v1.0"'
        ' xmlns:xlink="http://www.w3.org/1999/xlink">'
        f"<uws:jobId>{job_id}</uws:jobId>"
        f"<uws:phase>{phase}</uws:phase>"
        f"{start_block}"
        f"{end_block}"
        f"{result_block}"
        f"{error_block}"
        "</uws:job>"
    )


@pytest.fixture(autouse=True)
def patch_sleep(monkeypatch):
    """Ensure time.sleep is always a no-op in async_job tests."""
    monkeypatch.setattr("nexsci_rv.async_job.time.sleep", lambda *_: None)


def _make_job(xml: str, conf: Conf | None = None) -> tuple[AsyncJob, MagicMock]:
    """Construct an AsyncJob backed by a mock session that returns *xml* first."""
    session = MagicMock(spec=requests.Session)
    session.get.return_value = _mock_response(200, xml)
    conf = conf or Conf()
    job = AsyncJob("https://tap.example/job/abc123", session, conf=conf)
    return job, session


# ---------------------------------------------------------------------------
# Constructor + refresh + properties
# ---------------------------------------------------------------------------


def test_constructor_parses_completed_xml():
    """Asserts job_id, phase, result_url, times, and error are parsed correctly."""
    xml = _make_uws_xml(
        phase="COMPLETED",
        job_id="abc123",
        result_href="https://tap.example/result/abc123",
        error_message=None,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T00:05:00Z",
    )
    job, _ = _make_job(xml)

    assert job.job_id == "abc123"
    assert job.phase == "completed"
    assert job.result_url == "https://tap.example/result/abc123"
    assert job.error is None
    assert "startTime" in job.times
    assert "endTime" in job.times


def test_status_url_property():
    """Asserts status_url returns the URL passed to the constructor."""
    xml = _make_uws_xml(phase="PENDING")
    job, _ = _make_job(xml)
    assert job.status_url == "https://tap.example/job/abc123"


def test_is_terminal_true_for_completed():
    """Asserts is_terminal is True when phase == completed."""
    job, _ = _make_job(_make_uws_xml(phase="COMPLETED"))
    assert job.is_terminal is True


def test_is_terminal_true_for_error():
    """Asserts is_terminal is True when phase == error."""
    xml = _make_uws_xml(phase="error", result_href=None, error_message="bad query")
    job, _ = _make_job(xml)
    assert job.is_terminal is True


def test_is_terminal_true_for_aborted():
    """Asserts is_terminal is True when phase == aborted."""
    job, _ = _make_job(_make_uws_xml(phase="aborted", result_href=None))
    assert job.is_terminal is True


def test_is_terminal_false_for_executing():
    """Asserts is_terminal is False for a non-terminal phase."""
    job, _ = _make_job(_make_uws_xml(phase="executing", result_href=None))
    assert job.is_terminal is False


def test_error_property_populated_from_error_summary():
    """Asserts error is parsed from the errorSummary element."""
    xml = _make_uws_xml(phase="error", result_href=None, error_message="table not found")
    job, _ = _make_job(xml)
    assert job.error == "table not found"


def test_times_returned_as_copy():
    """Asserts times returns a copy, not the internal dict."""
    job, _ = _make_job(_make_uws_xml(phase="completed"))
    t1 = job.times
    t2 = job.times
    assert t1 is not t2


def test_constructor_calls_refresh_once():
    """Asserts constructor calls session.get exactly once (to refresh state)."""
    xml = _make_uws_xml(phase="COMPLETED")
    _, session = _make_job(xml)
    session.get.assert_called_once()


# ---------------------------------------------------------------------------
# Phase mapping quirks
# ---------------------------------------------------------------------------


def test_phase_held_maps_to_queued():
    """Asserts 'held' phase is normalized to 'queued'."""
    job, _ = _make_job(_make_uws_xml(phase="held", result_href=None))
    assert job.phase == "queued"


def test_phase_suspended_maps_to_executing():
    """Asserts 'suspended' phase is normalized to 'executing'."""
    job, _ = _make_job(_make_uws_xml(phase="suspended", result_href=None))
    assert job.phase == "executing"


def test_phase_pending_preserved():
    """Asserts 'pending' phase is preserved as-is."""
    job, _ = _make_job(_make_uws_xml(phase="pending", result_href=None))
    assert job.phase == "pending"


def test_no_result_href_leaves_result_url_none():
    """Asserts result_url stays None when the results block is absent."""
    job, _ = _make_job(_make_uws_xml(phase="executing", result_href=None))
    assert job.result_url is None


# ---------------------------------------------------------------------------
# refresh()
# ---------------------------------------------------------------------------


def test_refresh_updates_phase():
    """Asserts refresh() updates the phase from a new GET response."""
    xml_executing = _make_uws_xml(phase="executing", result_href=None)
    xml_completed = _make_uws_xml(phase="completed")
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _mock_response(200, xml_executing),  # consumed by constructor
        _mock_response(200, xml_completed),  # consumed by explicit refresh()
    ]
    job = AsyncJob("https://tap.example/job/abc123", session, conf=Conf())

    assert job.phase == "executing"
    job.refresh()
    assert job.phase == "completed"


def test_refresh_raises_auth_expired_on_401():
    """Asserts refresh() raises AuthExpired when the server returns 401."""
    xml = _make_uws_xml(phase="completed")
    job, session = _make_job(xml)
    session.get.return_value = _mock_response(401)
    with pytest.raises(AuthExpired):
        job.refresh()


def test_refresh_raises_auth_expired_on_403():
    """Asserts refresh() raises AuthExpired when the server returns 403."""
    xml = _make_uws_xml(phase="completed")
    job, session = _make_job(xml)
    session.get.return_value = _mock_response(403)
    with pytest.raises(AuthExpired):
        job.refresh()


# ---------------------------------------------------------------------------
# wait()
# ---------------------------------------------------------------------------


def test_wait_succeeds_when_job_transitions_to_completed():
    """Asserts wait() returns normally when job reaches 'completed'."""
    xml_executing = _make_uws_xml(phase="executing", result_href=None)
    xml_completed = _make_uws_xml(phase="completed")
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _mock_response(200, xml_executing),  # constructor
        _mock_response(200, xml_completed),  # loop refresh
    ]
    job = AsyncJob("https://tap.example/job/abc123", session, conf=Conf())
    # Should not raise
    job.wait()
    assert job.phase == "completed"


def test_wait_raises_timeout_error_when_deadline_expires():
    """Asserts wait() raises TimeoutError when timeout=0 and job is not terminal."""
    xml_executing = _make_uws_xml(phase="executing", result_href=None)
    job, _ = _make_job(xml_executing)
    with pytest.raises(TimeoutError, match="did not reach a terminal phase"):
        job.wait(timeout=0)


def test_wait_raises_async_job_error_when_phase_is_error():
    """Asserts wait() raises AsyncJobError when job is in 'error' phase."""
    xml = _make_uws_xml(phase="error", result_href=None, error_message="server exploded")
    job, _ = _make_job(xml)
    with pytest.raises(AsyncJobError, match="error"):
        job.wait()


def test_wait_raises_async_job_error_when_phase_is_aborted():
    """Asserts wait() raises AsyncJobError when job is in 'aborted' phase."""
    xml = _make_uws_xml(phase="aborted", result_href=None)
    job, _ = _make_job(xml)
    with pytest.raises(AsyncJobError):
        job.wait()


def test_wait_raises_value_error_for_non_positive_poll_interval():
    """Asserts wait() raises ValueError when poll_interval <= 0."""
    xml = _make_uws_xml(phase="completed")
    job, _ = _make_job(xml)
    with pytest.raises(ValueError, match="poll_interval must be positive"):
        job.wait(poll_interval=0)


def test_wait_raises_value_error_for_negative_poll_interval():
    """Asserts wait() raises ValueError for negative poll_interval."""
    xml = _make_uws_xml(phase="completed")
    job, _ = _make_job(xml)
    with pytest.raises(ValueError, match="poll_interval must be positive"):
        job.wait(poll_interval=-1.0)


# ---------------------------------------------------------------------------
# result()
# ---------------------------------------------------------------------------


def test_result_returns_table_on_success():
    """Asserts result() fetches and parses the result body into a Table."""
    xml_completed = _make_uws_xml(
        phase="completed",
        result_href="https://tap.example/result/abc123",
    )
    csv_body = "a,b\n1,2\n3,4\n"
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _mock_response(200, xml_completed),  # constructor
        _mock_response(200, csv_body),  # result fetch
    ]
    job = AsyncJob(
        "https://tap.example/job/abc123",
        session,
        output_format="csv",
        conf=Conf(),
    )
    table = job.result()
    assert len(table) == 2
    assert list(table.colnames) == ["a", "b"]


def test_result_raises_async_job_error_when_phase_not_completed():
    """Asserts result() raises AsyncJobError if job is not in 'completed' phase."""
    xml = _make_uws_xml(phase="executing", result_href=None)
    job, _ = _make_job(xml)
    with pytest.raises(AsyncJobError, match="not 'completed'"):
        job.result()


def test_result_raises_async_job_error_when_no_result_url():
    """Asserts result() raises AsyncJobError if completed but result_url is None."""
    # Build a completed job that has no result href in the XML
    xml = _make_uws_xml(phase="completed", result_href=None)
    job, _ = _make_job(xml)
    # Manually ensure result_url is None (no href in results block)
    assert job._result_url is None
    with pytest.raises(AsyncJobError, match="no result URL"):
        job.result()


def test_result_raises_auth_expired_on_401():
    """Asserts result() raises AuthExpired when result fetch returns 401."""
    xml_completed = _make_uws_xml(phase="completed", result_href="https://tap.example/result")
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _mock_response(200, xml_completed),  # constructor
        _mock_response(401),  # result fetch
    ]
    job = AsyncJob("https://tap.example/job/abc123", session, output_format="csv", conf=Conf())
    with pytest.raises(AuthExpired):
        job.result()


def test_result_raises_auth_expired_on_403():
    """Asserts result() raises AuthExpired when result fetch returns 403."""
    xml_completed = _make_uws_xml(phase="completed", result_href="https://tap.example/result")
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _mock_response(200, xml_completed),  # constructor
        _mock_response(403),  # result fetch
    ]
    job = AsyncJob("https://tap.example/job/abc123", session, output_format="csv", conf=Conf())
    with pytest.raises(AuthExpired):
        job.result()


# ---------------------------------------------------------------------------
# abort()
# ---------------------------------------------------------------------------


def test_abort_posts_phase_abort_and_refreshes():
    """Asserts abort() POSTs PHASE=ABORT to the phase URL, then calls refresh."""
    xml_executing = _make_uws_xml(phase="executing", result_href=None)
    xml_aborted = _make_uws_xml(phase="aborted", result_href=None)
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _mock_response(200, xml_executing),  # constructor
        _mock_response(200, xml_aborted),  # refresh inside abort()
    ]
    session.post.return_value = _mock_response(200)

    job = AsyncJob("https://tap.example/job/abc123", session, conf=Conf())
    job.abort()

    # Assert POST was sent to the phase sub-URL with correct form data
    call_args = session.post.call_args
    assert call_args.args[0] == "https://tap.example/job/abc123/phase"
    assert call_args.kwargs["data"] == {"PHASE": "ABORT"}

    # Assert refresh was called (phase updated to aborted)
    assert job.phase == "aborted"


def test_abort_raises_auth_expired_on_401():
    """Asserts abort() raises AuthExpired when the server returns 401."""
    xml = _make_uws_xml(phase="executing", result_href=None)
    job, session = _make_job(xml)
    session.post.return_value = _mock_response(401)
    with pytest.raises(AuthExpired):
        job.abort()


def test_abort_raises_auth_expired_on_403():
    """Asserts abort() raises AuthExpired when the server returns 403."""
    xml = _make_uws_xml(phase="executing", result_href=None)
    job, session = _make_job(xml)
    session.post.return_value = _mock_response(403)
    with pytest.raises(AuthExpired):
        job.abort()


# ---------------------------------------------------------------------------
# _update_from_uws_xml — malformed XML
# ---------------------------------------------------------------------------


def test_malformed_xml_raises_tap_server_error():
    """Asserts _update_from_uws_xml raises TapServerError on unparseable XML."""
    # First, construct the job with valid XML
    xml = _make_uws_xml(phase="completed")
    job, _ = _make_job(xml)
    # Now directly call _update_from_uws_xml with broken markup
    with pytest.raises(TapServerError, match="Failed to parse UWS job XML"):
        job._update_from_uws_xml("<not-closed")


def test_result_http_error_raises_tap_server_error():
    xml_completed = _make_uws_xml(
        phase="completed",
        result_href="https://tap.example/result/abc123",
    )
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _mock_response(200, xml_completed),
        _mock_response(500, "internal failure while formatting results"),
    ]
    job = AsyncJob("https://tap.example/job/abc123", session, conf=Conf())
    with pytest.raises(TapServerError, match=r"HTTP 500.*internal failure"):
        job.result()

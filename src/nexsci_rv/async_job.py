"""IVOA async TAP job handle.

Use this when a sync query would time out (large result sets, expensive joins).

Workflow:

    job = archive.submit_async("SELECT ... FROM neidl2 WHERE ...")
    job.wait(timeout=600)
    table = job.result()

The class wraps the IVOA async TAP state machine:

    PENDING → QUEUED → EXECUTING → COMPLETED | ERROR | ABORTED

We replaced the legacy pyNEID ``TapJob`` zoo of ``get_*`` methods with
properties + a single :meth:`wait` helper.
"""

from __future__ import annotations

import contextlib
import logging
import time
from datetime import datetime
from typing import Literal
from xml.etree.ElementTree import ParseError

import defusedxml.ElementTree as ET
import requests
from astropy.table import Table

from .config import Conf
from .config import conf as default_conf
from .exceptions import AsyncJobError, AuthExpired, TapServerError
from .tap import OutputFormat, _parse_response

logger = logging.getLogger("nexsci_rv.async_job")

Phase = Literal["pending", "queued", "executing", "completed", "error", "aborted"]

_TERMINAL_PHASES: frozenset[str] = frozenset({"completed", "error", "aborted"})

# IVOA UWS (Universal Worker Service) XML namespace
_UWS_NS = {"uws": "http://www.ivoa.net/xml/UWS/v1.0"}


class AsyncJob:
    """Handle to an IVOA async TAP job.

    Args:
        status_url: Full URL of the job's status resource (returned by the
            TAP server on submit).
        session: HTTP session to use for polling and result fetches; supplied
            by the originating :class:`Archive`.
        output_format: Format requested when the job was submitted; needed to
            parse :meth:`result` correctly.
        conf: Process configuration.
    """

    def __init__(
        self,
        status_url: str,
        session: requests.Session,
        *,
        output_format: OutputFormat = "votable",
        conf: Conf | None = None,
    ):
        self._status_url = status_url
        self._session = session
        self._output_format = output_format
        self._conf = conf if conf is not None else default_conf

        self._phase: Phase = "pending"
        self._job_id: str = ""
        self._result_url: str | None = None
        self._error: str | None = None
        self._times: dict[str, datetime] = {}

        self.refresh()

    # ----- properties -------------------------------------------------------

    @property
    def status_url(self) -> str:
        """Full URL of the job's status resource."""
        return self._status_url

    @property
    def job_id(self) -> str:
        """Server-assigned job identifier."""
        return self._job_id

    @property
    def phase(self) -> Phase:
        """Current phase as last seen by :meth:`refresh`."""
        return self._phase

    @property
    def result_url(self) -> str | None:
        """URL of the completed result resource (``None`` until completed)."""
        return self._result_url

    @property
    def error(self) -> str | None:
        """Server-side error message if the job is in the ``error`` phase."""
        return self._error

    @property
    def times(self) -> dict[str, datetime]:
        """Map of ``startTime`` / ``endTime`` / ``destruction`` / ``executionDuration``.

        Only the keys present in the server's UWS response are populated.
        """
        return dict(self._times)

    @property
    def is_terminal(self) -> bool:
        """True if the job is in ``completed``, ``error``, or ``aborted``."""
        return self._phase in _TERMINAL_PHASES

    # ----- actions ----------------------------------------------------------

    def refresh(self) -> None:
        """Poll the status URL once and update local state."""
        logger.debug("polling %s", self._status_url)
        response = self._session.get(self._status_url, timeout=self._conf.timeout)
        if response.status_code in (401, 403):
            raise AuthExpired(
                f"Async job status poll rejected (HTTP {response.status_code}). Re-run .login()."
            )
        response.raise_for_status()
        self._update_from_uws_xml(response.text)

    def wait(self, *, timeout: float | None = None, poll_interval: float = 5.0) -> None:
        """Block until the job reaches a terminal phase or ``timeout`` elapses.

        Raises:
            TimeoutError: if ``timeout`` is exceeded before a terminal phase.
            AsyncJobError: if the job ends in ``error`` or ``aborted``.
        """
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        deadline = time.monotonic() + timeout if timeout is not None else None

        while not self.is_terminal:
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Async job {self._job_id} did not reach a terminal phase "
                    f"within {timeout}s (last phase: {self._phase})"
                )
            time.sleep(poll_interval)
            self.refresh()

        if self._phase != "completed":
            raise AsyncJobError(
                f"Async job {self._job_id} ended in phase={self._phase!r}: "
                f"{self._error or '(no message)'}"
            )

    def result(self) -> Table:
        """Fetch and parse the result table. Job must be ``completed``."""
        if self._phase != "completed":
            raise AsyncJobError(
                f"Cannot fetch result; job is in phase={self._phase!r}, not 'completed'"
            )
        if self._result_url is None:
            raise AsyncJobError("Completed job has no result URL")

        response = self._session.get(self._result_url, timeout=self._conf.timeout)
        if response.status_code in (401, 403):
            raise AuthExpired(
                f"Async job result fetch rejected (HTTP {response.status_code}). Re-run .login()."
            )
        response.raise_for_status()
        return _parse_response(response.text, self._output_format)

    def abort(self) -> None:
        """Request that the server abort the job."""
        phase_url = f"{self._status_url}/phase"
        logger.info("abort %s", self._status_url)
        response = self._session.post(
            phase_url, data={"PHASE": "ABORT"}, timeout=self._conf.timeout
        )
        if response.status_code in (401, 403):
            raise AuthExpired(
                f"Async job abort rejected (HTTP {response.status_code}). Re-run .login()."
            )
        response.raise_for_status()
        self.refresh()

    # ----- internals --------------------------------------------------------

    def _update_from_uws_xml(self, body: str) -> None:
        try:
            root = ET.fromstring(body)
        except ParseError as exc:
            raise TapServerError(
                f"Failed to parse UWS job XML: {exc}; body starts with {body[:200]!r}"
            ) from exc

        # Strip namespace prefix from tag for simpler matching.
        def tag(name: str) -> str:
            return f"{{{_UWS_NS['uws']}}}{name}"

        job_id_el = root.find(tag("jobId"))
        if job_id_el is not None and job_id_el.text:
            self._job_id = job_id_el.text

        phase_el = root.find(tag("phase"))
        if phase_el is not None and phase_el.text:
            phase_raw = phase_el.text.strip().lower()
            if phase_raw in ("pending", "queued", "executing", "completed", "error", "aborted"):
                self._phase = phase_raw  # narrowed by the in-tuple check above
            elif phase_raw == "held":
                self._phase = "queued"
            elif phase_raw == "suspended":
                self._phase = "executing"

        for key, xml_name in (
            ("startTime", "startTime"),
            ("endTime", "endTime"),
            ("destruction", "destruction"),
        ):
            el = root.find(tag(xml_name))
            if el is not None and el.text:
                with contextlib.suppress(ValueError):
                    self._times[key] = datetime.fromisoformat(el.text.replace("Z", "+00:00"))

        results_el = root.find(tag("results"))
        if results_el is not None:
            for result_el in results_el.findall(tag("result")):
                href = result_el.get("{http://www.w3.org/1999/xlink}href")
                if href:
                    self._result_url = href
                    break

        err_el = root.find(tag("errorSummary"))
        if err_el is not None:
            msg_el = err_el.find(tag("message"))
            if msg_el is not None and msg_el.text:
                self._error = msg_el.text.strip()


__all__ = ["AsyncJob", "Phase"]

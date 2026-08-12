"""Sync TAP (Table Access Protocol) transport.

This module is archive-agnostic: it knows how to POST an ADQL query to a TAP
service, parse the IPAC/CSV/VOTable response, and surface server-side errors
as exceptions. Archive-specific URL templates and table maps live in
``archives/<name>/``.

Async TAP jobs (submit → poll → fetch) are handled by :mod:`nexsci_rv.async_job`.
"""

from __future__ import annotations

import io
import logging
import re
from typing import TYPE_CHECKING, Literal

import requests
from astropy.io import ascii as astropy_ascii
from astropy.io.votable import parse as parse_votable
from astropy.table import Table

from .config import Conf
from .config import conf as default_conf
from .exceptions import AuthExpired, TapServerError

if TYPE_CHECKING:
    pass

logger = logging.getLogger("nexsci_rv.tap")

OutputFormat = Literal["ipac", "csv", "votable"]
VALID_FORMATS: tuple[OutputFormat, ...] = ("ipac", "csv", "votable")

_VOTABLE_ERROR_RE = re.compile(
    r'<INFO[^>]+name="QUERY_STATUS"[^>]+value="ERROR"[^>]*>(.*?)</INFO>',
    re.IGNORECASE | re.DOTALL,
)


class TapClient:
    """Sync TAP client.

    Args:
        tap_url: Base URL of the TAP service (the part *before* ``/sync`` or
            ``/async``). For NEID and EXPRES this is ``{server}TAP``.
        session: HTTP session to use, normally supplied by
            :class:`nexsci_rv.auth.SessionManager`.
        conf: Process configuration; defaults to the module-level conf.
    """

    def __init__(
        self,
        tap_url: str,
        session: requests.Session,
        *,
        conf: Conf | None = None,
    ):
        self.tap_url = tap_url.rstrip("/")
        self._session = session
        self._conf = conf if conf is not None else default_conf

    def query(
        self,
        adql: str,
        *,
        output_format: OutputFormat = "ipac",
        maxrec: int | None = None,
    ) -> Table:
        """Execute a sync ADQL query against the TAP service.

        Returns an :class:`astropy.table.Table`.

        Raises:
            TapServerError: if the server returned ``QUERY_STATUS=ERROR``
                (HTTP 200 with an error embedded in the response body).
            AuthExpired: if the server returned HTTP 401/403.
            requests.HTTPError: for other unsuccessful HTTP responses.
        """
        if output_format not in VALID_FORMATS:
            raise ValueError(
                f"Unknown output_format {output_format!r}; expected one of {VALID_FORMATS}"
            )

        sync_url = f"{self.tap_url}/sync"
        data: dict[str, str] = {
            "query": adql,
            "format": output_format,
            "request": "doQuery",
            "lang": "ADQL",
        }
        if maxrec is not None:
            data["maxrec"] = str(maxrec)

        logger.info("TAP sync POST %s", sync_url)
        logger.debug("ADQL: %s", adql)

        response = self._session.post(
            sync_url,
            data=data,
            timeout=self._conf.timeout,
            allow_redirects=False,
        )

        if response.status_code in (401, 403):
            raise AuthExpired(
                f"TAP server rejected the session (HTTP {response.status_code}). Re-run .login()."
            )
        response.raise_for_status()

        body = response.text
        return _parse_response(body, output_format)


def _parse_response(body: str, output_format: OutputFormat) -> Table:
    """Parse a TAP response body into an astropy Table.

    Detects TAP error responses (VOTable ``QUERY_STATUS=ERROR``) before
    handing off to the format-specific parser.
    """
    if output_format == "votable":
        # Check for embedded error before attempting full parse.
        if _is_votable_error(body):
            raise TapServerError(_extract_votable_error(body))
        # Note: astropy.io.votable.parse uses stdlib xml.etree internally, not
        # defusedxml, so it is not hardened against billion-laughs / XXE on
        # untrusted input. We rely on the TAP server being trusted and
        # TLS-pinned. If we ever need to parse third-party VOTables, swap to
        # a defusedxml-backed path.
        votable = parse_votable(io.BytesIO(body.encode("utf-8")))
        first_table = next(iter(votable.iter_tables()), None)
        if first_table is None:
            raise TapServerError("VOTable response contained no <TABLE> element")
        return first_table.to_table(use_names_over_ids=True)

    if output_format == "ipac":
        # IPAC error responses from the NEID TAP server tend to come back as
        # VOTable XML even when format=ipac was requested.
        if body.lstrip().startswith("<"):
            if _is_votable_error(body):
                raise TapServerError(_extract_votable_error(body))
            raise TapServerError(f"Expected IPAC format but server returned XML: {body[:200]!r}...")
        return astropy_ascii.read(body, format="ipac")

    # csv
    if body.lstrip().startswith("<"):
        if _is_votable_error(body):
            raise TapServerError(_extract_votable_error(body))
        raise TapServerError(f"Expected CSV but server returned XML: {body[:200]!r}...")
    return astropy_ascii.read(body, format="csv")


def _is_votable_error(body: str) -> bool:
    return bool(_VOTABLE_ERROR_RE.search(body))


def _extract_votable_error(body: str) -> str:
    match = _VOTABLE_ERROR_RE.search(body)
    if match is None:
        return "TAP server reported QUERY_STATUS=ERROR (no message extractable)"
    return match.group(1).strip()


__all__ = ["VALID_FORMATS", "OutputFormat", "TapClient"]

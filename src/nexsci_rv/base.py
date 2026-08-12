"""Abstract base class for archive backends.

A subclass declares:

- ``name`` (e.g. ``"neid"``)
- ``data_levels`` — tuple of accepted data-level strings
- :attr:`_table_columns`, :attr:`_datalevel_to_table`, :attr:`_login_url`,
  :attr:`_tap_url`, :attr:`_default_server`, :attr:`_filename_column`,
  :attr:`_filepath_column`, :meth:`_build_download_url`

…and inherits the full query/auth/download surface.

Per-archive specifics belong in ``archives/<name>/``; nothing in this file
should know about NEID-specific tables or EXPRES quirks.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from . import _adql_utils as adql
from .async_job import AsyncJob
from .auth import SessionManager
from .config import Conf
from .config import conf as default_conf
from .download import RowToUrl, parallel_download
from .exceptions import NotApplicable, NotAuthenticated, QueryError, UnknownDataLevel
from .tap import OutputFormat, TapClient

if TYPE_CHECKING:
    from ._types import DateRange


logger = logging.getLogger("nexsci_rv.base")


class BaseArchive(ABC):
    """Common surface for all archive backends."""

    # ---- subclass-supplied class-level config ------------------------------
    name: ClassVar[str]
    data_levels: ClassVar[tuple[str, ...]]
    _default_server: ClassVar[str]
    _tap_path: ClassVar[str] = "TAP"
    _login_path: ClassVar[str | None] = None  # None means: no login supported
    _datalevel_to_table: ClassVar[dict[str, str]]
    _table_columns: ClassVar[dict[str, tuple[str, ...]]]
    _datelike_column: ClassVar[str] = "date_obs"
    _ra_column: ClassVar[str] = "ra"
    _dec_column: ClassVar[str] = "dec"
    _object_column: ClassVar[str] = "object"
    _qobject_column: ClassVar[str] = "qobject"
    _program_column: ClassVar[str] = "program"
    _piname_column: ClassVar[str] = "piname"

    def __init__(
        self,
        *,
        server: str | None = None,
        cookie_path: Path | None = None,
        timeout: float | None = None,
        conf: Conf | None = None,
    ):
        self._conf = conf if conf is not None else default_conf
        if timeout is not None:
            # Build a per-instance conf override.
            self._conf = Conf(
                timeout=timeout,
                download_workers=self._conf.download_workers,
                download_retries=self._conf.download_retries,
                cookie_root=self._conf.cookie_root,
            )

        self._server = (server or self._default_server).rstrip("/") + "/"
        self._session_manager = SessionManager(self.name, cookie_path=cookie_path, conf=self._conf)
        self._tap = TapClient(
            f"{self._server}{self._tap_path}",
            self._session_manager.session,
            conf=self._conf,
        )

    # ---- auth --------------------------------------------------------------

    def login(self, username: str | None = None, password: str | None = None) -> None:
        """Authenticate against the archive's login endpoint.

        Raises:
            NotApplicable: if the archive does not support login.
        """
        if self._login_path is None:
            raise NotApplicable(f"{self.name} does not support login")
        login_url = self._server + self._login_path
        self._session_manager.login(login_url, username=username, password=password)

    def logout(self) -> None:
        """Drop the in-memory session and delete the cookie file."""
        self._session_manager.logout()

    @property
    def is_authenticated(self) -> bool:
        """True if a session cookie is loaded."""
        return self._session_manager.is_authenticated

    # ---- queries -----------------------------------------------------------

    def query_datetime(
        self,
        data_level: str,
        date_range: DateRange,
        *,
        columns: list[str] | None = None,
        where: str | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        """Return rows whose observation datetime is in ``date_range``.

        ``date_range`` is an inclusive ``(start, end)`` pair; either side may
        be ``None`` for an open-ended interval.
        """
        table = self._table_for(data_level)
        validated_cols = self._validate_columns(table, columns)

        start, end = date_range
        clauses = self._datetime_clauses(start, end)
        if where:
            clauses.append(f"({where})")
        full_where = " AND ".join(clauses) if clauses else None

        sql = adql.build_select(validated_cols, table, where=full_where)
        return self._tap.query(sql, output_format=output_format, maxrec=maxrec)

    def query_position(
        self,
        data_level: str,
        coord: adql.CoordInput,
        radius: adql.RadiusInput,
        *,
        columns: list[str] | None = None,
        where: str | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        """Return rows whose (ra, dec) lies within ``radius`` of ``coord``."""
        table = self._table_for(data_level)
        validated_cols = self._validate_columns(table, columns)

        clauses = [adql.format_circle_predicate(coord, radius)]
        if where:
            clauses.append(f"({where})")

        sql = adql.build_select(validated_cols, table, where=" AND ".join(clauses))
        return self._tap.query(sql, output_format=output_format, maxrec=maxrec)

    def query_object(
        self,
        data_level: str,
        name: str,
        radius: adql.RadiusInput = 30 * u.arcsec,
        **kw: Any,
    ) -> Table:
        """Resolve ``name`` via Simbad/NED, then run a position search."""
        try:
            coord = SkyCoord.from_name(name)
        except Exception as exc:
            raise QueryError(f"Failed to resolve object {name!r}: {exc}") from exc
        return self.query_position(data_level, coord, radius, **kw)

    def query_qobject(
        self,
        data_level: str,
        qobject: str,
        *,
        columns: list[str] | None = None,
        where: str | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        """Search by the ``QOBJECT`` column (typically a Gaia DR2 ID).

        Unlike :meth:`query_object`, no name resolution is performed — this is
        a direct column match.
        """
        table = self._table_for(data_level)
        validated_cols = self._validate_columns(table, columns)
        clauses = [f"{self._qobject_column} = {adql.quote_string_literal(qobject)}"]
        if where:
            clauses.append(f"({where})")
        sql = adql.build_select(validated_cols, table, where=" AND ".join(clauses))
        return self._tap.query(sql, output_format=output_format, maxrec=maxrec)

    def query_program(
        self,
        data_level: str,
        program: str,
        *,
        columns: list[str] | None = None,
        where: str | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        """Search by the ``PROGRAM`` column (exact match)."""
        table = self._table_for(data_level)
        validated_cols = self._validate_columns(table, columns)
        clauses = [f"{self._program_column} = {adql.quote_string_literal(program)}"]
        if where:
            clauses.append(f"({where})")
        sql = adql.build_select(validated_cols, table, where=" AND ".join(clauses))
        return self._tap.query(sql, output_format=output_format, maxrec=maxrec)

    def query_pi(
        self,
        data_level: str,
        pi_name: str,
        *,
        columns: list[str] | None = None,
        where: str | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        """Search by the ``PINAME`` column (exact match)."""
        table = self._table_for(data_level)
        validated_cols = self._validate_columns(table, columns)
        clauses = [f"{self._piname_column} = {adql.quote_string_literal(pi_name)}"]
        if where:
            clauses.append(f"({where})")
        sql = adql.build_select(validated_cols, table, where=" AND ".join(clauses))
        return self._tap.query(sql, output_format=output_format, maxrec=maxrec)

    def query_criteria(
        self,
        criteria: dict[str, Any],
        *,
        columns: list[str] | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        """Combine multiple constraints in a single ADQL round-trip.

        Accepted keys (besides the required ``data_level``):

        - ``datetime``: ``(start, end)`` tuple — same form as :meth:`query_datetime`
        - ``position``: ``(coord, radius)`` tuple
        - ``object``: name → resolved via Simbad/NED, with optional ``radius``
        - ``qobject``: exact match on the QOBJECT column
        - ``program``: exact match on PROGRAM
        - ``pi_name``: exact match on PINAME
        - ``where``: raw ADQL fragment ANDed with the above
        """
        if "data_level" not in criteria:
            raise QueryError("query_criteria requires 'data_level' in the criteria dict")
        data_level = criteria["data_level"]
        table = self._table_for(data_level)
        validated_cols = self._validate_columns(table, columns)

        clauses: list[str] = []

        if "datetime" in criteria:
            start, end = criteria["datetime"]
            clauses.extend(self._datetime_clauses(start, end))

        if "position" in criteria:
            coord, radius = criteria["position"]
            clauses.append(adql.format_circle_predicate(coord, radius))

        if "object" in criteria:
            obj = criteria["object"]
            try:
                coord = SkyCoord.from_name(obj)
            except Exception as exc:
                raise QueryError(f"Failed to resolve object {obj!r}: {exc}") from exc
            radius = criteria.get("object_radius", 30 * u.arcsec)
            clauses.append(adql.format_circle_predicate(coord, radius))

        if "qobject" in criteria:
            clauses.append(
                f"{self._qobject_column} = {adql.quote_string_literal(criteria['qobject'])}"
            )

        if "program" in criteria:
            clauses.append(
                f"{self._program_column} = {adql.quote_string_literal(criteria['program'])}"
            )

        if "pi_name" in criteria:
            clauses.append(
                f"{self._piname_column} = {adql.quote_string_literal(criteria['pi_name'])}"
            )

        if "where" in criteria:
            clauses.append(f"({criteria['where']})")

        full_where = " AND ".join(clauses) if clauses else None
        sql = adql.build_select(validated_cols, table, where=full_where)
        return self._tap.query(sql, output_format=output_format, maxrec=maxrec)

    def query_adql(
        self,
        adql_query: str,
        *,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        """Raw ADQL escape hatch — caller is responsible for the query string."""
        return self._tap.query(adql_query, output_format=output_format, maxrec=maxrec)

    # ---- discovery ---------------------------------------------------------

    def list_tables(self) -> list[str]:
        """Names of tables this backend knows about (static)."""
        return sorted(self._table_columns.keys())

    def describe_table(self, table: str) -> Table:
        """Query TAP_SCHEMA for column metadata of ``table``."""
        adql.validate_identifier(table, kind="table")
        # `table` is identifier-validated above; literal is properly quoted.
        literal = adql.quote_string_literal(table)
        sql = (
            "SELECT column_name, datatype, unit, description "  # noqa: S608
            "FROM TAP_SCHEMA.columns "
            f"WHERE table_name = {literal}"
        )
        return self._tap.query(sql, output_format="ipac")

    # ---- async -------------------------------------------------------------

    def submit_async(
        self,
        adql_query: str,
        *,
        maxrec: int | None = None,
        output_format: OutputFormat = "votable",
    ) -> AsyncJob:
        """Submit an async ADQL job; returns an :class:`AsyncJob` handle."""
        async_url = f"{self._server}{self._tap_path}/async"
        data: dict[str, str] = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "QUERY": adql_query,
            "FORMAT": output_format,
            "PHASE": "RUN",
        }
        if maxrec is not None:
            data["MAXREC"] = str(maxrec)

        response = self._session_manager.session.post(
            async_url, data=data, timeout=self._conf.timeout, allow_redirects=False
        )
        if response.status_code not in (200, 303):
            response.raise_for_status()
        status_url = response.headers.get("Location") or response.url
        return AsyncJob(
            status_url,
            self._session_manager.session,
            output_format=output_format,
            conf=self._conf,
        )

    # ---- downloads ---------------------------------------------------------

    def download(
        self,
        result_table: Table,
        outdir: Path | str = ".",
        *,
        data_level: str | None = None,
        workers: int | None = None,
        resume: bool = True,
        progress: bool = True,
    ) -> list[Path]:
        """Download all FITS files referenced by ``result_table``.

        Returns the list of successfully downloaded paths. Partial failures
        raise :class:`DownloadError` after best-effort completion.

        ``data_level`` is required if it cannot be inferred from the table
        columns (e.g. a custom ADQL query that selected only the filename
        column). Subclasses that route downloads through level-specific URLs
        use this to pick the right URL template.
        """
        outdir = Path(outdir)
        level = data_level or self._infer_data_level(result_table)
        url_builder = self._row_to_url_factory(level)
        return parallel_download(
            result_table,
            url_builder,
            outdir,
            self._session_manager.session,
            workers=workers,
            resume=resume,
            progress=progress,
            conf=self._conf,
        )

    # ---- subclass hooks ----------------------------------------------------

    @abstractmethod
    def _build_download_url(self, data_level: str, filepath: str) -> str:
        """Per-archive download URL construction."""

    def _filename_column(self, data_level: str) -> str:
        """Return the ADQL column name holding the FITS filename for ``data_level``.

        Default convention: ``l<n>filename`` for ``l0``/``l1``/``l2``,
        ``solarl<n>filename`` for solar variants, ``engfilename`` for eng.
        Override in subclasses if the convention doesn't match.
        """
        return f"{data_level}filename"

    def _filepath_column(self, data_level: str) -> str:
        """Return the ADQL column name holding the per-file handle/path."""
        return f"{data_level}filepath"

    # ---- internals ---------------------------------------------------------

    def _table_for(self, data_level: str) -> str:
        if data_level not in self._datalevel_to_table:
            raise UnknownDataLevel(
                f"{data_level!r} is not a recognized data level for {self.name}; "
                f"expected one of {self.data_levels}"
            )
        return self._datalevel_to_table[data_level]

    def _validate_columns(self, table: str, columns: list[str] | None) -> list[str] | None:
        if columns is None:
            return None
        known = self._table_columns.get(table)
        if known is None:
            # Trust caller if we don't have a schema cached; identifier-shape
            # validation still applies.
            return [adql.validate_identifier(c, kind="column") for c in columns]
        return adql.validate_columns(columns, known)

    def _datetime_clauses(self, start: object, end: object) -> list[str]:
        clauses: list[str] = []
        col = self._datelike_column
        if start is not None:
            clauses.append(f"{col} >= {adql.format_date_for_adql(start)}")
        if end is not None:
            clauses.append(f"{col} <= {adql.format_date_for_adql(end)}")
        return clauses

    def _infer_data_level(self, table: Table) -> str:
        """Look at the columns in the result table to guess the data level."""
        cols = {c.lower() for c in table.colnames}
        # Prefer the most-specific match.
        for level in self.data_levels:
            if self._filename_column(level).lower() in cols:
                return level
        raise QueryError("Cannot infer data_level from result columns; pass data_level= explicitly")

    def _row_to_url_factory(self, data_level: str) -> RowToUrl:
        """Build the row → (filename, url) callable for ``parallel_download``."""
        fname_col = self._filename_column(data_level)
        path_col = self._filepath_column(data_level)

        def row_to_url(row: dict[str, object]) -> tuple[str, str]:
            filename = _coerce_str(row.get(fname_col))
            filepath = _coerce_str(row.get(path_col))
            if not filename or not filepath:
                raise QueryError(
                    f"Result row missing {fname_col}/{path_col} for {data_level}: {row!r}"
                )
            return filename, self._build_download_url(data_level, filepath)

        return row_to_url

    # ---- internals (auth checks) -------------------------------------------

    def _require_auth(self) -> None:
        if not self.is_authenticated:
            raise NotAuthenticated(f"{self.name}: this operation requires login")


def _coerce_str(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value) if value is not None else ""


__all__ = ["BaseArchive"]

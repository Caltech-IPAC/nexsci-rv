"""EXPRES archive backend (solar L1/L2 only in v1)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from astropy import units as u

from ..._adql_utils import CoordInput, RadiusInput
from ...base import BaseArchive
from ...exceptions import NotApplicable
from ...tap import OutputFormat
from .endpoints import DEFAULT_SERVER, build_download_url
from .tables import DATALEVEL_TO_TABLE, TABLE_COLUMNS

if TYPE_CHECKING:
    from astropy.table import Table


class EXPRESArchive(BaseArchive):
    """Client for EXPRES solar data hosted on the NEID/IPAC TAP service.

    Example:

        >>> from nexsci_rv import EXPRESArchive
        >>> expres = EXPRESArchive()
        >>> sun = expres.query_datetime(
        ...     "solarl2",
        ...     ("2024-11-01", "2024-11-06"),
        ...     columns=["l2filename", "obsdate", "v", "e_v", "dvrms", "extsnr"],
        ... )

    All EXPRES solar data is public; ``login()`` is not required and raises
    :class:`NotApplicable` if called.

    EXPRES solar rows carry sentinel ``qrad``/``qdecd`` values of ``-99.9``,
    so :meth:`query_position`, :meth:`query_object`, and :meth:`query_qobject`
    all raise :class:`NotApplicable`.
    """

    name: ClassVar[str] = "expres"
    data_levels: ClassVar[tuple[str, ...]] = ("solarl1", "solarl2")
    _default_server: ClassVar[str] = DEFAULT_SERVER
    _login_path: ClassVar[str | None] = None
    _datalevel_to_table: ClassVar[dict[str, str]] = DATALEVEL_TO_TABLE
    _table_columns: ClassVar[dict[str, tuple[str, ...]]] = TABLE_COLUMNS

    # EXPRES solar tables carry 'obsdate' for the observation timestamp
    # (as do the NEID tables; the BaseArchive 'date_obs' default fits neither).
    _datelike_column: ClassVar[str] = "obsdate"
    # No object-name column at all in EXPRES solar — object is always 'Sun'.
    _qobject_column: ClassVar[str] = "object"
    # PI/observer convention differs from NEID; the closest analogue is 'observer'.
    _piname_column: ClassVar[str] = "observer"
    # Program for solar data is always 'EXPRESSOLAR'; treat as exact match.

    # ---- queries that don't make sense for EXPRES solar --------------------

    def query_position(
        self,
        data_level: str,
        coord: CoordInput,
        radius: RadiusInput,
        *,
        columns: list[str] | None = None,
        where: str | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        raise NotApplicable(
            "EXPRES solar rows carry sentinel qrad/qdecd values (-99.9); "
            "position search would not return meaningful results."
        )

    def query_object(
        self,
        data_level: str,
        name: str,
        radius: RadiusInput = 30 * u.arcsec,
        **kw: Any,
    ) -> Table:
        raise NotApplicable(
            "EXPRES solar observations have no celestial target; "
            "use query_datetime or query_program instead."
        )

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
        raise NotApplicable(
            "EXPRES solar observations have no QOBJECT identifier; "
            "use query_datetime or query_program instead."
        )

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
        # 'observer' lives only on expressolarl1; the L2 table omits it.
        if data_level == "solarl2":
            raise NotApplicable(
                "expressolarl2 does not carry an observer column; "
                "use query_program (program='EXPRESSOLAR') or query_datetime instead."
            )
        return super().query_pi(
            data_level,
            pi_name,
            columns=columns,
            where=where,
            maxrec=maxrec,
            output_format=output_format,
        )

    def query_criteria(
        self,
        criteria: dict[str, Any],
        *,
        columns: list[str] | None = None,
        maxrec: int | None = None,
        output_format: OutputFormat = "ipac",
    ) -> Table:
        # Block keys that route to columns EXPRES solar doesn't have.
        forbidden = {"position", "object", "qobject"}
        present = forbidden & set(criteria.keys())
        if present:
            raise NotApplicable(
                f"EXPRES solar does not support {sorted(present)} in query_criteria; "
                "qrad/qdecd are sentinel -99.9 and there is no QOBJECT column."
            )
        if criteria.get("data_level") == "solarl2" and "pi_name" in criteria:
            raise NotApplicable(
                "expressolarl2 does not carry an observer column; pi_name is not "
                "supported for solarl2 in query_criteria."
            )
        return super().query_criteria(
            criteria,
            columns=columns,
            maxrec=maxrec,
            output_format=output_format,
        )

    # ---- per-archive download wiring ---------------------------------------

    def _build_download_url(self, data_level: str, filepath: str) -> str:
        return build_download_url(data_level, filepath, server=self._server)

    def _filename_column(self, data_level: str) -> str:
        # solarl1 → l1filename, solarl2 → l2filename
        return f"l{data_level[-1]}filename"

    def _filepath_column(self, data_level: str) -> str:
        # EXPRES uses l<n>filehand as the canonical download handle.
        return f"l{data_level[-1]}filehand"


__all__ = ["EXPRESArchive"]

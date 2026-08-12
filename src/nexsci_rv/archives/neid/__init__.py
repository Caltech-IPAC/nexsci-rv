"""NEID archive backend."""

from __future__ import annotations

from typing import ClassVar

from ...base import BaseArchive
from .endpoints import DEFAULT_SERVER, LOGIN_PATH, build_download_url
from .tables import DATALEVEL_TO_TABLE, TABLE_COLUMNS


class NEIDArchive(BaseArchive):
    """Client for the NEID archive at IPAC.

    Example:

        >>> from nexsci_rv import NEIDArchive
        >>> neid = NEIDArchive()
        >>> tbl = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))

    Authentication is only required for proprietary data; public observations
    are queryable without ``login()``.
    """

    name: ClassVar[str] = "neid"
    data_levels: ClassVar[tuple[str, ...]] = (
        "l0",
        "l1",
        "l2",
        "eng",
        "solarl0",
        "solarl1",
        "solarl2",
        "solareng",
    )
    _default_server: ClassVar[str] = DEFAULT_SERVER
    _login_path: ClassVar[str | None] = LOGIN_PATH
    _datalevel_to_table: ClassVar[dict[str, str]] = DATALEVEL_TO_TABLE
    _table_columns: ClassVar[dict[str, tuple[str, ...]]] = TABLE_COLUMNS

    def _build_download_url(self, data_level: str, filepath: str) -> str:
        return build_download_url(data_level, filepath)


__all__ = ["NEIDArchive"]

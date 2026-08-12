"""EXPRES table → column metadata.

v1 covers only the solar L1 and L2 tables that currently exist on the
production NEID server (the EXPRES instrument shares the IPAC TAP service).

The table names use a single ``s`` between ``expres`` and ``solar`` —
``expressolarl1`` / ``expressolarl2``. Double-s spellings (``expresssolarl1``)
return ``ORA-00942``. See the ``neid-archive-quirks`` skill for context.
"""

from __future__ import annotations

DATALEVEL_TO_TABLE: dict[str, str] = {
    "solarl1": "expressolarl1",
    "solarl2": "expressolarl2",
}


# Solar L1 columns (24 total), per the production server's TAP_SCHEMA as of
# 2026-02-27 (see expresssolar_test_log.md in the predecessor repo).
_EXPRESSOLARL1_COLUMNS: tuple[str, ...] = (
    "airmass",
    "expid",
    "exptime",
    "extracttype",
    "filedate",
    "l1filehand",
    "l1filename",
    "l1filepath",
    "l1ofname",
    "l1procversion",
    "l1propint",
    "mjd",
    "nightdate",
    "object",
    "obsdate",
    "observer",
    "obsjd",
    "obstype",
    "program",
    "qdecd",
    "qrad",
    "swversion",
    "tcsdec",
    "tcsra",
    "cntr",
)


# Solar L2 columns (28 total) — adds RV products: v, e_v, dvrms, ccfrvmod, extsnr.
_EXPRESSOLARL2_COLUMNS: tuple[str, ...] = (
    "airmass",
    "ccfjdsum",
    "ccfrvmod",
    "dvrms",
    "e_v",
    "expid",
    "exptime",
    "extsnr",
    "l2filehand",
    "l2filename",
    "l2filepath",
    "l2ofname",
    "l2procversion",
    "l2propint",
    "mjd",
    "obsdate",
    "obsjd",
    "obstype",
    "program",
    "qdecd",
    "qrad",
    "swversion",
    "v",
    "cntr",
)


TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "expressolarl1": _EXPRESSOLARL1_COLUMNS,
    "expressolarl2": _EXPRESSOLARL2_COLUMNS,
}


__all__ = ["DATALEVEL_TO_TABLE", "TABLE_COLUMNS"]

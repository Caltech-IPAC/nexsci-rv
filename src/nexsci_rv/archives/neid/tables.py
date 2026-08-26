"""NEID table → column metadata.

Static maps used by :class:`NEIDArchive` for column validation and data-level
dispatch. The server's full schema lives in TAP_SCHEMA and is reachable via
``archive.describe_table(name)`` for discovery; this file holds the columns
we actively support in the high-level API.
"""

from __future__ import annotations

DATALEVEL_TO_TABLE: dict[str, str] = {
    "l0": "neidl0",
    "l1": "neidl1",
    "l2": "neidl2",
    "eng": "neideng",
    "solarl0": "neidsolarl0",
    "solarl1": "neidsolarl1",
    "solarl2": "neidsolarl2",
    "solareng": "neidsolareng",
}

# Columns common to all NEID data levels.
_COMMON_COLUMNS: tuple[str, ...] = (
    "qobject",
    "object",
    "qra",
    "qdec",
    "obsdate",
    "exptime",
    "obsmode",
    "obstype",
    "program",
    "piname",
    "datalvl",
    "ra",
    "dec",
)

# Level-specific extra columns.
_L0_EXTRA: tuple[str, ...] = ("l0filename", "l0filepath", "l0propint", "l0checksum")
_L1_EXTRA: tuple[str, ...] = (
    "l1filename",
    "l1filepath",
    "l1propint",
    "l1checksum",
    "seeing",
    "airmass",
    "moonagl",
    "swversion",
)
_L2_EXTRA: tuple[str, ...] = (
    "l2filename",
    "l2filepath",
    "l2propint",
    "l2checksum",
    "seeing",
    "airmass",
    "moonagl",
    "ccfnoise",
    "ccfjdsum",
    "ccfrvmod",
    "ccfrvsum",
    "swversion",
)
_ENG_EXTRA: tuple[str, ...] = ("engfilename", "engfilepath", "engpropint")
_SOLAR_L0_EXTRA: tuple[str, ...] = (
    "solarl0filename",
    "solarl0filepath",
    "solarl0propint",
)
_SOLAR_L1_EXTRA: tuple[str, ...] = (
    "solarl1filename",
    "solarl1filepath",
    "solarl1propint",
    "airmass",
    "swversion",
)
_SOLAR_L2_EXTRA: tuple[str, ...] = (
    "solarl2filename",
    "solarl2filepath",
    "solarl2propint",
    "airmass",
    "ccfjdsum",
    "ccfrvmod",
    "ccfrvsum",
    "swversion",
)
_SOLAR_ENG_EXTRA: tuple[str, ...] = (
    "solarengfilename",
    "solarengfilepath",
    "solarengpropint",
)


TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "neidl0": _COMMON_COLUMNS + _L0_EXTRA,
    "neidl1": _COMMON_COLUMNS + _L1_EXTRA,
    "neidl2": _COMMON_COLUMNS + _L2_EXTRA,
    "neideng": _COMMON_COLUMNS + _ENG_EXTRA,
    "neidsolarl0": _COMMON_COLUMNS + _SOLAR_L0_EXTRA,
    "neidsolarl1": _COMMON_COLUMNS + _SOLAR_L1_EXTRA,
    "neidsolarl2": _COMMON_COLUMNS + _SOLAR_L2_EXTRA,
    "neidsolareng": _COMMON_COLUMNS + _SOLAR_ENG_EXTRA,
}


__all__ = ["DATALEVEL_TO_TABLE", "TABLE_COLUMNS"]

"""ADQL construction helpers.

All user-supplied query inputs (dates, coordinates, column names, identifier
strings) pass through this module before being placed into ADQL strings.
Centralizing this prevents:

- format drift (e.g. the NEID server requires Oracle ``to_date()`` rather than
  bare string comparisons; this module is the only place that knows that)
- ADQL injection via unescaped string literals
- subtle bugs from mixing ``datetime`` / ``Time`` / strings at call sites

This module is intentionally archive-agnostic. NEID/EXPRES specifics live in
``archives/<name>/``.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, TypeAlias

from astropy import units as u
from astropy.coordinates import Angle, SkyCoord
from astropy.time import Time

from .exceptions import QueryError, UnknownColumn

if TYPE_CHECKING:
    from collections.abc import Iterable


DateInput: TypeAlias = "str | datetime | Time"
CoordInput: TypeAlias = "SkyCoord | tuple[float, float]"
RadiusInput: TypeAlias = "Angle | u.Quantity | float"

_ORACLE_DATETIME_FMT = "yyyy-mm-dd HH24:MI:SS"

# ADQL identifiers (column names, table names) — letters, digits, underscore,
# and must start with a letter. We use this for *validation*, not escaping.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def normalize_date(value: DateInput) -> Time:
    """Coerce a user-supplied date to an :class:`astropy.time.Time`."""
    if isinstance(value, Time):
        return value
    if isinstance(value, datetime):
        return Time(value)
    if isinstance(value, str):
        # astropy.Time handles ISO-8601 + a few common variants.
        return Time(value)
    raise QueryError(f"Unrecognized date input: {value!r} (type {type(value).__name__})")


def format_date_for_adql(value: DateInput) -> str:
    """Return an Oracle ``to_date('YYYY-MM-DD HH24:MI:SS','...')`` literal.

    The NEID TAP service requires this form for date predicates — bare string
    comparisons (e.g. ``obsdate >= '2024-11-01'``) cause a server-side XML
    parsing error.
    """
    t = normalize_date(value)
    s = t.iso  # 'YYYY-MM-DD HH:MM:SS.sss' — astropy default
    # Trim sub-second precision; Oracle to_date with HH24:MI:SS rejects it.
    s = s.split(".")[0]
    if len(s) == 10:  # date-only — promote to midnight
        s += " 00:00:00"
    return f"to_date('{s}','{_ORACLE_DATETIME_FMT}')"


def normalize_coord(value: CoordInput) -> SkyCoord:
    """Coerce a user-supplied coordinate to a :class:`SkyCoord` in ICRS degrees."""
    if isinstance(value, SkyCoord):
        return value.icrs
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and all(isinstance(v, (int, float)) for v in value)
    ):
        ra, dec = value
        return SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    raise QueryError(f"Unrecognized coordinate input: {value!r}")


def normalize_radius(value: RadiusInput) -> Angle:
    """Coerce a radius input to an :class:`Angle`.

    Bare numbers (``int`` / ``float``) are interpreted as **degrees** — this
    matches astroquery's longstanding convention. ``NaN`` and ``inf`` are
    rejected so they can't slip into ADQL CIRCLE predicates.
    """
    if isinstance(value, Angle):
        angle = value
    elif isinstance(value, u.Quantity):
        angle = Angle(value)
    elif isinstance(value, (int, float)):
        if not _is_finite_real(float(value)):
            raise QueryError(f"Radius must be a finite real number, got {value!r}")
        angle = Angle(value * u.deg)
    else:
        raise QueryError(f"Unrecognized radius input: {value!r}")

    deg = angle.to(u.deg).value
    if not _is_finite_real(float(deg)) or deg <= 0:
        raise QueryError(f"Radius must be positive and finite, got {angle}")
    return angle


def _is_finite_real(x: float) -> bool:
    import math

    return math.isfinite(x)


def format_circle_predicate(coord: CoordInput, radius: RadiusInput) -> str:
    """Build a TAP ``CONTAINS(POINT(...),CIRCLE(...))=1`` predicate fragment."""
    c = normalize_coord(coord)
    r = normalize_radius(radius)
    ra_deg = c.ra.to(u.deg).value
    dec_deg = c.dec.to(u.deg).value
    r_deg = r.to(u.deg).value
    return (
        f"CONTAINS(POINT('ICRS', ra, dec), "
        f"CIRCLE('ICRS', {ra_deg:.10f}, {dec_deg:.10f}, {r_deg:.10f}))=1"
    )


def validate_identifier(name: str, *, kind: str = "identifier") -> str:
    """Reject any string that isn't a plain ADQL identifier.

    Used for column names, table names, and similar SQL fragments. Validation,
    not escaping — we never want to *quote* user-supplied identifiers because
    that would silently let through dangerous characters.
    """
    if not isinstance(name, str) or not _IDENT_RE.match(name):
        raise QueryError(f"Invalid {kind}: {name!r}")
    return name


def validate_columns(columns: Iterable[str], known: Iterable[str]) -> list[str]:
    """Validate that each requested column exists in ``known``.

    Comparison is case-insensitive (Oracle conventions), but the returned list
    preserves the user-supplied casing for legibility in generated ADQL.
    """
    known_lower = {k.lower() for k in known}
    result: list[str] = []
    for col in columns:
        validate_identifier(col, kind="column")
        if col.lower() not in known_lower:
            raise UnknownColumn(col)
        result.append(col)
    return result


def quote_string_literal(value: str) -> str:
    """Quote a string for inclusion as an SQL literal.

    Oracle-style: double any embedded single quotes. Newlines and control
    characters are rejected outright to limit injection surface.
    """
    if not isinstance(value, str):
        raise QueryError(f"Expected str, got {type(value).__name__}")
    if any(c in value for c in "\r\n\x00"):
        raise QueryError("Control characters are not permitted in string literals")
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def build_select(
    columns: Iterable[str] | None,
    table: str,
    *,
    where: str | None = None,
    order_by: str | None = None,
) -> str:
    """Assemble a SELECT statement from validated components.

    ``table`` and ``order_by`` are passed through :func:`validate_identifier`;
    ``columns`` (if provided) is assumed to already be validated by
    :func:`validate_columns`. ``where`` is a free-form ADQL fragment trusted
    to be safe — only call sites that build their own WHERE clauses from
    validated inputs should pass anything here.
    """
    validate_identifier(table, kind="table")
    select = ", ".join(columns) if columns else "*"
    # `table` is validated above; `select` is either "*" or a join of caller-
    # validated columns; `where` is documented as caller-trusted. Bandit's
    # S608 cannot prove those preconditions, so we suppress it here.
    sql = f"SELECT {select} FROM {table}"  # noqa: S608
    if where:
        sql += f" WHERE {where}"
    if order_by:
        validate_identifier(order_by, kind="order_by column")
        sql += f" ORDER BY {order_by}"
    return sql


__all__ = [
    "CoordInput",
    "DateInput",
    "RadiusInput",
    "build_select",
    "format_circle_predicate",
    "format_date_for_adql",
    "normalize_coord",
    "normalize_date",
    "normalize_radius",
    "quote_string_literal",
    "validate_columns",
    "validate_identifier",
]

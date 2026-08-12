"""ADQL helpers — date/coord normalization, identifier validation, predicates."""

from __future__ import annotations

import math
from datetime import datetime

import pytest
from astropy import units as u
from astropy.coordinates import Angle, SkyCoord
from astropy.time import Time

from nexsci_rv._adql_utils import (
    build_select,
    format_circle_predicate,
    format_date_for_adql,
    normalize_coord,
    normalize_date,
    normalize_radius,
    quote_string_literal,
    validate_columns,
    validate_identifier,
)
from nexsci_rv.exceptions import QueryError, UnknownColumn

# ---- date ------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "2024-11-01",
        "2024-11-01 12:34:56",
        datetime(2024, 11, 1, 12, 34, 56),
        Time("2024-11-01T12:34:56"),
    ],
)
def test_normalize_date_accepts_common_forms(value):
    t = normalize_date(value)
    assert isinstance(t, Time)


def test_normalize_date_rejects_garbage():
    with pytest.raises(QueryError):
        normalize_date(12345)  # type: ignore[arg-type]


def test_format_date_for_adql_uses_oracle_to_date():
    out = format_date_for_adql("2024-11-01 12:34:56")
    assert out == "to_date('2024-11-01 12:34:56','yyyy-mm-dd HH24:MI:SS')"


def test_format_date_for_adql_promotes_date_to_midnight():
    out = format_date_for_adql("2024-11-01")
    assert "2024-11-01 00:00:00" in out


def test_format_date_for_adql_trims_subseconds():
    out = format_date_for_adql(Time("2024-11-01T12:34:56.789"))
    assert ".789" not in out
    assert "12:34:56" in out


# ---- coord -----------------------------------------------------------------


def test_normalize_coord_accepts_tuple_in_degrees():
    c = normalize_coord((10.5, -20.0))
    assert c.ra.to(u.deg).value == pytest.approx(10.5)
    assert c.dec.to(u.deg).value == pytest.approx(-20.0)


def test_normalize_coord_passes_skycoord_through():
    sc = SkyCoord(ra=10 * u.deg, dec=20 * u.deg, frame="icrs")
    assert normalize_coord(sc).ra.to(u.deg).value == pytest.approx(10.0)


def test_normalize_coord_rejects_garbage():
    with pytest.raises(QueryError):
        normalize_coord("nope")  # type: ignore[arg-type]


# ---- radius ----------------------------------------------------------------


def test_normalize_radius_bare_float_is_degrees():
    r = normalize_radius(0.5)
    assert r.to(u.arcmin).value == pytest.approx(30.0)


def test_normalize_radius_accepts_angle():
    r = normalize_radius(30 * u.arcsec)
    assert r.to(u.deg).value == pytest.approx(30 / 3600)


def test_normalize_radius_accepts_angle_object():
    r = normalize_radius(Angle("1d"))
    assert r.to(u.deg).value == pytest.approx(1.0)


# ---- predicate -------------------------------------------------------------


def test_circle_predicate_emits_icrs_with_full_precision():
    pred = format_circle_predicate((10.0, 20.0), 0.1)
    assert pred.startswith("CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS',")
    assert pred.endswith("))=1")
    assert "10.0000000000" in pred
    assert "20.0000000000" in pred


# ---- identifier validation -------------------------------------------------


@pytest.mark.parametrize("name", ["foo", "obsdate", "L1_filename", "_x"])
def test_validate_identifier_accepts_good(name):
    assert validate_identifier(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        "1foo",
        "foo bar",
        "foo;",
        "foo'; DROP TABLE neidl2; --",
        "foo.bar",
    ],
)
def test_validate_identifier_rejects_bad(name):
    with pytest.raises(QueryError):
        validate_identifier(name)


def test_validate_columns_passes_known():
    cols = validate_columns(["obsdate", "exptime"], ["obsdate", "exptime", "airmass"])
    assert cols == ["obsdate", "exptime"]


def test_validate_columns_is_case_insensitive():
    cols = validate_columns(["OBSDATE"], ["obsdate"])
    assert cols == ["OBSDATE"]


def test_validate_columns_raises_on_unknown():
    with pytest.raises(UnknownColumn):
        validate_columns(["obsdate", "no_such_col"], ["obsdate"])


# ---- string literals -------------------------------------------------------


def test_quote_string_literal_escapes_single_quotes():
    assert quote_string_literal("O'Brien") == "'O''Brien'"


def test_quote_string_literal_rejects_newlines():
    with pytest.raises(QueryError):
        quote_string_literal("foo\nbar")


def test_quote_string_literal_rejects_null():
    with pytest.raises(QueryError):
        quote_string_literal("foo\x00bar")


# ---- build_select ----------------------------------------------------------


def test_build_select_star():
    sql = build_select(None, "neidl2")
    assert sql == "SELECT * FROM neidl2"


def test_build_select_with_columns_and_where():
    sql = build_select(["obsdate", "exptime"], "neidl2", where="exptime > 30")
    assert sql == "SELECT obsdate, exptime FROM neidl2 WHERE exptime > 30"


def test_build_select_with_order_by():
    sql = build_select(None, "neidl2", order_by="obsdate")
    assert sql.endswith("ORDER BY obsdate")


def test_build_select_rejects_bad_table():
    with pytest.raises(QueryError):
        build_select(None, "neidl2; DROP TABLE")


def test_build_select_no_NaN_in_radius():
    # paranoia: make sure no NaN sneaks into the format string for predicates
    with pytest.raises(QueryError):
        normalize_radius(math.nan)

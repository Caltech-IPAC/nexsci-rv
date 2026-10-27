"""BaseArchive — query construction, data-level validation, etc.

We test through NEIDArchive (the concrete subclass) but with the TAP client
mocked out so no network is touched. The point is to verify the ADQL
construction logic in base.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from nexsci_rv import NEIDArchive
from nexsci_rv.base import DATA_LEVEL_META_KEY, _coerce_str
from nexsci_rv.config import Conf
from nexsci_rv.exceptions import (
    NotApplicable,
    NotAuthenticated,
    QueryError,
    UnknownColumn,
    UnknownDataLevel,
)


@pytest.fixture
def neid(tmp_cookie_root):
    arc = NEIDArchive(conf=Conf(cookie_root=tmp_cookie_root))
    # Replace the TAP client with a mock so query_* calls don't touch network.
    arc._tap = MagicMock()
    arc._tap.query.return_value = Table()
    return arc


def _last_adql(arc) -> str:
    return arc._tap.query.call_args.args[0]


def test_unknown_data_level_raises(neid):
    with pytest.raises(UnknownDataLevel):
        neid.query_datetime("l3", ("2024-11-01", "2024-11-06"))


def test_query_datetime_builds_oracle_to_date(neid):
    neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))
    sql = _last_adql(neid)
    assert "neidl2" in sql
    assert "to_date('2024-11-01 00:00:00','yyyy-mm-dd HH24:MI:SS')" in sql
    assert "to_date('2024-11-06 00:00:00','yyyy-mm-dd HH24:MI:SS')" in sql
    assert "obsdate >=" in sql
    assert "obsdate <=" in sql


def test_query_datetime_open_ended_start(neid):
    neid.query_datetime("l2", (None, "2024-11-06"))
    sql = _last_adql(neid)
    assert "obsdate <=" in sql
    assert "obsdate >=" not in sql


def test_query_datetime_with_columns_validates(neid):
    neid.query_datetime(
        "l2",
        ("2024-11-01", "2024-11-06"),
        columns=["l2filename", "obsdate", "exptime"],
    )
    sql = _last_adql(neid)
    assert "l2filename" in sql
    assert "obsdate" in sql
    assert "exptime" in sql


def test_query_datetime_rejects_unknown_column(neid):
    with pytest.raises(UnknownColumn):
        neid.query_datetime("l2", ("2024-11-01", "2024-11-06"), columns=["no_such_col"])


def test_download_url_honors_server_override(tmp_cookie_root):
    arc = NEIDArchive(
        server="https://proxy.example.org",
        conf=Conf(cookie_root=tmp_cookie_root),
    )
    url = arc._build_download_url("l2", "/p/x.fits")
    assert url.startswith("https://proxy.example.org/get_file.php?filehand=/p/x.fits")


def test_download_url_defaults_to_production(neid):
    url = neid._build_download_url("l2", "/p/x.fits")
    assert url.startswith("https://neid.ipac.caltech.edu/get_file.php")


def test_query_position_builds_circle_predicate(neid):
    neid.query_position("l2", (10.0, 20.0), 0.1)
    sql = _last_adql(neid)
    # NEID's position columns are qrad/qdecd; the server rejects ra/dec.
    assert "CONTAINS(POINT('ICRS', qrad, qdecd)" in sql
    assert "CIRCLE('ICRS'," in sql


def test_query_qobject_quotes_value(neid):
    neid.query_qobject("l2", "Gaia DR2 12345")
    sql = _last_adql(neid)
    assert "qobject = 'Gaia DR2 12345'" in sql


def test_query_qobject_escapes_single_quote(neid):
    neid.query_qobject("l2", "O'Brien-1")
    sql = _last_adql(neid)
    assert "'O''Brien-1'" in sql


def test_query_program_quotes_value(neid):
    neid.query_program("l2", "2021A-2014")
    sql = _last_adql(neid)
    assert "program = '2021A-2014'" in sql


def test_query_pi_quotes_value(neid):
    neid.query_pi("l2", "Sarah Logsdon")
    sql = _last_adql(neid)
    assert "piname = 'Sarah Logsdon'" in sql


def test_query_criteria_combines(neid):
    neid.query_criteria(
        {
            "data_level": "l2",
            "datetime": ("2024-11-01", "2024-11-06"),
            "qobject": "Gaia DR2 999",
            "program": "2024A-001",
        }
    )
    sql = _last_adql(neid)
    assert "neidl2" in sql
    assert "qobject = 'Gaia DR2 999'" in sql
    assert "program = '2024A-001'" in sql
    assert "to_date('2024-11-01" in sql


def test_query_criteria_requires_data_level(neid):
    with pytest.raises(QueryError):
        neid.query_criteria({"datetime": ("2024-11-01", "2024-11-06")})


def test_query_criteria_raw_where_passed_through(neid):
    neid.query_criteria({"data_level": "l2", "where": "exptime > 30"})
    sql = _last_adql(neid)
    assert "(exptime > 30)" in sql


def test_describe_table_uses_tap_schema(neid):
    neid.describe_table("neidl2")
    sql = _last_adql(neid)
    assert "TAP_SCHEMA.columns" in sql
    assert "table_name = 'neidl2'" in sql


def test_list_tables_returns_known(neid):
    tables = neid.list_tables()
    assert "neidl0" in tables
    assert "neidl2" in tables
    assert "neidsolarl2" in tables


def test_query_adql_is_escape_hatch(neid):
    neid.query_adql("SELECT 1 FROM dual")
    sql = _last_adql(neid)
    assert sql == "SELECT 1 FROM dual"


def test_login_path_set_for_neid(neid):
    assert NEIDArchive._login_path is not None


def test_archive_without_login_path_raises_not_applicable(monkeypatch, tmp_cookie_root):
    """If a subclass omits _login_path, login() raises NotApplicable."""
    monkeypatch.setattr(NEIDArchive, "_login_path", None)
    arc = NEIDArchive(conf=Conf(cookie_root=tmp_cookie_root))
    with pytest.raises(NotApplicable):
        arc.login(username="u", password="p")


def test_infer_data_level_refuses_night_vs_solar_ambiguity(neid):
    """NEID night and solar tables share l2filename, and their download URLs differ."""
    table = Table({"l2filename": ["a"], "l2filepath": ["/p/a"]})
    with pytest.raises(QueryError, match="several data levels"):
        neid._infer_data_level(table)


@pytest.mark.parametrize("level", ["l2", "solarl2", "eng"])
def test_query_result_records_data_level(neid, level):
    result = neid.query_datetime(level, ("2024-11-01", "2024-11-02"))
    assert result.meta[DATA_LEVEL_META_KEY] == level


@pytest.mark.parametrize(
    ("level", "expected_path", "solar"),
    [
        ("l2", "/p/L2.fits", False),
        ("l1", "/p/L1.fits", False),
        ("l0", "/p/L0.fits", False),
        ("solarl2", "/p/L2.fits", True),
        ("eng", "/p/L0.fits", False),
    ],
)
def test_download_uses_recorded_level_files(neid, level, expected_path, solar):
    """An L2 result must download L2 files, not the L0 files its rows also reference."""
    row = {
        "l0filename": "L0.fits",
        "l0filepath": "/p/L0.fits",
        "l1filename": "L1.fits",
        "l1filepath": "/p/L1.fits",
        "l2filename": "L2.fits",
        "l2filepath": "/p/L2.fits",
    }
    name, url = neid._row_to_url_factory(level)(row)
    assert name == expected_path.rsplit("/", 1)[1]
    assert f"filehand={expected_path}" in url
    assert ("&solar" in url) is solar


def test_infer_data_level_raises_when_ambiguous(neid):
    table = Table({"foo": [1], "bar": [2]})
    with pytest.raises(QueryError):
        neid._infer_data_level(table)


# ---------------------------------------------------------------------------
# timeout override in __init__
# ---------------------------------------------------------------------------


def test_timeout_override_sets_conf_timeout(tmp_cookie_root):
    """Asserts passing timeout= to constructor creates a per-instance conf override."""
    arc = NEIDArchive(conf=Conf(cookie_root=tmp_cookie_root), timeout=99.0)
    assert arc._conf.timeout == 99.0


# ---------------------------------------------------------------------------
# auth pass-through: login, logout, is_authenticated, _require_auth
# ---------------------------------------------------------------------------


def test_login_delegates_to_session_manager(neid):
    """Asserts login() calls session_manager.login with the constructed URL."""
    neid._session_manager = MagicMock()
    neid.login(username="testuser", password="secret")
    neid._session_manager.login.assert_called_once()
    call_kwargs = neid._session_manager.login.call_args
    url_arg = call_kwargs.args[0]
    assert "cgi-bin" in url_arg or "login" in url_arg.lower() or url_arg.startswith("https://")
    assert call_kwargs.kwargs.get("username") == "testuser"
    assert call_kwargs.kwargs.get("password") == "secret"


def test_logout_delegates_to_session_manager(neid):
    """Asserts logout() calls session_manager.logout."""
    neid._session_manager = MagicMock()
    neid.logout()
    neid._session_manager.logout.assert_called_once()


def test_is_authenticated_delegates_to_session_manager(neid):
    """Asserts is_authenticated reflects session_manager.is_authenticated."""
    neid._session_manager = MagicMock()
    neid._session_manager.is_authenticated = True
    assert neid.is_authenticated is True
    neid._session_manager.is_authenticated = False
    assert neid.is_authenticated is False


def test_require_auth_raises_when_not_authenticated(neid):
    """Asserts _require_auth raises NotAuthenticated when not logged in."""
    neid._session_manager = MagicMock()
    neid._session_manager.is_authenticated = False
    with pytest.raises(NotAuthenticated):
        neid._require_auth()


def test_require_auth_passes_when_authenticated(neid):
    """Asserts _require_auth does not raise when session is authenticated."""
    neid._session_manager = MagicMock()
    neid._session_manager.is_authenticated = True
    neid._require_auth()  # should not raise


# ---------------------------------------------------------------------------
# query_datetime with where clause
# ---------------------------------------------------------------------------


def test_query_datetime_with_where_clause(neid):
    """Asserts query_datetime includes the raw where clause in the ADQL."""
    neid.query_datetime("l2", ("2024-11-01", "2024-11-06"), where="exptime > 30")
    sql = _last_adql(neid)
    assert "(exptime > 30)" in sql


def test_query_datetime_start_only(neid):
    """Asserts query_datetime with only start date omits the end clause."""
    neid.query_datetime("l2", ("2024-11-01", None))
    sql = _last_adql(neid)
    assert "obsdate >=" in sql
    assert "obsdate <=" not in sql


# ---------------------------------------------------------------------------
# query_position with where clause
# ---------------------------------------------------------------------------


def test_query_position_with_where_clause(neid):
    """Asserts query_position includes the raw where clause in the ADQL."""
    neid.query_position("l2", (10.0, 20.0), 0.1, where="exptime > 60")
    sql = _last_adql(neid)
    assert "(exptime > 60)" in sql
    assert "CIRCLE" in sql


# ---------------------------------------------------------------------------
# query_qobject / query_program / query_pi with where clause
# ---------------------------------------------------------------------------


def test_query_qobject_with_where_clause(neid):
    """Asserts query_qobject includes the raw where clause in the ADQL."""
    neid.query_qobject("l2", "Gaia DR2 12345", where="exptime > 10")
    sql = _last_adql(neid)
    assert "(exptime > 10)" in sql
    assert "qobject" in sql


def test_query_program_with_where_clause(neid):
    """Asserts query_program includes the raw where clause in the ADQL."""
    neid.query_program("l2", "2021A-2014", where="exptime > 10")
    sql = _last_adql(neid)
    assert "(exptime > 10)" in sql
    assert "program" in sql


def test_query_pi_with_where_clause(neid):
    """Asserts query_pi includes the raw where clause in the ADQL."""
    neid.query_pi("l2", "Sarah Logsdon", where="exptime > 10")
    sql = _last_adql(neid)
    assert "(exptime > 10)" in sql
    assert "piname" in sql


# ---------------------------------------------------------------------------
# query_object (SkyCoord.from_name path)
# ---------------------------------------------------------------------------


def test_query_object_resolves_name_and_builds_circle(neid, monkeypatch):
    """Asserts query_object monkeypatches SkyCoord.from_name and builds a CIRCLE predicate."""
    fake_coord = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    monkeypatch.setattr("nexsci_rv.base.SkyCoord.from_name", lambda name: fake_coord)
    neid.query_object("l2", "Tau Ceti")
    sql = _last_adql(neid)
    assert "CIRCLE" in sql
    assert "CONTAINS" in sql


def test_query_object_raises_query_error_on_resolution_failure(neid, monkeypatch):
    """Asserts query_object raises QueryError when SkyCoord.from_name fails."""

    def fail_name(name):
        raise RuntimeError("name resolution failed")

    monkeypatch.setattr("nexsci_rv.base.SkyCoord.from_name", fail_name)
    with pytest.raises(QueryError, match="Failed to resolve object"):
        neid.query_object("l2", "NoSuchStar")


# ---------------------------------------------------------------------------
# query_criteria — position and object paths
# ---------------------------------------------------------------------------


def test_query_criteria_with_position(neid):
    """Asserts query_criteria handles the 'position' key and builds CIRCLE predicate."""
    neid.query_criteria(
        {
            "data_level": "l2",
            "position": ((10.0, 20.0), 0.1),
        }
    )
    sql = _last_adql(neid)
    assert "CIRCLE" in sql


def test_query_criteria_with_object(neid, monkeypatch):
    """Asserts query_criteria handles the 'object' key using SkyCoord.from_name."""
    fake_coord = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    monkeypatch.setattr("nexsci_rv.base.SkyCoord.from_name", lambda name: fake_coord)
    neid.query_criteria({"data_level": "l2", "object": "Tau Ceti"})
    sql = _last_adql(neid)
    assert "CIRCLE" in sql


def test_query_criteria_object_failure_raises_query_error(neid, monkeypatch):
    """Asserts query_criteria raises QueryError when object resolution fails."""

    def fail_name(name):
        raise RuntimeError("no resolver")

    monkeypatch.setattr("nexsci_rv.base.SkyCoord.from_name", fail_name)
    with pytest.raises(QueryError, match="Failed to resolve object"):
        neid.query_criteria({"data_level": "l2", "object": "Nonexistent"})


def test_query_criteria_with_pi_name(neid):
    """Asserts query_criteria handles the 'pi_name' key in the criteria dict."""
    neid.query_criteria({"data_level": "l2", "pi_name": "Alice Smith"})
    sql = _last_adql(neid)
    assert "piname = 'Alice Smith'" in sql


# ---------------------------------------------------------------------------
# submit_async
# ---------------------------------------------------------------------------


def test_submit_async_posts_correct_form_and_returns_async_job(neid, monkeypatch):
    """Asserts submit_async POSTs the right form and constructs AsyncJob with the Location URL."""
    from nexsci_rv.async_job import AsyncJob as RealAsyncJob

    mock_response = MagicMock()
    mock_response.status_code = 303
    mock_response.headers = {"Location": "https://tap.example/job/xyz999"}
    mock_response.url = "https://tap.example/job/xyz999"

    neid._session_manager = MagicMock()
    neid._session_manager.session.post.return_value = mock_response

    # Patch AsyncJob so the constructor doesn't actually poll
    MockAsyncJob = MagicMock(spec=RealAsyncJob)
    monkeypatch.setattr("nexsci_rv.base.AsyncJob", MockAsyncJob)

    neid.submit_async("SELECT 1 FROM neidl2", maxrec=50)

    post_call = neid._session_manager.session.post.call_args
    form = post_call.kwargs["data"]
    assert form["REQUEST"] == "doQuery"
    assert form["LANG"] == "ADQL"
    assert form["QUERY"] == "SELECT 1 FROM neidl2"
    assert form["PHASE"] == "RUN"
    assert form["MAXREC"] == "50"

    # AsyncJob was constructed with the Location URL
    MockAsyncJob.assert_called_once()
    first_arg = MockAsyncJob.call_args.args[0]
    assert first_arg == "https://tap.example/job/xyz999"


# ---------------------------------------------------------------------------
# _row_to_url_factory
# ---------------------------------------------------------------------------


def test_row_to_url_factory_returns_filename_and_url(neid):
    """Asserts the row→url closure returns (filename, url) for a valid row."""
    factory = neid._row_to_url_factory("l2")
    filename, url = factory({"l2filename": "obs.fits", "l2filepath": "/data/obs.fits"})
    assert filename == "obs.fits"
    assert "filehand" in url


def test_row_to_url_factory_raises_query_error_on_missing_path(neid):
    """Asserts the row→url closure raises QueryError when filepath is missing."""
    factory = neid._row_to_url_factory("l2")
    with pytest.raises(QueryError, match="missing"):
        factory({"l2filename": "obs.fits", "l2filepath": None})


def test_row_to_url_factory_raises_query_error_on_missing_filename(neid):
    """Asserts the row→url closure raises QueryError when filename is missing."""
    factory = neid._row_to_url_factory("l2")
    with pytest.raises(QueryError, match="missing"):
        factory({"l2filename": None, "l2filepath": "/data/obs.fits"})


# ---------------------------------------------------------------------------
# download (parallel_download delegation)
# ---------------------------------------------------------------------------


def test_download_delegates_to_parallel_download(neid, tmp_path, monkeypatch):
    """Asserts download() calls parallel_download with the right arguments."""
    result_table = Table({"l2filename": ["obs.fits"], "l2filepath": ["/data/obs.fits"]})
    result_table.meta[DATA_LEVEL_META_KEY] = "l2"
    mock_parallel = MagicMock(return_value=[tmp_path / "obs.fits"])
    monkeypatch.setattr("nexsci_rv.base.parallel_download", mock_parallel)
    neid._session_manager = MagicMock()

    paths = neid.download(result_table, outdir=tmp_path, workers=2, resume=False, progress=False)

    mock_parallel.assert_called_once()
    call_kwargs = mock_parallel.call_args
    assert call_kwargs.args[2] == tmp_path  # outdir
    assert call_kwargs.kwargs["workers"] == 2
    assert call_kwargs.kwargs["resume"] is False
    assert paths == [tmp_path / "obs.fits"]


# ---------------------------------------------------------------------------
# _coerce_str
# ---------------------------------------------------------------------------


def test_coerce_str_bytes_decoded():
    """Asserts _coerce_str decodes bytes to utf-8 string."""
    assert _coerce_str(b"hello") == "hello"


def test_coerce_str_none_returns_empty():
    """Asserts _coerce_str returns empty string for None."""
    assert _coerce_str(None) == ""


def test_coerce_str_int_converted():
    """Asserts _coerce_str converts non-string non-bytes values via str()."""
    assert _coerce_str(42) == "42"


def test_coerce_str_str_passthrough():
    """Asserts _coerce_str returns string values unchanged."""
    assert _coerce_str("obs.fits") == "obs.fits"


# ---------------------------------------------------------------------------
# _validate_columns — unknown table (no schema cached)
# ---------------------------------------------------------------------------


def test_validate_columns_without_cached_schema(neid):
    """Asserts _validate_columns passes through valid identifiers for unknown tables."""
    # 'unknown_table' is not in _table_columns, so validation trusts the caller
    result = neid._validate_columns("unknown_table", ["col_a", "col_b"])
    assert result == ["col_a", "col_b"]

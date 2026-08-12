"""EXPRESArchive — query construction, NotApplicable surfaces, download URL.

No network; TAP client is mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from astropy.table import Table

from nexsci_rv import EXPRESArchive
from nexsci_rv.archives.expres.endpoints import build_download_url
from nexsci_rv.archives.expres.tables import DATALEVEL_TO_TABLE, TABLE_COLUMNS
from nexsci_rv.config import Conf
from nexsci_rv.exceptions import NotApplicable, UnknownColumn, UnknownDataLevel


@pytest.fixture
def expres(tmp_cookie_root):
    arc = EXPRESArchive(conf=Conf(cookie_root=tmp_cookie_root))
    arc._tap = MagicMock()
    arc._tap.query.return_value = Table()
    return arc


def _last_adql(arc) -> str:
    return arc._tap.query.call_args.args[0]


# ---- table map -------------------------------------------------------------


def test_only_solar_levels_supported():
    assert EXPRESArchive.data_levels == ("solarl1", "solarl2")


def test_datalevel_map_uses_single_s_spelling():
    assert DATALEVEL_TO_TABLE["solarl1"] == "expressolarl1"
    assert DATALEVEL_TO_TABLE["solarl2"] == "expressolarl2"


def test_solarl2_has_rv_columns():
    cols = TABLE_COLUMNS["expressolarl2"]
    assert "v" in cols  # cm/s RV
    assert "e_v" in cols  # cm/s RV uncertainty
    assert "dvrms" in cols  # km/s
    assert "ccfrvmod" in cols
    assert "extsnr" in cols


def test_unknown_data_level_raises(expres):
    with pytest.raises(UnknownDataLevel):
        expres.query_datetime("l2", ("2024-11-01", "2024-11-06"))


# ---- query construction ----------------------------------------------------


def test_query_datetime_uses_obsdate_column(expres):
    """EXPRES uses ``obsdate`` for the timestamp, not ``date_obs``."""
    expres.query_datetime("solarl2", ("2024-11-01", "2024-11-06"))
    sql = _last_adql(expres)
    assert "expressolarl2" in sql
    assert "obsdate >=" in sql
    assert "obsdate <=" in sql
    assert "date_obs" not in sql


def test_query_datetime_column_validation(expres):
    expres.query_datetime(
        "solarl2",
        ("2024-11-01", "2024-11-06"),
        columns=["l2filename", "obsdate", "v", "e_v"],
    )
    sql = _last_adql(expres)
    for col in ["l2filename", "obsdate", "v", "e_v"]:
        assert col in sql


def test_query_datetime_rejects_unknown_column(expres):
    with pytest.raises(UnknownColumn):
        expres.query_datetime("solarl1", ("2024-11-01", "2024-11-06"), columns=["no_such_col"])


def test_query_program_works(expres):
    expres.query_program("solarl2", "EXPRESSOLAR")
    sql = _last_adql(expres)
    assert "program = 'EXPRESSOLAR'" in sql


# ---- NotApplicable surfaces ------------------------------------------------


def test_query_position_raises_not_applicable(expres):
    with pytest.raises(NotApplicable, match="qrad/qdecd"):
        expres.query_position("solarl1", (10.0, 20.0), 0.1)


def test_query_object_raises_not_applicable(expres):
    with pytest.raises(NotApplicable):
        expres.query_object("solarl2", "Sun")


def test_query_qobject_raises_not_applicable(expres):
    with pytest.raises(NotApplicable):
        expres.query_qobject("solarl2", "Sun")


def test_login_raises_not_applicable(expres):
    with pytest.raises(NotApplicable):
        expres.login(username="u", password="p")


# ---- query_pi / query_criteria guards (audit finding) ----------------------


def test_query_pi_works_on_solarl1(expres):
    """L1 has an `observer` column, so query_pi composes a valid ADQL."""
    expres.query_pi("solarl1", "Solar . Telescope")
    sql = _last_adql(expres)
    assert "observer =" in sql
    assert "expressolarl1" in sql


def test_query_pi_raises_not_applicable_on_solarl2(expres):
    """L2 does NOT have an `observer` column; calling it would yield ORA-00904."""
    with pytest.raises(NotApplicable, match="observer"):
        expres.query_pi("solarl2", "anyone")


def test_query_criteria_blocks_position(expres):
    with pytest.raises(NotApplicable, match="position"):
        expres.query_criteria({"data_level": "solarl2", "position": ((10.0, 20.0), 0.1)})


def test_query_criteria_blocks_object(expres):
    with pytest.raises(NotApplicable, match="object"):
        expres.query_criteria({"data_level": "solarl2", "object": "Sun"})


def test_query_criteria_blocks_qobject(expres):
    with pytest.raises(NotApplicable, match="qobject"):
        expres.query_criteria({"data_level": "solarl2", "qobject": "anything"})


def test_query_criteria_blocks_pi_on_solarl2(expres):
    with pytest.raises(NotApplicable, match="observer"):
        expres.query_criteria({"data_level": "solarl2", "pi_name": "x"})


def test_query_criteria_allows_pi_on_solarl1(expres):
    """Still works for L1 since the column exists there."""
    expres.query_criteria({"data_level": "solarl1", "pi_name": "Solar . Telescope"})
    sql = _last_adql(expres)
    assert "observer =" in sql


def test_query_criteria_allows_datetime_and_program(expres):
    """Pure datetime + program criteria still go through."""
    expres.query_criteria(
        {
            "data_level": "solarl2",
            "datetime": ("2024-11-01", "2024-11-06"),
            "program": "EXPRESSOLAR",
        }
    )
    sql = _last_adql(expres)
    assert "expressolarl2" in sql
    assert "obsdate" in sql
    assert "program = 'EXPRESSOLAR'" in sql


# ---- download wiring -------------------------------------------------------


def test_download_url_includes_express_solar_flags():
    url = build_download_url("solarl2", "/p/expresL2_20241101.fits")
    assert "express" in url
    assert "solar" in url
    assert url.endswith("&json")


def test_filename_column_for_solarl1(expres):
    assert expres._filename_column("solarl1") == "l1filename"


def test_filename_column_for_solarl2(expres):
    assert expres._filename_column("solarl2") == "l2filename"


def test_filepath_column_uses_filehand(expres):
    """EXPRES uses 'l<n>filehand', not 'l<n>filepath', as the download handle."""
    assert expres._filepath_column("solarl1") == "l1filehand"
    assert expres._filepath_column("solarl2") == "l2filehand"


def test_infer_data_level_from_l2_filename(expres):
    table = Table({"l2filename": ["x"], "l2filehand": ["/p/x"]})
    assert expres._infer_data_level(table) == "solarl2"

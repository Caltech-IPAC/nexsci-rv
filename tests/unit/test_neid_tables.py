"""Invariants on the NEID table/column maps."""

from __future__ import annotations

from nexsci_rv.archives.neid.tables import DATALEVEL_TO_TABLE, TABLE_COLUMNS


def test_every_datalevel_maps_to_a_known_table():
    for level, table in DATALEVEL_TO_TABLE.items():
        assert table in TABLE_COLUMNS, f"level {level} maps to unknown table {table}"


def test_every_table_has_columns():
    for table, cols in TABLE_COLUMNS.items():
        assert cols, f"table {table} has no columns"
        assert "object" in cols, f"table {table} missing 'object'"
        assert "date_obs" in cols, f"table {table} missing 'date_obs'"


def test_l1_l2_have_filename_and_filepath():
    assert "l1filename" in TABLE_COLUMNS["neidl1"]
    assert "l1filepath" in TABLE_COLUMNS["neidl1"]
    assert "l2filename" in TABLE_COLUMNS["neidl2"]
    assert "l2filepath" in TABLE_COLUMNS["neidl2"]


def test_solarl2_has_rv_columns():
    cols = TABLE_COLUMNS["neidsolarl2"]
    assert "ccfrvmod" in cols
    assert "ccfrvsum" in cols
    assert "ccfjdsum" in cols


def test_no_duplicate_columns_per_table():
    for table, cols in TABLE_COLUMNS.items():
        assert len(set(cols)) == len(cols), f"{table} has duplicates: {cols}"

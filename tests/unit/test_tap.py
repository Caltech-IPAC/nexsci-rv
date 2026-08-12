"""TapClient — response parsing, format dispatch, error surfacing.

No network — TAP responses are injected via mock sessions.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests
from astropy.table import Table

from nexsci_rv.exceptions import AuthExpired, TapServerError
from nexsci_rv.tap import TapClient


def _mock_response(status_code: int = 200, body: str = "") -> MagicMock:
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.text = body
    r.raise_for_status.side_effect = (
        None if status_code < 400 else requests.HTTPError(f"HTTP {status_code}")
    )
    return r


def _make_client(body: str, status: int = 200) -> tuple[TapClient, MagicMock]:
    session = MagicMock(spec=requests.Session)
    session.post.return_value = _mock_response(status, body)
    return TapClient("https://example/TAP", session), session


IPAC_TABLE = """\
| col1 |  col2 |
|  int | double|
     1    3.14
     2    2.71
"""


def test_ipac_response_parsed_to_table():
    client, _session = _make_client(IPAC_TABLE)
    table = client.query("SELECT * FROM neidl2", output_format="ipac")
    assert isinstance(table, Table)
    assert len(table) == 2
    assert list(table.colnames) == ["col1", "col2"]


def test_csv_response_parsed_to_table():
    body = "a,b\n1,2\n3,4\n"
    client, _ = _make_client(body)
    table = client.query("SELECT * FROM neidl2", output_format="csv")
    assert len(table) == 2
    assert list(table.colnames) == ["a", "b"]


def test_votable_query_status_error_raises_tap_server_error():
    body = """\
<?xml version="1.0"?>
<VOTABLE>
  <RESOURCE>
    <INFO name="QUERY_STATUS" value="ERROR">ORA-00942: table or view does not exist</INFO>
  </RESOURCE>
</VOTABLE>
"""
    client, _ = _make_client(body)
    with pytest.raises(TapServerError, match="ORA-00942"):
        client.query("SELECT * FROM does_not_exist", output_format="votable")


def test_ipac_format_but_xml_error_response_raises_tap_server_error():
    """If the server returns a VOTable error even though format=ipac was requested."""
    body = """<?xml version="1.0"?>
<VOTABLE><RESOURCE><INFO name="QUERY_STATUS" value="ERROR">some-error</INFO></RESOURCE></VOTABLE>
"""
    client, _ = _make_client(body)
    with pytest.raises(TapServerError, match="some-error"):
        client.query("SELECT * FROM neidl2", output_format="ipac")


def test_auth_expired_on_401():
    client, _ = _make_client("", status=401)
    with pytest.raises(AuthExpired):
        client.query("SELECT * FROM neidl2")


def test_auth_expired_on_403():
    client, _ = _make_client("", status=403)
    with pytest.raises(AuthExpired):
        client.query("SELECT * FROM neidl2")


def test_unknown_format_rejected():
    client, _ = _make_client("")
    with pytest.raises(ValueError):
        client.query("SELECT * FROM neidl2", output_format="weird")  # type: ignore[arg-type]


def test_maxrec_passed_in_form_data():
    client, session = _make_client(IPAC_TABLE)
    client.query("SELECT * FROM neidl2", maxrec=100)
    sent_form = session.post.call_args.kwargs["data"]
    assert sent_form["maxrec"] == "100"


def test_query_uses_sync_endpoint():
    client, session = _make_client(IPAC_TABLE)
    client.query("SELECT * FROM neidl2")
    sent_url = session.post.call_args.args[0]
    assert sent_url.endswith("/sync")

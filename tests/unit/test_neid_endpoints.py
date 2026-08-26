"""NEID download URL composition."""

from __future__ import annotations

from nexsci_rv.archives.neid.endpoints import build_download_url


def test_l1_url_no_flags():
    url = build_download_url("l1", "/some/path/file.fits")
    assert url == ("https://neid.ipac.caltech.edu/get_file.php?filehand=/some/path/file.fits&json")


def test_eng_url_has_eng_flag():
    url = build_download_url("eng", "/some/path/eng.fits")
    assert "&eng" in url
    assert "&solar" not in url


def test_solarl1_url_has_solar_flag():
    url = build_download_url("solarl1", "/p/sun.fits")
    assert "&solar" in url
    assert "&eng" not in url


def test_solareng_url_has_both_flags():
    url = build_download_url("solareng", "/p/eng.fits")
    assert "&eng" in url
    assert "&solar" in url


def test_server_override_changes_host():
    url = build_download_url("l1", "/p/f.fits", server="https://proxy.example.org/")
    assert url == "https://proxy.example.org/get_file.php?filehand=/p/f.fits&json"


def test_json_suffix_is_last():
    """The legacy contract ends with '&json'."""
    url = build_download_url("l2", "/p/x.fits")
    assert url.endswith("&json")

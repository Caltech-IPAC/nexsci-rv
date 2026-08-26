"""NEID URL templates and per-data-level download wiring."""

from __future__ import annotations

DEFAULT_SERVER = "https://neid.ipac.caltech.edu/"

LOGIN_PATH = "cgi-bin/NeidAPI/nph-neidLogin.py"

# Download endpoint lives on the public web tree, not under the
# /cgi-bin/NeidAPI/ TAP root.
_DOWNLOAD_PATH = "get_file.php"
DOWNLOAD_BASE_URL = f"{DEFAULT_SERVER}{_DOWNLOAD_PATH}"

# Maps a data-level string to the URL-flag suffix the get_file.php endpoint expects.
_ENG_LEVELS: frozenset[str] = frozenset({"eng", "solareng"})
_SOLAR_LEVELS: frozenset[str] = frozenset({"solarl0", "solarl1", "solarl2", "solareng"})


def build_download_url(data_level: str, filepath: str, *, server: str = DEFAULT_SERVER) -> str:
    """Return the full GET URL for a single NEID FITS file.

    ``filepath`` is the value of the ``l<n>filepath`` column from a NEID
    query result. ``server`` must be the same base the queries run against
    so a ``NEIDArchive(server=...)`` override applies to downloads too.
    """
    base = server.rstrip("/") + "/" + _DOWNLOAD_PATH
    url = f"{base}?filehand={filepath}"
    if data_level in _ENG_LEVELS:
        url += "&eng"
    if data_level in _SOLAR_LEVELS:
        url += "&solar"
    url += "&json"
    return url


__all__ = ["DEFAULT_SERVER", "DOWNLOAD_BASE_URL", "LOGIN_PATH", "build_download_url"]

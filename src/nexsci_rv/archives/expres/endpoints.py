"""EXPRES URL templates.

EXPRES shares the production NEID TAP service at neid.ipac.caltech.edu;
its solar tables live alongside NEID's native tables.
"""

from __future__ import annotations

DEFAULT_SERVER = "https://neid.ipac.caltech.edu/"

# EXPRES solar data is fully public; no login endpoint needed.
LOGIN_PATH: str | None = None

_DOWNLOAD_PATH = "get_file.php"
DOWNLOAD_BASE_URL = f"{DEFAULT_SERVER}{_DOWNLOAD_PATH}"


def build_download_url(data_level: str, filepath: str, *, server: str = DEFAULT_SERVER) -> str:
    """Return the GET URL for one EXPRES solar FITS file.

    ``filepath`` is the value of the ``l<n>filepath`` column from a query
    result (``l<n>filehand`` holds only the directory and is rejected). The
    ``&express&solar`` flags mirror the NEID convention for distinguishing
    solar/eng/express data through the same ``get_file.php`` endpoint.
    ``server`` must be the same base the queries run against so an
    ``EXPRESArchive(server=...)`` override applies to downloads too.
    """
    base = server.rstrip("/") + "/" + _DOWNLOAD_PATH
    return f"{base}?filehand={filepath}&express&solar&json"


__all__ = ["DEFAULT_SERVER", "DOWNLOAD_BASE_URL", "LOGIN_PATH", "build_download_url"]

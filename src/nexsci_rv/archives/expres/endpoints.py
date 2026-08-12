"""EXPRES URL templates.

EXPRES shares the production NEID TAP service at neid.ipac.caltech.edu;
its solar tables live alongside NEID's native tables.
"""

from __future__ import annotations

DEFAULT_SERVER = "https://neid.ipac.caltech.edu/"

# EXPRES solar data is fully public; no login endpoint needed.
LOGIN_PATH: str | None = None

DOWNLOAD_BASE_URL = "https://neid.ipac.caltech.edu/get_file.php"


def build_download_url(data_level: str, filepath: str) -> str:
    """Return the GET URL for one EXPRES solar FITS file.

    ``filepath`` is the value of the ``l<n>filehand`` (or ``l<n>filepath``)
    column from a query result. The ``&express&solar`` flags mirror the
    NEID convention for distinguishing solar/eng/express data through the
    same ``get_file.php`` endpoint.

    Note:
        This URL form has not been verified against the live server in v1
        (the public TAP query path is exercised end-to-end but download
        requires authentication for some EXPRES products). Adjust here if
        the integration tests reveal a different URL shape.
    """
    return f"{DOWNLOAD_BASE_URL}?filehand={filepath}&express&solar&json"


__all__ = ["DEFAULT_SERVER", "DOWNLOAD_BASE_URL", "LOGIN_PATH", "build_download_url"]

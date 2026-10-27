"""Exception hierarchy for nexsci-rv.

User code can catch :class:`NexsciRVError` to handle any error originating from
this package. The narrower subclasses let callers distinguish auth issues from
query problems from download failures.
"""

from __future__ import annotations


class NexsciRVError(Exception):
    """Root of the nexsci-rv exception hierarchy."""


class ConfigError(NexsciRVError):
    """Invalid or missing configuration (bad server URL, unwritable cookie path, etc.)."""


# ----- auth ------------------------------------------------------------------


class AuthError(NexsciRVError):
    """Base class for authentication-related errors."""


class LoginFailed(AuthError):
    """The login endpoint rejected the provided credentials."""


class AuthExpired(AuthError):
    """The server returned 401/403 with an existing cookie loaded.

    Users should call ``archive.login()`` again. We deliberately do not
    silently re-login so that credentials are not held in memory.
    """


class NotAuthenticated(AuthError):
    """An operation that requires login was attempted with no cookie present."""


# ----- query -----------------------------------------------------------------


class QueryError(NexsciRVError):
    """Base class for query-construction or query-execution errors."""


class UnknownDataLevel(QueryError):
    """The requested ``data_level`` is not one of the archive's known levels."""


class UnknownColumn(QueryError):
    """A requested column is not present in the target table's schema."""


class NotApplicable(QueryError):
    """The query method does not apply to this archive / data level.

    Example: ``EXPRESArchive.query_position`` — EXPRES solar rows have
    sentinel ``qrad``/``qdecd`` values (``-99.9``) so position search returns
    nothing meaningful.
    """


class TapServerError(QueryError):
    """The TAP server returned ``QUERY_STATUS=ERROR`` in a VOTable response."""


# ----- download --------------------------------------------------------------


class DownloadError(NexsciRVError):
    """One or more files in a parallel download failed.

    Attributes:
        failures: list of ``(filename, underlying_exception)`` tuples for the
            files that failed. Successfully downloaded files are still
            returned to the caller; this exception is raised at the end so
            partial progress is preserved.
    """

    def __init__(self, message: str, failures: list[tuple[str, Exception]]):
        super().__init__(message)
        self.failures = failures


class FileUnavailable(NexsciRVError):
    """The archive answered a file request with an error instead of the file.

    The NEID download endpoint reports problems (file not available, invalid
    file handle) as a JSON body with HTTP 200, so this is detected from the
    response content rather than the status code.
    """


# ----- async job -------------------------------------------------------------


class AsyncJobError(NexsciRVError):
    """An async TAP job ended in ``error`` or ``aborted`` phase."""


__all__ = [
    "AsyncJobError",
    "AuthError",
    "AuthExpired",
    "ConfigError",
    "DownloadError",
    "FileUnavailable",
    "LoginFailed",
    "NexsciRVError",
    "NotApplicable",
    "NotAuthenticated",
    "QueryError",
    "TapServerError",
    "UnknownColumn",
    "UnknownDataLevel",
]

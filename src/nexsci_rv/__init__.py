"""nexsci-rv — Python client for radial-velocity archives at NExScI."""

from importlib.metadata import PackageNotFoundError, version

from . import exceptions
from .archives.expres import EXPRESArchive
from .archives.neid import NEIDArchive
from .async_job import AsyncJob
from .base import BaseArchive
from .config import Conf, conf
from .exceptions import (
    AsyncJobError,
    AuthError,
    AuthExpired,
    ConfigError,
    DownloadError,
    LoginFailed,
    NexsciRVError,
    NotApplicable,
    NotAuthenticated,
    QueryError,
    TapServerError,
    UnknownColumn,
    UnknownDataLevel,
)

try:
    __version__ = version("nexsci-rv")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = [
    "AsyncJob",
    "AsyncJobError",
    "AuthError",
    "AuthExpired",
    "BaseArchive",
    "Conf",
    "ConfigError",
    "DownloadError",
    "EXPRESArchive",
    "LoginFailed",
    "NEIDArchive",
    "NexsciRVError",
    "NotApplicable",
    "NotAuthenticated",
    "QueryError",
    "TapServerError",
    "UnknownColumn",
    "UnknownDataLevel",
    "__version__",
    "conf",
    "exceptions",
]

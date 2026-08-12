"""Process-wide defaults for nexsci-rv.

Most users never touch this module — per-archive overrides via constructor
arguments are the common path. The defaults here exist so that:

- a sensible cookie root directory exists (``platformdirs``-driven)
- HTTP timeouts and retry counts have explicit values
- environment-variable overrides have a single resolution point
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import platformdirs

_APP_NAME = "nexsci-rv"

_DEFAULT_TIMEOUT_SECONDS = 60.0
_DEFAULT_DOWNLOAD_WORKERS = 4
_DEFAULT_DOWNLOAD_RETRIES = 3


def _default_cookie_root() -> Path:
    return Path(platformdirs.user_config_path(_APP_NAME))


@dataclass(frozen=True)
class Conf:
    """Immutable configuration record.

    Construct a new ``Conf`` (rather than mutating) when overrides are needed,
    e.g. ``Conf(timeout=120, cookie_root=Path('/tmp/cookies'))``.
    """

    timeout: float = _DEFAULT_TIMEOUT_SECONDS
    download_workers: int = _DEFAULT_DOWNLOAD_WORKERS
    download_retries: int = _DEFAULT_DOWNLOAD_RETRIES
    cookie_root: Path = field(default_factory=_default_cookie_root)

    @classmethod
    def from_env(cls) -> Conf:
        """Build a Conf populated from ``NEXSCI_RV_*`` environment variables.

        Unset variables fall back to the dataclass defaults.
        """
        kwargs: dict[str, object] = {}

        if (raw := os.environ.get("NEXSCI_RV_TIMEOUT")) is not None:
            kwargs["timeout"] = float(raw)
        if (raw := os.environ.get("NEXSCI_RV_DOWNLOAD_WORKERS")) is not None:
            kwargs["download_workers"] = int(raw)
        if (raw := os.environ.get("NEXSCI_RV_DOWNLOAD_RETRIES")) is not None:
            kwargs["download_retries"] = int(raw)
        if (raw := os.environ.get("NEXSCI_RV_COOKIE_ROOT")) is not None:
            kwargs["cookie_root"] = Path(raw).expanduser()

        return cls(**kwargs)  # type: ignore[arg-type]


conf = Conf.from_env()
"""The default :class:`Conf` instance, populated from environment variables.

Library code that needs a default should import ``conf`` from this module
rather than constructing its own.
"""


__all__ = ["Conf", "conf"]

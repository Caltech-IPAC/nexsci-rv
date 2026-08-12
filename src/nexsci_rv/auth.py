"""Cookie-based session management.

One :class:`SessionManager` per archive instance. Owns:

- a ``requests.Session`` with attached cookies
- the on-disk cookie file (created with mode ``0o600``)
- the credential-resolution order: explicit args → env vars → ``getpass`` prompt

The class does **not** know about query endpoints — those belong to each
archive backend. It only handles login and cookie persistence.
"""

from __future__ import annotations

import contextlib
import getpass
import http.cookiejar
import logging
import os
import sys
from pathlib import Path

import requests

from .config import Conf
from .config import conf as default_conf
from .exceptions import ConfigError, LoginFailed, NotAuthenticated

logger = logging.getLogger("nexsci_rv.auth")


class SessionManager:
    """Owns the HTTP session and cookie for one archive.

    Args:
        archive_name: Short identifier used to namespace the on-disk cookie
            and the env-var names (e.g. ``"neid"`` →
            ``~/.config/nexsci-rv/neid/cookie`` and
            ``NEXSCI_RV_NEID_USER`` / ``NEXSCI_RV_NEID_PASSWORD``).
        cookie_path: Override for the default cookie file location.
        conf: Process configuration to use. Defaults to the module-level
            :data:`nexsci_rv.config.conf` populated from env vars.
    """

    def __init__(
        self,
        archive_name: str,
        *,
        cookie_path: Path | None = None,
        conf: Conf | None = None,
    ):
        if not archive_name or not archive_name.replace("_", "").isalnum():
            # Guard against archive_name being used in a filesystem path with
            # traversal characters.
            raise ConfigError(f"Invalid archive_name for cookie path: {archive_name!r}")

        self.archive_name = archive_name
        self._conf = conf if conf is not None else default_conf
        self.cookie_path = (
            cookie_path
            if cookie_path is not None
            else self._conf.cookie_root / archive_name / "cookie"
        )

        self._session = requests.Session()
        self._jar = http.cookiejar.MozillaCookieJar(str(self.cookie_path))
        self._session.cookies = self._jar  # type: ignore[assignment]
        self._load_cookie_if_exists()

    @property
    def session(self) -> requests.Session:
        """The configured :class:`requests.Session` for transport code to use."""
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """True if a non-expired cookie is loaded.

        Note: this only inspects what's *on disk* / in the cookie jar. The
        server can still reject a stale-looking-but-actually-valid cookie at
        query time; that case raises :class:`AuthExpired`.
        """
        return any(c.value for c in self._jar)

    def login(
        self,
        login_url: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Acquire and persist a session cookie.

        Credential resolution order:

        1. Explicit ``username`` / ``password`` arguments.
        2. ``NEXSCI_RV_<ARCHIVE>_USER`` / ``NEXSCI_RV_<ARCHIVE>_PASSWORD`` env vars.
        3. Interactive ``getpass`` prompts to stderr (suppressed when
           ``NEXSCI_RV_NO_PROMPT=1`` is set).

        On success the cookie is written to :attr:`cookie_path` with mode ``0o600``.
        """
        username, password = self._resolve_credentials(username, password)

        # POST body — never URL — so credentials don't end up in access logs
        # of intermediate proxies, server access logs, or shell history.
        form = {"userid": username, "password": password}

        logger.info("POST %s (login)", login_url)
        try:
            response = self._session.post(login_url, data=form, timeout=self._conf.timeout)
        except requests.RequestException as exc:
            raise LoginFailed(f"login request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise LoginFailed(
                f"login endpoint returned non-JSON (status {response.status_code})"
            ) from exc

        status = payload.get("status", "")
        msg = payload.get("msg", "")
        if status != "ok":
            raise LoginFailed(f"login rejected: {msg}")

        self._persist_cookie()

    def logout(self) -> None:
        """Drop in-memory cookies and delete the on-disk cookie file."""
        self._session.cookies.clear()
        with contextlib.suppress(FileNotFoundError):
            self.cookie_path.unlink()

    # ------------------------------------------------------------------------
    # internals

    def _resolve_credentials(self, username: str | None, password: str | None) -> tuple[str, str]:
        env_user = os.environ.get(f"NEXSCI_RV_{self.archive_name.upper()}_USER")
        env_password = os.environ.get(f"NEXSCI_RV_{self.archive_name.upper()}_PASSWORD")

        if username is None:
            username = env_user
        if password is None:
            password = env_password

        if username is None or password is None:
            if os.environ.get("NEXSCI_RV_NO_PROMPT") == "1":
                raise NotAuthenticated(
                    "Credentials not supplied via args or env vars, and "
                    "NEXSCI_RV_NO_PROMPT=1 disables interactive prompting."
                )
            username = username or _prompt(f"{self.archive_name} username: ")
            password = password or _prompt_password(f"{self.archive_name} password: ")

        if not username or not password:
            raise NotAuthenticated("Empty username or password supplied.")

        return username, password

    def _load_cookie_if_exists(self) -> None:
        if self.cookie_path.exists():
            try:
                self._jar.load(ignore_discard=True, ignore_expires=True)
            except (http.cookiejar.LoadError, OSError) as exc:
                logger.warning("failed to load cookie at %s: %s", self.cookie_path, exc)

    def _persist_cookie(self) -> None:
        # Avoid a race where the cookie is briefly world-readable between the
        # naive save() (which respects the prevailing umask, often 0o644) and
        # a follow-up chmod. We tighten the parent directory to 0o700 first,
        # then save, then chmod the file — and on platforms where umask is a
        # concern, we also temporarily restrict it.
        parent = self.cookie_path.parent
        parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(parent, 0o700)
        except OSError as exc:
            logger.warning("failed to chmod cookie dir %s: %s", parent, exc)

        old_umask = os.umask(0o077)
        try:
            self._jar.save(ignore_discard=True, ignore_expires=True)
        finally:
            os.umask(old_umask)

        try:
            os.chmod(self.cookie_path, 0o600)
        except OSError as exc:
            logger.warning("failed to chmod cookie %s: %s", self.cookie_path, exc)


def _prompt(message: str) -> str:
    print(message, end="", file=sys.stderr, flush=True)
    return sys.stdin.readline().rstrip("\n")


def _prompt_password(message: str) -> str:
    return getpass.getpass(message, stream=sys.stderr)


__all__ = ["SessionManager"]

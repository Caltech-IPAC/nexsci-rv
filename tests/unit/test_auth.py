"""SessionManager — credential resolution, cookie persistence, file modes.

No network — login is exercised against a mocked requests session.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexsci_rv.auth import SessionManager
from nexsci_rv.config import Conf
from nexsci_rv.exceptions import ConfigError, LoginFailed, NotAuthenticated


@pytest.fixture
def sm(tmp_cookie_root: Path) -> SessionManager:
    return SessionManager("neid", conf=Conf(cookie_root=tmp_cookie_root))


def _ok_login_response() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"status": "ok", "msg": "welcome", "token": "tok"}
    return resp


def _rejected_login_response() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"status": "error", "msg": "bad password"}
    return resp


def test_archive_name_validation():
    with pytest.raises(ConfigError):
        SessionManager("../etc")
    with pytest.raises(ConfigError):
        SessionManager("")


def test_cookie_path_defaults_to_conf_root(tmp_cookie_root):
    sm = SessionManager("neid", conf=Conf(cookie_root=tmp_cookie_root))
    assert sm.cookie_path == tmp_cookie_root / "neid" / "cookie"


def test_login_with_explicit_credentials_persists_cookie(sm: SessionManager):
    with patch.object(sm._session, "post", return_value=_ok_login_response()) as p:
        sm.login("https://example/login.py", username="u", password="p")

    # Cookie file was created (even if empty — MozillaCookieJar.save writes headers)
    assert sm.cookie_path.exists()
    # And 0600
    mode = stat.S_IMODE(os.stat(sm.cookie_path).st_mode)
    assert mode == 0o600

    # Credentials live in the POST body, NOT the URL. URLs end up in access
    # logs of intermediate proxies; bodies generally do not.
    sent_url = p.call_args.args[0]
    assert "userid=" not in sent_url
    assert "password=" not in sent_url
    sent_form = p.call_args.kwargs["data"]
    assert sent_form == {"userid": "u", "password": "p"}


def test_login_rejected_raises_login_failed(sm: SessionManager):
    with (
        patch.object(sm._session, "post", return_value=_rejected_login_response()),
        pytest.raises(LoginFailed),
    ):
        sm.login("https://example/login.py", username="u", password="p")


def test_login_non_json_response_raises(sm: SessionManager):
    resp = MagicMock()
    resp.status_code = 500
    resp.json.side_effect = ValueError("no JSON")
    with patch.object(sm._session, "post", return_value=resp), pytest.raises(LoginFailed):
        sm.login("https://example/login.py", username="u", password="p")


def test_credentials_from_env(sm: SessionManager, monkeypatch):
    monkeypatch.setenv("NEXSCI_RV_NEID_USER", "envuser")
    monkeypatch.setenv("NEXSCI_RV_NEID_PASSWORD", "envpass")
    with patch.object(sm._session, "post", return_value=_ok_login_response()) as p:
        sm.login("https://example/login.py")
    sent_form = p.call_args.kwargs["data"]
    assert sent_form["userid"] == "envuser"
    assert sent_form["password"] == "envpass"


def test_no_prompt_env_blocks_interactive(sm: SessionManager, monkeypatch):
    monkeypatch.setenv("NEXSCI_RV_NO_PROMPT", "1")
    monkeypatch.delenv("NEXSCI_RV_NEID_USER", raising=False)
    monkeypatch.delenv("NEXSCI_RV_NEID_PASSWORD", raising=False)
    with pytest.raises(NotAuthenticated):
        sm.login("https://example/login.py")


def test_logout_clears_cookie(sm: SessionManager):
    with patch.object(sm._session, "post", return_value=_ok_login_response()):
        sm.login("https://example/login.py", username="u", password="p")
    assert sm.cookie_path.exists()
    sm.logout()
    assert not sm.cookie_path.exists()


def test_logout_when_no_cookie_is_noop(sm: SessionManager):
    # Should not raise even if the cookie file was never created.
    sm.logout()


def test_password_not_in_log_records(sm: SessionManager, caplog):
    """Cookie/credential redaction: nexsci_rv.auth must not log the password."""
    secret = "hunter2_dont_log_me"
    with (
        patch.object(sm._session, "post", return_value=_ok_login_response()),
        caplog.at_level("DEBUG", logger="nexsci_rv.auth"),
    ):
        sm.login("https://example/login.py", username="u", password=secret)
    full_log = "\n".join(r.getMessage() for r in caplog.records)
    assert secret not in full_log

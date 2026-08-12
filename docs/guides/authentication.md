# Authentication & your credentials

Most of what you do with `nexsci-rv` needs no login at all. NEID public data
and **all** EXPRES solar data are queryable and downloadable anonymously. You
only need to authenticate to reach NEID observations still inside their
{term}`proprietary period` — the protected window (often about a year) during
which only the observing team can see their data. This page explains where your
credentials come from, what the session cookie is, and how to keep your own
scripts and notebooks tidy.

For the bigger picture of public versus proprietary data, see
{doc}`../concepts/downloading-and-proprietary`.

## Logging in to NEID

```python
from nexsci_rv import NEIDArchive

neid = NEIDArchive()
neid.login()                              # prompts for username + password
neid.login(username="me", password="…")   # explicit
```

`login()` exchanges your IPAC NEID username and password for a session cookie.
After that, both queries and downloads of proprietary data work for as long as
the cookie is valid.

## Where credentials come from

When you call `neid.login()`, the client looks for your username and password in
three places, in order, and stops at the first that supplies them:

1. **Explicit arguments** — `neid.login(username="me", password="…")`.
2. **Environment variables** — `NEXSCI_RV_NEID_USER` and
   `NEXSCI_RV_NEID_PASSWORD`:

   ```bash
   export NEXSCI_RV_NEID_USER=me
   export NEXSCI_RV_NEID_PASSWORD=…
   ```

3. **An interactive prompt** — if neither of the above supplies a value, the
   client prompts you on the terminal. The password prompt uses
   {py:func}`getpass.getpass`, so your typing is not echoed.

The password is only ever held in memory for the duration of the login request.
**It is never written to disk** by the library, and the client deliberately does
not keep it around to retry transparently after a session expires.

```{note}
If you run in an environment with no terminal (a batch job, some notebook
kernels), set `NEXSCI_RV_NO_PROMPT=1` to turn the interactive prompt into a
clear {py:exc}`~nexsci_rv.exceptions.NotAuthenticated` error instead of hanging
on a prompt nobody can answer. Supply credentials via the env vars in that case.
```

## The session cookie

A successful login writes a single session cookie to:

```text
~/.config/nexsci-rv/neid/cookie
```

(The root is `~/.config/nexsci-rv/` by default — strictly, your platform's
user-config directory — with a per-archive subdirectory. You can relocate it
with the `NEXSCI_RV_COOKIE_ROOT` environment variable.)

The cookie is written with `0o600` permissions (readable only by you) and is
**reused across runs**: log in once, and later Python sessions pick the cookie
back up automatically — no second login needed until it expires.

### Logging out

To "log out", delete the cookie. The tidy way is:

```python
neid.logout()   # clears the in-memory session and deletes the cookie file
```

which is equivalent to removing `~/.config/nexsci-rv/neid/cookie` by hand.

### When the session expires

If a query or download of proprietary data later fails with
{py:exc}`~nexsci_rv.exceptions.AuthExpired` (the server returned a 401 or 403),
your cookie has expired. The client will not silently reuse your password to
re-authenticate; just call `neid.login()` again.

## EXPRES needs no login

EXPRES solar data is fully public, so the EXPRES archive has no authentication
at all. Calling `login()` on it is a programming mistake rather than a no-op:

```python
from nexsci_rv import EXPRESArchive

expres = EXPRESArchive()
expres.login()   # raises NotApplicable
```

This raises {py:exc}`~nexsci_rv.exceptions.NotApplicable` to make clear that
there is nothing to log in to.

## Transport security

All archive connections use verified HTTPS. The client never disables TLS
certificate verification, so credentials and cookies travel encrypted and the
server's identity is checked on every request. Login credentials are sent in the
request **body**, not the URL, so they do not leak into proxy or server access
logs.

## Credential hygiene for your own code

A few habits keep your credentials safe in the scripts and notebooks you write
around this library:

- **Don't hard-code your password** in a script or a notebook cell. Anything you
  commit to version control or share is a leak.
- **Prefer the environment variables or the interactive prompt.** Both keep the
  password out of your source files. For unattended jobs, set
  `NEXSCI_RV_NEID_USER` / `NEXSCI_RV_NEID_PASSWORD` from your shell or a secrets
  manager rather than literals in the code.
- **Don't commit the cookie.** The cookie file is a live credential. It lives
  under `~/.config/`, away from your project, precisely so it does not land in a
  repo — keep it that way, and add it to `.gitignore` if you ever relocate it
  with `NEXSCI_RV_COOKIE_ROOT`.
- **Clear notebook output** before sharing if you ever echo environment
  variables or login details while debugging.

## Reporting a security issue

If you find a security problem in `nexsci-rv` itself — a credential leak, an
unsafe download path, anything that could expose another user's data — please
report it rather than filing it as an ordinary public bug. Use GitHub's private
vulnerability reporting on the
[Caltech-IPAC/nexsci-rv](https://github.com/Caltech-IPAC/nexsci-rv/security/advisories)
repository, or contact the maintainers directly. For non-sensitive bugs and
feature requests, the public
[issue tracker](https://github.com/Caltech-IPAC/nexsci-rv/issues) is the right place.

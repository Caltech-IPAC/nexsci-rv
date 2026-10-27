# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation: a "Migrating from pyNEID" guide mapping every pyNEID call to
  its `nexsci-rv` equivalent.

### Changed
- Documentation: the concepts pages and glossary are now archive-neutral, with
  instrument-specific details on each archive's page and per-archive glossary
  sections.

## [1.0.1] — 2026-10-27

### Fixed
- Queries no longer fail out of the box when the NEID TAP server cannot
  render a result in IPAC table format: the default `output_format` for all
  query methods and `describe_table` is now `"votable"` (previously `"ipac"`).
  Results are still returned as an `astropy.table.Table`; pass
  `output_format="ipac"` to get the old behavior.
- Unsuccessful HTTP responses from the TAP service (sync queries and async
  job submit, poll, result fetch, and abort) now raise `TapServerError`
  carrying the server's error message, instead of a bare
  `requests.HTTPError` with only the status code.
- `download()` on an L1 or L2 query result fetched the **L0** files instead,
  because NEID rows list the L0, L1, and L2 files and the first match won.
  Results from the `query_*` methods now record their data level
  (`Table.meta["nexsci_rv_data_level"]`) and `download()` uses it. When the
  level cannot be determined unambiguously, `download()` raises `QueryError`
  asking for `data_level=` instead of guessing.
- NEID solar and engineering downloads looked for nonexistent columns
  (`solarl2filename`, `engfilename`, ...); they now use the `l0`/`l1`/`l2`
  file columns those tables actually carry. Those columns can also now be
  requested with `columns=`.
- `NEIDArchive.query_position`, `query_object`, and the `position`/`object`
  keys of `query_criteria` searched on `ra`/`dec`, which NEID tables do not
  have; they now search on `qrad`/`qdecd`.
- EXPRES downloads sent the `l<n>filehand` column (a directory only), which
  the server rejects; they now send the full `l<n>filepath`.
- When the archive answers a file request with an error (it returns HTTP 200
  with a JSON body for unavailable files), `download()` no longer saves that
  JSON under the `.fits` name and reports success; the file is recorded as a
  failure (new `FileUnavailable` exception, collected in
  `DownloadError.failures`).

## [1.0.0] — 2026-10-27

First public release.

### Added
- `NEIDArchive` backend covering NEID L0/L1/L2, engineering, and solar tables.
- `EXPRESArchive` backend covering EXPRES solar L1 and L2.
- Shared core: TAP client, cookie-based `SessionManager`, parallel `download()` with
  retry and resume, `AsyncJob` for async TAP queries.
- Sphinx (MyST) documentation on GitHub Pages, written for astronomers new to
  RV archives: quickstart, a guided "first query" page, an "Understanding the
  data" concepts layer, glossary, per-archive pages, guides, and API reference.
- Three tutorial notebooks under `docs/tutorials/`, exercised in CI via
  `nbmake` in an offline stub mode (`NEXSCI_RV_OFFLINE_FIXTURES=1`).
- Support section pointing to `neid-help@ipac.caltech.edu` and GitHub Issues.

### Fixed
- `NEIDArchive.query_datetime` filtered on a nonexistent `date_obs` column
  (server error `ORA-00904`); NEID tables use `obsdate`, as EXPRES does.
- `download()` ignored the `server=` override and always fetched from the
  production host; downloads now go to the same server as queries and login,
  for both NEID and EXPRES.

### Security
- Pre-release audit with remediations applied: EXPRES query gaps raise
  `NotApplicable`, cookie-file race fix, defusedxml documentation,
  pip-audit clean. User-facing credential guidance lives in the
  Authentication guide.

### Relationship to pyNEID
`nexsci-rv` is a clean-room successor to the
[pyNEID](https://github.com/Caltech-IPAC/pyNEID) package. It is **not** API
compatible. Motivations for the rewrite:

- Multi-archive support (NEID + EXPRES, with extensibility for more) rather
  than NEID-only.
- New PyPI project (the original `pyneid` PyPI account is no longer accessible).
- Cleaner internal architecture: archive-backends + shared core, replacing a
  3,900-line monolithic `core.py`.
- Modern packaging (`pyproject.toml`, ruff, mypy, GitHub Actions, Trusted Publishing).
- Polished auth (per-archive cookies in `~/.config/nexsci-rv/`, env-var
  credentials, `getpass` prompts, 0600 file mode).
- Default server is the NEID production server.

Existing pyNEID users should migrate by rewriting imports and call sites. There
is no compatibility shim.

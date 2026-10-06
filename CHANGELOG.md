# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Documentation migrated from MkDocs Material to Sphinx (MyST) on GitHub Pages,
  and rewritten for astronomers new to RV archives: added a "Understanding the
  data" concepts layer and a glossary, reframed the landing, quickstart, archive,
  and API pages, rewrote the tutorials, and added a guided "first query" page.

### Removed
- The published `docs/security-audit.md` page. Its developer-process content is
  tracked internally; user-facing credential guidance now lives in the
  Authentication guide.

## [0.1.0] — 2026-05-21

### Added
- Initial scaffold for the `nexsci-rv` package.
- `NEIDArchive` backend covering NEID L0/L1/L2, engineering, and solar tables.
- `EXPRESArchive` backend covering EXPRES solar L1 and L2.
- Shared core: TAP client, cookie-based `SessionManager`, parallel `download()` with
  retry and resume, `AsyncJob` for async TAP queries.
- MkDocs documentation site (index, quickstart, per-archive pages, mkdocstrings
  API reference).
- Three example notebooks under `docs/tutorials/` exercised in CI via `nbmake`
  in an offline stub mode (`NEXSCI_RV_OFFLINE_FIXTURES=1`).
- Security audit with remediations applied: EXPRES query gaps raise
  `NotApplicable`, cookie-file race fix, defusedxml documentation,
  pip-audit clean.

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

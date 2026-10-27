# EXPRES

## What is the EXPRES solar feed?

{term}`EXPRES`, the EXtreme PREcision Spectrograph, is a high-precision
{term}`radial velocity (RV)` instrument on the Lowell Discovery Telescope. A
small auxiliary telescope feeds sunlight into it during the day so it can
observe the Sun as if it were a distant star (the {term}`solar feed`). The Sun
is a bright, well-understood "star", so this dense, high-cadence RV series is
ideal for studying the activity signals — granulation, oscillations, magnetic
activity — that limit precision RV planet searches everywhere else.

This client exposes only the EXPRES solar feed, which {term}`NExScI` hosts on
the same IPAC {term}`TAP` service as NEID, at the solar L1 and L2 levels. The
**L2 radial velocities are the main product**.

```python
from nexsci_rv import EXPRESArchive
expres = EXPRESArchive()
```

## Data levels

| `data_level` | Table             | Contents                                          |
|--------------|-------------------|---------------------------------------------------|
| `solarl1`    | `expressolarl1`   | Extracted, wavelength-calibrated solar spectra    |
| `solarl2`    | `expressolarl2`   | Solar RV products (`v`, `e_v`, `dvrms`, `extsnr`) |

**Which one do I want?** Most users want `solarl2` — the radial velocities the
pipeline already measured. Reach for `solarl1` only if you want the spectra
themselves to run your own line or activity analysis. See
{doc}`../concepts/data-levels` for the broader picture.

## The columns you'll actually use

L2 rows are produced by a {term}`CCF (cross-correlation function)` — the
spectrum is cross-correlated against a template of known lines to recover the
Doppler shift. The headline solar L2 columns:

| Column | Meaning |
| --- | --- |
| {term}`v / e_v (EXPRES)` (`v`) | The measured radial velocity, m/s. |
| {term}`v / e_v (EXPRES)` (`e_v`) | Formal uncertainty on `v`, m/s. |
| {term}`dvrms` | Photon-limited RV precision predicted for the exposure, m/s. |
| {term}`extsnr` | Extracted spectrum signal-to-noise; a natural quality cut. |
| {term}`obsdate` | UTC observation time stamp; what date queries filter on. |
| `mjd` | The same time as a {term}`Julian Date (JD / MJD)` (Modified JD), for time series. |
| {term}`filename / filepath / filehand` (`l2filename`, `l2filepath`) | The FITS file's name and server path; {term}`download` needs both. |

If you port a NEID workflow over, swap `ccfrvmod` → `v` and `ccfnoise` → `e_v`.
For a full, plain-language column tour see {doc}`../concepts/results-columns`.

### Time columns

Three time columns appear in the L2 table and it helps to know which is which:

- `obsdate` — the UTC calendar time stamp. This is the column
  {term}`query_datetime` filters on; you never type it yourself for date queries.
- `mjd` — Modified Julian Date (`JD − 2400000.5`), a compact numeric time good
  for plotting and fitting.
- `obsjd` — the full Julian Date for the same exposure.

## Querying solar data

For solar data you filter by **time** — and optionally by quality — not by sky
position or target name. There is no star to point at, so
{term}`query_datetime` is the right entry point. See
{doc}`../concepts/choosing-a-query` for the general guide.

```python
tbl = expres.query_datetime(
    "solarl2",
    ("2024-11-01", "2024-11-06"),
    columns=["l2filename", "obsdate", "v", "e_v", "dvrms", "extsnr"],
)
print(tbl)

# Combine a date window with a quality cut, in one query:
tbl = expres.query_criteria({
    "data_level": "solarl2",
    "datetime": ("2024-11-01", "2024-11-06"),
    "where": "extsnr > 200",
})

# Download the L2 FITS files for the rows you selected:
paths = expres.download(tbl, outdir="solar_l2/", workers=4)
```

`query_program` exists, but every solar exposure shares the single
{term}`program` string `'EXPRESSOLAR'` (the proposal/campaign identifier the
archive groups exposures under), so it is a sanity check rather than a filter.
`query_pi` works on `solarl1`, where it matches the recorded `observer` string —
though since the solar feed runs automatically there is no human PI per
observation, so it is rarely useful; `solarl2` has no `observer` column and so
raises {py:exc}`~nexsci_rv.exceptions.NotApplicable`.

### Why position and object searches don't apply

A solar observation points at the Sun, not at a catalog target, so the rows
carry no real sky coordinate (the
{term}`query coordinates (qra / qdec / qrad / qdecd)` are
{term}`sentinel value`s of `-99.9`). Any search that would match on a celestial
position therefore raises {py:exc}`~nexsci_rv.exceptions.NotApplicable`:

- `query_position(...)` — no sky coordinate to search.
- `query_object(...)` — no celestial target to resolve.
- `query_qobject(...)` — no real catalog ID.

The same applies inside `query_criteria`: passing `"position"`, `"object"`, or
`"qobject"` keys (or `"pi_name"` with `data_level="solarl2"`) raises the same
{py:exc}`~nexsci_rv.exceptions.NotApplicable`.

## Downloading

The query returns metadata; the data products are {term}`FITS` files you fetch
with {term}`download`, which retrieves the L1 or L2 files for the rows you pass
it and returns a list of {py:class}`pathlib.Path` objects. Keep the
filename column if you trim the result with `columns=`. See
{doc}`../tutorials/03_download_and_plot` for a full query-download-plot
walkthrough.

## Authentication

EXPRES solar data is fully **public** — no account, no login, and no cookie
written to disk (in contrast to proprietary NEID data). There is no login
endpoint, so `expres.login()` raises
{py:exc}`~nexsci_rv.exceptions.NotApplicable`.

## Useful columns

For the authoritative list, with units and descriptions, call
`expres.describe_table("expressolarl2")`. The common columns:

**`solarl2`**: `l2filename`, `l2filepath`, `l2filehand`, `obsdate`, `mjd`,
`obsjd`, `exptime`, `airmass`, `v`, `e_v`, `dvrms`, `extsnr`, `ccfrvmod`,
`ccfjdsum`, `swversion`, `l2procversion`.

**`solarl1`**: `l1filename`, `l1filepath`, `l1filehand`, `obsdate`, `mjd`,
`obsjd`, `exptime`, `airmass`, `extracttype`, `observer`, `obstype`,
`swversion`, `l1procversion`.

```{admonition} Production-only
:class: note

EXPRES tables exist **only on the production server**
(`https://neid.ipac.caltech.edu`). The test server returns `ORA-00942:
table or view does not exist`. `EXPRESArchive()` defaults to production, so
you do not normally need to think about this.
```

```{admonition} Table name spelling
:class: warning

The TAP table names use a single `s` between `expres` and `solar`:
`expressolarl1`, `expressolarl2`. Double-`s` spellings
(`expresssolarl1`) return `ORA-00942`. The typed methods always use the
correct spelling; only raw {term}`query_adql` callers need to.
```

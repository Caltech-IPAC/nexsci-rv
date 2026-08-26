# Quickstart

`nexsci-rv` searches two radial-velocity archives at NExScI: {term}`NEID` (a
spectrograph on the WIYN 3.5-m at Kitt Peak) and {term}`EXPRES` (here, its
{term}`solar feed`). Every search starts by picking a {term}`data level` — how
far the data has been processed, from raw frames up to science-ready velocities
(see {doc}`concepts/data-levels`) — and a query method that matches what you
already know about the data you want (see {doc}`concepts/choosing-a-query`).

This page walks the patterns most users reach for first. Every example assumes:

```python
from nexsci_rv import NEIDArchive, EXPRESArchive

neid = NEIDArchive()
expres = EXPRESArchive()
```

All query methods return an `astropy.table.Table`;
`download()` returns `list[pathlib.Path]`.

## Querying

### By date range

```python
tbl = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))
print(tbl)
```

`date_range` is inclusive `(start, end)`; either side can be `None` for an
open-ended interval. Dates accept anything `astropy.time.Time` can parse —
ISO strings, `datetime.datetime`, `Time` instances themselves.

### By sky position

```python
from astropy.coordinates import SkyCoord
from astropy import units as u

tbl = neid.query_position("l2", SkyCoord("12h00m00s", "+00d00m00s"), 0.5 * u.deg)
```

`coord` accepts a {py:class}`astropy.coordinates.SkyCoord` or an
`(ra_deg, dec_deg)` tuple; `radius` accepts an `Angle`/quantity or a bare float
(degrees).

### By object name

```python
tbl = neid.query_object("l2", "HD 189733", radius=30 * u.arcsec)
```

`query_object` resolves the name via Simbad/NED and then runs a position
search. For exact-match on a column (no resolution), use `query_qobject`.

### By PI or program

```python
tbl = neid.query_pi("l2", "Smith")
tbl = neid.query_program("l2", "2024A-001")
```

### Combined criteria (one round-trip)

```python
tbl = neid.query_criteria({
    "data_level": "l2",
    "datetime": ("2024-11-01", "2024-11-06"),
    "object": "HD 189733",
    "object_radius": 1 * u.arcmin,
})
```

`query_criteria` composes constraints into a single ADQL query so the server
only does one search. Accepted keys (besides `data_level`):
`datetime`, `position`, `object`, `qobject`, `program`, `pi_name`, `where`.

### Raw ADQL escape hatch

```python
tbl = neid.query_adql(
    "SELECT TOP 100 l2filename, obsdate FROM neidl2 "
    "WHERE obsdate > to_date('2024-11-01 00:00:00', 'YYYY-MM-DD HH24:MI:SS')"
)
```

`query_adql` is the unmediated path — caller owns the query string. Most users
should hit `query_criteria` first.

## Column selection and limits

Every query method takes `columns=` and `maxrec=`:

```python
tbl = neid.query_datetime(
    "l2",
    ("2024-11-01", "2024-11-06"),
    columns=["l2filename", "obsdate", "object", "exptime"],
    maxrec=500,
)
```

Those columns are: `l2filename` the FITS file's name (keep it if you plan to
{term}`download`), {term}`obsdate` the observation time stamp,
{term}`object` the free-text target name, and {term}`exptime` the exposure time
in seconds. For a tour of the columns you'll meet most — RV values, quality
metrics, download keys — see {doc}`concepts/results-columns`.

Unknown columns raise {py:exc}`~nexsci_rv.exceptions.UnknownColumn`. List the
columns a table exposes with `neid.describe_table("neidl2")`.

## Output formats

```python
votable = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"), output_format="votable")
```

Choices are `"ipac"` (default, fast), `"csv"`, and `"votable"`. They differ only
in how the data is sent over the wire; all three parse into the same
`astropy.table.Table`.

## Authentication (NEID only)

NEID public data is queryable without authentication; data still inside its
{term}`proprietary period` requires {term}`login`.

```python
neid.login()                              # prompts for username + password
neid.login(username="me", password="…")   # explicit
# Or set:
#   export NEXSCI_RV_NEID_USER=me
#   export NEXSCI_RV_NEID_PASSWORD=…
```

The session is cached, so you log in once and later runs reuse it.

`expres.login()` raises {py:exc}`~nexsci_rv.exceptions.NotApplicable`
— EXPRES solar data is fully public.

## Downloading FITS

```python
tbl = neid.query_datetime("l2", ("2024-11-01", "2024-11-02"), maxrec=10)
paths = neid.download(tbl, outdir="data/", workers=4, resume=True)
```

- `workers=4` by default (astronomy archives throttle aggressively).
- `resume=True` skips files already present at full size.
- `tqdm` progress bar; pass `progress=False` to suppress.
- If some files fail, {py:exc}`~nexsci_rv.exceptions.DownloadError` is raised
  after the rest finish; successes are still returned in the path list, and the
  exception carries `.failures: list[tuple[str, Exception]]`.

`download` locates each file using the filename/filepath columns of your table,
so keep those in any `columns=` selection. See
{doc}`concepts/downloading-and-proprietary`.

## Long-running queries (async TAP)

For queries that would time out under the sync `TAP/sync` endpoint, submit
asynchronously:

```python
job = neid.submit_async(
    "SELECT obsdate, exptime, object FROM neidl2 "
    "WHERE obsdate BETWEEN "
    "to_date('2023-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') AND "
    "to_date('2024-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS')"
)
job.wait(timeout=600)        # polls every 5s by default
tbl = job.result()
```

The job has `.phase`, `.error`, `.status_url`, `.result_url`, and a
{py:meth}`~nexsci_rv.async_job.AsyncJob.refresh` /
{py:meth}`~nexsci_rv.async_job.AsyncJob.abort` pair. See
{py:class}`~nexsci_rv.async_job.AsyncJob`.

## EXPRES solar specifics

```python
tbl = expres.query_datetime(
    "solarl2",
    ("2024-11-01", "2024-11-06"),
    columns=["l2filename", "obsdate", "v", "e_v", "dvrms", "extsnr"],
)
```

- `data_level` is `"solarl1"` or `"solarl2"`.
- The datetime column is `obsdate`, the same as NEID.
- The RV columns are {term}`v / e_v (EXPRES)` — `v` is the radial velocity and
  `e_v` its uncertainty (the EXPRES equivalents of NEID's `ccfrvmod`/`ccfnoise`).
- `query_position`, `query_object`, and `query_qobject` are not available for
  EXPRES solar data — those rows have no sky target (the Sun has no fixed
  celestial coordinate), so a position search has nothing to match. Calling them
  raises {py:exc}`~nexsci_rv.exceptions.NotApplicable`.
- `query_pi` works on `solarl1` (column `observer`) but not on `solarl2`
  (no observer column).

See [Archives → EXPRES](archives/expres.md) for the full quirk catalog.

## Configuration

Per-instance:

```python
neid = NEIDArchive(server="https://neid.ipac.caltech.edu", timeout=120)
```

To change several settings at once, build a
{py:class}`Conf <nexsci_rv.config.Conf>` and hand it to the archive. `Conf` is
immutable, so you construct one rather than mutating the defaults:

```python
from nexsci_rv import NEIDArchive, Conf

neid = NEIDArchive(conf=Conf(timeout=120, download_workers=8))
```

## Errors at a glance

Catch broadly with {py:exc}`~nexsci_rv.exceptions.NexsciRVError`, or
narrowly:

```python
from nexsci_rv import (
    AuthExpired, LoginFailed, NotApplicable, NotAuthenticated,
    TapServerError, UnknownColumn, UnknownDataLevel, DownloadError,
)
```

See [API → Exceptions](api/exceptions.md) for the full hierarchy.

## Logging

To see what's happening under the hood — the queries being sent and the
responses coming back — turn on logging for the `nexsci_rv` logger:

```python
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("nexsci_rv").setLevel(logging.DEBUG)
```

DEBUG-level entries include the ADQL query and a summary of the parsed response.

## Next steps

- [NEID archive details](archives/neid.md)
- [EXPRES archive details](archives/expres.md)
- [API reference](api/index.md)
- Example notebooks under [Tutorials](tutorials/01_neid_query_l2.ipynb)

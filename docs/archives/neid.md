# NEID

{term}`NEID` is a high-precision {term}`radial velocity (RV)` spectrograph on the
WIYN 3.5-m telescope at Kitt Peak — precise enough to detect the small wobble a
planet induces on its host star. Its archive at {term}`NExScI` carries the full
reduction hierarchy for stellar targets (raw frames through RV-ready products)
plus a parallel {term}`solar feed` that observes the Sun as a star during the
day. This page is your map to what NEID offers and how to query it.

```python
from nexsci_rv import NEIDArchive
neid = NEIDArchive()
```

## Which data level do I want?

A {term}`data level` is the first argument to every query. It picks how far the
data has been processed — and therefore which table you search. Frame it as one
question: **how processed do you need the data to be?**

| Want... | Use | Table |
| --- | --- | --- |
| A final RV time series (the common case) | {term}`L2` | `neidl2` |
| Reduced 1D spectra to re-analyze yourself | {term}`L1` | `neidl1` |
| Raw 2D detector frames to reduce from scratch | {term}`L0` | `neidl0` |
| Instrument / calibration diagnostics | {term}`eng (engineering level)` | `neideng` |

Each level also has a {term}`solar feed` twin for the Sun-as-a-star data:
`solarl0`, `solarl1`, `solarl2`, and `solareng` (tables `neidsolarl0` …
`neidsolareng`). The solar feed is a dense, high-cadence RV series used to study
solar activity and to validate the instrument's long-term stability.

You pass the **level string** (`'l2'`, `'solarl2'`, …), never the table name;
the package translates for you. Start with `'l2'` for stellar science and
`'solarl2'` for the solar feed — that is where the radial velocities live.
For the full picture see {doc}`../concepts/data-levels`.

## What L2 gives you: the CCF and the RV

L2 is where most users start, so it is worth knowing what comes back. The L2
pipeline runs a {term}`CCF (cross-correlation function)`: it cross-correlates
each spectrum against a template of known stellar lines to produce a single
average line profile whose center is the Doppler shift — the radial velocity.
You never compute this yourself; the archive stores the finished results.

The columns that hold the answer:

- {term}`ccfrvmod` — the model radial velocity (m/s). This is the primary RV
  number; it is what you plot against time.
- `ccfrvsum` — an alternate co-added-CCF RV, a cross-check on `ccfrvmod`.
- {term}`ccfnoise` — the photon-noise uncertainty on the RV (your per-point
  error bar).
- {term}`ccfjdsum` — the precise time stamp (a {term}`Julian Date (JD / MJD)`)
  for that RV, often the right x-axis for a time series.

For what these numbers mean physically, see
{doc}`../concepts/radial-velocities`; for a tour of every column you are likely
to use, see {doc}`../concepts/results-columns`.

## Querying NEID

Pick a query method by **what you already know** about the data you want. NEID
supports all of them; for the full decision guide see
{doc}`../concepts/choosing-a-query`.

```python
# A time window — the safest first query, always works
tbl = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))

# A sky region, when you have coordinates
from astropy.coordinates import SkyCoord
from astropy import units as u
tbl = neid.query_position("l2", SkyCoord("12h00m00s", "+00d00m00s"), 0.5 * u.deg)

# A star by name (resolved via Simbad / NED)
tbl = neid.query_object("l2", "HD 189733")

# An exact catalog ID (usually a Gaia DR2 source ID; no name resolution)
tbl = neid.query_qobject("l2", "Gaia DR2 4889286574103556352")

# An observing program or PI
tbl = neid.query_program("l2", "2024A-001")
tbl = neid.query_pi("l2", "Smith")

# Several constraints at once, in a single query — more precise results
tbl = neid.query_criteria({
    "data_level": "l2",
    "datetime": ("2024-11-01", "2024-11-06"),
    "object": "HD 189733",
    "object_radius": 1 * u.arcmin,
    "where": "exptime > 60",
})
```

### The `q*` search columns versus the per-observation columns

NEID rows carry two flavors of identity and coordinate columns, and knowing the
difference tells you what a search actually matches:

- {term}`object` describes **each observation** as recorded — the free-text
  target name the observer typed. It is whatever someone wrote, so it is
  unreliable for exact matching.
- {term}`qobject` / `qrad` / `qdecd` are the archive's **indexed search
  fields**: a normalized catalog ID (typically Gaia DR2) and clean RA/Dec in
  decimal degrees that the archive assigned. `qra` / `qdec` hold the same
  position as sexagesimal strings. Positional and object searches run against
  these.

So {term}`query_position` and {term}`query_object` cone-search on
`qrad`/`qdecd` (a name is resolved to coordinates first), and {term}`query_qobject` does an
exact match on `qobject`. If you want every observation of one target with no
name-resolution ambiguity, and you know its Gaia ID, `query_qobject` is the
precise choice.

## Understanding your results

Every query returns an {term}`astropy Table`. To see the full column list a
table offers — with units and descriptions — call
`neid.describe_table("neidl2")`. It reports the archive's declared columns; a
given query may not return every column listed.

For the common levels, the columns you will actually reach for:

**`l2` (RV products):** `l2filename`, `l2filepath`, `obsdate`, `object`,
`exptime`, `seeing`, `airmass`, `ccfrvmod`, `ccfrvsum`, `ccfnoise`,
`ccfjdsum`, `program`, `piname`.

**`l1` (extracted spectra):** `l1filename`, `l1filepath`, `obsdate`,
`object`, `exptime`, `seeing`, `airmass`, `swversion`.

**`l0` (raw frames):** `l0filename`, `l0filepath`, `obsdate`, `object`,
`exptime`, `obsmode`, `obstype`.

See {doc}`../concepts/results-columns` for a grouped, plain-language tour of
what each of these means.

## Downloading

The query returns metadata; the spectra themselves are {term}`FITS` files you
fetch with {term}`download`. It returns a list of {py:class}`pathlib.Path`
objects.

```python
tbl = neid.query_datetime("l2", ("2024-11-01", "2024-11-02"), maxrec=10)
paths = neid.download(tbl, outdir="data/", workers=4)
```

`download` reads the `l<n>filename` / `l<n>filepath` columns from the table, so
keep them if you trim the result with `columns=`. If the table has no obvious
filename column (for example, you ran a custom `query_adql`), pass
`data_level=` explicitly so `download` can build the right URL.

See {doc}`../tutorials/03_download_and_plot` for a full query-download-plot
walkthrough.

## Authentication (only for proprietary data)

Public NEID data is queryable and downloadable with **no login**. You only need
to authenticate to reach observations still inside their
{term}`proprietary period` — the protected window (often about a year) during
which only the observing team can access their files.

```python
neid.login()                                 # interactive getpass prompt
neid.login(username="myuser", password=...)  # explicit (avoid in checked-in code)
```

Credentials are resolved in this order:

1. Explicit `username` / `password` args.
2. Environment: `NEXSCI_RV_NEID_USER`, `NEXSCI_RV_NEID_PASSWORD`.
3. A `getpass` prompt on stderr.

Set `NEXSCI_RV_NO_PROMPT=1` to disable the interactive prompt (useful in CI). A
successful login stores a session cookie that later runs reuse, so you log in
once per machine, not once per script.

```{admonition} If your session expires
:class: tip

A query or download of proprietary data may fail because your session has
expired. The client never silently re-uses your password — just call
`neid.login()` again. (Under the hood this surfaces as
{py:exc}`~nexsci_rv.exceptions.AuthExpired`.)
```

## Choosing a server

`NEIDArchive()` with no arguments points at the production server
(`neid.ipac.caltech.edu`) — the real, complete data, and the right default. A
test instance exists but carries incomplete data, so leave the default unless
you have a specific reason.

```python
neid = NEIDArchive()                          # production (default)
neid = NEIDArchive(server="https://…/")       # override the server (rarely needed)
```

```{admonition} Use production for EXPRES tables
:class: warning

The test server does **not** carry EXPRES tables. If you touch EXPRES data — and
for most NEID work too — production (`neid.ipac.caltech.edu`) is the right
default, which is what `NEIDArchive()` resolves to with no args. See
{term}`production vs test server`.
```

## A couple of things worth knowing

You will rarely hit these, because the typed `query_*` methods handle them for
you. They matter only if you drop down to {term}`query_adql` and write
{term}`ADQL` by hand:

- **Dates:** pass plain strings (`"2024-11-01"`) or
  {py:class}`astropy.time.Time` objects to the query methods and the client
  formats them correctly for the server. In raw ADQL you must use the server's
  Oracle `to_date('YYYY-MM-DD HH24:MI:SS', ...)` form; a bare string comparison
  against a date column is rejected.
- **Table-name spelling:** the typed methods always pick the correct table name.
  In raw ADQL, use the exact spelling (`neidl2`, `expressolarl2`, …); a
  misspelling returns an `ORA-00942: table or view does not exist` error.

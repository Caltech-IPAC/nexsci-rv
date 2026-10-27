# Glossary

Plain-language definitions of the radial-velocity and archive terms you will
meet throughout these docs. Each entry says what the term means and why it
matters when you query an archive. The general sections apply to every archive
this package supports; terms specific to one archive are collected under that
archive at the end.

## Radial velocities and data products

```{glossary}
radial velocity (RV)
  The speed at which a star is moving toward or away from us along our line of
  sight, in m/s. A planet tugs its star in a small orbit, alternately
  blueshifting and redshifting the star's spectrum; the RV is what you extract
  from those shifts, and modern RV spectrographs aim for sub-m/s precision. RV
  is the headline measurement these archives deliver: the L2 products give you
  one RV value per observation, the quantity you would phase-fold and fit for a
  planet.

extracted spectrum
  A measurement of how much light a star emits at each wavelength, full of
  narrow dark absorption lines from atoms in the star's atmosphere. An
  "extracted" spectrum is the 1D flux-vs-wavelength curve pulled out of the raw
  2D detector image; RV is measured from how those absorption lines shift in
  wavelength over time. Defines what L1 data is: want the spectra themselves
  (for your own line analysis), choose L1; want the RV the pipeline already
  measured, choose L2.

CCF (cross-correlation function)
  The standard way an RV pipeline turns a spectrum into a velocity. The observed
  spectrum is cross-correlated against a binary "mask" or template of known
  stellar lines; the result is a single average line profile whose center tells
  you the Doppler shift, while its depth and width also diagnose the
  measurement. It is the engine behind the RV columns in the L2 tables (for
  example NEID's {term}`ccfrvmod`). You do not compute it yourself; the archive
  stores the results.

data level
  A label for how far a file has been processed through the reduction pipeline:
  {term}`L0` = raw detector frame, {term}`L1` = calibrated extracted 1D
  spectrum, {term}`L2` = science-ready RV products, and
  {term}`eng (engineering level)` = engineering frames for instrument health. It
  is the first argument to almost every query method (e.g.
  `query_datetime('l2', ...)`) and picks which underlying table you search, so
  choosing the wrong level means raw pixels when you wanted velocities, or vice
  versa. Each archive's page lists the levels it offers.

L0
  Raw 2D detector frames, exactly as read off the spectrograph CCD before any
  extraction. You want L0 only if you intend to run your own reduction; most
  users skip it.

L1
  Calibrated, wavelength-solved, 1D extracted spectra (flux vs wavelength per
  echelle order). This is the level for users who want the spectra themselves,
  e.g. for custom line analysis, activity indicators, or a non-standard RV
  pipeline.

L2
  RV-ready science products: the {term}`CCF (cross-correlation function)` and
  the derived radial velocity for each observation. This is what most science
  users want, since the RV columns live here, which is why the docs default to
  `'l2'`.

eng (engineering level)
  Instrument engineering and diagnostic frames (calibration lamps, detector
  tests, health monitoring). Rarely needed for science; listed so you recognize
  it and know to skip it unless you are debugging instrument behavior.

solar feed
  A small telescope that feeds sunlight into the spectrograph during the day,
  observing the Sun as if it were a star. Solar data has its own parallel set of
  data levels (`solarl0`, `solarl1`, `solarl2`, ...), and is a dense,
  high-cadence RV time series used to study stellar/solar activity and to
  validate the instrument's stability. Because the target is always the Sun,
  position and object queries do not apply to solar-only holdings.

dvrms
  The photon-limited RV precision (root-mean-square velocity error) predicted
  from the spectrum's information content, in m/s. It tells you the best
  precision achievable for that exposure given its signal, a quality /
  quick-look filter for RV points.

extsnr
  The extracted signal-to-noise ratio of the spectrum (how clean the data is);
  higher is better. A natural quality cut, e.g. `where='extsnr > 200'` to drop
  low-quality exposures.

pipeline version (swversion / procversion)
  The version of the reduction pipeline software that produced a given file
  (e.g. `swversion`, `l2procversion`). Pipeline versions change RV values
  slightly, so for reproducible science you may want to filter to a single
  processing version so all your points are consistent.

FITS
  Flexible Image Transport System: the standard astronomy file format that holds
  the actual spectra/frames (image data plus header metadata). The archive query
  returns a table of metadata; the FITS files are the data themselves.
  {term}`download` retrieves the FITS files, and you open them with
  {py:mod}`astropy.io.fits` or specfile tools.
```

## Observations and targets

```{glossary}
object
  The free-text target name the observer typed in (e.g. `'HD 189733'`, or
  `'Sun'` for solar). It is whatever the observer wrote, so spelling and format
  vary. It is what you get back in results and what {term}`query_object`
  ultimately filters near (after resolving a real name to coordinates); because
  it is free text it is unreliable for exact matching across programs.

qobject
  A "query object" identifier: a normalized catalog target ID assigned by the
  archive, typically a Gaia DR2 source ID. It is a clean, exact-match key,
  unlike the free-text {term}`object`. If you already know the Gaia ID,
  {term}`query_qobject` is the precise way to pull every observation of that
  target with no name-resolution ambiguity. Solar-only holdings have no real
  qobject.

query coordinates (qra / qdec / qrad / qdecd)
  The archive's "query" coordinates for a row (RA/Dec of the target): `qrad` /
  `qdecd` in decimal degrees, and `qra` / `qdec` as sexagesimal strings.
  Position-based searches use `qrad` / `qdecd`. Where a row has no real sky
  position (solar data), these hold {term}`sentinel value`s and position
  searches raise {term}`NotApplicable`.

sentinel value
  A placeholder number that means "no real value here", not an actual
  measurement — for example `-99.9` in the coordinate columns of a solar
  observation. If you did not know it is a sentinel, `-99.9` degrees would look
  like a (nonsensical) coordinate; the package guards against this by refusing
  position queries where coordinates are sentinels.

cone search
  A query that returns everything within a given angular radius of a sky point
  ("a cone on the sky"). {term}`query_position` does this directly;
  {term}`query_object` resolves a name to coordinates first, then cone-searches.
  It is how you find all observations of a region or a star whose coordinates
  you know. Does not apply to solar data (no sky position).

name resolution (Simbad / NED)
  Looking up a target's coordinates from its catalog name using online services
  (Simbad, NED). {term}`query_object` and the `object` criterion call astropy's
  {py:meth}`~astropy.coordinates.SkyCoord.from_name` under the hood, letting you
  say `'HD 189733'` instead of typing RA/Dec. If the name cannot be resolved, the
  query raises {term}`QueryError` before contacting the archive.

program
  The observing program / proposal identifier the data was taken under (e.g.
  `'2024A-001'`). {term}`query_program` pulls every observation from one
  proposal.

PI (Principal Investigator)
  The lead scientist on the observing program. {term}`query_pi` finds all
  observations led by a given person, matching the archive's PI column exactly
  (the full name as the archive stores it). The column name differs between
  archives, and not every table has one.

obsdate
  The observation time stamp; what date-range queries filter on, and the column
  behind {term}`query_datetime`. You never type the column name yourself for
  date queries, though you do see it in results.

Julian Date (JD / MJD)
  Standard astronomical time formats. JD counts days since 4713 BC; MJD = JD -
  2400000.5 (a smaller, modern number). Columns such as `obsjd` and `mjd` carry
  these precise numeric times, which you use as the x-axis of an RV time series
  and for any orbital fitting.

exptime
  Exposure time in seconds: how long the shutter was open for that observation.
  A common quality/selection filter (e.g. drop very short test exposures with
  `where='exptime > 60'`) and a basic descriptor of each row.

airmass
  How much atmosphere the light passed through, relative to straight overhead
  (1.0 = zenith, higher = closer to the horizon) — a proxy for observing
  conditions. A standard data-quality indicator; high-airmass points are noisier
  and you may want to filter them.

seeing
  The blurring of the image by atmospheric turbulence, in arcseconds; smaller is
  sharper/better. A quality metric useful for vetting which exposures to trust.

obsmode / obstype
  Descriptors of how/what was observed: `obsmode` is the instrument
  mode/configuration; `obstype` is the kind of exposure (science target,
  calibration, sky, etc.). Useful for separating real science frames from
  calibrations when scanning raw (L0) holdings.

proprietary period
  A protected window (often ~1 year) during which only the observing team can
  access their data; after it expires the data becomes public. Public data is
  queryable with no login; to reach data still inside its proprietary period
  you must {term}`login`. Archives whose data is fully public have no login at
  all.

login
  Proving to an archive that you are entitled to proprietary data.
  `archive.login()` exchanges your username/password for a session cookie that
  later runs reuse. Without it you can still query and download all public data
  — you only need it for proprietary observations. A 401/403 after login means
  the session expired ({term}`AuthExpired`).
```

## Querying

```{glossary}
TAP
  The Table Access Protocol, an IVOA standard web protocol for querying
  astronomical catalogs/tables over HTTP. The archives expose their data as TAP
  tables, and this package speaks TAP for you so you never construct HTTP
  requests by hand. You only need to know it exists when you read about sync vs
  async endpoints or see {term}`TAP_SCHEMA` in {term}`describe_table`.

ADQL
  Astronomical Data Query Language: a SQL dialect for astronomy tables, with
  extra geometry functions for cone/region searches. The high-level `query_*`
  methods build ADQL for you; {term}`query_adql` lets you write it raw, in which
  case you must follow server quirks yourself (e.g. Oracle `to_date` for dates).

TAP_SCHEMA
  A built-in {term}`TAP` metadata catalog describing every table and column
  (names, datatypes, units, descriptions) on the server. {term}`describe_table`
  queries it. It is the authoritative source for what columns exist and what they
  mean: when the docs say "use `describe_table` for the full list", that list
  comes from TAP_SCHEMA.

VOTable
  An IVOA XML format for tabular data, the native output format of {term}`TAP`,
  and the default {term}`output format` (`output_format='votable'`); the package
  parses it into an {py:class}`astropy.table.Table` for you. Mostly an
  implementation detail.

output format
  The wire format the server uses to send results back. `'votable'` is the
  default; `'csv'` and `'ipac'` (fixed-width IPAC table) are alternatives, and
  all three are parsed into the same {py:class}`astropy.table.Table`. You
  rarely change it: it affects only how the data is transmitted, not what data
  you get.

maxrec
  The maximum number of rows the server should return for a query (a row cap).
  `maxrec=500` means "at most 500 matching rows". Essential for keeping
  exploratory queries fast and small: set it low (e.g. 10) when you are just
  checking that a query works before downloading.

columns
  An optional list telling the query which columns to return, instead of all of
  them; unknown column names are rejected before any HTTP call. Smaller result
  tables are faster and easier to read — just remember to keep the
  filename/filepath columns if you plan to {term}`download` afterward.

where (ADQL fragment)
  An extra {term}`ADQL` condition string that is ANDed onto the query the method
  builds (e.g. `where='exptime > 60'`). It is the one place you write raw query
  syntax inside an otherwise high-level call, and you are responsible for valid
  ADQL in that string.

query_datetime
  The query method for when you know a time window: `query_datetime(level,
  (start, end))`. It always works and is the only sky-independent query, so it is
  the safest first query and the right entry point for solar data.

query_object
  The query method for when you know a star by name (e.g. `'HD 189733'`). It
  resolves the name to coordinates via {term}`name resolution (Simbad / NED)`,
  then runs a {term}`cone search` (default radius 30 arcsec). Use it when you do
  not have exact coordinates or a catalog ID.

query_position
  The query method for when you know RA/Dec: `query_position(level, coord,
  radius)` with an {py:class}`astropy.coordinates.SkyCoord`. It runs a direct
  {term}`cone search`; use it when you already have coordinates or want to search
  a region rather than a named target.

query_qobject
  The query method for when you know the exact catalog ID (usually Gaia DR2):
  `query_qobject(level, id)`. It does an exact column match against
  {term}`qobject` with no name resolution and no positional ambiguity, the best
  choice when you want every observation of one specific target reliably.

query_program
  The query method for when you know the proposal/program ID:
  `query_program(level, program)`. Pulls every observation from one program.

query_pi
  The query method for when you know the lead scientist: `query_pi(level,
  name)`. It exact-matches the archive's {term}`PI (Principal Investigator)`
  column.

query_criteria
  The query method for when you know several constraints at once: pass a dict to
  combine them in a single server round-trip (preferred over running several
  queries). Keys include `datetime`, `position`, `object` (+ `object_radius`),
  `qobject`, `program`, `pi_name`, and `where` for a raw {term}`ADQL` add-on.

query_adql
  The raw escape hatch for when nothing else fits: `query_adql(raw_string)`. You
  own the {term}`ADQL` and must follow server quirks (Oracle `to_date` for dates,
  exact table spelling). Most users should prefer the higher-level `query_*`
  methods.

async TAP job (AsyncJob)
  For queries too slow to return immediately, {term}`TAP` can run them in the
  background. `submit_async()` returns an {py:class}`~nexsci_rv.async_job.AsyncJob`
  handle you poll (`.wait()`, `.phase`) and then collect with `.result()`; the
  synchronous path returns immediately instead. Large multi-year pulls can time
  out on the sync endpoint, so submitting async lets the server work while you
  wait, then hands you the full {py:class}`astropy.table.Table`.

job phase
  The state of an {term}`async TAP job (AsyncJob)`: PENDING/QUEUED, EXECUTING,
  COMPLETED, ERROR, or ABORTED, exposed as `job.phase`. You check it to know
  whether to keep waiting, collect results, or read the error; `wait()` blocks
  until it leaves the running states.

describe_table
  A method that lists every column a table offers, with units and descriptions,
  by reading the server's {term}`TAP_SCHEMA`. Use it to discover fields beyond
  the common ones, e.g. `describe_table('neidl2')`. The reported columns are the
  archive's declared schema; a given query may not return every column listed.

astropy Table
  The {py:class}`astropy.table.Table` object that every query method returns: a
  column-oriented table with units and metadata, the standard astronomy
  in-memory table. All results come back as one of these, so you filter, sort,
  and plot them with tools you already know. {term}`download` then consumes the
  Table to fetch files.

download
  The method that fetches the FITS files for the rows in a result Table:
  `download(table, outdir=...)`. It returns a list of {py:class}`pathlib.Path`
  objects. It reads the {term}`filename / filepath / filehand` columns to locate
  files, so keep those in any `columns=` selection. Tables from the `query_*`
  methods remember their data level, so the right files are fetched.

filename / filepath / filehand
  The columns that identify the actual FITS file for a row, named after the
  data level of the file: `l2filename` is the file's name and `l2filepath` the
  server-side path used to build a download URL. {term}`download` reads these
  columns to fetch files, so if you select columns manually and omit them,
  download cannot find the files. `l2filehand` holds only the file's directory.
```

## Errors

```{glossary}
NotApplicable
  The exception ({py:exc}`~nexsci_rv.exceptions.NotApplicable`) raised when a
  query method does not make sense for the chosen archive or level — for example
  any position/object/qobject search on solar data, where the Sun has no fixed
  sky position.

QueryError
  The exception ({py:exc}`~nexsci_rv.exceptions.QueryError`) raised when a query
  cannot be carried out — for example when a target name cannot be resolved by
  {term}`name resolution (Simbad / NED)` before the archive is even contacted.

AuthExpired
  The exception ({py:exc}`~nexsci_rv.exceptions.AuthExpired`) raised when a
  query or download of proprietary data fails because your session has
  expired (a 401/403 after {term}`login`). The client never silently re-uses
  your password; call `login()` again.
```

## Archives

```{glossary}
NExScI
  The NASA Exoplanet Science Institute at IPAC/Caltech, which hosts the
  radial-velocity data archives this package queries.

production vs test server
  An archive can run more than one server instance: production (the real,
  complete data, and the default) and test instances used for development.
  Leave the default unless you have a reason; a test instance may hold
  incomplete data or lack tables entirely.
```

### NEID

```{glossary}
NEID
  A high-precision radial-velocity spectrograph on the WIYN 3.5-m telescope at
  Kitt Peak. Its archive at NExScI covers all data levels (`l0`, `l1`, `l2`,
  `eng`) plus a {term}`solar feed` (`solarl0` ... `solareng`). `NEIDArchive()`
  points at the production server `neid.ipac.caltech.edu`. See
  {doc}`archives/neid`.

ccfrvmod
  NEID's primary radial velocity (m/s) for an L2 observation, derived from the
  {term}`CCF (cross-correlation function)`. For most planet-hunting and
  RV-timeseries work it is the column you plot against time.

ccfnoise
  The photon-noise uncertainty on {term}`ccfrvmod` for NEID L2: your per-point
  RV error bar, needed to weight points in a fit or to judge whether a signal is
  significant.

ccfjdsum
  The time stamp (a Julian Date) of the summed CCF / RV measurement, in NEID L2
  (EXPRES solar L2 carries it too). Often the precise time to use as the x-axis
  of an RV time series, rather than a coarser frame time.
```

### EXPRES

```{glossary}
EXPRES
  The EXtreme PREcision Spectrograph on the Lowell Discovery Telescope. This
  package exposes its solar-feed data (the Sun observed as a star) at the solar
  L1 and L2 levels, all public. Because the data is solar-only, the sky-based
  query methods raise {term}`NotApplicable`. See {doc}`archives/expres`.

v / e_v (EXPRES)
  For EXPRES solar L2, `v` is the measured radial velocity (m/s) and `e_v` is
  its uncertainty. They play the role {term}`ccfrvmod` and {term}`ccfnoise`
  play for NEID, so when porting a NEID workflow, swap `ccfrvmod` → `v` and
  `ccfnoise` → `e_v`.
```

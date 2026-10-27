# Understanding your results

Every query returns an {term}`astropy Table`. Rather than face the full schema,
here are the kinds of columns a science user actually reaches for, grouped by
what they tell you. Archives share many column names, but not all; the table at
the end maps the ones that differ, and each archive's page lists its common
columns. For the authoritative, complete list of any table — with units and
descriptions — call {term}`describe_table`, e.g. `describe_table('neidl2')`.

## Identity and time

- {term}`object` — the free-text target name the observer entered (`'HD 189733'`,
  or `'Sun'`). Good for a sanity check, not for exact matching.
- {term}`qobject` — the normalized catalog ID (typically Gaia DR2); the clean
  exact-match key.
- {term}`obsdate` — the observation time stamp; the column behind
  {term}`query_datetime`.
- `obsjd`, `mjd`, {term}`ccfjdsum` — precise numeric times
  ({term}`Julian Date (JD / MJD)`) for building an RV time series and orbital
  fits.

## The RV answer

The radial velocity and its error bar. See {doc}`radial-velocities` for what
they mean, and the table below for each archive's column names.

## Quality and conditions

- {term}`exptime` — exposure time in seconds; a common selection filter.
- {term}`airmass` — atmosphere traversed (1.0 = overhead); a conditions proxy.
- {term}`seeing` — atmospheric blur in arcsec; smaller is better.
- {term}`extsnr` — extracted signal-to-noise; a natural quality cut.
- {term}`dvrms` — the photon-limited RV precision predicted for the exposure.

## Provenance

- {term}`program` — the proposal ID the data was taken under.
- The {term}`PI (Principal Investigator)` or observer.
- `swversion`, `l2procversion` — the
  {term}`pipeline version (swversion / procversion)`; pin it for reproducible
  RV sets.

## Download keys

- `l2filename` / `l2filepath` (and the `l0`/`l1` equivalents) — the
  {term}`filename / filepath / filehand` columns. {term}`download` needs them,
  so keep them in any `columns=` selection.

## Column names by archive

The concepts above are shared; where archives name a column differently, this is
the translation to use when porting a workflow:

| Concept | NEID | EXPRES (solar) |
| --- | --- | --- |
| Radial velocity | `ccfrvmod` | `v` |
| RV uncertainty | `ccfnoise` | `e_v` |
| Observation time | `obsdate` | `obsdate` |
| PI / observer | `piname` | `observer` (L1 only) |
| Catalog target ID | `qobject` | none (always the Sun) |

See {doc}`downloading-and-proprietary` for using the download keys.

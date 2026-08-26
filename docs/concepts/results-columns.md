# Understanding your results

Every query returns an {term}`astropy Table`. Rather than face the full schema,
here are the columns a science user actually reaches for, grouped by what they
tell you. For the authoritative, complete list of any table — with units and
descriptions — call {term}`describe_table`, e.g. `describe_table('neidl2')` or
`describe_table('expressolarl2')`.

## Identity and time

- {term}`object` — the free-text target name the observer entered (`'HD 189733'`,
  or `'Sun'`). Good for a sanity check, not for exact matching.
- {term}`qobject` — the normalized catalog ID (typically Gaia DR2); the clean
  exact-match key. (EXPRES solar: the constant `'Sun'`, not a real ID.)
- {term}`obsdate` — the observation time stamp on both archives; the column
  behind {term}`query_datetime`.
- `mjd`, `obsjd`, {term}`ccfjdsum` — precise numeric times
  ({term}`Julian Date (JD / MJD)`) for building an RV time series and orbital
  fits.

## The RV answer

- {term}`ccfrvmod` (+ {term}`ccfnoise`) — NEID: the primary radial velocity and
  its error bar.
- {term}`v / e_v (EXPRES)` — EXPRES: the radial velocity and its uncertainty.
- `ccfrvsum` — NEID: an alternate co-added-CCF RV, a cross-check on `ccfrvmod`.

## Quality and conditions

- {term}`exptime` — exposure time in seconds; a common selection filter.
- {term}`airmass` — atmosphere traversed (1.0 = overhead); a conditions proxy.
- {term}`seeing` — atmospheric blur in arcsec (NEID L1/L2); smaller is better.
- {term}`extsnr (EXPRES)` — extracted signal-to-noise; a natural quality cut.
- {term}`dvrms (EXPRES)` — the photon-limited RV precision predicted for the
  exposure.

## Provenance

- {term}`program` — the proposal ID the data was taken under (EXPRES solar is
  always `'EXPRESSOLAR'`).
- `piname` (NEID) / `observer` (EXPRES L1) — the
  {term}`PI (Principal Investigator)` / observer.
- `swversion`, `l2procversion` — the
  {term}`pipeline version (swversion / procversion)`; pin it for reproducible
  RV sets.

## Download keys

- `l2filename` / `l2filepath` (NEID) and `l2filename` / `l2filehand` (EXPRES) —
  the {term}`filename / filepath / filehand` columns. {term}`download` needs
  them, so keep them in any `columns=` selection.

## NEID ↔ EXPRES naming bridge

The two archives use different column names for the same concepts. If you port a
NEID workflow to EXPRES, translate:

| Concept | NEID | EXPRES |
| --- | --- | --- |
| Radial velocity | `ccfrvmod` | `v` |
| RV uncertainty | `ccfnoise` | `e_v` |
| Observation time | `obsdate` | `obsdate` |

See {doc}`radial-velocities` for what these RV columns mean, and
{doc}`downloading-and-proprietary` for using the download keys.

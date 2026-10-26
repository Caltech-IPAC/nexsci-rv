# Archives at NExScI

Before any code, it helps to know what you are actually querying.

`nexsci-rv` is a client for the {term}`radial velocity (RV)` archives hosted at
{term}`NExScI` (the NASA Exoplanet Science Institute at IPAC/Caltech). Each
archive is exposed as its own class with the same set of query and download
methods. Two archives are supported today.

## NEID

{term}`NEID` is a high-precision {term}`radial velocity (RV)` spectrograph on
the WIYN 3.5-m telescope at Kitt Peak. It records starlight spectra precisely
enough to detect the tiny wobble a planet induces on its host star.

## EXPRES

{term}`EXPRES`, the EXtreme PREcision Spectrograph, sits on the Lowell Discovery
Telescope. This client exposes only its **solar-feed** data — the Sun observed
as a star — which NExScI hosts on the same IPAC {term}`TAP` service as NEID, and
only at the solar L1 and L2 levels.

## The solar feed

Both instruments have a small telescope that feeds sunlight into the
spectrograph during the day, observing the Sun as if it were a distant star.
That data lives in a parallel set of {term}`solar feed` data levels
(`solarl0`...`solareng` for NEID; `solarl1`/`solarl2` for EXPRES). It is a
dense, high-cadence RV time series, used to study solar activity and to validate
each instrument's long-term stability.

## What a query gives you

An archive query returns a **table of metadata** describing matching
observations — times, targets, conditions, RV values, file names. The actual
spectra are {term}`FITS` files you fetch separately with {term}`download`. See
{doc}`downloading-and-proprietary` for that two-step workflow.

The default and recommended server is production
(`neid.ipac.caltech.edu`); EXPRES tables exist only there, so leave the default
unless you have a specific reason to change it (see
{term}`production vs test server`).

## The mental model

One paragraph to carry through the rest of the docs:

> Pick an archive (for example `NEIDArchive()` or `EXPRESArchive()`) → pick a
> {term}`data level` → filter rows with a `query_*` method → get back an
> {term}`astropy Table` → optionally {term}`download` the FITS files.

Next: {doc}`radial-velocities` (what the numbers mean), {doc}`data-levels`
(picking a level), and {doc}`choosing-a-query` (picking a method).

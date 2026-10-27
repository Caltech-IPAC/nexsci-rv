# Data levels

A {term}`data level` labels how far a file has been processed through the
reduction pipeline. It is the first argument to almost every query method (e.g.
`query_datetime('l2', ...)`) and it picks which underlying table you search, so
getting it right is the first decision you make.

Frame it as one question: **how processed do you need the data to be?**

| Level | What it contains | Who wants it |
| --- | --- | --- |
| {term}`L0` | Raw 2D detector frames, straight off the CCD | Only if you run your own reduction |
| {term}`L1` | Calibrated, wavelength-solved 1D extracted spectra | Custom spectral / line / activity analysis |
| {term}`L2` | RV-ready products: the CCF and the radial velocity | Most science users |
| {term}`eng (engineering level)` | Engineering / calibration frames | Instrument debugging only |

## Levels map to tables

Each archive maps its `data_level` strings to its own server tables (for
example, NEID's `'l2'` is the table `neidl2`). You pass the **level string**,
never the table name; the package translates for you, and `archive.data_levels`
lists the levels an archive offers.

## The solar variants

Archives with a {term}`solar feed` mirror the same hierarchy for Sun-as-a-star
data, with levels named `solarl0`, `solarl1`, `solarl2`, and so on. An archive
may offer only some levels; each archive's page has its table of levels.

## Practical default

Start with the level that holds the radial velocities — `'l2'`, or `'solarl2'`
for solar data — since that is what most users came for. Drop to `'l1'` only
when you want the spectra themselves, and to `'l0'` only when you intend to
reduce raw frames yourself.

Once you have picked a level, see {doc}`choosing-a-query` for picking the query
method.

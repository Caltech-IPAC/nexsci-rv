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

Each `data_level` string maps to a specific server table — `'l2'` → `neidl2`,
`'solarl2'` → `expressolarl2`, and so on. You pass the **level string**, never
the table name; the package translates for you.

## The solar variants

The {term}`solar feed` mirrors the same hierarchy for Sun-as-a-star data:
`solarl0` / `solarl1` / `solarl2` / `solareng` for NEID, and `solarl1` /
`solarl2` for EXPRES. (Remember EXPRES is solar-only — see {doc}`instruments`.)

## Practical default

Start with `'l2'` for NEID science and `'solarl2'` for EXPRES. That is where the
radial velocities live, which is what most users came for. Drop to `'l1'` only
when you want the spectra themselves, and to `'l0'` only when you intend to
reduce raw frames yourself.

Once you have picked a level, see {doc}`choosing-a-query` for picking the query
method.

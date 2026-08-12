# Your first query

This page walks you from a blank Python prompt to a real result table from the
{term}`NEID` archive. No account, no setup beyond installing the package — NEID's
public {term}`L2` data is queryable by anyone.

## Open the archive

Everything starts with an archive object. For NEID, that is `NEIDArchive`:

```python
from nexsci_rv import NEIDArchive

neid = NEIDArchive()
```

That's it. `NEIDArchive()` points at the production NEID holdings at
{term}`NExScI`. You only need to {term}`login` if you want data still inside its
{term}`proprietary period`; the public archive needs no credentials, so we'll
stay public here.

## Ask for a few observations

The simplest thing to ask the archive is "what did NEID observe during this time
window?" That's {term}`query_datetime`. It's the friendliest first query because
it doesn't depend on a sky position or a target name — it just filters on the
observation date.

```python
table = neid.query_datetime(
    "l2",
    ("2024-11-01", "2024-11-06"),
    columns=["date_obs", "object", "ccfrvmod", "ccfnoise", "exptime"],
    maxrec=5,
)
print(table)
```

A few things to notice in that call:

- The first argument, `"l2"`, is the {term}`data level`. {term}`L2` is the
  science-ready level — one {term}`radial velocity (RV)` per observation — which
  is what most people want. (Want the spectra themselves instead? That's
  {term}`L1`. See {doc}`../concepts/data-levels`.)
- The date range is an inclusive `(start, end)` pair. Dates accept anything
  `astropy.time.Time` understands, so ISO strings like `"2024-11-01"` are fine.
- `columns=` asks for just the fields we care about, instead of the whole row.
- {term}`maxrec` caps the result at 5 rows — handy while you're still finding
  your footing, so each query comes back fast.

## Read the result

The result is an {py:class}`astropy.table.Table` — the same table object you
already use elsewhere in astropy. You can sort it, filter it, write it to disk,
or feed it straight into a plot:

```text
       date_obs         object   ccfrvmod  ccfnoise  exptime
                                    m / s     m / s      s
----------------------- -------- --------- --------- -------
2024-11-01T03:12:44.521 HD 3651  -33012.4       1.8   120.0
2024-11-01T05:47:18.903 HD 9407   12880.1       2.1    90.0
...
```

Here's what those columns are telling you:

- {term}`date_obs / obsdate` — when the exposure was taken. (NEID calls this
  `date_obs`; EXPRES calls it `obsdate`.)
- {term}`object` — the free-text target name the observer typed in. Useful as a
  sanity check, but don't rely on it for exact matching.
- {term}`ccfrvmod` — the headline radial velocity for that observation, in m/s.
  This is the number you'd plot against time to hunt for a planet.
- {term}`ccfnoise` — the formal uncertainty (error bar) on that RV.
- {term}`exptime` — how long the shutter was open, in seconds.

For a guided tour of the columns you'll meet most often — and how to find the
rest — see {doc}`../concepts/results-columns`.

## Where to go next

You searched by date because it's the simplest entry point, but it's only one of
several ways in. If you instead know a star by name, its coordinates, a catalog
ID, an observing program, or a PI, there's a `query_*` method tailored to each.
{doc}`../concepts/choosing-a-query` lays them out side by side and helps you pick.

When a query returns the observations you want, the next step is fetching the
actual {term}`FITS` files with {term}`download` — see
{doc}`../concepts/downloading-and-proprietary` for how querying and downloading
fit together, and {doc}`../tutorials/03_download_and_plot` for a worked
download-and-plot example.

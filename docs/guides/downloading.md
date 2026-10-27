# Downloading FITS files

A query gives you an {term}`astropy Table` describing matching observations; it
does **not** fetch any data. To pull down the actual {term}`FITS` files, pass
that table to {term}`download`. The split is deliberate — explore cheaply with
queries, then fetch only the rows you decided you want. For the why behind that
two-step model, see {doc}`../concepts/downloading-and-proprietary`.

## The basic recipe

Query a small batch first, then download it:

```python
from nexsci_rv import NEIDArchive

neid = NEIDArchive()

tbl = neid.query_datetime("l2", ("2024-11-01", "2024-11-02"), maxrec=10)
paths = neid.download(tbl, outdir="data/", workers=4, resume=True)
```

`download` returns a `list[`{py:class}`pathlib.Path`` `]` — one path per file
it successfully fetched, pointing into `outdir` (which is created if it doesn't
exist).

## Keep the file columns in your table

`download` locates each file using the filename/filepath columns of the table
you hand it. If you narrowed a query with `columns=` and dropped those, download
has nothing to work from.

Every archive uses a `*filename` plus `*filepath` pair named after the data
level (e.g. `l2filename`, `l2filepath`).

So if you select columns explicitly, keep the relevant pair:

```python
tbl = neid.query_datetime(
    "l2", ("2024-11-01", "2024-11-02"),
    columns=["l2filename", "l2filepath", "obsdate", "object"],
)
paths = neid.download(tbl, outdir="data/")
```

The default selection (no `columns=`) already includes them. For a tour of which
columns mean what — including the download keys — see
{doc}`../concepts/results-columns`.

```{tip}
A table returned by a `query_*` method remembers which data level it came from,
so `download` fetches the right files: an L2 query downloads L2 spectra even
though NEID rows also list their L0 and L1 files. Tables from
{term}`query_adql`, or built by hand, carry no data level. NEID night-time and
solar tables use the same filename columns, so pass `data_level=` explicitly
for those, e.g. `neid.download(tbl, data_level="l2")`.
```

## Handling partial failures

Downloads are best-effort: every file is attempted, and only after the whole
batch finishes does `download` decide whether to raise. If any file failed,
{py:exc}`~nexsci_rv.exceptions.DownloadError` is raised — but the files that
**did** succeed are already written to disk and are not removed. The exception
carries a `.failures` attribute listing `(filename, underlying_exception)`
tuples so you can see exactly what went wrong:

```python
from nexsci_rv.exceptions import DownloadError

try:
    paths = neid.download(tbl, outdir="data/")
except DownloadError as exc:
    for filename, err in exc.failures:
        print(f"failed: {filename}: {err}")
    # The files that succeeded are still on disk; re-run with resume=True
    # to retry just the missing ones.
```

A 401 or 403 during a download of proprietary data is treated differently: it
raises {py:exc}`~nexsci_rv.exceptions.AuthExpired` instead, meaning your NEID
session expired. Call `neid.login()` again and re-run the download (see
{doc}`authentication`).

## Useful options

- **`resume=True`** (the default) skips any destination file that already exists
  at the same size as the remote file. Re-running a download after a partial
  failure therefore fetches only what's missing — cheap and idempotent.
- **`workers=`** sets how many files download in parallel (default `4`).
  Astronomy archives throttle aggressively, so a modest number is both polite
  and usually faster overall than a large one. Resist the urge to crank it up.
- **`progress=False`** silences the `tqdm` progress bar — handy in scripts, logs,
  or batch jobs where a live bar is just noise.

```python
paths = neid.download(tbl, outdir="data/", workers=2, progress=False)
```

## Be kind to the archive

FITS spectra are not small — individual files run from a few megabytes up to
tens or hundreds of megabytes depending on data level, with raw L0 frames the
heaviest. A few hundred files is a real transfer.

- **Cap exploratory queries** with {term}`maxrec` (e.g. `maxrec=10`) while you're
  still working out the right filter, so you don't download a year of data to
  discover you wanted a week.
- **Keep `workers` modest** — the default of 4 is a good citizen.
- **Let `resume=True` do the retrying** rather than hammering the server in a
  tight loop.

The archives are a shared resource; a steady, bounded download is faster for you
and easier on everyone else.

# Migrating from pyNEID

`nexsci-rv` replaces [pyNEID](https://github.com/Caltech-IPAC/pyNEID). It covers
the same NEID searches and downloads, but it is **not** API-compatible: there is
no compatibility shim, so existing code is rewritten call by call. This page is
the mapping.

The biggest change is that queries **return** an {term}`astropy Table` instead
of writing a file to `outpath`, and {term}`download` takes that table instead of
a path to a saved metadata file.

## Setup and login

```python
# pyNEID
from pyneid.neid import Neid
Neid.login(userid="me", password="...", cookiepath="./neidcookie.txt")

# nexsci-rv
from nexsci_rv import NEIDArchive
neid = NEIDArchive()
neid.login(username="me", password="...")
```

- There is no `cookiepath`. The session cookie is stored for you (under
  `~/.config/nexsci-rv/neid/`) and reused by every later query and download, in
  this and future sessions.
- Credentials can come from the environment instead of code:
  `NEXSCI_RV_NEID_USER` and `NEXSCI_RV_NEID_PASSWORD`. With neither arguments
  nor environment variables, `login()` prompts.
- Public data needs no login at all, as before.

## Method mapping

| pyNEID | nexsci-rv |
| --- | --- |
| `Neid.query_datetime(level, "t1/t2", outpath=..., format=...)` | `neid.query_datetime(level, ("t1", "t2"))` |
| `Neid.query_position(level, "circle ra dec r")` | `neid.query_position(level, (ra, dec), r)` |
| `Neid.query_object(level, name)` | `neid.query_object(level, name, radius=0.5 * u.deg)` (see below) |
| `Neid.query_qobject(level, qobject)` | `neid.query_qobject(level, qobject)` |
| `Neid.query_piname(level, piname)` | `neid.query_pi(level, piname)` |
| `Neid.query_program(level, program)` | `neid.query_program(level, program)` |
| `Neid.query_criteria(param)` | `neid.query_criteria(criteria)` (keys renamed, see below) |
| `Neid.query_adql(query, outpath=...)` | `neid.query_adql(query)` |
| `Neid.download(metapath, level, format, outdir)` | `neid.download(table, outdir)` |
| `NeidTap.send_async(query)` + `get_data(path)` | `neid.submit_async(query)`, then `.wait()` and `.result()` |
| `print_data()`, `debugfile=` | `print(table)`; `logging.getLogger("nexsci_rv")` |

## Arguments that changed shape

**Date ranges** are a `(start, end)` tuple instead of a `"start/end"` string.
Either side may be `None` for an open range, replacing pyNEID's `"t1/"` and
`"/t2"` forms. Strings, `datetime` objects, and `astropy.time.Time` all work.

**Positions** are a coordinate plus a radius instead of a `"circle ra dec r"`
string. The coordinate is an `astropy.coordinates.SkyCoord` or an
`(ra, dec)` tuple in degrees; a bare-number radius is in degrees, or pass an
`astropy` angle such as `30 * u.arcsec`. pyNEID's `polygon` and `box` shapes
have no high-level equivalent — write them with {term}`query_adql` using
ADQL's `POLYGON` / `BOX` against the `qrad` / `qdecd` columns.

**`query_object` radius:** pyNEID searched within **0.5 degrees** of the
resolved name by default; `nexsci-rv` defaults to **30 arcseconds**. Pass
`radius=0.5 * u.deg` to reproduce pyNEID's result sets exactly.

**`query_pi`** matches the PI column exactly, as pyNEID's `query_piname` did:
pass the full name as the archive stores it (e.g. `"Robert Mathieu"`).

**`query_criteria` keys:**

| pyNEID `param` key | nexsci-rv `criteria` key |
| --- | --- |
| `datalevel` | `data_level` |
| `datetime` (`"t1/t2"`) | `datetime` (`(t1, t2)`) |
| `position` (`"circle ra dec r"`) | `position` (`(coord, radius)`) |
| `object` | `object` (radius via `object_radius`) |
| `qobject` | `qobject` |
| `program` | `program` |
| `piname` | `pi_name` |

`nexsci-rv` adds a `where` key for an extra raw ADQL condition.

**`maxrec`** works as before. **`format`** is now `output_format=` and only
affects how results travel over the wire — you always get a Table back.
pyNEID's `tsv` format is not offered.

## Saving results

Where pyNEID wrote the result to `outpath`, write the returned table yourself in
whatever format you want:

```python
table = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))
table.write("l2_results.tbl", format="ascii.ipac")
```

## Downloading

```python
# pyNEID
Neid.download("./criteria.tbl", "l2", "ipac", "./dnload_dir",
              cookiepath="mycookie", start_row=0, end_row=10)

# nexsci-rv
paths = neid.download(table[0:10], outdir="./dnload_dir")
```

- Pass the table a query returned. It remembers its data level, so `download`
  fetches the right files — an L2 result downloads L2 spectra.
- `start_row` / `end_row` become ordinary table slicing.
- If you saved a table to disk and read it back with `Table.read`, it no longer
  knows its data level: pass it explicitly, e.g.
  `neid.download(table, outdir="data/", data_level="l2")`.
- `download` returns a list of `pathlib.Path`s. Files that fail are retried and
  then reported together in a {py:exc}`~nexsci_rv.exceptions.DownloadError`
  while the successful files stay on disk.

```{note}
pyNEID's `calibfile=1` option, which also fetched each observation's
associated calibration files, has no equivalent in `nexsci-rv` yet.
```

## Errors

pyNEID reported many failures by printing or by returning a status. `nexsci-rv`
raises typed exceptions from {py:mod}`nexsci_rv.exceptions` — for example
{py:exc}`~nexsci_rv.exceptions.TapServerError` with the server's message when a
query fails, and {py:exc}`~nexsci_rv.exceptions.AuthExpired` when a session
needs a fresh `login()`. Catch {py:exc}`~nexsci_rv.exceptions.NexsciRVError` to
handle anything from the package.

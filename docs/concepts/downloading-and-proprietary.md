# Querying vs downloading, and proprietary data

Getting files from the archive is two steps, and it helps to keep them
separate.

## Query first, download second

A query gives you an {term}`astropy Table` describing the matching observations
— times, targets, RV values, file names. It does **not** fetch any data files.
To get the actual {term}`FITS` files, pass that table to {term}`download`:

```python
table = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))
paths = neid.download(table, outdir="data/")
```

`download` returns a list of {py:class}`pathlib.Path` objects pointing at the
files it fetched.

```{note}
`download` finds each file using the
{term}`filename / filepath / filehand` columns of your table. If you narrowed
the result with `columns=` and dropped those columns, download cannot locate the
files. Keep `l2filename` and `l2filepath` (or the `l0`/`l1` equivalents for
your level) in any selection you plan to download.
```

## Explore small, then pull what you need

While you are still working out the right query, keep results small with
{term}`maxrec` (e.g. `maxrec=10`) so each round-trip is fast. Once the query
returns the rows you want, drop or raise the cap and download only those.

## When you need to log in

Some archives hold data under a {term}`proprietary period` (often about a
year), during which only the observing team can reach it; after that it becomes
public.

- **Public data** needs no login — query and download freely.
- **Proprietary data** (still inside its window) requires {term}`login` with
  your archive credentials, e.g. `neid.login()`. The client caches your
  session, so you log in once.
- **Fully public archives** (such as the EXPRES solar data) have no login at
  all.

If a query or download of proprietary data fails with
{py:exc}`~nexsci_rv.exceptions.AuthExpired`, your session expired; call
`login()` again. Each archive's page says whether it has proprietary data.

## Very large pulls

A normal `query_*` call is synchronous and returns immediately, which is fine
for bounded queries. For very large or multi-year pulls that would time out, use
the {term}`async TAP job (AsyncJob)` path instead: `submit_async()`, then
`.wait()` and `.result()`. The server works in the background while you wait.
See {doc}`tap-adql`.

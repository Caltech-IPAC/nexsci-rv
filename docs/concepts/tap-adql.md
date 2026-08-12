# TAP and ADQL, just enough

Two acronyms run under everything in this package. You do not need to master
them — but it helps to know what they are and the one place they peek through.

## TAP is the plumbing

{term}`TAP` (Table Access Protocol) is the IVOA standard for querying
astronomical tables over HTTP. The archive exposes its holdings as TAP tables,
and this package speaks TAP for you — so you call `query_*` methods instead of
building HTTP requests by hand. You mainly meet the name in two places: the
sync-vs-async distinction below, and {term}`TAP_SCHEMA`, the server's
self-description that {term}`describe_table` reads to list the real columns,
units, and descriptions of a table.

## ADQL is the query language

{term}`ADQL` (Astronomical Data Query Language) is SQL for astronomy, with extra
geometry functions for {term}`cone search`es. The high-level methods build ADQL
for you from your arguments, so most users never write a line of it.

You only meet ADQL directly in two ways:

- a {term}`where (ADQL fragment)` string ANDed onto a high-level query (e.g.
  `where='extsnr > 200'`), or
- the {term}`query_adql` escape hatch, where you write the whole query.

```{warning}
When you do write ADQL yourself, two server quirks bite:

- **Dates** must use Oracle `to_date('YYYY-MM-DD HH24:MI:SS', ...)`; a bare
  string comparison fails. (The high-level methods handle this for you.)
- **Table names are spelling- and case-sensitive** — `expressolarl1` has a
  single `s` between `expres` and `solar`. Double-s spellings return a
  "table or view does not exist" error.
```

## Sync versus async

A normal `query_*` call is **synchronous**: it sends the query and waits for the
rows, returning them immediately. That is ideal for bounded queries — keep them
small with {term}`maxrec` while exploring.

For a query too large or slow to return in one shot, run it **asynchronously**:
the server queues it and works in the background while you poll an
{term}`async TAP job (AsyncJob)`. You submit with `submit_async()`, watch its
{term}`job phase`, then collect the full {term}`astropy Table` with `.result()`.

For mapping a question to a method, see {doc}`choosing-a-query`.

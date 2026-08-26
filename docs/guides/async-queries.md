# Long-running (async) queries

Almost every query you run with `nexsci-rv` is synchronous: you call a `query_*`
method, the server works while you wait, and the {term}`astropy Table` comes
back in a few seconds. **Most users never need anything else.** This page is for
the exception.

## When do I need this?

The synchronous TAP endpoint has a time budget. A query that has to scan a large
table — a multi-year date range, a very wide cone search, an expensive join —
can exceed that budget and time out before the server finishes. When that
happens, you submit the same query *asynchronously* instead: the server queues
it, works on it in the background, and lets you poll for completion and then
collect the full result.

If your queries return promptly, stay synchronous. Reach for async only when a
real query is timing out.

## A complete worked example

```python
from nexsci_rv import NEIDArchive

neid = NEIDArchive()

adql = (
    "SELECT obsdate, exptime, object FROM neidl2 "
    "WHERE obsdate BETWEEN "
    "to_date('2020-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') AND "
    "to_date('2024-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS')"
)

job = neid.submit_async(adql)   # returns immediately with a handle
job.wait(timeout=600)           # blocks until the server finishes (or times out)
tbl = job.result()              # fetch and parse the completed result table
```

`submit_async()` hands you an {py:class}`~nexsci_rv.async_job.AsyncJob` straight
away — the server has only *accepted* the job at that point, not run it.
`wait()` polls the job's status until it reaches a terminal phase, and
`result()` downloads the finished table.

```{note}
The ADQL string is the raw escape hatch, so you follow the server's quirks
yourself — in particular Oracle's `to_date('YYYY-MM-DD HH24:MI:SS', ...)` for
date comparisons. See {term}`query_adql` and {term}`ADQL`.
```

## Choosing `timeout` and the poll interval

`wait()` takes two knobs:

```python
job.wait(timeout=600, poll_interval=5.0)
```

- **`timeout`** (seconds) is your patience budget. If the job hasn't finished
  within it, `wait()` raises {py:exc}`TimeoutError` — but the job keeps running
  on the server. You can call `wait()` again, or poll `job.phase` yourself, to
  pick it back up. Setting `timeout=None` waits indefinitely. Pick a value
  comfortably larger than you expect the query to take; minutes, not seconds,
  for the big pulls that justify going async in the first place.
- **`poll_interval`** (seconds, default `5.0`) is how often `wait()` re-checks
  the server. The default is sensible for jobs that take minutes — don't drop it
  to a fraction of a second, since that just hammers the status endpoint without
  making your result arrive any sooner.

## When something goes wrong

`wait()` raises {py:exc}`~nexsci_rv.exceptions.AsyncJobError` automatically if
the job ends in `error` or `aborted`, so the simple path above already surfaces
failures. If you poll `job.phase` yourself instead of calling `wait()`, check
for the error phase and read the server's message:

```python
if job.phase == "error":
    print("server rejected the job:", job.error)
```

`job.error` holds the server-side error summary (often a malformed-ADQL or
schema complaint) — read it to fix the query and resubmit.

A 401 or 403 while polling or fetching results raises
{py:exc}`~nexsci_rv.exceptions.AuthExpired`: your NEID session expired. Call
`neid.login()` again and resubmit the job (see {doc}`authentication`).

To stop a job you no longer want, call `job.abort()`.

## Results don't live forever

A finished job's result is not kept indefinitely. The server assigns each job a
*destruction time*, after which the result resource is cleaned up and
`result()` will no longer find anything. The practical rule: **fetch your result
soon after the job completes.** If you need it later, fetch the table and save it
yourself (e.g. `tbl.write(...)`). You can inspect the times the server reported
via `job.times` (it includes a `"destruction"` entry when the server provides
one).

## Reference

- {py:class}`~nexsci_rv.async_job.AsyncJob` — the full handle API (`phase`,
  `error`, `result_url`, `wait()`, `result()`, `refresh()`, `abort()`).
- {doc}`../api/async_job` — the generated reference page.

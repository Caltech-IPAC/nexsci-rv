# AsyncJob

**When do I need this?** Most queries return in a few seconds and you will
never touch this class. Use it when a query is large enough (multi-year pulls,
very wide cone searches) that the synchronous TAP endpoint would time out before
returning. In that case, call `submit_async()` on an archive object instead of
a `query_*` method; it hands you back an `AsyncJob` handle immediately. You can
then poll `job.phase`, call `job.wait()` to block until the server finishes, and
collect the full {py:class}`astropy.table.Table` with `job.result()`. See the
async example in {doc}`../quickstart`.

```{eval-rst}
.. autoclass:: nexsci_rv.async_job.AsyncJob
   :members:
   :show-inheritance:
   :member-order: bysource
```

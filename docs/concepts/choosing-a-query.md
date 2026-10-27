# Choosing a query

You have picked an archive and a {term}`data level` (see {doc}`data-levels`).
Now pick a query method by **what you already know** about the data you want.

| You know... | Use | What it does |
| --- | --- | --- |
| A time window | {term}`query_datetime` | Filters on the observation date. Always works. |
| A star by name | {term}`query_object` | Resolves the name to coordinates, then cone-searches. |
| RA/Dec | {term}`query_position` | Direct {term}`cone search` around a {py:class}`astropy.coordinates.SkyCoord`. |
| The exact catalog ID | {term}`query_qobject` | Exact match on {term}`qobject` (usually Gaia DR2); no resolver, no ambiguity. |
| The proposal ID | {term}`query_program` | Every observation from one program. |
| The lead scientist | {term}`query_pi` | Every observation led by that person. |
| Several of the above | {term}`query_criteria` | Combines constraints in one server round-trip. |
| Nothing above fits | {term}`query_adql` | Raw escape hatch; you own the {term}`ADQL`. |

## Start with a time window

{term}`query_datetime` is the safest first query: it always works and is the
only sky-independent one. When in doubt — or when working with solar data — it
is the right entry point.

## Name versus catalog ID

Two methods find a specific target, and the difference matters:

- {term}`query_object` takes a human-readable name (`'HD 189733'`), resolves it
  via {term}`name resolution (Simbad / NED)`, and cone-searches around the
  resulting coordinates. Use it when you have a name but not exact coordinates
  or an ID. Note the free-text {term}`object` field is inconsistent across
  programs, so do not try to exact-match on it.
- {term}`query_qobject` takes the archive's normalized catalog ID (Gaia DR2) and
  does an exact, unambiguous match with no network name-resolution step. Use it
  when you want every observation of one specific target, reliably.

## Combine, do not chain

When you know several things at once — say a date range *and* a target — reach
for {term}`query_criteria` with a dict (keys: `datetime`, `position`, `object`
plus `object_radius`, `qobject`, `program`, `pi_name`, and `where` for a raw
{term}`ADQL` add-on). One combined query beats running several and merging the
results.

## When a method does not apply

Not every method makes sense for every archive or level. Solar observations have
no celestial target — their
{term}`query coordinates (qra / qdec / qrad / qdecd)` are
{term}`sentinel value`s — so position, object, and qobject searches on solar
data raise {py:exc}`~nexsci_rv.exceptions.NotApplicable` rather than return
meaningless rows. Likewise {term}`query_pi` raises it on tables with no PI
column. Each archive's page lists exactly which methods apply. For solar data,
reach for {term}`query_datetime`, optionally narrowed with a `where=` cut (e.g.
`extsnr > 200`).

## Sync versus async

A normal `query_*` call is synchronous and returns immediately — fine for
bounded queries (keep them small with {term}`maxrec` while exploring). For very
large or multi-year pulls that would time out, use an
{term}`async TAP job (AsyncJob)` instead. See {doc}`tap-adql` and
{doc}`downloading-and-proprietary`.

# API reference

This section is the precise reference for every public class and method in
`nexsci-rv`. If you are new, start with the {doc}`../quickstart` and the
{doc}`../tutorials/01_neid_query_l2` before diving in here.

**Find the right method by intent:**

| I want to search by … | Method to reach for |
|---|---|
| Observation date or time window | {doc}`../concepts/choosing-a-query` → `query_datetime` |
| Sky position (RA/Dec) | {doc}`../concepts/choosing-a-query` → `query_position` |
| Target name (e.g. `'HD 189733'`) | {doc}`../concepts/choosing-a-query` → `query_object` |
| Gaia or catalog ID | {doc}`../concepts/choosing-a-query` → `query_qobject` |
| Observing program or PI | {doc}`../concepts/choosing-a-query` → `query_program` / `query_pi` |
| Several criteria at once | {doc}`../concepts/choosing-a-query` → `query_criteria` |

- {doc}`archives` — `NEIDArchive` and `EXPRESArchive`: create one and call `query_*` / `download` on it.
- {doc}`async_job` — `AsyncJob`: handle for large queries that run in the background.
- {doc}`exceptions` — the full `NexsciRVError` hierarchy.
- {doc}`config` — `Conf`: timeouts and download behaviour.

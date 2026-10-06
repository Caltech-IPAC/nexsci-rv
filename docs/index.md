# nexsci-rv

**NEID** is a high-precision radial-velocity (RV) spectrograph on the WIYN 3.5-m
telescope at Kitt Peak, and **EXPRES** is a spectrograph on the Lowell Discovery
Telescope (this client exposes its solar-feed data). Their data are archived at
[NExScI](https://nexsci.caltech.edu/). `nexsci-rv` is a Python client for
searching those archives and downloading their data products.

## A quick example

Find all NEID Level-2 spectra taken in a given week:

```python
from nexsci_rv import NEIDArchive

neid = NEIDArchive()
table = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))
print(table)
```

## What you can do

Search the archives the way you actually think about your data, then pull down
the files you need:

- **Find spectra** by observation date, sky position, target name, Gaia ID,
  observing program, or PI.
- **Combine criteria** — for example, a target name *and* a date range — in a
  single query.
- **Download the FITS data products** for the rows you selected.
- **Run long searches asynchronously** so a big query doesn't block your session.

Every search returns an `astropy.table.Table`, so you can filter, sort, and join
results with the tools you already use.

## Relationship to pyNEID

`nexsci-rv` is a clean-room successor to
[pyNEID](https://github.com/Caltech-IPAC/pyNEID). It is **not** API-compatible:
existing pyNEID users rewrite their imports and call sites, and it adds support
for the EXPRES solar archive.

## Project status

Alpha (`0.1.0`). The code is production-quality, but the public API may still
shift based on user feedback before `1.0.0`. Issues and design feedback are
welcome at
[github.com/Caltech-IPAC/nexsci-rv/issues](https://github.com/Caltech-IPAC/nexsci-rv/issues).

## Getting help

- **Questions about the data or archive access** — email the NEID/NExScI archive
  helpdesk at <neid-help@ipac.caltech.edu>.
- **Bugs or feature requests in this client** — open an issue at
  [github.com/Caltech-IPAC/nexsci-rv/issues](https://github.com/Caltech-IPAC/nexsci-rv/issues).

Never include a password or session cookie in an issue or an email. See
{doc}`guides/authentication` for how credentials are handled.

## Next steps

- {doc}`quickstart` — the search-and-download patterns most users hit first.
- {doc}`tutorials/01_neid_query_l2` — a worked NEID Level-2 query, end to end.
- {doc}`archives/neid` — what NEID offers, including its data levels.
- {doc}`archives/expres` — the EXPRES solar archive.

```{toctree}
:hidden:
:caption: Getting started

install
getting-started/first-query
```

```{toctree}
:hidden:
:caption: Understanding the data

concepts/instruments
concepts/radial-velocities
concepts/data-levels
concepts/choosing-a-query
concepts/results-columns
concepts/downloading-and-proprietary
concepts/tap-adql
glossary
```

```{toctree}
:hidden:
:caption: Guides

quickstart
guides/authentication
guides/downloading
guides/async-queries
```

```{toctree}
:hidden:
:caption: Archives

archives/neid
archives/expres
```

```{toctree}
:hidden:
:caption: Tutorials

tutorials/01_neid_query_l2
tutorials/02_expres_solar
tutorials/03_download_and_plot
```

```{toctree}
:hidden:
:caption: Reference

api/index
api/archives
api/async_job
api/config
api/exceptions
changelog
```

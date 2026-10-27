# nexsci-rv

A Python client for radial-velocity data archives hosted at [NExScI](https://nexsci.caltech.edu/).

[![Docs](https://github.com/Caltech-IPAC/nexsci-rv/actions/workflows/docs.yml/badge.svg)](https://caltech-ipac.github.io/nexsci-rv/)

📖 **Documentation:** <https://caltech-ipac.github.io/nexsci-rv/>

**Status:** stable (`1.0.0`). The public API follows [Semantic Versioning](https://semver.org/): breaking changes only in a new major version.

`nexsci-rv` gives every supported archive the same interface: search
observations by date, position, target, or program, get the results back as
an `astropy` table, and download the data products you need.

## Supported archives

| Archive | Data levels | Auth |
|---|---|---|
| NEID    | L0, L1, L2, eng, solar L0/L1/L2/eng | cookie-based login (public access without) |
| EXPRES  | solar L1, solar L2                  | public |

## Install

```bash
pip install nexsci-rv
# or, from source:
pip install -e ".[dev]"
```

## Quickstart

```python
from nexsci_rv import NEIDArchive, EXPRESArchive

neid = NEIDArchive()
table = neid.query_datetime("l2", ("2024-11-01", "2024-11-06"))
print(table)

expres = EXPRESArchive()
sun = expres.query_datetime(
    "solarl2",
    ("2024-11-01", "2024-11-06"),
    columns=["l2filename", "obsdate", "v", "e_v", "dvrms", "extsnr"],
)
print(sun)
```

See the [quickstart](https://caltech-ipac.github.io/nexsci-rv/quickstart.html) and the [tutorials](https://caltech-ipac.github.io/nexsci-rv/tutorials/01_neid_query_l2.html) in the documentation.

## Predecessor

`nexsci-rv` is a clean-room successor to [pyNEID](https://github.com/Caltech-IPAC/pyNEID). It is **not** API-compatible — see the [changelog](https://github.com/Caltech-IPAC/nexsci-rv/blob/main/CHANGELOG.md) for the rationale.

## Support

Questions, bug reports, and feature requests are welcome:

- **Email:** <neid-help@ipac.caltech.edu> — the NEID/NExScI archive helpdesk, and the
  best route for questions about the data itself or about archive access.
- **GitHub Issues:** <https://github.com/Caltech-IPAC/nexsci-rv/issues> — for bugs in
  this client library.

Please do not include passwords or session cookies in an issue or an email.

## License

BSD 3-Clause. See [`LICENSE`](https://github.com/Caltech-IPAC/nexsci-rv/blob/main/LICENSE).

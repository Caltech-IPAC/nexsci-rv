# Exceptions

Every error raised by `nexsci-rv` inherits from
{py:exc}`~nexsci_rv.exceptions.NexsciRVError`, so you can catch the whole
package broadly with `except NexsciRVError` or handle a specific failure
narrowly (for example, retrying after an `AuthExpired`). The errors carry
descriptive messages and map to recoverable situations — a bad credential, an
unsupported query on a given archive, or a server-side problem — rather than
generic Python exceptions.

All exceptions raised by `nexsci-rv` derive from `NexsciRVError`. Catch broadly
for "anything from this package," or narrowly for a specific failure mode.

```
NexsciRVError
├── ConfigError
├── AuthError
│   ├── LoginFailed
│   ├── AuthExpired
│   └── NotAuthenticated
├── QueryError
│   ├── UnknownDataLevel
│   ├── UnknownColumn
│   ├── NotApplicable
│   └── TapServerError
├── DownloadError
├── FileUnavailable
└── AsyncJobError
```

```{eval-rst}
.. automodule:: nexsci_rv.exceptions
   :members:
   :show-inheritance:
```

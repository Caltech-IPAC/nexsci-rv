# Configuration

Most readers can skip this page. The defaults work for typical interactive use.
Come here only if you need to change a timeout or adjust download behaviour —
for example, to increase the server timeout for a slow connection you can pass
`NEIDArchive(timeout=120)`, or hand the archive a `Conf` carrying several
settings at once: `NEIDArchive(conf=Conf(timeout=120, download_workers=8))`.
`Conf` is immutable, so you construct one rather than mutating it. The reference
below documents every available setting.

```{eval-rst}
.. autoclass:: nexsci_rv.config.Conf
   :members:
   :show-inheritance:

.. autodata:: nexsci_rv.config.conf
   :no-value:
```

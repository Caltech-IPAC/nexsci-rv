# Archives

{py:class}`~nexsci_rv.NEIDArchive` and {py:class}`~nexsci_rv.EXPRESArchive`
are the two classes you will use directly. Instantiate one, call a `query_*`
method to search the archive, and optionally call `download` on the result.
Every query returns an {py:class}`astropy.table.Table`.

For guidance on which query method to reach for, see
{doc}`../concepts/choosing-a-query`. For a description of each archive's data
products and access rules, see {doc}`../archives/neid` and
{doc}`../archives/expres`.

`BaseArchive` (below) is the shared abstract base class both archives inherit
from. Most users never instantiate it directly; it is documented here as the
authoritative reference for inherited behaviour.

## NEIDArchive

```{eval-rst}
.. autoclass:: nexsci_rv.NEIDArchive
   :members:
   :show-inheritance:
   :member-order: bysource
```

## EXPRESArchive

```{eval-rst}
.. autoclass:: nexsci_rv.EXPRESArchive
   :members:
   :show-inheritance:
   :member-order: bysource
```

## BaseArchive

```{eval-rst}
.. autoclass:: nexsci_rv.BaseArchive
   :members:
   :show-inheritance:
   :member-order: bysource
```

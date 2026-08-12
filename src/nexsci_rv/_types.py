"""Internal type aliases.

Only types used across module boundaries belong here; module-local aliases
should stay close to where they're used.
"""

from __future__ import annotations

from typing import TypeAlias

# Date range used by query_datetime — open-ended on either side is allowed
# (use ``None`` to mean "no constraint on that side").
from ._adql_utils import DateInput

DateRange: TypeAlias = "tuple[DateInput | None, DateInput | None]"


__all__ = ["DateInput", "DateRange"]

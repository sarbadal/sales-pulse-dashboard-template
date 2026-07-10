from __future__ import annotations

from datetime import date
from typing import TypeAlias

import pandas as pd

RegionRawInput: TypeAlias = str | list[str] | tuple[str, ...] | None
DateRange: TypeAlias = tuple[date | None, date | None]
DataFrameTriplet: TypeAlias = tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]

"""Cohort filters used by Chapter 1 reporting."""

from __future__ import annotations

import pandas as pd


def exclude_current_event_rows(df: pd.DataFrame, column: str = "DaysFromCurrentToEvent") -> pd.DataFrame:
    """Return rows where the current sample is not at the event date."""
    if column not in df.columns:
        raise KeyError(f"{column} not found")
    return df[df[column].ne(0)].copy()


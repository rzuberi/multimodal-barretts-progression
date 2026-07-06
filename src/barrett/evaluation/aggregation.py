"""Prediction aggregation for patient, biopsy, and sample reporting."""

from __future__ import annotations

import pandas as pd


def aggregate_predictions(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """Aggregate prediction rows to patient, biopsy, or sample level."""
    if level == "sample":
        out = df.copy()
        out["unit_id"] = out["sample_key"]
        return out
    if level.startswith("patient_"):
        key = "patient_id"
    elif level.startswith("biopsy_"):
        key = "biopsy_id"
    else:
        raise ValueError(level)
    agg = "max" if level.endswith("_max") else "mean"
    grouped = df.dropna(subset=[key]).groupby(key, dropna=False)
    y_prob = grouped["y_prob"].max() if agg == "max" else grouped["y_prob"].mean()
    out = pd.DataFrame(
        {
            "unit_id": y_prob.index.astype(str),
            "y_prob": y_prob.values,
            "y_true": grouped["y_true"].max().values,
            "patient_id": grouped["patient_id"].first().values,
            "fold": grouped["fold"].agg(lambda x: ",".join(sorted(set(x.dropna().astype(str))))).values,
        }
    )
    return out


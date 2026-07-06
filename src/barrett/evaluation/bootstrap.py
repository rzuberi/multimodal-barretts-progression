"""Bootstrap confidence intervals for small summary tables."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from barrett.evaluation.metrics import (
    average_precision_binary,
    confusion_counts,
    roc_auc_binary,
    safe_div,
)


def bootstrap_cis(df: pd.DataFrame, n_boot: int, seed: int) -> dict[str, float]:
    """Bootstrap selected binary metrics by resampling rows."""
    metrics = ["roc_auc", "auprc", "sensitivity", "specificity", "ppv", "npv"]
    out = {f"{m}_ci_low": math.nan for m in metrics}
    out.update({f"{m}_ci_high": math.nan for m in metrics})
    if n_boot <= 0 or df.empty:
        return out
    rng = np.random.default_rng(seed)
    values = {m: [] for m in metrics}
    idx = np.arange(len(df))
    y_all = pd.to_numeric(df["y_true"], errors="coerce").to_numpy(dtype=float)
    p_all = pd.to_numeric(df["y_prob"], errors="coerce").to_numpy(dtype=float)
    for _ in range(n_boot):
        sample_idx = rng.choice(idx, size=len(idx), replace=True)
        y_true = y_all[sample_idx]
        y_prob = p_all[sample_idx]
        mask = np.isfinite(y_true) & np.isfinite(y_prob)
        y_true = y_true[mask].astype(int)
        y_prob = y_prob[mask]
        if len(y_true) == 0 or len(np.unique(y_true)) < 2:
            continue
        y_pred = (y_prob >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_counts(y_true, y_pred)
        row = {
            "roc_auc": roc_auc_binary(y_true, y_prob),
            "auprc": average_precision_binary(y_true, y_prob),
            "sensitivity": safe_div(tp, tp + fn),
            "specificity": safe_div(tn, tn + fp),
            "ppv": safe_div(tp, tp + fp),
            "npv": safe_div(tn, tn + fn),
        }
        for metric, value in row.items():
            if np.isfinite(value):
                values[metric].append(value)
    for metric, vals in values.items():
        if vals:
            out[f"{metric}_ci_low"] = float(np.percentile(vals, 2.5))
            out[f"{metric}_ci_high"] = float(np.percentile(vals, 97.5))
    return out


"""Fixed operating point threshold helpers."""

from __future__ import annotations

import math

import numpy as np


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else math.nan


def _confusion_counts(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[int, int, int, int]:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tn, fp, fn, tp


def fixed_operating_points(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """Report sensitivity/specificity at 90% and 95% opposing operating points."""
    thresholds = np.unique(np.r_[0.0, y_prob, 1.0])
    rows = []
    for threshold in thresholds:
        pred = (y_prob >= threshold).astype(int)
        tn, fp, fn, tp = _confusion_counts(y_true, pred)
        sens = _safe_div(tp, tp + fn)
        spec = _safe_div(tn, tn + fp)
        rows.append((threshold, sens, spec))
    out: dict[str, float] = {}
    for target in (0.90, 0.95):
        valid = [r for r in rows if not math.isnan(r[2]) and r[2] >= target]
        if valid:
            threshold, sens, _ = max(valid, key=lambda r: (r[1], -r[0]))
            out[f"sensitivity_at_{int(target * 100)}_specificity"] = sens
            out[f"threshold_at_{int(target * 100)}_specificity"] = threshold
        else:
            out[f"sensitivity_at_{int(target * 100)}_specificity"] = math.nan
            out[f"threshold_at_{int(target * 100)}_specificity"] = math.nan
        valid = [r for r in rows if not math.isnan(r[1]) and r[1] >= target]
        if valid:
            threshold, _, spec = max(valid, key=lambda r: (r[2], r[0]))
            out[f"specificity_at_{int(target * 100)}_sensitivity"] = spec
            out[f"threshold_at_{int(target * 100)}_sensitivity"] = threshold
        else:
            out[f"specificity_at_{int(target * 100)}_sensitivity"] = math.nan
            out[f"threshold_at_{int(target * 100)}_sensitivity"] = math.nan
    return out


"""Binary clinical detection metrics without heavy dependencies."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from barrett.evaluation.calibration import expected_calibration_error
from barrett.evaluation.thresholds import fixed_operating_points

METRIC_ORDER = [
    "roc_auc",
    "auprc",
    "accuracy",
    "balanced_accuracy",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
    "tp",
    "fp",
    "tn",
    "fn",
    "progressors_detected",
    "progressors_missed",
    "false_positives_per_detected_progressor",
    "brier_score",
    "ece",
    "sensitivity_at_90_specificity",
    "threshold_at_90_specificity",
    "sensitivity_at_95_specificity",
    "threshold_at_95_specificity",
    "specificity_at_90_sensitivity",
    "threshold_at_90_sensitivity",
    "specificity_at_95_sensitivity",
    "threshold_at_95_sensitivity",
    "threshold_used",
    "n_units",
    "n_patients",
    "n_positive_patients",
    "n_negative_patients",
]


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else math.nan


def confusion_counts(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[int, int, int, int]:
    """Return TN, FP, FN, TP for binary labels."""
    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tn, fp, fn, tp


def roc_auc_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    pos = y_true == 1
    neg = y_true == 0
    n_pos = int(pos.sum())
    n_neg = int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return math.nan
    order = np.argsort(y_prob)
    ranks = np.empty(len(y_prob), dtype=float)
    sorted_scores = y_prob[order]
    start = 0
    while start < len(y_prob):
        end = start + 1
        while end < len(y_prob) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        avg_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = avg_rank
        start = end
    rank_sum_pos = ranks[pos].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def average_precision_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    pos_total = int((y_true == 1).sum())
    if pos_total == 0:
        return math.nan
    order = np.argsort(-y_prob, kind="mergesort")
    y_sorted = y_true[order]
    tp_cum = np.cumsum(y_sorted == 1)
    ranks = np.arange(1, len(y_sorted) + 1)
    precision = tp_cum / ranks
    return float(precision[y_sorted == 1].sum() / pos_total)


def compute_metrics(
    y_true_in: Iterable[float],
    y_prob_in: Iterable[float],
    threshold: float = 0.5,
) -> dict[str, float]:
    """Compute binary clinical metrics at default and fixed operating thresholds."""
    y_true = np.asarray(list(y_true_in), dtype=float)
    y_prob = np.asarray(list(y_prob_in), dtype=float)
    mask = np.isfinite(y_true) & np.isfinite(y_prob)
    y_true = y_true[mask].astype(int)
    y_prob = y_prob[mask]
    y_pred = (y_prob >= threshold).astype(int)
    out: dict[str, float] = {k: math.nan for k in METRIC_ORDER}
    out["threshold_used"] = threshold
    out["n_units"] = int(len(y_true))
    if len(y_true) == 0 or len(np.unique(y_true)) < 2:
        return out
    tn, fp, fn, tp = confusion_counts(y_true, y_pred)
    sensitivity = safe_div(tp, tp + fn)
    specificity = safe_div(tn, tn + fp)
    ppv = safe_div(tp, tp + fp)
    npv = safe_div(tn, tn + fn)
    out.update(
        {
            "roc_auc": roc_auc_binary(y_true, y_prob),
            "auprc": average_precision_binary(y_true, y_prob),
            "accuracy": safe_div(tp + tn, tp + tn + fp + fn),
            "balanced_accuracy": np.nanmean([sensitivity, specificity]),
            "sensitivity": sensitivity,
            "specificity": specificity,
            "ppv": ppv,
            "npv": npv,
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
            "progressors_detected": int(tp),
            "progressors_missed": int(fn),
            "false_positives_per_detected_progressor": safe_div(fp, tp),
            "brier_score": float(np.mean((y_prob - y_true) ** 2)),
            "ece": expected_calibration_error(y_true, y_prob),
        }
    )
    out.update(fixed_operating_points(y_true, y_prob))
    return out


"""Patient-level paired model comparisons via shared-index bootstrap.

Given two models' out-of-fold patient-level predictions on the SAME patients and
labels, estimate the difference in discrimination/calibration and a percentile
bootstrap CI using one shared patient resample per replicate. This moves from
separate per-model CIs to a direct paired answer about whether one model beats
another. No model training; inputs are saved OOF predictions.

Brier deltas are oriented as (a - b); lower Brier is better, so a NEGATIVE delta
Brier favours model ``a``. AUPRC/AUC deltas favour ``a`` when POSITIVE.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SCORE_COLS = ["patient_id", "y_true", "y_prob"]


def align_pair(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Inner-align two patient-level score frames; fail if patients/labels differ."""
    for name, df in (("a", a), ("b", b)):
        if not set(SCORE_COLS) <= set(df.columns):
            raise ValueError(f"model {name} missing columns {SCORE_COLS}")
        if df["patient_id"].duplicated().any():
            raise ValueError(f"model {name} has duplicate patient_id rows")
    m = a[SCORE_COLS].merge(b[SCORE_COLS], on="patient_id", how="outer",
                            suffixes=("_a", "_b"), validate="one_to_one", indicator=True)
    if (m["_merge"] != "both").any():
        only_a = int((m["_merge"] == "left_only").sum())
        only_b = int((m["_merge"] == "right_only").sum())
        raise ValueError(f"patient sets differ: only_a={only_a} only_b={only_b}")
    if (m["y_true_a"].astype(int) != m["y_true_b"].astype(int)).any():
        raise ValueError("labels disagree between the two models on shared patients")
    return m.rename(columns={"y_true_a": "y_true"}).drop(columns=["y_true_b", "_merge"])


def _metrics(y, p):
    from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    if len(np.unique(y)) < 2:
        return None
    return {
        "auprc": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
    }


def paired_bootstrap(aligned: pd.DataFrame, n_boot: int = 5000, seed: int = 17) -> dict:
    """Shared-index patient bootstrap of (a - b) deltas with percentile 95% CIs."""
    y = aligned["y_true"].to_numpy(dtype=int)
    pa = aligned["y_prob_a"].to_numpy(dtype=float)
    pb = aligned["y_prob_b"].to_numpy(dtype=float)
    n = len(y)
    point_a, point_b = _metrics(y, pa), _metrics(y, pb)
    if point_a is None or point_b is None:
        raise ValueError("cannot compute metrics: only one label class present")
    keys = ("auprc", "roc_auc", "brier")
    point = {k: point_a[k] - point_b[k] for k in keys}

    rng = np.random.default_rng(seed)
    draws = {k: [] for k in keys}
    valid = 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)  # one shared index for both models
        ma, mb = _metrics(y[idx], pa[idx]), _metrics(y[idx], pb[idx])
        if ma is None or mb is None:
            continue
        valid += 1
        for k in keys:
            draws[k].append(ma[k] - mb[k])

    out = {
        "n_patients": int(n),
        "n_positive": int((y == 1).sum()),
        "n_negative": int((y == 0).sum()),
        "n_boot": int(n_boot),
        "valid_fraction": (valid / n_boot) if n_boot else 0.0,
    }
    for k in keys:
        arr = np.asarray(draws[k], dtype=float)
        out[f"delta_{k}"] = point[k]
        if arr.size:
            out[f"delta_{k}_ci_low"] = float(np.percentile(arr, 2.5))
            out[f"delta_{k}_ci_high"] = float(np.percentile(arr, 97.5))
            # two-sided bootstrap sign probability (labelled; not a frequentist p-value)
            frac_le0 = float((arr <= 0).mean())
            out[f"delta_{k}_sign_prob"] = 2 * min(frac_le0, 1 - frac_le0)
        else:
            out[f"delta_{k}_ci_low"] = out[f"delta_{k}_ci_high"] = out[f"delta_{k}_sign_prob"] = float("nan")
    return out


def compare(a: pd.DataFrame, b: pd.DataFrame, n_boot: int = 5000, seed: int = 17) -> dict:
    return paired_bootstrap(align_pair(a, b), n_boot=n_boot, seed=seed)

"""Cross-fitted (validation-derived) thresholding.

The whole point of this module: a decision threshold (and, optionally, a
probability calibrator) is chosen on *inner-validation* patients only, then
applied UNCHANGED to the matching outer-test patients. Outer-test labels never
touch threshold selection or calibrator fitting, so pooled outer-test confusion
is a fair estimate of the operating point picked on validation.

Inputs are per-outer-fold pairs of patient-level prediction tables. Each table
is anything with ``patient_id``, ``y_true`` (0/1) and ``y_prob`` columns
(pandas DataFrame, or a list of dict-likes / row-tuples via ``pandas``).

Primary clinical criterion (prespecified): ``target_specificity`` at 0.90,
maximising sensitivity subject to it, selected on validation.

Calibration note: ``fit_apply_calibration`` fits on validation and applies to
test. Callers MUST report raw and calibrated metrics separately -- do not
overwrite raw probabilities with calibrated ones in the same column.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

CRITERIA = ("default_0p5", "target_specificity", "target_sensitivity")


def _cols(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    y = df["y_true"].to_numpy().astype(int)
    p = df["y_prob"].to_numpy().astype(float)
    return y, p


def _confusion(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[int, int, int, int]:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tp, fp, tn, fn


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else math.nan


@dataclass
class ThresholdChoice:
    threshold: float
    criterion: str
    target: float | None
    fallback: bool
    achieved: float  # achieved spec (target_specificity) / sens (target_sensitivity) / nan


def select_threshold(val_df: pd.DataFrame, criterion: str, target: float = 0.90) -> ThresholdChoice:
    """Choose a threshold on VALIDATION patients only.

    Candidate thresholds are the observed probabilities plus 0/1 endpoints, and
    prediction is ``y_prob >= threshold``. Deterministic tie-breaking.

    - ``default_0p5``: returns 0.5, ignores target.
    - ``target_specificity``: highest sensitivity among thresholds with
      specificity >= target (ties broken toward higher threshold, i.e. higher
      spec). Fallback if unachievable: the threshold giving max achievable
      specificity (most conservative), fallback=True.
    - ``target_sensitivity``: symmetric on sensitivity.
    """
    if criterion == "default_0p5":
        return ThresholdChoice(0.5, criterion, None, fallback=False, achieved=math.nan)
    if criterion not in ("target_specificity", "target_sensitivity"):
        raise ValueError(f"unknown criterion {criterion!r}; expected one of {CRITERIA}")

    y, p = _cols(val_df)
    cand = np.unique(np.concatenate([[0.0, 1.0], p]))
    rows = []  # (threshold, sens, spec)
    for t in cand:
        tp, fp, tn, fn = _confusion(y, (p >= t).astype(int))
        rows.append((float(t), _safe_div(tp, tp + fn), _safe_div(tn, tn + fp)))

    if criterion == "target_specificity":
        constrained, maximised = 2, 1  # index of spec (constraint), sens (objective)
    else:
        constrained, maximised = 1, 2

    achievable = [r for r in rows if not math.isnan(r[constrained]) and r[constrained] >= target]
    if achievable:
        # maximise objective; tie-break toward higher threshold (more conservative)
        best = max(achievable, key=lambda r: (r[maximised], r[0]))
        return ThresholdChoice(best[0], criterion, target, fallback=False, achieved=best[constrained])

    # Fallback: no threshold reaches target -> pick max achievable constrained
    # metric, highest threshold among ties (most conservative). If the metric is
    # nan everywhere (degenerate: constrained class absent in validation), fall
    # back to the most conservative threshold 1.0.
    valid = [r for r in rows if not math.isnan(r[constrained])]
    if not valid:
        return ThresholdChoice(1.0, criterion, target, fallback=True, achieved=math.nan)
    best = max(valid, key=lambda r: (r[constrained], r[0]))
    return ThresholdChoice(best[0], criterion, target, fallback=True, achieved=best[constrained])


@dataclass
class CrossFittedResult:
    criterion: str
    target: float | None
    tp: int
    fp: int
    tn: int
    fn: int
    sensitivity: float
    specificity: float
    ppv: float
    npv: float
    thresholds: list[float] = field(default_factory=list)
    fallbacks: list[bool] = field(default_factory=list)
    n_folds: int = 0

    def as_dict(self) -> dict:
        return {
            "criterion": self.criterion,
            "target": self.target,
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "ppv": self.ppv,
            "npv": self.npv,
            "thresholds": list(self.thresholds),
            "fallbacks": list(self.fallbacks),
            "n_folds": self.n_folds,
        }


def cross_fitted_confusion(
    folds: list[tuple[pd.DataFrame, pd.DataFrame]],
    criterion: str = "target_specificity",
    target: float = 0.90,
) -> CrossFittedResult:
    """Select threshold per fold on validation, apply to outer test, pool counts.

    ``folds`` is a list of ``(val_df, test_df)`` per outer fold. The threshold
    is chosen from ``val_df`` alone and applied unchanged to ``test_df``.
    """
    TP = FP = TN = FN = 0
    thresholds: list[float] = []
    fallbacks: list[bool] = []
    for val_df, test_df in folds:
        choice = select_threshold(val_df, criterion, target)
        y, p = _cols(test_df)
        tp, fp, tn, fn = _confusion(y, (p >= choice.threshold).astype(int))
        TP += tp
        FP += fp
        TN += tn
        FN += fn
        thresholds.append(choice.threshold)
        fallbacks.append(choice.fallback)

    return CrossFittedResult(
        criterion=criterion,
        target=None if criterion == "default_0p5" else target,
        tp=TP,
        fp=FP,
        tn=TN,
        fn=FN,
        sensitivity=_safe_div(TP, TP + FN),
        specificity=_safe_div(TN, TN + FP),
        ppv=_safe_div(TP, TP + FP),
        npv=_safe_div(TN, TN + FN),
        thresholds=thresholds,
        fallbacks=fallbacks,
        n_folds=len(folds),
    )


def fit_apply_calibration(
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    method: str = "isotonic",
) -> np.ndarray:
    """Fit a calibrator on VALIDATION only, return calibrated TEST probabilities.

    ``method`` is ``'isotonic'`` or ``'platt'`` (logistic). Test labels are
    never used. Keep the returned calibrated probs SEPARATE from raw probs when
    reporting -- the caller owns raw vs calibrated Brier/calibration comparison.
    """
    yv, pv = _cols(val_df)
    _, pt = _cols(test_df)
    if method == "isotonic":
        from sklearn.isotonic import IsotonicRegression

        cal = IsotonicRegression(out_of_bounds="clip")
        cal.fit(pv, yv)
        return np.asarray(cal.predict(pt), dtype=float)
    if method == "platt":
        from sklearn.linear_model import LogisticRegression

        cal = LogisticRegression()
        cal.fit(pv.reshape(-1, 1), yv)
        return np.asarray(cal.predict_proba(pt.reshape(-1, 1))[:, 1], dtype=float)
    raise ValueError(f"unknown method {method!r}; expected 'isotonic' or 'platt'")

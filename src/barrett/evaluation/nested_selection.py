"""Leakage-safe nested candidate selection.

Operates on abstract inner-validation prediction frames, never real data, so it
can be unit-tested with synthetic DataFrames. Inner-validation predictions have
columns: outer_fold, inner_fold, configuration_id, patient_id, y_true, y_prob.

Selection follows Phase 4 of the final-analysis foundation plan:
pool inner held-out predictions per outer fold, aggregate to patient level with
patient_max, then rank candidates by AUPRC desc, ROC AUC desc, Brier asc, and a
deterministic configuration_id tiebreak.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "outer_fold",
    "inner_fold",
    "configuration_id",
    "patient_id",
    "y_true",
    "y_prob",
]


# ponytail: lazy sklearn import per plan; also keeps import cost off module load.
def _auprc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    import sklearn.metrics as skm

    return float(skm.average_precision_score(y_true, y_prob))


def _roc_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    import sklearn.metrics as skm

    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(skm.roc_auc_score(y_true, y_prob))


def _brier(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    import sklearn.metrics as skm

    return float(skm.brier_score_loss(y_true, y_prob))


def make_inner_folds(patients, n_inner: int, seed: int) -> dict:
    """Assign outer-training patients to patient-disjoint inner folds.

    Deterministic for a given (patient set, n_inner, seed). Returns
    {patient_id: inner_fold_index}. Patients are sorted first so input order
    does not change the result.
    """
    unique = sorted(set(patients))
    if n_inner < 1:
        raise ValueError("n_inner must be >= 1")
    if len(unique) < n_inner:
        raise ValueError(
            f"cannot make {n_inner} inner folds from {len(unique)} patients"
        )
    order = np.random.default_rng(seed).permutation(len(unique))
    fold_of = np.empty(len(unique), dtype=int)
    fold_of[order] = np.arange(len(unique)) % n_inner
    return {unique[i]: int(fold_of[i]) for i in range(len(unique))}


def patient_max(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to one row per patient using the max y_prob (patient_max)."""
    idx = df.groupby("patient_id")["y_prob"].idxmax()
    return df.loc[idx].reset_index(drop=True)


def _check_leakage(fold_df: pd.DataFrame, outer_test_patients: set) -> None:
    leaked = set(fold_df["patient_id"]) & outer_test_patients
    if leaked:
        raise ValueError(
            f"outer-test patients present in inner predictions: {sorted(leaked)}"
        )
    # A patient may appear once per candidate, but only in one inner held-out
    # fold. Check per configuration to allow the same patient across candidates.
    for cfg, g in fold_df.groupby("configuration_id"):
        dup = g.groupby("patient_id")["inner_fold"].nunique()
        bad = dup[dup > 1]
        if len(bad):
            raise ValueError(
                f"patient(s) in >1 inner fold for config {cfg!r}: "
                f"{sorted(bad.index)}"
            )


def select_per_outer_fold(inner_preds: pd.DataFrame, outer_test_patients=None):
    """Select the winning configuration per outer fold from inner predictions.

    Parameters
    ----------
    inner_preds : DataFrame with REQUIRED_COLUMNS.
    outer_test_patients : mapping {outer_fold: set(patient_id)} or a single set
        applied to every outer fold. Used only for the fail-closed leakage
        check; pass the outer-test patients so selection can never see them.

    Returns
    -------
    winners : dict {outer_fold: configuration_id}
    leaderboard : DataFrame with every candidate's metrics, sorted, one block
        per outer fold. Columns: outer_fold, configuration_id, auprc, roc_auc,
        brier, n_patients, rank.
    """
    missing = set(REQUIRED_COLUMNS) - set(inner_preds.columns)
    if missing:
        raise ValueError(f"inner_preds missing columns: {sorted(missing)}")

    winners: dict = {}
    rows = []
    for outer_fold, fold_df in inner_preds.groupby("outer_fold"):
        test_set = _resolve_test_set(outer_test_patients, outer_fold)
        _check_leakage(fold_df, test_set)

        cand_metrics = []
        for cfg, cand_df in fold_df.groupby("configuration_id"):
            agg = patient_max(cand_df)
            yt = agg["y_true"].to_numpy()
            yp = agg["y_prob"].to_numpy()
            cand_metrics.append(
                {
                    "outer_fold": outer_fold,
                    "configuration_id": cfg,
                    "auprc": _auprc(yt, yp),
                    "roc_auc": _roc_auc(yt, yp),
                    "brier": _brier(yt, yp),
                    "n_patients": int(len(agg)),
                }
            )

        board = pd.DataFrame(cand_metrics)
        # AUPRC desc, ROC AUC desc, Brier asc, configuration_id asc (tiebreak).
        board = board.sort_values(
            by=["auprc", "roc_auc", "brier", "configuration_id"],
            ascending=[False, False, True, True],
            kind="mergesort",
        ).reset_index(drop=True)
        board["rank"] = np.arange(1, len(board) + 1)
        winners[outer_fold] = board.loc[0, "configuration_id"]
        rows.append(board)

    leaderboard = pd.concat(rows, ignore_index=True)
    return winners, leaderboard


def _resolve_test_set(outer_test_patients, outer_fold) -> set:
    if outer_test_patients is None:
        return set()
    if isinstance(outer_test_patients, dict):
        return set(outer_test_patients.get(outer_fold, set()))
    return set(outer_test_patients)

"""Immutable patient-level outer split release (Phase 3).

Five patient-disjoint outer folds. Patient labels are the max endpoint across the
patient's eligible rows (consistent with patient_max reporting). One deterministic
seed, stratified where feasible. All of a patient's samples go to one fold.
"""

from __future__ import annotations

import pandas as pd

from barrett.labels.endpoints import LGD2_ENDPOINT

N_FOLDS = 5
SEED = 20260713


def patient_labels(manifest: pd.DataFrame) -> pd.DataFrame:
    """Patient-level label = max endpoint across the patient's eligible rows."""
    ep = pd.to_numeric(manifest[LGD2_ENDPOINT], errors="coerce")
    lab = ep.groupby(manifest["patient_id"]).max()
    return lab.rename("patient_label").reset_index()


def make_patient_folds(labels: pd.DataFrame, n_folds: int = N_FOLDS, seed: int = SEED) -> pd.DataFrame:
    """Assign each patient to exactly one outer fold (stratified, deterministic)."""
    from sklearn.model_selection import StratifiedKFold

    df = labels.sort_values("patient_id").reset_index(drop=True)
    y = df["patient_label"].fillna(0).astype(int).to_numpy()
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    df["outer_fold"] = -1
    for fold, (_, test_idx) in enumerate(skf.split(df.index.to_numpy(), y), start=1):
        df.loc[df.index[test_idx], "outer_fold"] = fold
    return df[["patient_id", "patient_label", "outer_fold"]]


def assign_rows_to_folds(manifest: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    out = manifest.merge(folds[["patient_id", "outer_fold"]], on="patient_id", how="left", validate="many_to_one")
    return out


def validate_splits(rows_with_fold: pd.DataFrame, folds: pd.DataFrame, n_folds: int = N_FOLDS) -> list[str]:
    """Fail-closed checks. Returns problems (empty = OK)."""
    problems: list[str] = []
    if folds["patient_id"].duplicated().any():
        problems.append("a patient is assigned to more than one outer fold")
    present = sorted(folds["outer_fold"].unique())
    if present != list(range(1, n_folds + 1)):
        problems.append(f"expected folds {list(range(1, n_folds + 1))}, found {present}")
    # every row got a fold
    if rows_with_fold["outer_fold"].isna().any():
        problems.append(f"{int(rows_with_fold['outer_fold'].isna().sum())} rows without a fold assignment")
    # class presence per fold (patient level)
    for fold in present:
        labs = set(folds.loc[folds["outer_fold"] == fold, "patient_label"].fillna(0).astype(int))
        if labs != {0, 1}:
            problems.append(f"fold {fold} missing a class (patient labels present: {sorted(labs)})")
    # patient disjointness across folds at the row level
    cross = rows_with_fold.groupby("patient_id")["outer_fold"].nunique()
    if (cross > 1).any():
        problems.append(f"{int((cross > 1).sum())} patients span multiple outer folds at row level")
    return problems


def split_audit(folds: pd.DataFrame, rows_with_fold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fold in sorted(folds["outer_fold"].unique()):
        fp = folds[folds["outer_fold"] == fold]
        fr = rows_with_fold[rows_with_fold["outer_fold"] == fold]
        rows.append({
            "outer_fold": int(fold),
            "patients": int(len(fp)),
            "positive_patients": int((fp["patient_label"] == 1).sum()),
            "negative_patients": int((fp["patient_label"] == 0).sum()),
            "sample_rows": int(len(fr)),
        })
    return pd.DataFrame(rows)

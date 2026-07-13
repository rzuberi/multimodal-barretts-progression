"""Patient-disjoint inner folds for nested selection."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import StratifiedKFold


def make_inner_assignments(frame: pd.DataFrame, n_folds: int, seed: int) -> pd.DataFrame:
    patients = (
        frame.groupby("patient_id", as_index=False)["y_progressor"]
        .max()
        .sort_values("patient_id")
        .reset_index(drop=True)
    )
    splitter = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    patients["inner_fold"] = -1
    for fold, (_, validation_index) in enumerate(
        splitter.split(patients["patient_id"], patients["y_progressor"]), start=1
    ):
        patients.loc[validation_index, "inner_fold"] = fold
    if patients["inner_fold"].lt(1).any():
        raise ValueError("incomplete inner-fold assignment")
    return patients[["patient_id", "y_progressor", "inner_fold"]]


def split_inner(frame: pd.DataFrame, assignments: pd.DataFrame, fold: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    mapping = assignments.set_index("patient_id")["inner_fold"]
    work = frame.copy()
    work["inner_fold"] = work["patient_id"].map(mapping)
    if work["inner_fold"].isna().any():
        raise ValueError("rows missing inner-fold assignment")
    train = work[work["inner_fold"].ne(fold)].drop(columns="inner_fold")
    validation = work[work["inner_fold"].eq(fold)].drop(columns="inner_fold")
    overlap = set(train["patient_id"]) & set(validation["patient_id"])
    if overlap:
        raise ValueError(f"inner patient leakage: {sorted(overlap)}")
    return train, validation

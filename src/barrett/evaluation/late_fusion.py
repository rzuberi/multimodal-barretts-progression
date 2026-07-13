"""Reproducible LGD2+ late fusion of CNV and image out-of-fold predictions.

Minimal, path-independent migration of the external late-fusion logic. Reads
saved OOF prediction files (campaign schema), validates paired keys and
patient-disjoint folds, and produces two late-fusion scores per held-out fold:

- ``mean``: simple probability average of CNV and image OOF scores.
- ``stack_logit``: fold-pure logistic stacking. For held-out fold ``k`` the
  logistic regression is fitted only on the other folds of the same
  condition/repeat, so the test fold never trains its own stacker.

The unimodal ``cnv_only`` and ``img_only`` baselines are also emitted for
provenance; downstream manifest rows keep only ``mean`` and ``stack_logit``.

scikit-learn is imported lazily so the rest of the evaluation package stays
importable in environments without it.
"""

from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd

JOIN_KEYS = ["condition", "rep", "fold", "patient_id", "sample_id"]
REQUIRED_COLS = set(JOIN_KEYS) | {"y_true", "y_prob"}
LATE_FUSION_METHODS = ("mean", "stack_logit")


def _read_glob(patterns: list[str]) -> pd.DataFrame:
    files: list[str] = []
    for pat in patterns:
        files.extend(sorted(glob.glob(pat)))
    if not files:
        raise FileNotFoundError(f"No prediction files matched: {patterns}")
    frames = [pd.read_csv(f, low_memory=False) for f in sorted(set(files))]
    return pd.concat(frames, ignore_index=True)


def _validate_side(df: pd.DataFrame, name: str) -> None:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"{name} predictions missing required columns: {sorted(missing)}")


def _norm_keys(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for k in ("patient_id", "sample_id", "condition"):
        df[k] = df[k].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    df["rep"] = pd.to_numeric(df["rep"], errors="coerce").astype("Int64")
    df["fold"] = pd.to_numeric(df["fold"], errors="coerce").astype("Int64")
    df["y_true"] = pd.to_numeric(df["y_true"], errors="coerce").astype("Int64")
    df["y_prob"] = pd.to_numeric(df["y_prob"], errors="coerce")
    return df


def merge_oof(cnv: pd.DataFrame, image: pd.DataFrame) -> pd.DataFrame:
    """Inner-join CNV and image OOF predictions on the paired keys, validating labels."""
    _validate_side(cnv, "CNV")
    _validate_side(image, "image")
    cnv = _norm_keys(cnv).rename(columns={"y_prob": "cnv_prob"})
    image = _norm_keys(image).rename(columns={"y_prob": "img_prob"})
    image["image_model"] = image.get("model_name", "image")
    merged = cnv[JOIN_KEYS + ["y_true", "cnv_prob"]].merge(
        image[JOIN_KEYS + ["y_true", "img_prob", "image_model"]],
        on=JOIN_KEYS, how="inner", suffixes=("_cnv", "_img"),
    )
    if merged.empty:
        raise ValueError("No overlap between CNV and image predictions on join keys")
    mism = int((merged["y_true_cnv"] != merged["y_true_img"]).sum())
    if mism:
        raise ValueError(f"{mism} label disagreements between CNV and image on joined rows")
    merged["y_true"] = merged["y_true_cnv"].astype(int)
    merged = merged.drop(columns=["y_true_cnv", "y_true_img"])
    _assert_patient_disjoint_folds(merged)
    return merged


def _assert_patient_disjoint_folds(df: pd.DataFrame) -> None:
    per_cond = df.groupby(["condition", "rep"])
    for (cond, rep), g in per_cond:
        multi = g.groupby("patient_id")["fold"].nunique()
        bad = multi[multi > 1]
        if len(bad):
            raise ValueError(
                f"{len(bad)} patients cross held-out folds in condition={cond} rep={rep}: "
                f"{list(bad.index[:5])}"
            )


def _fold_pure_stack(train: pd.DataFrame, test: pd.DataFrame, seed: int) -> tuple[np.ndarray, str]:
    if train["y_true"].nunique() < 2:
        return 0.5 * (test["cnv_prob"].values + test["img_prob"].values), "fallback_mean_single_class_train"
    from sklearn.linear_model import LogisticRegression  # lazy: keep package usable without sklearn

    model = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=seed)
    model.fit(train[["cnv_prob", "img_prob"]].values, train["y_true"].values)
    return model.predict_proba(test[["cnv_prob", "img_prob"]].values)[:, 1], "ok"


def compute_late_fusion(merged: pd.DataFrame, seed: int = 20260304) -> pd.DataFrame:
    """Return standardized long predictions for all methods (fold-pure stacking)."""
    rows = []
    base = ["condition", "rep", "fold", "patient_id", "sample_id", "y_true", "image_model"]
    for (cond, rep, fold), test in merged.groupby(["condition", "rep", "fold"], sort=True):
        train = merged[(merged["condition"] == cond) & (merged["rep"] == rep) & (merged["fold"] != fold)]
        scores = {
            "cnv_only": (test["cnv_prob"].values, "ok"),
            "img_only": (test["img_prob"].values, "ok"),
            "mean": (0.5 * (test["cnv_prob"].values + test["img_prob"].values), "ok"),
            "stack_logit": _fold_pure_stack(train, test, seed),
        }
        for method, (prob, note) in scores.items():
            out = test[base].copy()
            out["fusion_method"] = method
            out["y_prob"] = prob
            out["stack_note"] = note
            rows.append(out)
    return pd.concat(rows, ignore_index=True)


def _reject_repo_output(out_dir: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out = out_dir.resolve()
    inside = repo_root == out or repo_root in out.parents
    tempish = any(tok in out.parts for tok in ("tmp", "test", "pytest", "_norm"))
    if inside and not tempish:
        raise ValueError(f"Refusing to write late-fusion output inside the clean repo: {out}")


def run_late_fusion(cnv_patterns: list[str], image_patterns: list[str],
                    out_dir: Path, seed: int = 20260304) -> Path:
    """End-to-end: read OOF preds, fuse, write standardized predictions externally."""
    out_dir = Path(out_dir)
    _reject_repo_output(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    merged = merge_oof(_read_glob(cnv_patterns), _read_glob(image_patterns))
    preds = compute_late_fusion(merged, seed=seed)
    dest = out_dir / "cv_predictions_late_fusion.csv"
    preds.to_csv(dest, index=False)
    return dest

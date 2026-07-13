"""Reproducible LGD2+ late fusion of CNV and image out-of-fold predictions.

Minimal, path-independent, fail-closed migration of the external late-fusion
logic. Reads saved OOF prediction files (campaign schema), enforces exact
CNV/image pairing per image model, validates patient-disjoint folds, and
produces two late-fusion scores per held-out fold:

- ``mean``: simple probability average of CNV and image OOF scores.
- ``stack_logit``: fold-pure logistic stacking. For held-out fold ``k`` the
  logistic regression is fitted only on the other folds of the same
  condition/repeat/image_model, so the test fold never trains its own stacker.

The unimodal ``cnv_only`` and ``img_only`` baselines are also emitted for
provenance; downstream manifest rows keep only ``mean`` and ``stack_logit``.

scikit-learn is imported lazily so the rest of the evaluation package stays
importable in environments without it. The mathematical definitions of ``mean``
and ``stack_logit`` are unchanged for valid single-image-model inputs, so
existing canonical outputs remain reproducible.
"""

from __future__ import annotations

import glob
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

PAIR_KEYS = ["condition", "rep", "fold", "patient_id", "sample_id"]
IMAGE_PAIR_KEYS = PAIR_KEYS + ["image_model"]
REQUIRED_COLS = set(PAIR_KEYS) | {"y_true", "y_prob"}
LATE_FUSION_METHODS = ("mean", "stack_logit")
STR_KEYS = ("condition", "patient_id", "sample_id")


def _read_glob(patterns: list[str]) -> pd.DataFrame:
    files: list[str] = []
    for pat in patterns:
        files.extend(sorted(glob.glob(pat)))
    if not files:
        raise FileNotFoundError(f"No prediction files matched: {patterns}")
    frames = [pd.read_csv(f, low_memory=False) for f in sorted(set(files))]
    return pd.concat(frames, ignore_index=True)


def _norm_and_validate(df: pd.DataFrame, name: str, *, is_image: bool) -> pd.DataFrame:
    """Normalize identifiers and fail closed on any integrity violation."""
    missing = REQUIRED_COLS - set(df.columns)
    if is_image and "image_model" not in df.columns and "model_name" not in df.columns:
        missing = missing | {"image_model|model_name"}
    if missing:
        raise ValueError(f"{name} predictions missing required columns: {sorted(missing)}")
    df = df.copy()
    if is_image and "image_model" not in df.columns:
        df["image_model"] = df["model_name"]

    # Integer-like keys: coerce; nulls become NA (not the string "nan").
    for c in ("rep", "fold"):
        coerced = pd.to_numeric(df[c], errors="coerce")
        if coerced.isna().any() or not np.allclose(coerced.dropna() % 1, 0):
            raise ValueError(f"{name}: column '{c}' has null or non-integer values")
        df[c] = coerced.astype(int)
    df["y_true"] = pd.to_numeric(df["y_true"], errors="coerce")
    df["y_prob"] = pd.to_numeric(df["y_prob"], errors="coerce")

    # String keys: strip; blank/na is a failure, never coerced to "nan".
    str_cols = list(STR_KEYS) + (["image_model"] if is_image else [])
    for c in str_cols:
        s = df[c].astype("string").str.strip()
        if s.isna().any() or (s == "").any() or (s.str.lower() == "nan").any():
            raise ValueError(f"{name}: column '{c}' has null/blank values")
        df[c] = s.astype(str)

    if df["y_true"].isna().any():
        raise ValueError(f"{name}: null labels present")
    if not set(pd.unique(df["y_true"].astype(int))) <= {0, 1}:
        raise ValueError(f"{name}: labels must be 0/1")
    df["y_true"] = df["y_true"].astype(int)
    if df["y_prob"].isna().any() or not np.isfinite(df["y_prob"]).all():
        raise ValueError(f"{name}: null/non-finite probabilities present")
    if (df["y_prob"] < 0).any() or (df["y_prob"] > 1).any():
        raise ValueError(f"{name}: probabilities outside [0, 1]")

    # Uniqueness at expected granularity.
    key = IMAGE_PAIR_KEYS if is_image else PAIR_KEYS
    dup = int(df.duplicated(subset=key).sum())
    if dup:
        raise ValueError(f"{name}: {dup} duplicate rows on keys {key}")
    return df


def _assert_patient_disjoint_folds(df: pd.DataFrame, name: str, by: list[str]) -> None:
    for keys, g in df.groupby(by):
        multi = g.groupby("patient_id")["fold"].nunique()
        bad = multi[multi > 1]
        if len(bad):
            raise ValueError(
                f"{name}: {len(bad)} patients cross held-out folds for {list(zip(by, np.atleast_1d(keys)))}: "
                f"{list(bad.index[:5])}"
            )


def merge_oof(cnv: pd.DataFrame, image: pd.DataFrame) -> pd.DataFrame:
    """Exact one-to-one join of CNV and image OOF predictions, per image model.

    Fails closed on unmatched keys, label disagreements, duplicate keys, or
    patients crossing held-out folds. Never silently evaluates an intersection.
    """
    cnv = _norm_and_validate(cnv, "CNV", is_image=False).rename(columns={"y_prob": "cnv_prob"})
    image = _norm_and_validate(image, "image", is_image=True).rename(columns={"y_prob": "img_prob"})
    _assert_patient_disjoint_folds(cnv, "CNV", ["condition", "rep"])
    _assert_patient_disjoint_folds(image, "image", ["condition", "rep", "image_model"])

    out_parts = []
    for model, img_m in image.groupby("image_model"):
        cnv_keys = set(map(tuple, cnv[PAIR_KEYS].to_numpy()))
        img_keys = set(map(tuple, img_m[PAIR_KEYS].to_numpy()))
        only_cnv = cnv_keys - img_keys
        only_img = img_keys - cnv_keys
        if only_cnv or only_img:
            raise ValueError(
                f"image_model={model}: CNV/image key sets differ. "
                f"unmatched_cnv={len(only_cnv)} unmatched_image={len(only_img)}. "
                f"cnv_examples={list(only_cnv)[:5]} image_examples={list(only_img)[:5]}"
            )
        merged = cnv[PAIR_KEYS + ["y_true", "cnv_prob"]].merge(
            img_m[PAIR_KEYS + ["image_model", "y_true", "img_prob"]],
            on=PAIR_KEYS, how="inner", suffixes=("_cnv", "_img"), validate="one_to_one",
        )
        if len(merged) != len(cnv) or len(merged) != len(img_m):
            raise ValueError(
                f"image_model={model}: merged rows {len(merged)} != cnv {len(cnv)} / image {len(img_m)}"
            )
        mism = int((merged["y_true_cnv"] != merged["y_true_img"]).sum())
        if mism:
            raise ValueError(f"image_model={model}: {mism} label disagreements on joined rows")
        merged["y_true"] = merged["y_true_cnv"].astype(int)
        out_parts.append(merged.drop(columns=["y_true_cnv", "y_true_img"]))
    return pd.concat(out_parts, ignore_index=True)


def _fold_pure_stack(train: pd.DataFrame, test: pd.DataFrame, seed: int, fitter=None):
    if train["y_true"].nunique() < 2:
        return 0.5 * (test["cnv_prob"].values + test["img_prob"].values), "fallback_mean_single_class_train"
    if fitter is None:
        from sklearn.linear_model import LogisticRegression  # lazy: keep package usable without sklearn

        fitter = lambda: LogisticRegression(solver="lbfgs", max_iter=1000, random_state=seed)
    model = fitter()
    model.fit(train[["cnv_prob", "img_prob"]].values, train["y_true"].values)
    return model.predict_proba(test[["cnv_prob", "img_prob"]].values)[:, 1], "ok"


def compute_late_fusion(merged: pd.DataFrame, seed: int = 20260304, fitter=None):
    """Return (long predictions, per-group diagnostics). Fold-pure per image model."""
    rows, diag = [], []
    base = ["condition", "rep", "fold", "patient_id", "sample_id", "y_true", "image_model"]
    for (cond, rep, model, fold), test in merged.groupby(["condition", "rep", "image_model", "fold"], sort=True):
        train = merged[
            (merged["condition"] == cond) & (merged["rep"] == rep)
            & (merged["image_model"] == model) & (merged["fold"] != fold)
        ]
        # Fold-purity guards: no shared patients, no shared keys between train and test.
        test_patients = set(test["patient_id"])
        if test_patients & set(train["patient_id"]):
            raise ValueError(f"fold {fold} ({model}): train/test patient overlap")
        test_keys = set(map(tuple, test[PAIR_KEYS].to_numpy()))
        if test_keys & set(map(tuple, train[PAIR_KEYS].to_numpy())):
            raise ValueError(f"fold {fold} ({model}): held-out rows present in stacker training set")
        stack_prob, note = _fold_pure_stack(train, test, seed, fitter=fitter)
        scores = {
            "cnv_only": (test["cnv_prob"].values, "ok"),
            "img_only": (test["img_prob"].values, "ok"),
            "mean": (0.5 * (test["cnv_prob"].values + test["img_prob"].values), "ok"),
            "stack_logit": (stack_prob, note),
        }
        for method, (prob, mnote) in scores.items():
            out = test[base].copy()
            out["fusion_method"] = method
            out["y_prob"] = prob
            out["stack_note"] = mnote
            rows.append(out)
        diag.append({
            "condition": cond, "rep": int(rep), "image_model": model, "held_out_fold": int(fold),
            "train_rows": int(len(train)), "train_patients": int(train["patient_id"].nunique()),
            "test_rows": int(len(test)), "stack_status": note,
        })
    return pd.concat(rows, ignore_index=True), diag


def _reject_repo_output(out_dir: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out = out_dir.resolve()
    if repo_root == out or repo_root in out.parents:
        raise ValueError(f"Refusing to write late-fusion output inside the clean repo: {out}")


def _atomic_write_csv(df: pd.DataFrame, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(dest)


def run_late_fusion(cnv_patterns: list[str], image_patterns: list[str], out_dir: Path,
                    seed: int = 20260304, overwrite: bool = False,
                    now: str | None = None) -> Path:
    """End-to-end: validate, fuse, atomically write standardized predictions externally."""
    out_dir = Path(out_dir)
    _reject_repo_output(out_dir)
    dest = out_dir / "cv_predictions_late_fusion.csv"
    if dest.exists() and not overwrite:
        raise FileExistsError(f"{dest} exists; refusing to overwrite. Pass overwrite=True to replace.")
    out_dir.mkdir(parents=True, exist_ok=True)

    cnv_files = sorted({f for p in cnv_patterns for f in glob.glob(p)})
    img_files = sorted({f for p in image_patterns for f in glob.glob(p)})
    merged = merge_oof(_read_glob(cnv_patterns), _read_glob(image_patterns))
    preds, diag = compute_late_fusion(merged, seed=seed)
    _atomic_write_csv(preds, dest)

    meta = {
        "command": "run_late_fusion",
        "cnv_patterns": cnv_patterns, "image_patterns": image_patterns,
        "cnv_files": [{"path": f, "bytes": Path(f).stat().st_size} for f in cnv_files],
        "image_files": [{"path": f, "bytes": Path(f).stat().st_size} for f in img_files],
        "n_rows": int(len(preds)), "n_patients": int(preds["patient_id"].nunique()),
        "folds": sorted(int(x) for x in preds["fold"].unique()),
        "image_models": sorted(preds["image_model"].unique().tolist()),
        "seed": seed, "output_schema": list(preds.columns),
        "fold_diagnostics": diag,
        "timestamp": now or datetime.now().isoformat(timespec="seconds"),
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2))
    return dest

#!/usr/bin/env python
"""Run one leakage-safe outer fold of the landmarking longitudinal model.

Mirrors ``24_run_lgd2_final_outer_fold.py`` (same nested-CV protocol, same
patient-disjoint folds, same inner-selection and thresholding helpers) but for
the ``longitudinal`` family: each landmark is one biopsy row plus its
history-to-date, and the prediction target is the Chapter 1 endpoint
``NextBiopsyProgression_LGD2plus``. Because there is exactly one landmark per
biopsy row, the outer-test predictions cover the identical rows as the frozen
single-timepoint baseline, so the two can be compared as a paired test.

Data never leaves the cluster; outputs are written under ``--output-root`` which
must be outside the Git tree. The candidate grid is small by design (GPU time),
selected by the same patient-max AUPRC nested criterion as the baseline.

Usage:
    python scripts/27_run_longitudinal_outer_fold.py \
        --release-root <frozen release dir> \
        --output-root <scratch output dir> \
        --outer-fold 1 [--device auto] [--smoke]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.cross_fitted_thresholds import select_threshold  # noqa: E402
from barrett.evaluation.nested_selection import select_per_outer_fold  # noqa: E402
from barrett.training.data import CanonicalFeatureStore, load_cnv_matrix  # noqa: E402
from barrett.training.inner_cv import make_inner_assignments, split_inner  # noqa: E402
from barrett.training.longitudinal import (  # noqa: E402
    build_landmark_histories,
    fit_longitudinal,
    patient_max_predictions,
    predict_longitudinal,
)

# Small candidate grid: GRU vs attention aggregator, two capacities.
CANDIDATES = [
    {"configuration_id": "gru_h256", "aggregator": "gru", "temporal_hidden": 256,
     "img_hidden": 256, "cnv_hidden": 128, "lr": 1e-4, "max_epochs": 30, "patience": 6, "batch_size": 8},
    {"configuration_id": "gru_h128", "aggregator": "gru", "temporal_hidden": 128,
     "img_hidden": 256, "cnv_hidden": 128, "lr": 1e-4, "max_epochs": 30, "patience": 6, "batch_size": 8},
    {"configuration_id": "attn_h256", "aggregator": "attn", "temporal_hidden": 256,
     "img_hidden": 256, "cnv_hidden": 128, "lr": 1e-4, "max_epochs": 30, "patience": 6, "batch_size": 8},
]

INNER_FOLDS = 3
INNER_SEED = 20260713


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest_with_dates(release: Path) -> pd.DataFrame:
    """Manifest rows keyed by sample_id, with Date joined from the cohort table.

    Uses training_manifest_v2.csv (sample_id, patient_id, y_progressor,
    fold_id_rep01) and joins the biopsy Date from pre_event_cohort.csv on
    SampleID. Fails closed if any Date is missing.
    """
    manifest = pd.read_csv(release / "training_manifest_v2.csv", dtype={"sample_id": str})
    cohort = pd.read_csv(release / "pre_event_cohort.csv", dtype={"SampleID": str})
    dates = cohort[["SampleID", "Date"]].rename(columns={"SampleID": "sample_id"})
    merged = manifest.merge(dates, on="sample_id", how="left", validate="one_to_one")
    if merged["Date"].isna().any():
        n = int(merged["Date"].isna().sum())
        raise SystemExit(f"{n} manifest rows have no Date after cohort join")
    return merged


def histories_for_patients(all_histories, patient_ids) -> list:
    keep = set(str(p) for p in patient_ids)
    return [h for h in all_histories if h.patient_id in keep]


def _jsonable_threshold(threshold) -> dict:
    """Serialize a ThresholdChoice (or bare float) to JSON-safe plain types.

    Fields can be numpy scalars, which json.dumps cannot encode; coerce each
    to a native float/str/bool/None.
    """
    def _coerce(value):
        if value is None or isinstance(value, (bool, str)):
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)

    source = vars(threshold) if hasattr(threshold, "__dict__") else {"threshold": threshold}
    return {key: _coerce(val) for key, val in source.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--outer-fold", required=True, type=int, choices=range(1, 6))
    parser.add_argument("--device", default="auto")
    parser.add_argument("--smoke", action="store_true",
                        help="one candidate, few epochs — end-to-end sanity check")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    release = Path(args.release_root).resolve()
    output_root = Path(args.output_root).resolve()
    if REPO_ROOT == output_root or REPO_ROOT in output_root.parents:
        raise SystemExit("training output must remain outside Git")
    fold_dir = output_root / "longitudinal" / f"fold{args.outer_fold}"
    if fold_dir.exists() and any(fold_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"non-empty output exists: {fold_dir}; pass --overwrite")
    fold_dir.mkdir(parents=True, exist_ok=True)

    device = (
        torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if args.device == "auto" else torch.device(args.device)
    )
    if device.type != "cuda":
        print("[warn] longitudinal model running without CUDA", file=sys.stderr)

    manifest = load_manifest_with_dates(release)
    fold_col = "fold_id_rep01"
    outer_test = manifest[manifest[fold_col].eq(args.outer_fold)].copy()
    outer_train = manifest[manifest[fold_col].ne(args.outer_fold)].copy()
    overlap = set(outer_train["patient_id"]) & set(outer_test["patient_id"])
    if overlap:
        raise SystemExit(f"outer patient leakage: {sorted(overlap)}")

    # landmark histories are built per split from that split's own rows only, so
    # a landmark's history never reaches across the outer train/test boundary
    train_frame = outer_train.rename(columns={})[["sample_id", "patient_id", "Date", "y_progressor"]]
    test_frame = outer_test[["sample_id", "patient_id", "Date", "y_progressor"]]
    train_histories = build_landmark_histories(train_frame)
    test_histories = build_landmark_histories(test_frame)

    # feature store (same views as the baseline)
    cnv_matrix, feature_names = load_cnv_matrix(release / "feature_views/cnv")
    uni2_index = pd.read_csv(release / "feature_views/uni2/uni2_index.csv", dtype={"sample_id": str})
    store = CanonicalFeatureStore(uni2_index, cnv_matrix, feature_names)

    candidates = CANDIDATES[:1] if args.smoke else CANDIDATES
    if args.smoke:
        candidates = [dict(candidates[0], max_epochs=2, patience=5)]

    seed = INNER_SEED + args.outer_fold * 1000
    assignments = make_inner_assignments(outer_train, INNER_FOLDS, seed)
    assignments.to_csv(fold_dir / "inner_fold_assignments.csv", index=False)

    # ---- inner CV: select the winning candidate on patient-max AUPRC ---------
    inner_rows = []
    epochs: dict[str, list[int]] = {c["configuration_id"]: [] for c in candidates}
    for ci, candidate in enumerate(candidates):
        cfg_id = candidate["configuration_id"]
        for inner_fold in sorted(assignments["inner_fold"].unique()):
            train_split, val_split = split_inner(outer_train, assignments, int(inner_fold))
            tr = histories_for_patients(train_histories, train_split["patient_id"])
            va = histories_for_patients(train_histories, val_split["patient_id"])
            fit = fit_longitudinal(tr, va, store, candidate, device, seed + ci * 100 + int(inner_fold))
            epochs[cfg_id].append(fit.best_epoch)
            preds = fit.validation_predictions.copy()
            preds["outer_fold"] = args.outer_fold
            preds["inner_fold"] = int(inner_fold)
            preds["configuration_id"] = cfg_id
            inner_rows.extend(preds.to_dict("records"))
    inner_predictions = pd.DataFrame(inner_rows)
    inner_predictions.to_csv(fold_dir / "inner_validation_predictions.csv", index=False)

    winner, leaderboard = select_per_outer_fold(
        inner_predictions,
        outer_test_patients={args.outer_fold: set(outer_test["patient_id"].astype(str))},
    )
    leaderboard.to_csv(fold_dir / "inner_validation_leaderboard.csv", index=False)
    selected_id = str(winner[args.outer_fold])
    selected = next(c for c in candidates if c["configuration_id"] == selected_id)

    # ---- retrain on full outer-train at the median selected epoch ------------
    final_epochs = max(1, int(np.median(epochs[selected_id])))
    fit = fit_longitudinal(
        train_histories, None, store, selected, device, seed, fixed_epochs=final_epochs
    )
    outer_predictions = predict_longitudinal(
        fit.model, test_histories, store, device, fit.cnv_median, fit.cnv_mean, fit.cnv_std
    )

    # keys must match the outer-test rows exactly (paired comparability)
    expected = set(outer_test["sample_id"].astype(str))
    actual = set(outer_predictions["sample_id"].astype(str))
    if expected != actual:
        raise SystemExit(
            f"outer prediction row-key mismatch: missing={len(expected - actual)} extra={len(actual - expected)}"
        )
    if outer_predictions["y_prob"].nunique(dropna=False) < 2:
        raise SystemExit("outer-test probabilities are constant")

    # ---- threshold from inner-validation patients (unchanged, applied to test)
    selected_inner = inner_predictions[inner_predictions["configuration_id"].eq(selected_id)].copy()
    validation_patient = patient_max_predictions(selected_inner)
    threshold = select_threshold(validation_patient, "target_specificity", 0.90)

    outer_predictions["outer_fold"] = args.outer_fold
    outer_predictions["model_family"] = "longitudinal"
    outer_predictions["configuration_id"] = selected_id
    outer_predictions.to_csv(fold_dir / "outer_test_predictions.csv", index=False)

    checkpoint = fold_dir / "model.pt"
    torch.save({
        "state_dict": fit.model.state_dict(),
        "family": "longitudinal",
        "configuration": selected,
        "final_epochs": final_epochs,
        "cnv_median": fit.cnv_median,
        "cnv_mean": fit.cnv_mean,
        "cnv_std": fit.cnv_std,
    }, checkpoint)

    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    metadata = {
        "family": "longitudinal",
        "outer_fold": args.outer_fold,
        "selected_configuration_id": selected_id,
        "final_epochs": final_epochs,
        "n_outer_train_landmarks": len(train_histories),
        "n_outer_test_landmarks": len(test_histories),
        "n_outer_train_patients": int(outer_train["patient_id"].nunique()),
        "n_outer_test_patients": int(outer_test["patient_id"].nunique()),
        "validation_threshold": _jsonable_threshold(threshold),
        "git_commit": git_commit,
        "manifest_sha256": sha256_file(release / "training_manifest_v2.csv"),
        "device": str(device),
        "smoke": bool(args.smoke),
    }
    (fold_dir / "fold_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (fold_dir / "fold_completion.json").write_text(
        json.dumps({"status": "PASS", "family": "longitudinal", "outer_fold": args.outer_fold,
                    "n_predictions": int(len(outer_predictions))}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

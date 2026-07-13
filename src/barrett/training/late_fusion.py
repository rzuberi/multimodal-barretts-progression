"""Leakage-safe late fusion from matching inner and outer base predictions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from barrett.evaluation.cross_fitted_thresholds import select_threshold
from barrett.evaluation.output_contract import validate_predictions
from barrett.training.loops import patient_max_predictions


def _selected_inner(fold_dir: Path) -> pd.DataFrame:
    completion = json.loads((fold_dir / "fold_completion.json").read_text(encoding="utf-8"))
    selected = str(completion["selected_configuration_id"])
    frame = pd.read_csv(fold_dir / "inner_validation_predictions.csv", dtype={"sample_id": str})
    frame = frame[frame["configuration_id"].astype(str).eq(selected)].copy()
    if frame.empty:
        raise ValueError(f"no selected inner predictions in {fold_dir}")
    key = ["sample_id", "inner_fold"]
    if frame.duplicated(key).any():
        raise ValueError(f"duplicate selected inner prediction keys in {fold_dir}")
    return frame


def _merge_inner(cnv_dir: Path, image_dir: Path) -> pd.DataFrame:
    cnv = _selected_inner(cnv_dir).rename(columns={"y_prob": "cnv_prob"})
    image = _selected_inner(image_dir).rename(columns={"y_prob": "image_prob"})
    keys = ["outer_fold", "inner_fold", "sample_id", "patient_id", "y_true"]
    merged = cnv[keys + ["cnv_prob"]].merge(
        image[keys + ["image_prob"]], on=keys, how="outer", validate="one_to_one", indicator=True
    )
    if set(merged["_merge"]) != {"both"}:
        raise ValueError("CNV/image selected inner prediction keys differ")
    return merged.drop(columns="_merge")


def _merge_outer(cnv_dir: Path, image_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    cnv = pd.read_csv(cnv_dir / "outer_test_predictions.csv", dtype={"row_key": str, "sample_id": str})
    image = pd.read_csv(image_dir / "outer_test_predictions.csv", dtype={"row_key": str, "sample_id": str})
    keys = ["outer_fold", "row_key", "sample_id", "patient_id", "y_true"]
    merged = cnv[keys + ["y_prob"]].rename(columns={"y_prob": "cnv_prob"}).merge(
        image[keys + ["y_prob"]].rename(columns={"y_prob": "image_prob"}),
        on=keys, how="outer", validate="one_to_one", indicator=True,
    )
    if set(merged["_merge"]) != {"both"}:
        raise ValueError("CNV/image outer prediction keys differ")
    return merged.drop(columns="_merge"), cnv


def _weights(frame: pd.DataFrame) -> np.ndarray:
    counts = frame.groupby("patient_id")["sample_id"].transform("count").to_numpy(dtype=float)
    return 1.0 / counts


def _new_stacker(seed: int) -> LogisticRegression:
    return LogisticRegression(solver="lbfgs", max_iter=1000, random_state=seed)


def _cross_fitted_stack(inner: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, LogisticRegression]:
    parts = []
    for held_fold in sorted(inner["inner_fold"].unique()):
        train = inner[inner["inner_fold"].ne(held_fold)]
        held = inner[inner["inner_fold"].eq(held_fold)].copy()
        if set(train["patient_id"]) & set(held["patient_id"]):
            raise ValueError("patient leakage in late-stacker inner cross-fit")
        model = _new_stacker(seed + int(held_fold))
        model.fit(
            train[["cnv_prob", "image_prob"]], train["y_true"],
            sample_weight=_weights(train),
        )
        held["y_prob"] = model.predict_proba(held[["cnv_prob", "image_prob"]])[:, 1]
        parts.append(held)
    cross_fitted = pd.concat(parts, ignore_index=True)
    final = _new_stacker(seed)
    final.fit(
        inner[["cnv_prob", "image_prob"]], inner["y_true"],
        sample_weight=_weights(inner),
    )
    return cross_fitted, final


def _calibrate(inner: pd.DataFrame, outer_prob: np.ndarray) -> tuple[np.ndarray, LogisticRegression | None, str]:
    patient = patient_max_predictions(inner[["patient_id", "y_true", "y_prob"]])
    if patient["y_true"].nunique() < 2:
        return np.asarray(outer_prob), None, "fallback_uncalibrated_single_class"
    model = LogisticRegression(random_state=0)
    model.fit(patient[["y_prob"]], patient["y_true"])
    values = model.predict_proba(pd.DataFrame({"y_prob": outer_prob}))[:, 1]
    return values, model, "ok"


def _write_late_fold(
    family: str,
    method: str,
    fold: int,
    base_template: pd.DataFrame,
    outer_probability: np.ndarray,
    inner_predictions: pd.DataFrame,
    output_root: Path,
    registry_path: Path,
    model_artifact: object,
    model_details: dict,
) -> Path:
    directory = output_root / family / f"fold{fold}"
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty late-fusion fold: {directory}")
    directory.mkdir(parents=True, exist_ok=False)
    checkpoint = directory / "model.joblib"
    joblib.dump(model_artifact, checkpoint)
    inner = inner_predictions.copy()
    patient_inner = patient_max_predictions(inner[["patient_id", "y_true", "y_prob"]])
    threshold = select_threshold(patient_inner, "target_specificity", 0.90)
    calibrated, calibrator, calibration_status = _calibrate(inner, outer_probability)
    joblib.dump({"model": calibrator, "status": calibration_status}, directory / "platt_calibrator.joblib")

    out = base_template.copy()
    out["model_family"] = family
    out["model_name"] = family
    out["configuration_id"] = family + "_fixed"
    out["fusion_type"] = "late"
    out["feature_model"] = "uni2"
    out["cnv_representation"] = "windows_armdiff_plus_arms_plus_cx"
    out["checkpoint_ref"] = str(checkpoint)
    out["config_ref"] = str(registry_path)
    out["y_prob"] = np.asarray(outer_probability, dtype=float)
    clipped = np.clip(out["y_prob"].to_numpy(), 1e-8, 1 - 1e-8)
    out["y_logit"] = np.log(clipped / (1 - clipped))
    out["y_prob_calibrated"] = calibrated
    problems = validate_predictions(out, expected_fold_values=[fold])
    if problems:
        raise ValueError(f"late-fusion output contract failed: {problems}")

    out.to_csv(directory / "outer_test_predictions.csv", index=False)
    inner.to_csv(directory / "inner_validation_predictions.csv", index=False)
    inner[["patient_id", "inner_fold"]].drop_duplicates().to_csv(
        directory / "inner_fold_assignments.csv", index=False
    )
    pd.DataFrame([{
        "outer_fold": fold, "configuration_id": family + "_fixed", "rank": 1,
        "selection": "prespecified_fixed",
    }]).to_csv(directory / "inner_validation_leaderboard.csv", index=False)
    (directory / "resolved_config.yaml").write_text(
        f"family: {family}\nmethod: {method}\nouter_fold: {fold}\n", encoding="utf-8"
    )
    (directory / "training_history.json").write_text(
        json.dumps(model_details, indent=2) + "\n", encoding="utf-8"
    )
    (directory / "environment.txt").write_text(
        f"python={sys.executable}\nderived_from=cnv_only,image_only\n", encoding="utf-8"
    )
    metadata = {
        "family": family, "outer_fold": fold, "method": method,
        "validation_threshold": threshold.__dict__, "calibration_status": calibration_status,
        "n_outer_test_rows": int(len(out)), "n_outer_test_patients": int(out["patient_id"].nunique()),
        **model_details,
    }
    (directory / "fold_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (directory / "artifact_validation.json").write_text(
        json.dumps({"status": "PASS", "problems": []}, indent=2) + "\n", encoding="utf-8"
    )
    completion = {
        "status": "PASS", "family": family, "outer_fold": fold,
        "selected_configuration_id": family + "_fixed",
        "n_predictions": int(len(out)), "n_patients": int(out["patient_id"].nunique()),
        "validation_problems": [],
    }
    (directory / "fold_completion.json").write_text(json.dumps(completion, indent=2) + "\n", encoding="utf-8")
    return directory


def derive_late_fold(output_root: str | Path, registry_path: str | Path, fold: int, seed: int) -> list[Path]:
    output_root = Path(output_root)
    registry_path = Path(registry_path).resolve()
    cnv_dir = output_root / "cnv_only" / f"fold{fold}"
    image_dir = output_root / "image_only" / f"fold{fold}"
    inner = _merge_inner(cnv_dir, image_dir)
    outer, template = _merge_outer(cnv_dir, image_dir)

    inner_mean = inner.copy()
    inner_mean["y_prob"] = 0.5 * (inner_mean["cnv_prob"] + inner_mean["image_prob"])
    outer_mean = 0.5 * (outer["cnv_prob"].to_numpy() + outer["image_prob"].to_numpy())
    mean_dir = _write_late_fold(
        "late_mean", "mean", fold, template, outer_mean, inner_mean,
        output_root, registry_path, {"method": "arithmetic_mean"},
        {"base_families": ["cnv_only", "image_only"]},
    )

    inner_stack, stacker = _cross_fitted_stack(inner, seed + fold * 1000)
    outer_stack = stacker.predict_proba(outer[["cnv_prob", "image_prob"]])[:, 1]
    stack_dir = _write_late_fold(
        "late_stack_logit", "stack_logit", fold, template, outer_stack, inner_stack,
        output_root, registry_path, stacker,
        {
            "base_families": ["cnv_only", "image_only"],
            "inner_meta_cross_fitted": True,
            "patient_equal_sample_weights": True,
            "coefficients": stacker.coef_.tolist(),
            "intercept": stacker.intercept_.tolist(),
        },
    )
    return [mean_dir, stack_dir]

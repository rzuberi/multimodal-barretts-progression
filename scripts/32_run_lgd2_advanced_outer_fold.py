#!/usr/bin/env python
"""Run one nested-CV outer fold for an experimental fusion architecture."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.linear_model import LogisticRegression

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.cross_fitted_thresholds import select_threshold  # noqa: E402
from barrett.evaluation.nested_selection import select_per_outer_fold  # noqa: E402
from barrett.evaluation.output_contract import validate_predictions  # noqa: E402
from barrett.training.advanced import ALL_FAMILIES, AdvancedFeatureStore, fit_advanced, predict_advanced  # noqa: E402
from barrett.training.inner_cv import make_inner_assignments, split_inner  # noqa: E402
from barrett.training.loops import patient_max_predictions  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_platt(validation: pd.DataFrame, probability: np.ndarray):
    if validation["y_true"].nunique() < 2:
        return probability, None, "fallback_uncalibrated_single_class"
    model = LogisticRegression(random_state=0).fit(validation[["y_prob"]], validation["y_true"])
    return model.predict_proba(pd.DataFrame({"y_prob": probability}))[:, 1], model, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--model-registry", required=True)
    parser.add_argument("--family", required=True, choices=sorted(ALL_FAMILIES))
    parser.add_argument("--outer-fold", required=True, type=int, choices=range(1, 6))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    release, registry_path, output = Path(args.release_root).resolve(), Path(args.model_registry).resolve(), Path(args.output_root).resolve()
    if REPO_ROOT == output or REPO_ROOT in output.parents:
        raise SystemExit("training output must remain outside Git")
    fold_dir = output / args.family / f"fold{args.outer_fold}"
    completion = fold_dir / "fold_completion.json"
    if args.resume and completion.exists():
        print(f"already complete: {completion}")
        return 0
    if fold_dir.exists() and any(fold_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"non-empty output exists: {fold_dir}")
    fold_dir.mkdir(parents=True, exist_ok=True)
    registry = yaml.safe_load(registry_path.read_text())
    config = registry["families"][args.family]
    candidates = config["candidates"]
    manifest_path = release / registry["training_manifest"]
    manifest = pd.read_csv(manifest_path, dtype={"sample_id": str})
    test = manifest[manifest["fold_id_rep01"].eq(args.outer_fold)].copy()
    train = manifest[manifest["fold_id_rep01"].ne(args.outer_fold)].copy()
    if set(train["patient_id"]) & set(test["patient_id"]):
        raise SystemExit("outer patient leakage")
    seed = int(registry["inner_cv"]["seed"]) + args.outer_fold * 1000
    assignments = make_inner_assignments(train, int(registry["inner_cv"]["n_folds"]), seed)
    assignments.to_csv(fold_dir / "inner_fold_assignments.csv", index=False)
    store = AdvancedFeatureStore.from_release(release, registry["feature_views"])
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")

    rows, epochs, histories = [], {}, []
    for candidate_index, candidate in enumerate(candidates):
        cfg_id = candidate["configuration_id"]
        epochs[cfg_id] = []
        for inner_fold in sorted(assignments["inner_fold"].unique()):
            inner_train, validation = split_inner(train, assignments, int(inner_fold))
            fit = fit_advanced(args.family, inner_train, validation, store, candidate, device,
                               seed + candidate_index * 100 + int(inner_fold))
            epochs[cfg_id].append(fit.best_epoch)
            prediction = fit.validation_predictions.copy()
            prediction["outer_fold"] = args.outer_fold
            prediction["inner_fold"] = int(inner_fold)
            prediction["configuration_id"] = cfg_id
            rows.extend(prediction.to_dict("records"))
            histories.append({"configuration_id": cfg_id, "inner_fold": int(inner_fold),
                              "best_epoch": fit.best_epoch, "history": fit.history})
    inner_predictions = pd.DataFrame(rows)
    winner, leaderboard = select_per_outer_fold(
        inner_predictions,
        outer_test_patients={args.outer_fold: set(test["patient_id"].astype(str))},
    )
    selected_id = str(winner[args.outer_fold])
    selected = next(value for value in candidates if value["configuration_id"] == selected_id)
    final_epochs = max(1, int(np.median(epochs[selected_id])))
    final = fit_advanced(args.family, train, None, store, selected, device, seed, fixed_epochs=final_epochs)
    outer = predict_advanced(final.model, args.family, test, store, device, int(selected.get("batch_size", 8)),
                             final.cnv_median, final.cnv_mean, final.cnv_std)
    checkpoint = fold_dir / "model.pt"
    torch.save({
        "state_dict": final.model.state_dict(), "family": args.family, "configuration": selected,
        "final_epochs": final_epochs, "cnv_median": final.cnv_median,
        "cnv_mean": final.cnv_mean, "cnv_std": final.cnv_std,
        "cnv_feature_names": store.cnv_features, "foundation_names": store.foundation_names,
    }, checkpoint)
    histories.append({"configuration_id": selected_id, "stage": "final_outer_train",
                      "fixed_epochs": final_epochs, "history": final.history})

    inner_predictions.to_csv(fold_dir / "inner_validation_predictions.csv", index=False)
    leaderboard.to_csv(fold_dir / "inner_validation_leaderboard.csv", index=False)
    validation_patient = patient_max_predictions(inner_predictions[inner_predictions["configuration_id"].eq(selected_id)])
    threshold = select_threshold(validation_patient, registry["threshold"]["criterion"], float(registry["threshold"]["target"]))
    calibrated, calibrator, calibration_status = fit_platt(validation_patient, outer["y_prob"].to_numpy())
    outer["y_prob_calibrated"] = calibrated
    joblib.dump({"model": calibrator, "status": calibration_status}, fold_dir / "platt_calibrator.joblib")
    metadata = test.set_index("sample_id")
    enriched = outer.copy()
    enriched["run_id"] = output.name
    enriched["cohort_release_id"] = release.name
    enriched["cohort_hash"] = sha256(release / "pre_event_cohort.csv")
    enriched["split_release_id"] = release.name + "_splits"
    enriched["split_hash"] = sha256(release / "patient_splits.csv")
    enriched["model_family"] = args.family
    enriched["model_name"] = config["model_name"]
    enriched["configuration_id"] = selected_id
    enriched["feature_model"] = "gigapath+uni2+virchow2" if args.family == "foundation_ensemble_fusion" else "uni2"
    enriched["fusion_type"] = args.family
    enriched["cnv_representation"] = "windows_armdiff_plus_arms_plus_cx"
    enriched["outer_fold"] = args.outer_fold
    enriched["row_key"] = enriched["sample_id"].astype(str)
    for column in ["biopsy_id", "slide_id", "cnv_id", "strict_pre_event_eligible"]:
        enriched[column] = enriched["sample_id"].map(metadata[column])
    enriched["checkpoint_ref"] = str(checkpoint)
    enriched["config_ref"] = str(registry_path)
    enriched["seed"] = seed
    env_ref = fold_dir / "environment.txt"
    env_ref.write_text(f"python={sys.executable}\nversion={sys.version}\ntorch={torch.__version__}\ncuda={torch.cuda.is_available()}\n")
    enriched["env_ref"] = str(env_ref)
    order = [
        "run_id", "cohort_release_id", "cohort_hash", "split_release_id", "split_hash",
        "model_family", "model_name", "configuration_id", "feature_model", "fusion_type",
        "cnv_representation", "outer_fold", "row_key", "patient_id", "biopsy_id", "sample_id",
        "slide_id", "cnv_id", "y_true", "y_prob", "strict_pre_event_eligible", "checkpoint_ref",
        "config_ref", "seed", "env_ref", "y_logit", "y_prob_calibrated",
    ]
    enriched = enriched[order]
    enriched.to_csv(fold_dir / "outer_test_predictions.csv", index=False)
    problems = validate_predictions(enriched, expected_fold_values=[args.outer_fold])
    if set(enriched["row_key"]) != set(test["sample_id"].astype(str)):
        problems.append("outer prediction row-key mismatch")
    if enriched["y_prob"].nunique(dropna=False) < 2:
        problems.append("outer-test probabilities are constant")
    if problems:
        (fold_dir / "artifact_validation.json").write_text(json.dumps({"status": "FAIL", "problems": problems}, indent=2) + "\n")
        raise SystemExit("artifact validation failed: " + "; ".join(problems))
    (fold_dir / "resolved_config.yaml").write_text(yaml.safe_dump({
        "family": args.family, "outer_fold": args.outer_fold, "selected_configuration": selected,
        "registry_version": registry["registry_version"],
    }, sort_keys=False))
    (fold_dir / "training_history.json").write_text(json.dumps(histories, indent=2) + "\n")
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    fold_metadata = {
        "family": args.family, "outer_fold": args.outer_fold, "selected_configuration_id": selected_id,
        "validation_threshold": threshold.__dict__, "n_outer_train_rows": len(train),
        "n_outer_test_rows": len(test), "n_outer_train_patients": train["patient_id"].nunique(),
        "n_outer_test_patients": test["patient_id"].nunique(), "git_commit": git_commit,
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True).strip()),
        "manifest_sha256": sha256(manifest_path), "registry_sha256": sha256(registry_path),
        "device": str(device), "calibration_status": calibration_status,
    }
    (fold_dir / "fold_metadata.json").write_text(json.dumps(fold_metadata, indent=2) + "\n")
    completion_payload = {
        "status": "PASS", "family": args.family, "outer_fold": args.outer_fold,
        "selected_configuration_id": selected_id, "n_predictions": len(enriched),
        "n_patients": enriched["patient_id"].nunique(), "validation_problems": [],
    }
    completion.write_text(json.dumps(completion_payload, indent=2) + "\n")
    (fold_dir / "artifact_validation.json").write_text(json.dumps({"status": "PASS", "problems": []}, indent=2) + "\n")
    print(json.dumps(fold_metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

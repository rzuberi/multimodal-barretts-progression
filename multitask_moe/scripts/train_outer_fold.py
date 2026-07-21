#!/usr/bin/env python
"""Run one leakage-safe outer fold for a multitask family (incl. end-to-end MoE).

Copy of scripts/24_run_lgd2_final_outer_fold.py, generalised so that:
  * any binary label already bound to `y_progressor` in the manifest is trained
    (the endpoint is task metadata only; the harness is label-name-agnostic);
  * the image feature index is read from a backbone-agnostic `image_index` key
    (falls back to `uni2_index`), so UNI2 / GigaPath share one runner;
  * a new `moe` family trains the end-to-end MixtureOfExperts and also writes
    per-sample gate weights (`moe_routing.csv`) for the routing report.

Selection / inner-CV / threshold / Platt calibration / output contract are
reused UNCHANGED from the frozen chain.
"""

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

REPO_ROOT = Path(__file__).resolve().parents[2]
MM_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(MM_SRC))

from barrett.evaluation.cross_fitted_thresholds import select_threshold  # noqa: E402
from barrett.evaluation.nested_selection import select_per_outer_fold  # noqa: E402
from barrett.evaluation.output_contract import validate_predictions  # noqa: E402
from barrett.models.cnv import build_cnv_pipeline, genomic_feature_importance  # noqa: E402
from barrett.training.data import CanonicalFeatureStore, load_cnv_matrix  # noqa: E402
from barrett.training.inner_cv import make_inner_assignments, split_inner  # noqa: E402
from barrett.training.loops import fit_neural, patient_max_predictions, predict_neural  # noqa: E402

from moe_training import fit_moe, predict_moe  # noqa: E402


FUSION_TYPE = {
    "cnv_only": "none",
    "image_only": "none",
    "early_fusion": "early",
    "intermediate_fusion": "intermediate",
    "coattention_fusion": "coattention",
    "moe": "moe",
}
NEURAL_FAMILIES = ("image_only", "early_fusion", "intermediate_fusion", "coattention_fusion", "moe")
FUSION_CNV_FAMILIES = ("early_fusion", "intermediate_fusion", "coattention_fusion", "moe")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fit(family, train, validation, store, config, device, seed, fixed_epochs=None):
    if family == "moe":
        return fit_moe(train, validation, store, config, device, seed, fixed_epochs=fixed_epochs)
    return fit_neural(family, train, validation, store, config, device, seed, fixed_epochs=fixed_epochs)


def _predict(model, family, frame, store, device, batch_size, cnv_median, cnv_mean, cnv_std, with_gate=False):
    if family == "moe":
        return predict_moe(model, frame, store, device, batch_size, cnv_median, cnv_mean, cnv_std, with_gate=with_gate)
    return predict_neural(model, family, frame, store, device, batch_size, cnv_median, cnv_mean, cnv_std)


def _fit_platt(validation_patient, test_probability):
    if validation_patient["y_true"].nunique() < 2:
        return np.asarray(test_probability, dtype=float), None, "fallback_uncalibrated_single_class"
    model = LogisticRegression(random_state=0)
    model.fit(validation_patient[["y_prob"]], validation_patient["y_true"])
    test_frame = pd.DataFrame({"y_prob": np.asarray(test_probability, dtype=float)})
    return model.predict_proba(test_frame)[:, 1], model, "ok"


def _threshold_counts(patient, threshold):
    y_true = patient["y_true"].to_numpy(dtype=int)
    y_pred = (patient["y_prob"].to_numpy(dtype=float) >= float(threshold)).astype(int)
    return {
        "threshold": float(threshold),
        "tp": int(((y_true == 1) & (y_pred == 1)).sum()),
        "fp": int(((y_true == 0) & (y_pred == 1)).sum()),
        "tn": int(((y_true == 0) & (y_pred == 0)).sum()),
        "fn": int(((y_true == 1) & (y_pred == 0)).sum()),
    }


def _cnv_inner(outer_fold, outer_train, assignments, candidates, matrix, feature_names, seed, n_jobs):
    x_by_id = matrix.set_index("sample_id")[feature_names]
    rows = []
    for candidate_index, candidate in enumerate(candidates):
        cfg_id = candidate["configuration_id"]
        for inner_fold in sorted(assignments["inner_fold"].unique()):
            train, validation = split_inner(outer_train, assignments, int(inner_fold))
            model = build_cnv_pipeline(candidate, seed + candidate_index * 100 + int(inner_fold), n_jobs=n_jobs)
            model.fit(x_by_id.loc[train["sample_id"]], train["y_progressor"].astype(int))
            probability = model.predict_proba(x_by_id.loc[validation["sample_id"]])[:, 1]
            for (_, row), value in zip(validation.iterrows(), probability):
                rows.append({
                    "outer_fold": outer_fold, "inner_fold": int(inner_fold), "configuration_id": cfg_id,
                    "sample_id": str(row["sample_id"]), "patient_id": str(row["patient_id"]),
                    "y_true": int(row["y_progressor"]), "y_prob": float(value),
                })
    return pd.DataFrame(rows)


def _neural_inner(family, outer_fold, outer_train, assignments, candidates, store, device, seed):
    rows, epochs, histories = [], {}, []
    for candidate_index, candidate in enumerate(candidates):
        cfg_id = candidate["configuration_id"]
        epochs[cfg_id] = []
        for inner_fold in sorted(assignments["inner_fold"].unique()):
            train, validation = split_inner(outer_train, assignments, int(inner_fold))
            fit = _fit(family, train, validation, store, candidate, device, seed + candidate_index * 100 + int(inner_fold))
            epochs[cfg_id].append(fit.best_epoch)
            predictions = fit.validation_predictions.copy()
            predictions["outer_fold"] = outer_fold
            predictions["inner_fold"] = int(inner_fold)
            predictions["configuration_id"] = cfg_id
            rows.extend(predictions.to_dict("records"))
            histories.append({"configuration_id": cfg_id, "inner_fold": int(inner_fold),
                              "best_epoch": fit.best_epoch, "history": fit.history})
    return pd.DataFrame(rows), epochs, histories


def _enrich_predictions(predictions, test, family, family_config, configuration_id, outer_fold,
                        release, registry_path, checkpoint_path, seed, env_ref):
    metadata = test.set_index("sample_id")
    out = predictions.copy()
    out["run_id"] = release.name
    out["cohort_release_id"] = release.name
    out["cohort_hash"] = sha256_file(release / "pre_event_cohort.csv")
    out["split_release_id"] = release.name + "_splits"
    out["split_hash"] = sha256_file(release / "patient_splits.csv")
    out["model_family"] = family
    out["model_name"] = family_config["model_name"]
    out["configuration_id"] = configuration_id
    out["feature_model"] = family_config.get("feature_model", "none")
    out["fusion_type"] = FUSION_TYPE[family]
    out["cnv_representation"] = family_config.get("cnv_representation", "none")
    out["outer_fold"] = outer_fold
    out["row_key"] = out["sample_id"].astype(str)
    for column in ["biopsy_id", "slide_id", "cnv_id", "strict_pre_event_eligible"]:
        out[column] = out["sample_id"].astype(str).map(metadata[column])
    out["checkpoint_ref"] = str(checkpoint_path)
    out["config_ref"] = str(registry_path)
    out["seed"] = seed
    out["env_ref"] = str(env_ref)
    required_order = [
        "run_id", "cohort_release_id", "cohort_hash", "split_release_id", "split_hash",
        "model_family", "model_name", "configuration_id", "feature_model", "fusion_type",
        "cnv_representation", "outer_fold", "row_key", "patient_id", "biopsy_id", "sample_id",
        "slide_id", "cnv_id", "y_true", "y_prob", "strict_pre_event_eligible", "checkpoint_ref",
        "config_ref", "seed", "env_ref", "y_logit", "y_prob_calibrated",
    ]
    return out[[column for column in required_order if column in out.columns]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--model-registry", required=True)
    parser.add_argument("--family", required=True,
                        choices=["cnv_only", "image_only", "early_fusion", "intermediate_fusion",
                                 "coattention_fusion", "moe"])
    parser.add_argument("--outer-fold", required=True, type=int, choices=range(1, 6))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--cpu-threads", type=int, default=8)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    release = Path(args.release_root).resolve()
    registry_path = Path(args.model_registry).resolve()
    output_root = Path(args.output_root).resolve()
    if REPO_ROOT == output_root or REPO_ROOT in output_root.parents:
        raise SystemExit("training output must remain outside Git")
    fold_dir = output_root / args.family / f"fold{args.outer_fold}"
    completion_path = fold_dir / "fold_completion.json"
    if args.resume and completion_path.exists():
        print(f"already complete: {completion_path}")
        return 0
    if fold_dir.exists() and any(fold_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"non-empty output exists: {fold_dir}; pass --overwrite")
    fold_dir.mkdir(parents=True, exist_ok=True)
    with registry_path.open() as handle:
        registry = yaml.safe_load(handle)
    family_config = registry["families"][args.family]
    candidates = family_config["candidates"]
    manifest_path = release / "training_manifest_v2.csv"
    manifest = pd.read_csv(manifest_path, dtype={"sample_id": str, "canonical_row_key": str})
    fold_col = "fold_id_rep01"
    outer_test = manifest[manifest[fold_col].eq(args.outer_fold)].copy()
    outer_train = manifest[manifest[fold_col].ne(args.outer_fold)].copy()
    overlap = set(outer_train["patient_id"]) & set(outer_test["patient_id"])
    if overlap:
        raise SystemExit(f"outer patient leakage: {sorted(overlap)}")
    inner_folds = int(registry["inner_cv"]["n_folds"])
    seed = int(registry["inner_cv"]["seed"]) + args.outer_fold * 1000
    assignments = make_inner_assignments(outer_train, inner_folds, seed)
    assignments.to_csv(fold_dir / "inner_fold_assignments.csv", index=False)

    cnv_matrix, feature_names = load_cnv_matrix(release / registry["feature_views"]["cnv"])
    image_index_rel = registry["feature_views"].get("image_index") or registry["feature_views"]["uni2_index"]
    image_index = pd.read_csv(release / image_index_rel, dtype={"sample_id": str})
    store = CanonicalFeatureStore(image_index, cnv_matrix, feature_names)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else torch.device(args.device)
    if args.family != "cnv_only" and device.type != "cuda":
        print("[warn] neural family running without CUDA", file=sys.stderr)

    histories = []
    if args.family == "cnv_only":
        inner_predictions = _cnv_inner(args.outer_fold, outer_train, assignments, candidates,
                                       cnv_matrix, feature_names, seed, args.cpu_threads)
        winner, leaderboard = select_per_outer_fold(
            inner_predictions, outer_test_patients={args.outer_fold: set(outer_test["patient_id"].astype(str))})
        selected_id = str(winner[args.outer_fold])
        selected = next(c for c in candidates if c["configuration_id"] == selected_id)
        matrix = cnv_matrix.set_index("sample_id")[feature_names]
        final_model = build_cnv_pipeline(selected, seed, n_jobs=args.cpu_threads)
        final_model.fit(matrix.loc[outer_train["sample_id"]], outer_train["y_progressor"].astype(int))
        probability = final_model.predict_proba(matrix.loc[outer_test["sample_id"]])[:, 1]
        outer_predictions = pd.DataFrame({
            "sample_id": outer_test["sample_id"].astype(str).values,
            "patient_id": outer_test["patient_id"].astype(str).values,
            "y_true": outer_test["y_progressor"].astype(int).values,
            "y_prob": probability,
            "y_logit": np.log(np.clip(probability, 1e-8, 1 - 1e-8) / np.clip(1 - probability, 1e-8, 1)),
        })
        checkpoint = fold_dir / "model.joblib"
        joblib.dump(final_model, checkpoint)
        pd.DataFrame({"feature": feature_names,
                      "importance": genomic_feature_importance(final_model, feature_names)}
                     ).sort_values("importance", ascending=False).to_csv(
            fold_dir / "cnv_feature_importance.csv", index=False)
    else:
        inner_predictions, epochs, histories = _neural_inner(
            args.family, args.outer_fold, outer_train, assignments, candidates, store, device, seed)
        winner, leaderboard = select_per_outer_fold(
            inner_predictions, outer_test_patients={args.outer_fold: set(outer_test["patient_id"].astype(str))})
        selected_id = str(winner[args.outer_fold])
        selected = next(c for c in candidates if c["configuration_id"] == selected_id)
        final_epochs = max(1, int(np.median(epochs[selected_id])))
        fit = _fit(args.family, outer_train, None, store, selected, device, seed, fixed_epochs=final_epochs)
        batch_size = int(selected.get("batch_size", 8))
        outer_predictions = _predict(fit.model, args.family, outer_test, store, device, batch_size,
                                     fit.cnv_median, fit.cnv_mean, fit.cnv_std, with_gate=(args.family == "moe"))
        if args.family == "moe":
            gate_cols = ["sample_id", "patient_id", "y_true", "y_prob",
                         "w_image", "w_cnv", "w_multimodal", "routed_expert"]
            outer_predictions[[c for c in gate_cols if c in outer_predictions.columns]].to_csv(
                fold_dir / "moe_routing.csv", index=False)
            outer_predictions = outer_predictions.drop(
                columns=[c for c in ["w_image", "w_cnv", "w_multimodal", "routed_expert"] if c in outer_predictions.columns])
        checkpoint = fold_dir / "model.pt"
        torch.save({
            "state_dict": fit.model.state_dict(), "family": args.family, "configuration": selected,
            "final_epochs": final_epochs, "cnv_median": fit.cnv_median,
            "cnv_mean": fit.cnv_mean, "cnv_std": fit.cnv_std,
        }, checkpoint)
        histories.append({"configuration_id": selected_id, "stage": "final_outer_train",
                          "fixed_epochs": final_epochs, "history": fit.history})

    inner_predictions.to_csv(fold_dir / "inner_validation_predictions.csv", index=False)
    leaderboard.to_csv(fold_dir / "inner_validation_leaderboard.csv", index=False)
    selected_inner = inner_predictions[inner_predictions["configuration_id"].eq(selected_id)].copy()
    validation_patient = patient_max_predictions(selected_inner)
    threshold = select_threshold(validation_patient, registry["threshold"]["criterion"],
                                 float(registry["threshold"]["target"]))
    calibrated, calibrator, calibration_status = _fit_platt(validation_patient, outer_predictions["y_prob"].to_numpy())
    outer_predictions["y_prob_calibrated"] = calibrated
    calibrator_path = fold_dir / "platt_calibrator.joblib"
    joblib.dump({"model": calibrator, "status": calibration_status, "input_column": "y_prob"}, calibrator_path)
    env_ref = fold_dir / "environment.txt"
    env_ref.write_text(f"python={sys.executable}\nversion={sys.version}\ntorch={torch.__version__}\n"
                       f"cuda={torch.cuda.is_available()}\n", encoding="utf-8")
    enriched = _enrich_predictions(outer_predictions, outer_test, args.family, family_config, selected_id,
                                   args.outer_fold, release, registry_path, checkpoint, seed, env_ref)
    enriched.to_csv(fold_dir / "outer_test_predictions.csv", index=False)
    validation_problems = validate_predictions(enriched, expected_fold_values=[args.outer_fold])
    if set(outer_test["sample_id"].astype(str)) != set(enriched["row_key"].astype(str)):
        validation_problems.append("outer prediction row-key mismatch")
    if enriched["y_prob"].nunique(dropna=False) < 2:
        validation_problems.append("outer-test probabilities are constant")
    if validation_problems:
        (fold_dir / "artifact_validation.json").write_text(
            json.dumps({"status": "FAIL", "problems": validation_problems}, indent=2) + "\n", encoding="utf-8")
        raise SystemExit("artifact validation failed: " + "; ".join(validation_problems))
    (fold_dir / "resolved_config.yaml").write_text(yaml.safe_dump({
        "family": args.family, "outer_fold": args.outer_fold, "selected_configuration": selected,
        "registry_version": registry["registry_version"],
    }, sort_keys=False), encoding="utf-8")
    (fold_dir / "training_history.json").write_text(json.dumps(histories, indent=2) + "\n", encoding="utf-8")
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    metadata = {
        "family": args.family, "outer_fold": args.outer_fold, "selected_configuration_id": selected_id,
        "validation_threshold": threshold.__dict__,
        "n_outer_train_rows": len(outer_train), "n_outer_test_rows": len(outer_test),
        "n_outer_train_patients": int(outer_train["patient_id"].nunique()),
        "n_outer_test_patients": int(outer_test["patient_id"].nunique()),
        "git_commit": git_commit, "manifest_sha256": sha256_file(manifest_path),
        "registry_sha256": sha256_file(registry_path), "device": str(device),
        "calibration_status": calibration_status,
        "outer_threshold_counts": {
            "validation_selected": _threshold_counts(patient_max_predictions(outer_predictions), threshold.threshold),
            "default_0p5": _threshold_counts(patient_max_predictions(outer_predictions), 0.5),
        },
    }
    (fold_dir / "fold_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    completion = {"status": "PASS", "family": args.family, "outer_fold": args.outer_fold,
                  "selected_configuration_id": selected_id, "n_predictions": int(len(enriched)),
                  "n_patients": int(enriched["patient_id"].nunique()), "validation_problems": []}
    completion_path.write_text(json.dumps(completion, indent=2) + "\n", encoding="utf-8")
    (fold_dir / "artifact_validation.json").write_text(
        json.dumps({"status": "PASS", "problems": []}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

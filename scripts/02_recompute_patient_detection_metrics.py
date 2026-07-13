#!/usr/bin/env python
"""Recompute LGD2+ patient-level detection metrics from external predictions."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.cohort_filters import exclude_current_event_rows
from barrett.evaluation.aggregation import aggregate_predictions
from barrett.evaluation.bootstrap import bootstrap_cis
from barrett.evaluation.io import (
    MODEL_GROUP_COLS,
    WarningRow,
    group_columns,
    join_master,
    load_manifest,
    load_master,
    load_predictions,
    model_label,
    resolve_files,
)
from barrett.evaluation.metrics import METRIC_ORDER, compute_metrics
from barrett.labels.endpoints import LGD2_CLINICAL_DEFINITION, LGD2_ENDPOINT

DEFAULT_OUTPUT_DIR = Path("reports/thesis_ch1")
MANIFEST_PATH = Path("docs/final_results_manifest.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument(
        "--experiment-root",
        default=os.environ.get("BARRETTS_EXPERIMENT_ROOT"),
        help="Root for external relative paths. Defaults to repo parent.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--endpoint", default=LGD2_ENDPOINT)
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--include-status",
        action="append",
        default=["FINAL_CANDIDATE"],
        help="Manifest status to include. Repeatable.",
    )
    return parser.parse_args()


def experiment_root(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value).expanduser().resolve()
    return REPO_ROOT.parent.resolve()


def format_float(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return str(value)
    try:
        return f"{float(value):.3f}"
    except Exception:
        return str(value)


def make_markdown(df: pd.DataFrame, warnings: list[WarningRow], analysis_set: str) -> str:
    patient = df[df["aggregation"].eq("patient_max")].copy()
    patient = patient.sort_values(["auprc", "roc_auc"], ascending=False)
    lines = [
        f"# LGD2+ Patient-Level Metrics - {analysis_set}",
        "",
        f"Endpoint: `{LGD2_ENDPOINT}`.",
        f"Clinical definition: {LGD2_CLINICAL_DEFINITION}.",
        "Evaluation: 5-fold patient-disjoint out-of-fold predictions.",
        "Primary reporting level: `patient_max`.",
        "",
        "## Ranked patient_max table",
        "",
        "| rank | result_id | model | AUPRC | ROC AUC | sensitivity | specificity | PPV | NPV | TP | FP | TN | FN | FP/detected | Brier |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, (_, row) in enumerate(patient.iterrows(), 1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    f"`{row['result_id']}`",
                    str(row["model_key"]),
                    format_float(row["auprc"]),
                    format_float(row["roc_auc"]),
                    format_float(row["sensitivity"]),
                    format_float(row["specificity"]),
                    format_float(row["ppv"]),
                    format_float(row["npv"]),
                    format_float(row["tp"]),
                    format_float(row["fp"]),
                    format_float(row["tn"]),
                    format_float(row["fn"]),
                    format_float(row["false_positives_per_detected_progressor"]),
                    format_float(row["brier_score"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Detected and missed progressors",
            "",
            "| result_id | model | progressors detected | progressors missed | false positives | false positives per detected progressor |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in patient.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['result_id']}`",
                    str(row["model_key"]),
                    format_float(row["progressors_detected"]),
                    format_float(row["progressors_missed"]),
                    format_float(row["fp"]),
                    format_float(row["false_positives_per_detected_progressor"]),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Notes", ""])
    if analysis_set == "early_prediction_only":
        lines.append("- Excludes prediction rows joined to master rows with `DaysFromCurrentToEvent == 0`.")
    else:
        lines.append("- Includes all labelled prediction rows in the selected final-candidate LGD2+ files.")
    lines.append("- Threshold-dependent metrics use default threshold `0.5`; fixed operating point columns are in the CSV.")
    lines.append("- Bootstrap confidence intervals are reported for patient-level aggregations; biopsy/sample rows keep CI columns blank.")
    if any(w.severity in {"WARN", "SKIP"} for w in warnings):
        lines.append("- See `lgd2_metric_recompute_warnings.md` for skipped/manual-review details.")
    return "\n".join(lines) + "\n"


def warnings_markdown(warnings: list[WarningRow]) -> str:
    lines = [
        "# LGD2+ Metric Recompute Warnings",
        "",
        "| result_id | severity | message |",
        "|---|---|---|",
    ]
    if not warnings:
        lines.append("| none | OK | No warnings. |")
    else:
        for warning in warnings:
            lines.append(f"| `{warning.result_id}` | `{warning.severity}` | {warning.message} |")
    return "\n".join(lines) + "\n"


def add_patient_counts(metrics: dict[str, object], agg_df: pd.DataFrame) -> None:
    metrics["n_patients"] = int(agg_df["patient_id"].nunique(dropna=True))
    patient_labels = agg_df.groupby("patient_id")["y_true"].max()
    metrics["n_positive_patients"] = int((patient_labels == 1).sum())
    metrics["n_negative_patients"] = int((patient_labels == 0).sum())


def main() -> int:
    args = parse_args()
    root = experiment_root(args.experiment_root)
    manifest_path = Path(args.manifest)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    full_manifest = pd.read_csv(manifest_path).fillna("")
    manifest = load_manifest(manifest_path, args.endpoint, args.include_status)
    master = load_master(root, manifest_path, args.endpoint)
    warnings: list[WarningRow] = []
    all_rows: list[dict[str, object]] = []

    review_rows = full_manifest[
        full_manifest["endpoint"].eq(args.endpoint)
        & full_manifest["task"].eq("binary progression")
        & ~full_manifest["status"].isin(args.include_status)
        & full_manifest["status"].isin(["REVIEW_MANUALLY", "NEEDS_RECOMPUTE", "MISSING"])
    ]
    for _, review_row in review_rows.iterrows():
        warnings.append(
            WarningRow(
                str(review_row["result_id"]),
                "INFO",
                f"Not recomputed because manifest status is {review_row['status']}.",
            )
        )

    for _, manifest_row in manifest.iterrows():
        result_id = manifest_row["result_id"]
        files = resolve_files(root, str(manifest_row["prediction_file"]))
        if not files:
            warnings.append(WarningRow(result_id, "SKIP", "No prediction files resolved from manifest pattern."))
            continue
        pred = load_predictions(files)
        if pred.empty:
            warnings.append(WarningRow(result_id, "SKIP", "Prediction files loaded no rows."))
            continue
        # Late-fusion files embed cnv_only/img_only/mean/stack_logit; keep only the
        # fusion methods this manifest row declares (mean; stack_logit). The unimodal
        # baselines have their own canonical manifest rows, so excluding them here
        # prevents duplicate metric rows.
        if str(manifest_row["fusion_type"]) == "late_fusion" and "fusion_method" in pred.columns:
            allowed = {m.strip() for m in str(manifest_row["model_name"]).split(";") if m.strip()}
            pred = pred[pred["fusion_method"].isin(allowed)].copy()
            if pred.empty:
                warnings.append(WarningRow(result_id, "SKIP", f"No rows for late-fusion methods {sorted(allowed)}."))
                continue
            dup = pred.duplicated(subset=["fusion_method", "sample_id"]).sum()
            if dup:
                warnings.append(WarningRow(result_id, "WARN", f"{int(dup)} duplicate (fusion_method, sample_id) rows."))
        pred, join_key = join_master(pred, master)
        if pred["patient_id"].isna().any():
            n_missing = int(pred["patient_id"].isna().sum())
            warnings.append(WarningRow(result_id, "SKIP", f"{n_missing} rows lack patient_id after join; skipped."))
            continue
        if pred["y_true"].isna().any():
            n_missing = int(pred["y_true"].isna().sum())
            warnings.append(WarningRow(result_id, "WARN", f"{n_missing} rows with missing labels were dropped."))
        pred = pred.dropna(subset=["patient_id", "y_true", "y_prob"]).copy()
        if pred.empty:
            warnings.append(WarningRow(result_id, "SKIP", "No labelled prediction rows after cleaning."))
            continue
        if pred["fold"].notna().any():
            fold_counts = pred.groupby("patient_id")["fold"].nunique(dropna=True)
            leaked = int((fold_counts > 1).sum())
            if leaked:
                warnings.append(WarningRow(result_id, "WARN", f"{leaked} patients appear in multiple folds."))
        group_cols = group_columns(pred)
        grouped = pred.groupby(group_cols, dropna=False) if group_cols else [((), pred)]
        for group_key, model_df in grouped:
            if not isinstance(group_key, tuple):
                group_key = (group_key,)
            template = pd.Series({col: val for col, val in zip(group_cols, group_key)})
            model_key = model_label(template, str(manifest_row["model_name"]))
            for analysis_set in ["all_samples", "early_prediction_only"]:
                analysis_df = model_df
                removed_current_event = 0
                if analysis_set == "early_prediction_only":
                    before = len(analysis_df)
                    analysis_df = exclude_current_event_rows(analysis_df)
                    removed_current_event = before - len(analysis_df)
                    if removed_current_event == 0:
                        warnings.append(WarningRow(result_id, "WARN", f"{model_key}: early filter removed 0 rows."))
                for aggregation in ["patient_max", "patient_mean", "biopsy_max", "biopsy_mean", "sample"]:
                    agg_df = aggregate_predictions(analysis_df, aggregation)
                    agg_df = agg_df.dropna(subset=["unit_id", "y_true", "y_prob"]).copy()
                    if agg_df.empty or agg_df["unit_id"].duplicated().any():
                        warnings.append(WarningRow(result_id, "WARN", f"{model_key}: invalid {aggregation} aggregation."))
                        continue
                    metrics = compute_metrics(agg_df["y_true"], agg_df["y_prob"])
                    add_patient_counts(metrics, agg_df)
                    if aggregation.startswith("patient_"):
                        metrics.update(bootstrap_cis(agg_df[["y_true", "y_prob"]], args.bootstrap, args.seed))
                    else:
                        metrics.update(bootstrap_cis(agg_df[["y_true", "y_prob"]], 0, args.seed))
                    row = {
                        "result_id": result_id,
                        "analysis_set": analysis_set,
                        "aggregation": aggregation,
                        "endpoint": args.endpoint,
                        "clinical_definition": LGD2_CLINICAL_DEFINITION,
                        "evaluation_design": "5-fold patient-disjoint CV",
                        "model_family": manifest_row["model_family"],
                        "manifest_model_name": manifest_row["model_name"],
                        "model_key": model_key,
                        "fusion_type": manifest_row["fusion_type"],
                        "feature_model": manifest_row["feature_model"],
                        "join_key": join_key,
                        "n_prediction_files": len(files),
                        "removed_current_event_rows": int(removed_current_event),
                    }
                    row.update(metrics)
                    all_rows.append(row)

    results = pd.DataFrame(all_rows)
    if results.empty:
        raise RuntimeError("No metric rows were computed.")
    ordered_cols = [
        "result_id",
        "analysis_set",
        "aggregation",
        "endpoint",
        "clinical_definition",
        "evaluation_design",
        "model_family",
        "manifest_model_name",
        "model_key",
        "fusion_type",
        "feature_model",
        "join_key",
        "n_prediction_files",
        "removed_current_event_rows",
    ] + METRIC_ORDER
    ci_cols = [c for c in results.columns if c.endswith("_ci_low") or c.endswith("_ci_high")]
    results = results[[c for c in ordered_cols + sorted(ci_cols) if c in results.columns]]

    for analysis_set in ["all_samples", "early_prediction_only"]:
        subset = results[results["analysis_set"].eq(analysis_set)].copy()
        csv_path = out_dir / f"lgd2_patient_level_metrics_{analysis_set}.csv"
        md_path = out_dir / f"lgd2_patient_level_metrics_{analysis_set}.md"
        subset.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
        md_path.write_text(make_markdown(subset, warnings, analysis_set))

    (out_dir / "lgd2_metric_recompute_warnings.md").write_text(warnings_markdown(warnings))
    print(f"Wrote {len(results)} metric rows to {out_dir}")
    print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

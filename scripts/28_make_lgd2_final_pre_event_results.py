#!/usr/bin/env python
"""Generate final patient-level results from complete external OOF predictions."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.metrics import compute_metrics, confusion_counts, safe_div  # noqa: E402
from barrett.evaluation.paired_comparison import compare  # noqa: E402
from barrett.evaluation.tables import markdown_table  # noqa: E402


FAMILIES = (
    "cnv_only", "image_only", "early_fusion", "intermediate_fusion",
    "late_mean", "late_stack_logit",
)
PRIMARY_CONTRASTS = (
    ("early_fusion", "cnv_only", "primary"),
    ("intermediate_fusion", "cnv_only", "primary"),
    ("late_mean", "cnv_only", "primary"),
    ("late_stack_logit", "cnv_only", "primary"),
    ("image_only", "cnv_only", "contextual"),
    ("early_fusion", "image_only", "contextual"),
    ("intermediate_fusion", "image_only", "contextual"),
    ("late_mean", "image_only", "contextual"),
    ("late_stack_logit", "image_only", "contextual"),
)


def _patient_max(frame: pd.DataFrame, probability: str = "y_prob") -> pd.DataFrame:
    return frame.groupby(["patient_id", "outer_fold"], as_index=False).agg(
        y_true=("y_true", "max"), y_prob=(probability, "max")
    )


def _cross_fitted_decisions(frame: pd.DataFrame, output_root: Path, family: str) -> tuple[pd.DataFrame, list[dict]]:
    parts, fold_rows = [], []
    for fold in range(1, 6):
        patient = _patient_max(frame[frame["outer_fold"].eq(fold)])
        metadata = json.loads(
            (output_root / family / f"fold{fold}" / "fold_metadata.json").read_text(encoding="utf-8")
        )
        choice = metadata["validation_threshold"]
        threshold = float(choice["threshold"])
        patient["threshold"] = threshold
        patient["y_pred"] = (patient["y_prob"] >= threshold).astype(int)
        tn, fp, fn, tp = confusion_counts(patient["y_true"].to_numpy(), patient["y_pred"].to_numpy())
        fold_rows.append({
            "model_family": family, "outer_fold": fold, "threshold": threshold,
            "validation_achieved_specificity": choice.get("achieved"),
            "validation_fallback": choice.get("fallback"),
            "n_patients": len(patient), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        })
        parts.append(patient)
    return pd.concat(parts, ignore_index=True), fold_rows


def _decision_metrics(decisions: pd.DataFrame) -> dict[str, float]:
    tn, fp, fn, tp = confusion_counts(
        decisions["y_true"].to_numpy(), decisions["y_pred"].to_numpy()
    )
    sensitivity = safe_div(tp, tp + fn)
    specificity = safe_div(tn, tn + fp)
    return {
        "sensitivity": sensitivity, "specificity": specificity,
        "ppv": safe_div(tp, tp + fp), "npv": safe_div(tn, tn + fn),
        "balanced_accuracy": float(np.nanmean([sensitivity, specificity])),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "progressors_detected": tp, "progressors_missed": fn,
        "false_positives_per_detected_progressor": safe_div(fp, tp),
    }


def _fmt(value) -> str:
    if pd.isna(value):
        return "NA"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.3f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--reports-dir", default=str(REPO_ROOT / "reports/thesis_ch1"))
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args()
    output = Path(args.output_root).resolve()
    reports = Path(args.reports_dir)
    completeness_path = output / "oof/completeness_manifest.json"
    if not completeness_path.exists():
        raise SystemExit("missing OOF completeness manifest; run script 27 first")
    completeness = json.loads(completeness_path.read_text(encoding="utf-8"))
    if completeness.get("status") != "PASS":
        raise SystemExit("OOF completeness manifest is not PASS")

    patient_frames: dict[str, pd.DataFrame] = {}
    metric_rows, operating_rows = [], []
    for family in FAMILIES:
        path = output / f"oof/{family}_oof_predictions.csv"
        frame = pd.read_csv(path, dtype={"row_key": str})
        patient = _patient_max(frame)
        patient_frames[family] = patient
        discrimination = compute_metrics(patient["y_true"], patient["y_prob"], threshold=0.5)
        decisions, fold_rows = _cross_fitted_decisions(frame, output, family)
        clinical = _decision_metrics(decisions)
        row = {
            "model_family": family, "aggregation": "patient_max", "analysis_set": "strict_pre_event",
            "n_patients": len(patient), "n_positive_patients": int(patient["y_true"].sum()),
            "n_negative_patients": int((patient["y_true"] == 0).sum()),
            "auprc": discrimination["auprc"], "roc_auc": discrimination["roc_auc"],
            "brier_score": discrimination["brier_score"], "ece": discrimination["ece"],
            "threshold_method": "cross_fitted_inner_validation_target_90_specificity",
            **clinical,
        }
        metric_rows.append(row)
        operating_rows.extend(fold_rows)
    metrics = pd.DataFrame(metric_rows).sort_values(
        ["auprc", "roc_auc", "brier_score"], ascending=[False, False, True]
    ).reset_index(drop=True)
    metrics.insert(0, "rank", np.arange(1, len(metrics) + 1))

    paired_rows = []
    for index, (a, b, role) in enumerate(PRIMARY_CONTRASTS):
        result = compare(
            patient_frames[a][["patient_id", "y_true", "y_prob"]],
            patient_frames[b][["patient_id", "y_true", "y_prob"]],
            n_boot=args.bootstrap, seed=20260713 + index,
        )
        paired_rows.append({"model_a": a, "model_b": b, "contrast_role": role, **result})
    paired = pd.DataFrame(paired_rows)
    operating = pd.DataFrame(operating_rows)
    comparison = metrics[[
        "rank", "model_family", "auprc", "roc_auc", "brier_score", "ece",
        "sensitivity", "specificity", "ppv", "npv", "tp", "fp", "tn", "fn",
        "false_positives_per_detected_progressor",
    ]].copy()

    reports.mkdir(parents=True, exist_ok=True)
    outputs = {
        "lgd2_final_pre_event_patient_metrics": metrics,
        "lgd2_final_pre_event_model_comparison": comparison,
        "lgd2_final_pre_event_paired_differences": paired,
        "lgd2_final_pre_event_cross_fitted_operating_points": operating,
    }
    for name, table in outputs.items():
        table.to_csv(reports / f"{name}.csv", index=False)
        (reports / f"{name}.md").write_text(_markdown_table(name, table), encoding="utf-8")

    best = metrics.iloc[0]
    early = paired[(paired["model_a"] == "early_fusion") & (paired["model_b"] == "cnv_only")].iloc[0]
    supports_early = early["delta_auprc_ci_low"] > 0
    interpretation = [
        "# LGD2+ Final Pre-event Interpretation",
        "",
        f"Highest patient-level AUPRC: **{best['model_family']}** ({best['auprc']:.3f}).",
        f"Early fusion minus CNV AUPRC: {early['delta_auprc']:.3f} "
        f"(95% paired bootstrap CI {early['delta_auprc_ci_low']:.3f} to {early['delta_auprc_ci_high']:.3f}).",
        "",
        (
            "The paired interval excludes zero, supporting an internal-cohort improvement from adding histopathology."
            if supports_early else
            "The paired interval includes zero; the rerun does not establish a statistically clear early-fusion improvement."
        ),
        "",
        "This endpoint is future next-biopsy LGD2+ neoplastic progression, not OAC-only cancer progression. External generalisability was not tested.",
    ]
    (reports / "lgd2_final_pre_event_interpretation.md").write_text("\n".join(interpretation) + "\n", encoding="utf-8")
    (reports / "lgd2_final_pre_event_warnings.md").write_text(
        "# LGD2+ Final Pre-event Warnings\n\nNone generated by the result script.\n", encoding="utf-8"
    )
    print(f"PASS: wrote final reports; best AUPRC={best['model_family']} {best['auprc']:.3f}")
    return 0


def _markdown_table(title: str, table: pd.DataFrame) -> str:
    return (
        f"# {title.replace('_', ' ').title()}\n\n"
        + markdown_table(table, list(table.columns))
        + "\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())

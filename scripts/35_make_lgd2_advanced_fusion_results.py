#!/usr/bin/env python
"""Compare advanced architectures with frozen strict pre-event baselines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.metrics import compute_metrics, confusion_counts, safe_div  # noqa: E402
from barrett.evaluation.paired_comparison import compare  # noqa: E402
from barrett.evaluation.tables import markdown_table  # noqa: E402
from barrett.training.advanced import ALL_FAMILIES  # noqa: E402


BASELINES = ("cnv_only", "image_only", "early_fusion", "intermediate_fusion", "coattention_fusion", "late_mean", "late_stack_logit")


def patient_max(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby(["patient_id", "outer_fold"], as_index=False).agg(y_true=("y_true", "max"), y_prob=("y_prob", "max"))


def clinical(frame: pd.DataFrame, root: Path, family: str) -> dict:
    rows = []
    for fold in range(1, 6):
        patient = patient_max(frame[frame["outer_fold"].eq(fold)])
        metadata = json.loads((root / family / f"fold{fold}/fold_metadata.json").read_text())
        threshold = float(metadata["validation_threshold"]["threshold"])
        patient["y_pred"] = (patient["y_prob"] >= threshold).astype(int)
        rows.append(patient)
    decisions = pd.concat(rows, ignore_index=True)
    tn, fp, fn, tp = confusion_counts(decisions["y_true"], decisions["y_pred"])
    sensitivity, specificity = safe_div(tp, tp + fn), safe_div(tn, tn + fp)
    return {"sensitivity": sensitivity, "specificity": specificity, "ppv": safe_div(tp, tp + fp),
            "npv": safe_div(tn, tn + fn), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "false_positives_per_detected_progressor": safe_div(fp, tp)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--advanced-root", required=True)
    parser.add_argument("--baseline-root", required=True)
    parser.add_argument("--reports-dir", default=str(REPO_ROOT / "reports/thesis_ch1"))
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args()
    advanced, baseline, reports = Path(args.advanced_root).resolve(), Path(args.baseline_root).resolve(), Path(args.reports_dir)
    frames, roots = {}, {}
    for family in BASELINES:
        frames[family] = pd.read_csv(baseline / f"oof/{family}_oof_predictions.csv", dtype={"row_key": str})
        roots[family] = baseline
    for family in sorted(ALL_FAMILIES):
        frames[family] = pd.read_csv(advanced / f"oof/{family}_oof_predictions.csv", dtype={"row_key": str})
        roots[family] = advanced
    patients, metric_rows = {}, []
    for family, frame in frames.items():
        patient = patient_max(frame)
        patients[family] = patient
        metrics = compute_metrics(patient["y_true"], patient["y_prob"], threshold=0.5)
        metric_rows.append({"model_family": family, "analysis_role": "advanced_post_hoc" if family in ALL_FAMILIES else "locked_reference",
                            "n_patients": len(patient), "n_positive": int(patient["y_true"].sum()),
                            "auprc": metrics["auprc"], "roc_auc": metrics["roc_auc"],
                            "brier_score": metrics["brier_score"], "ece": metrics["ece"],
                            **clinical(frame, roots[family], family)})
    table = pd.DataFrame(metric_rows).sort_values(["auprc", "roc_auc", "brier_score"], ascending=[False, False, True]).reset_index(drop=True)
    table.insert(0, "rank", np.arange(1, len(table) + 1))
    paired_rows = []
    for index, family in enumerate(sorted(ALL_FAMILIES)):
        for reference in ("late_mean", "cnv_only", "image_only"):
            result = compare(patients[family][["patient_id", "y_true", "y_prob"]],
                             patients[reference][["patient_id", "y_true", "y_prob"]],
                             n_boot=args.bootstrap, seed=20260713 + index * 3 + BASELINES.index(reference))
            paired_rows.append({"model_a": family, "model_b": reference, "contrast_role": "supplementary_post_hoc", **result})
    paired = pd.DataFrame(paired_rows)
    reports.mkdir(parents=True, exist_ok=True)
    table.to_csv(reports / "lgd2_advanced_fusion_model_comparison.csv", index=False)
    paired.to_csv(reports / "lgd2_advanced_fusion_paired_differences.csv", index=False)
    (reports / "lgd2_advanced_fusion_model_comparison.md").write_text("# LGD2+ Advanced Fusion Model Comparison\n\n" + markdown_table(table, list(table.columns)) + "\n")
    (reports / "lgd2_advanced_fusion_paired_differences.md").write_text("# LGD2+ Advanced Fusion Paired Differences\n\n" + markdown_table(paired, list(paired.columns)) + "\n")
    best_advanced = table[table["model_family"].isin(ALL_FAMILIES)].iloc[0]
    best_all = table.iloc[0]
    lines = ["# LGD2+ Advanced Fusion Interpretation", "", "These architectures were specified after inspection of the locked primary results and are supplementary post-hoc comparisons.", "",
             f"Best advanced architecture by AUPRC: **{best_advanced.model_family}** ({best_advanced.auprc:.3f}).",
             f"Best model across the combined table: **{best_all.model_family}** ({best_all.auprc:.3f}).", ""]
    contrast = paired[(paired["model_a"] == best_advanced.model_family) & (paired["model_b"] == "late_mean")].iloc[0]
    lines.append(f"Best advanced minus late mean AUPRC: {contrast.delta_auprc:.3f} (95% paired bootstrap CI {contrast.delta_auprc_ci_low:.3f} to {contrast.delta_auprc_ci_high:.3f}).")
    (reports / "lgd2_advanced_fusion_interpretation.md").write_text("\n".join(lines) + "\n")
    print(f"PASS: best advanced={best_advanced.model_family} {best_advanced.auprc:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

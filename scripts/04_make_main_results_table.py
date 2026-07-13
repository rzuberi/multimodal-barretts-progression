#!/usr/bin/env python
"""Create thesis-facing LGD2+ model comparison tables and interpretation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.tables import markdown_table, rank_models, select_representative_models

OUT_DIR = Path("reports/thesis_ch1")
MANIFEST = Path("docs/final_results_manifest.csv")
METRIC_COLUMNS = [
    "comparison_slot",
    "rank",
    "result_id",
    "model_family",
    "manifest_model_name",
    "model_key",
    "feature_model",
    "fusion_type",
    "roc_auc",
    "auprc",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
    "tp",
    "fp",
    "tn",
    "fn",
    "progressors_detected",
    "progressors_missed",
    "false_positives_per_detected_progressor",
    "brier_score",
    "ece",
    "threshold_used",
    "n_patients",
    "n_positive_patients",
    "n_negative_patients",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-samples", default=str(OUT_DIR / "lgd2_patient_level_metrics_all_samples.csv"))
    parser.add_argument("--early", default=str(OUT_DIR / "lgd2_patient_level_metrics_early_prediction_only.csv"))
    parser.add_argument("--manifest", default=str(MANIFEST))
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    return parser.parse_args()


def read_patient_max(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"aggregation", "result_id", "model_family", "fusion_type", "auprc", "roc_auc"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"{path} missing required columns: {missing}")
    return df[df["aggregation"].eq("patient_max")].copy()


def make_comparison(metrics: pd.DataFrame) -> pd.DataFrame:
    selected = select_representative_models(metrics)
    return selected[[c for c in METRIC_COLUMNS if c in selected.columns]].copy()


def write_comparison(df: pd.DataFrame, path_csv: Path, path_md: Path, title: str) -> None:
    df.to_csv(path_csv, index=False)
    table_cols = [
        "comparison_slot",
        "result_id",
        "model_key",
        "auprc",
        "roc_auc",
        "sensitivity",
        "specificity",
        "ppv",
        "npv",
        "tp",
        "fp",
        "fn",
        "false_positives_per_detected_progressor",
        "brier_score",
    ]
    lines = [
        f"# {title}",
        "",
        "Rows are representative final-candidate models at `patient_max` aggregation.",
        "Ranking uses AUPRC, then ROC AUC, sensitivity/progressors detected, then lower false-positive burden.",
        "",
        markdown_table(df, [c for c in table_cols if c in df.columns]),
        "",
    ]
    path_md.write_text("\n".join(lines))


def model_name(row: pd.Series) -> str:
    return f"{row['result_id']} ({row['model_key']})"


def summarize_extremes(metrics: pd.DataFrame) -> dict[str, pd.Series]:
    patient = metrics[metrics["aggregation"].eq("patient_max")].copy()
    ranked = rank_models(patient)
    return {
        "best_auprc": ranked.iloc[0],
        "best_auc": patient.sort_values("roc_auc", ascending=False).iloc[0],
        "most_detected": patient.sort_values(["progressors_detected", "auprc"], ascending=[False, False]).iloc[0],
        "fewest_missed": patient.sort_values(["progressors_missed", "auprc"], ascending=[True, False]).iloc[0],
        "lowest_fp_burden": patient[patient["progressors_detected"].gt(0)]
        .sort_values(["false_positives_per_detected_progressor", "auprc"], ascending=[True, False])
        .iloc[0],
    }


def best_family(metrics: pd.DataFrame, family: str) -> pd.Series | None:
    subset = metrics[(metrics["aggregation"].eq("patient_max")) & (metrics["model_family"].eq(family))]
    if subset.empty:
        return None
    return rank_models(subset).iloc[0]


def interpretation(all_metrics: pd.DataFrame, early_metrics: pd.DataFrame, warnings_text: str) -> str:
    all_ext = summarize_extremes(all_metrics)
    early_ext = summarize_extremes(early_metrics)
    all_mm = best_family(all_metrics, "multimodal")
    all_img = best_family(all_metrics, "histology-only")
    all_cnv = best_family(all_metrics, "CNV-only")
    early_mm = best_family(early_metrics, "multimodal")
    lines = [
        "# LGD2+ Results Interpretation",
        "",
        "## All samples",
        "",
        f"- Best AUPRC: {model_name(all_ext['best_auprc'])}, AUPRC {all_ext['best_auprc']['auprc']:.3f}.",
        f"- Best AUC: {model_name(all_ext['best_auc'])}, AUC {all_ext['best_auc']['roc_auc']:.3f}.",
        f"- Most progressors detected: {model_name(all_ext['most_detected'])}, TP {int(all_ext['most_detected']['tp'])}.",
        f"- Fewest progressors missed: {model_name(all_ext['fewest_missed'])}, FN {int(all_ext['fewest_missed']['fn'])}.",
        f"- Lowest false-positive burden: {model_name(all_ext['lowest_fp_burden'])}, FP/detected {all_ext['lowest_fp_burden']['false_positives_per_detected_progressor']:.3f}.",
    ]
    if all_mm is not None and all_cnv is not None:
        lines.append(
            f"- Best multimodal vs CNV-only: multimodal AUPRC {all_mm['auprc']:.3f} vs CNV-only {all_cnv['auprc']:.3f}."
        )
    if all_mm is not None and all_img is not None:
        lines.append(
            f"- Best multimodal vs image-only: multimodal AUPRC {all_mm['auprc']:.3f} vs image-only {all_img['auprc']:.3f}."
        )
    lines.extend(
        [
            "",
            "## Early-prediction-only",
            "",
            f"- Best AUPRC: {model_name(early_ext['best_auprc'])}, AUPRC {early_ext['best_auprc']['auprc']:.3f}.",
            f"- Best AUC: {model_name(early_ext['best_auc'])}, AUC {early_ext['best_auc']['roc_auc']:.3f}.",
        ]
    )
    if all_mm is not None and early_mm is not None:
        same = all_mm["result_id"] == early_mm["result_id"] and all_mm["model_key"] == early_mm["model_key"]
        lines.append(
            "- Ranking conclusion is "
            + ("similar: the same best multimodal family remains strongest." if same else "not identical after excluding at-event rows.")
        )
    headline = early_mm if early_mm is not None else all_ext["best_auprc"]
    lines.extend(
        [
            "",
            "## Recommended headline",
            "",
            f"- Recommended headline model: {model_name(headline)}.",
            "- Use early-prediction-only results as an important sensitivity analysis because at-event rows inflate clinical detectability.",
            "- Do not overclaim small metric differences without confidence intervals and clinical review.",
            "",
            "## Exclusions and caveats",
            "",
            "- Foundation-combo and clinical-augmentation rows remain excluded unless manual-review status changes.",
            "- LGD2+ interpretability status: ABMIL histology interpretation is complete for all eight selected cases; "
            "probability-level fusion case interpretation is complete for the first three case packs; "
            "CNV region/gene interpretation and model-internal fusion attribution remain missing.",
            "- Model comparison is based on saved out-of-fold predictions; no model training was run here.",
            "",
            "## Paired patient-level comparison (added value of histopathology)",
            "",
            "- Paired shared-index bootstrap deltas are in `lgd2_paired_model_differences_all_samples.csv/.md` "
            "and the early-prediction equivalent.",
            "- Adding histopathology to CNV improved internal out-of-fold patient-level discrimination for "
            "next-biopsy LGD2+ progression in the matched cohort: early-fusion UNI2 minus CNV-only has a "
            "delta AUPRC 95% CI excluding zero, and late-fusion UNI2 (mean) minus CNV-only also excludes zero.",
            "- Image-only UNI2 minus CNV-only crosses zero for delta AUPRC, so image-only superiority over CNV "
            "is not established on this internal cohort.",
            "- Model-selected 'best' contrasts are optimistic; where a delta CI crosses zero, no superiority is claimed.",
            "",
            "## Supporting evidence and limitations",
            "",
            "- Modality ablation (image/CNV shuffling) is in `lgd2_modality_ablation_comparison.csv/.md`; "
            "image shuffling degrades performance, supporting a histology contribution. This is supporting "
            "evidence, not causal proof.",
            "- Endpoint is LGD2+ neoplastic progression (`NextBiopsyProgression_LGD2plus`), NOT cancer/OAC "
            "prediction: it includes LGD and HGD and the cohort has a single current-grade OAC row.",
            "- Timing/operating-point caveats: see `lgd2_timing_and_operating_point_limitations.md` "
            "(at-event excluded, not strict known-lead-time; fixed operating points are post-hoc).",
            "- These are internal cross-validated estimates; no external validation.",
        ]
    )
    if warnings_text.strip():
        lines.append("- See `lgd2_table_generation_warnings.md` for table-generation warnings.")
    return "\n".join(lines) + "\n"


def warnings_report(manifest: pd.DataFrame, all_metrics: pd.DataFrame, early_metrics: pd.DataFrame) -> str:
    lines = ["# LGD2+ Table Generation Warnings", "", "| category | item | note |", "|---|---|---|"]
    required = {"auprc", "roc_auc", "sensitivity", "specificity", "ppv", "npv", "tp", "fp", "tn", "fn"}
    for name, df in [("all_samples", all_metrics), ("early_prediction_only", early_metrics)]:
        missing = sorted(required - set(df.columns))
        if missing:
            lines.append(f"| missing_columns | {name} | {', '.join(missing)} |")
    review = manifest[manifest["status"].eq("REVIEW_MANUALLY")]
    for _, row in review.iterrows():
        lines.append(f"| review_manually | {row['result_id']} | {row['notes']} |")
    if "lgd2_foundation_combo" not in set(all_metrics["result_id"]):
        lines.append("| skipped | lgd2_foundation_combo | Not included because patient IDs were not validated in manifest. |")
    if not (all_metrics["fusion_type"].astype(str).str.contains("late", case=False, na=False)).any():
        lines.append("| unavailable | late_fusion | No validated patient-level late-fusion row found in recomputed metrics. |")
    if len(lines) == 4:
        lines.append("| none | none | No warnings. |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_metrics = read_patient_max(args.all_samples)
    early_metrics = read_patient_max(args.early)
    manifest = pd.read_csv(args.manifest).fillna("")
    all_cmp = make_comparison(all_metrics)
    early_cmp = make_comparison(early_metrics)
    write_comparison(
        all_cmp,
        out_dir / "lgd2_main_model_comparison.csv",
        out_dir / "lgd2_main_model_comparison.md",
        "LGD2+ Main Model Comparison",
    )
    write_comparison(
        early_cmp,
        out_dir / "lgd2_early_prediction_model_comparison.csv",
        out_dir / "lgd2_early_prediction_model_comparison.md",
        "LGD2+ Early-Prediction Model Comparison",
    )
    warnings = warnings_report(manifest, all_metrics, early_metrics)
    (out_dir / "lgd2_table_generation_warnings.md").write_text(warnings)
    (out_dir / "lgd2_results_interpretation.md").write_text(interpretation(all_metrics, early_metrics, warnings))
    print(f"Wrote model-comparison reports to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


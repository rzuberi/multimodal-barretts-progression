#!/usr/bin/env python
"""Create the LGD2+ thesis cohort-flow table from the external master cohort."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.cohort_filters import exclude_current_event_rows
from barrett.evaluation.io import join_master, load_predictions, resolve_files
from barrett.labels.endpoints import LGD2_ENDPOINT

MANIFEST_PATH = Path("docs/final_results_manifest.csv")
OUT_DIR = Path("reports/thesis_ch1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--experiment-root", default=os.environ.get("BARRETTS_EXPERIMENT_ROOT"))
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    return parser.parse_args()


def experiment_root(value: str | None) -> Path:
    return Path(value).expanduser().resolve() if value else REPO_ROOT.parent.resolve()


def read_master(root: Path, manifest: pd.DataFrame) -> tuple[pd.DataFrame, list[str], Path]:
    rows = manifest[manifest["result_id"].eq("lgd2_primary_cohort")]
    if rows.empty:
        raise RuntimeError("lgd2_primary_cohort not found in manifest")
    path = root / rows.iloc[0]["external_result_path"]
    master = pd.read_csv(path)
    warnings: list[str] = []
    for column in ["PatientID", "BiopsyID_int", "CNVAbsPath", "ImageAbsPath", "DaysFromCurrentToEvent", LGD2_ENDPOINT]:
        if column not in master.columns:
            warnings.append(f"Missing expected master column: {column}")
    return master, warnings, path


def add_row(rows: list[dict[str, object]], section: str, metric: str, value: object, notes: str = "") -> None:
    rows.append({"section": section, "metric": metric, "value": value, "notes": notes})


def label_counts(df: pd.DataFrame, label_col: str) -> dict[str, int]:
    labels = pd.to_numeric(df[label_col], errors="coerce")
    return {
        "positive": int((labels == 1).sum()),
        "negative": int((labels == 0).sum()),
        "missing": int(labels.isna().sum()),
    }


def patient_counts(df: pd.DataFrame, patient_col: str, label_col: str) -> dict[str, int]:
    labelled = df.dropna(subset=[patient_col]).copy()
    labels = labelled.groupby(patient_col)[label_col].max()
    return {
        "positive_patients": int((labels == 1).sum()),
        "negative_patients": int((labels == 0).sum()),
        "missing_label_patients": int(labels.isna().sum()),
        "labelled_patients": int(((labels == 1) | (labels == 0)).sum()),
    }


def cnv_basename(series: pd.Series) -> pd.Series:
    return series.dropna().astype(str).map(lambda x: Path(x).name)


def fold_balance(root: Path, manifest: pd.DataFrame, master_for_join: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    cnv_rows = manifest[manifest["result_id"].eq("lgd2_cnv_core")]
    if cnv_rows.empty:
        return pd.DataFrame(), ["lgd2_cnv_core not found; fold balance unavailable"]
    files = resolve_files(root, str(cnv_rows.iloc[0]["prediction_file"]))
    if not files:
        return pd.DataFrame(), ["lgd2_cnv_core prediction files not resolved; fold balance unavailable"]
    pred = load_predictions(files)
    joined, join_key = join_master(pred, master_for_join)
    if joined["patient_id"].isna().any():
        warnings.append("Fold balance has missing patient IDs after join")
    rows = []
    for fold, group in joined.dropna(subset=["fold"]).groupby("fold"):
        y = pd.to_numeric(group["y_true"], errors="coerce")
        patient_y = group.groupby("patient_id")["y_true"].max()
        rows.append(
            {
                "section": "fold_balance",
                "metric": f"fold_{fold}",
                "value": int(group["patient_id"].nunique()),
                "notes": (
                    f"samples={len(group)}; sample_pos={(y == 1).sum()}; sample_neg={(y == 0).sum()}; "
                    f"patient_pos={(patient_y == 1).sum()}; patient_neg={(patient_y == 0).sum()}; "
                    f"join={join_key}"
                ),
            }
        )
    return pd.DataFrame(rows), warnings


def make_markdown(flow: pd.DataFrame, warnings: list[str], master_path: Path) -> str:
    lines = [
        "# LGD2+ Cohort Flow",
        "",
        f"External master cohort: `{master_path}`",
        "",
        "| section | metric | value | notes |",
        "|---|---|---:|---|",
    ]
    for _, row in flow.iterrows():
        lines.append(f"| {row['section']} | {row['metric']} | {row['value']} | {row['notes']} |")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = experiment_root(args.experiment_root)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(args.manifest).fillna("")
    master, warnings, master_path = read_master(root, manifest)
    rows: list[dict[str, object]] = []

    patient_col = "PatientID"
    biopsy_col = "BiopsyID_int" if "BiopsyID_int" in master.columns else "BiopsyID_real"
    add_row(rows, "cohort", "sample_slide_rows", len(master))
    add_row(rows, "cohort", "patients", master[patient_col].nunique() if patient_col in master else "NA")
    add_row(rows, "cohort", "biopsies", master[biopsy_col].nunique() if biopsy_col in master else "NA")
    if "CNVAbsPath" in master:
        cnv = cnv_basename(master["CNVAbsPath"])
        add_row(rows, "cohort", "unique_cnv_profiles", cnv.nunique())
        add_row(rows, "cohort", "duplicated_cnv_paths", int(cnv.duplicated().sum()))
        add_row(rows, "missingness", "missing_cnv_paths", int(master["CNVAbsPath"].isna().sum()))
    if "ImageAbsPath" in master:
        add_row(rows, "missingness", "missing_image_paths", int(master["ImageAbsPath"].isna().sum()))
    if LGD2_ENDPOINT in master:
        counts = label_counts(master, LGD2_ENDPOINT)
        for key, value in counts.items():
            add_row(rows, "row_labels", f"lgd2_{key}_rows", value)
        if patient_col in master:
            for key, value in patient_counts(master, patient_col, LGD2_ENDPOINT).items():
                add_row(rows, "patient_labels_all_samples", key, value)
    if "DaysFromCurrentToEvent" in master:
        add_row(rows, "timing", "event_time_rows_days_0", int(master["DaysFromCurrentToEvent"].eq(0).sum()))
        early = exclude_current_event_rows(master)
        add_row(rows, "timing", "rows_after_early_prediction_filter", len(early))
        if LGD2_ENDPOINT in master and patient_col in master:
            for key, value in patient_counts(early, patient_col, LGD2_ENDPOINT).items():
                add_row(rows, "patient_labels_early_prediction_only", key, value)
    grade_col = next((c for c in ["CurrentGradeNorm", "CurrentGradeInt", "Label", "max_pathology"] if c in master.columns), None)
    if grade_col:
        for grade, count in master[grade_col].fillna("MISSING").value_counts(dropna=False).sort_index().items():
            add_row(rows, "current_grade_distribution", str(grade), int(count), f"column={grade_col}")
    else:
        warnings.append("No current-grade column found")

    master_for_join = master.copy()
    master_for_join["sample_key"] = master_for_join["SampleID"].astype("string").str.replace(r"\.0$", "", regex=True)
    if "PatientID_real" in master_for_join:
        master_for_join["patient_id_master"] = master_for_join["PatientID_real"].astype("string")
    else:
        master_for_join["patient_id_master"] = master_for_join[patient_col].astype("string")
    master_for_join["biopsy_id"] = master_for_join[biopsy_col].astype("string") if biopsy_col in master_for_join else pd.NA
    master_for_join["label_master"] = pd.to_numeric(master_for_join.get(LGD2_ENDPOINT), errors="coerce")
    master_for_join["cnv_key"] = master_for_join["CNVAbsPath"].map(lambda x: Path(str(x)).name if pd.notna(x) else pd.NA)
    folds, fold_warnings = fold_balance(root, manifest, master_for_join)
    warnings.extend(fold_warnings)
    flow = pd.concat([pd.DataFrame(rows), folds], ignore_index=True)
    flow.to_csv(out_dir / "lgd2_cohort_flow.csv", index=False)
    (out_dir / "lgd2_cohort_flow.md").write_text(make_markdown(flow, warnings, master_path))
    print(f"Wrote {len(flow)} cohort-flow rows to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

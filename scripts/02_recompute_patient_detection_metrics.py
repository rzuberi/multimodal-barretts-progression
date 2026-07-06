#!/usr/bin/env python
"""Recompute LGD2+ patient-level detection metrics from external predictions.

Reads only external prediction/cohort files referenced by
docs/final_results_manifest.csv. Writes small summary reports under
reports/thesis_ch1/.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ENDPOINT = "NextBiopsyProgression_LGD2plus"
CLINICAL_DEFINITION = "HGD/IMC/OAC or two consecutive LGD biopsies"
DEFAULT_OUTPUT_DIR = Path("reports/thesis_ch1")
MANIFEST_PATH = Path("docs/final_results_manifest.csv")

MASTER_COLS = [
    "SampleID",
    "PatientID",
    "BiopsyID_int",
    "BiopsyID_real",
    "CNVAbsPath",
    "ImageAbsPath",
    "DaysFromCurrentToEvent",
    ENDPOINT,
]

MODEL_GROUP_COLS = [
    "model_name",
    "cnv_variant",
    "cnv_mask_name",
    "instance_k",
    "subsample_mode",
    "embed_pca_dim",
    "method_name",
    "n_experts",
    "experts",
]

METRIC_ORDER = [
    "roc_auc",
    "auprc",
    "accuracy",
    "balanced_accuracy",
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
    "sensitivity_at_90_specificity",
    "threshold_at_90_specificity",
    "sensitivity_at_95_specificity",
    "threshold_at_95_specificity",
    "specificity_at_90_sensitivity",
    "threshold_at_90_sensitivity",
    "specificity_at_95_sensitivity",
    "threshold_at_95_sensitivity",
    "threshold_used",
    "n_units",
    "n_patients",
    "n_positive_patients",
    "n_negative_patients",
]


@dataclass
class WarningRow:
    result_id: str
    severity: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument(
        "--experiment-root",
        default=os.environ.get("BARRETTS_EXPERIMENT_ROOT"),
        help="Root for external relative paths. Defaults to repo parent.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--include-status",
        action="append",
        default=["FINAL_CANDIDATE"],
        help="Manifest status to include. Repeatable.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def experiment_root(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value).expanduser().resolve()
    return repo_root().parent.resolve()


def expand_braces(pattern: str) -> list[str]:
    match = re.search(r"\{([^{}]+)\}", pattern)
    if not match:
        return [pattern]
    body = match.group(1)
    if re.fullmatch(r"-?\d+\.\.-?\d+", body):
        start, end = [int(x) for x in body.split("..")]
        step = 1 if end >= start else -1
        values = [str(i) for i in range(start, end + step, step)]
    else:
        values = body.split(",")
    out = []
    for value in values:
        out.extend(expand_braces(pattern[: match.start()] + value + pattern[match.end() :]))
    return out


def resolve_files(root: Path, pattern: str) -> list[Path]:
    if not pattern or pattern in {"NA", "MISSING", "REVIEW_MANUALLY", "nan"}:
        return []
    raw = Path(pattern)
    full = raw if raw.is_absolute() else root / raw
    files: list[Path] = []
    for expanded in expand_braces(str(full)):
        if any(ch in expanded for ch in "*?[]"):
            files.extend(Path(p) for p in sorted(Path().glob(expanded) if not Path(expanded).is_absolute() else glob_abs(expanded)))
        else:
            p = Path(expanded)
            if p.exists():
                files.append(p)
    return sorted(set(files))


def glob_abs(pattern: str) -> Iterable[str]:
    import glob

    return glob.glob(pattern)


def normalize_key(series: pd.Series) -> pd.Series:
    return series.astype("string").str.replace(r"\.0$", "", regex=True).str.strip()


def load_manifest(path: Path, endpoint: str, statuses: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path).fillna("")
    keep = (
        df["status"].isin(statuses)
        & df["endpoint"].eq(endpoint)
        & df["task"].eq("binary progression")
        & ~df["prediction_file"].isin(["", "NA", "MISSING", "REVIEW_MANUALLY"])
    )
    return df.loc[keep].copy()


def load_master(root: Path, manifest: pd.DataFrame, endpoint: str) -> pd.DataFrame:
    cohort_rows = pd.read_csv(MANIFEST_PATH).fillna("")
    cohort_path = cohort_rows.loc[cohort_rows["result_id"].eq("lgd2_primary_cohort"), "external_result_path"]
    if cohort_path.empty:
        raise RuntimeError("lgd2_primary_cohort not found in manifest")
    path = root / cohort_path.iloc[0]
    header = pd.read_csv(path, nrows=0).columns.tolist()
    usecols = [c for c in MASTER_COLS if c in header]
    if endpoint not in usecols:
        raise RuntimeError(f"{endpoint} not found in master cohort: {path}")
    master = pd.read_csv(path, usecols=usecols)
    master["sample_key"] = normalize_key(master["SampleID"])
    if "PatientID_real" in master:
        master["patient_id_master"] = normalize_key(master["PatientID_real"])
    else:
        master["patient_id_master"] = normalize_key(master["PatientID"])
    if "BiopsyID_int" in master:
        master["biopsy_id"] = normalize_key(master["BiopsyID_int"])
    elif "BiopsyID_real" in master:
        master["biopsy_id"] = normalize_key(master["BiopsyID_real"])
    else:
        master["biopsy_id"] = pd.NA
    master["label_master"] = pd.to_numeric(master[endpoint], errors="coerce")
    if "CNVAbsPath" in master:
        master["cnv_key"] = master["CNVAbsPath"].map(lambda x: Path(str(x)).name if pd.notna(x) else pd.NA)
        master["cnv_key"] = normalize_key(master["cnv_key"])
    else:
        master["cnv_key"] = pd.NA
    return master


def master_lookup(master: pd.DataFrame, key_col: str) -> pd.DataFrame:
    rows = master.dropna(subset=[key_col]).copy()
    if rows.empty:
        return pd.DataFrame()

    def first_nonmissing(values: pd.Series) -> object:
        values = values.dropna()
        return values.iloc[0] if len(values) else pd.NA

    def event_or_min(values: pd.Series) -> float:
        vals = pd.to_numeric(values, errors="coerce")
        if (vals == 0).any():
            return 0.0
        vals = vals.dropna()
        return float(vals.min()) if len(vals) else math.nan

    lookup = (
        rows.groupby(key_col, dropna=False)
        .agg(
            patient_id_master=("patient_id_master", first_nonmissing),
            biopsy_id=("biopsy_id", first_nonmissing),
            DaysFromCurrentToEvent=("DaysFromCurrentToEvent", event_or_min),
            label_master=("label_master", "max"),
        )
        .reset_index()
        .rename(columns={key_col: "sample_key"})
    )
    return lookup


def load_predictions(files: list[Path], usecols_extra: list[str] | None = None) -> pd.DataFrame:
    frames = []
    for path in files:
        header = pd.read_csv(path, nrows=0).columns.tolist()
        base_cols = ["sample_id", "patient_id", "fold", "y_true", "y_prob", "y_pred", "condition", "task_name"]
        cols = [c for c in base_cols + MODEL_GROUP_COLS + (usecols_extra or []) if c in header]
        part = pd.read_csv(path, usecols=cols)
        part["prediction_file"] = str(path)
        frames.append(part)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def join_master(pred: pd.DataFrame, master: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if "sample_id" not in pred.columns:
        return pred, "failed:no_sample_id"
    pred = pred.copy()
    pred["sample_key"] = normalize_key(pred["sample_id"])
    candidates = [
        ("sample_id->SampleID", master_lookup(master, "sample_key")),
        ("sample_id->basename(CNVAbsPath)", master_lookup(master, "cnv_key")),
    ]
    scored = []
    pred_keys = set(pred["sample_key"].dropna().astype(str))
    for name, lookup in candidates:
        if lookup.empty:
            scored.append((0, name, lookup))
        else:
            keys = set(lookup["sample_key"].dropna().astype(str))
            scored.append((len(pred_keys & keys), name, lookup))
    _, key, lookup = max(scored, key=lambda item: item[0])
    if lookup.empty:
        return pred, "failed:no_master_lookup"
    joined = pred.merge(
        lookup,
        on="sample_key",
        how="left",
        validate="many_to_one",
    )
    if "patient_id" not in joined.columns or joined["patient_id"].isna().all():
        joined["patient_id"] = joined["patient_id_master"]
        key = f"{key}; patient_id from master"
    else:
        joined["patient_id"] = normalize_key(joined["patient_id"])
        missing = joined["patient_id"].isna()
        joined.loc[missing, "patient_id"] = joined.loc[missing, "patient_id_master"]
        key = f"prediction.patient_id; {key} for timing/biopsy"
    if "y_true" not in joined.columns or joined["y_true"].isna().all():
        joined["y_true"] = joined["label_master"]
    joined["y_true"] = pd.to_numeric(joined["y_true"], errors="coerce")
    joined["y_prob"] = pd.to_numeric(joined["y_prob"], errors="coerce")
    if "fold" in joined.columns:
        joined["fold"] = normalize_key(joined["fold"])
    else:
        joined["fold"] = pd.NA
    return joined, key


def group_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in MODEL_GROUP_COLS if c in df.columns]


def model_label(row: pd.Series, fallback: str) -> str:
    pieces = []
    for col in MODEL_GROUP_COLS:
        if col in row and pd.notna(row[col]) and str(row[col]) not in {"", "nan"}:
            pieces.append(f"{col}={row[col]}")
    return "; ".join(pieces) if pieces else fallback


def aggregate_predictions(df: pd.DataFrame, level: str) -> pd.DataFrame:
    if level == "sample":
        out = df.copy()
        out["unit_id"] = out["sample_key"]
        return out
    if level.startswith("patient_"):
        key = "patient_id"
    elif level.startswith("biopsy_"):
        key = "biopsy_id"
    else:
        raise ValueError(level)
    agg = "max" if level.endswith("_max") else "mean"
    grouped = df.dropna(subset=[key]).groupby(key, dropna=False)
    y_prob = grouped["y_prob"].max() if agg == "max" else grouped["y_prob"].mean()
    out = pd.DataFrame(
        {
            "unit_id": y_prob.index.astype(str),
            "y_prob": y_prob.values,
            "y_true": grouped["y_true"].max().values,
            "patient_id": grouped["patient_id"].first().values,
            "fold": grouped["fold"].agg(lambda x: ",".join(sorted(set(x.dropna().astype(str))))).values,
        }
    )
    return out


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else math.nan


def confusion_counts(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[int, int, int, int]:
    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tn, fp, fn, tp


def roc_auc_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    pos = y_true == 1
    neg = y_true == 0
    n_pos = int(pos.sum())
    n_neg = int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return math.nan
    order = np.argsort(y_prob)
    ranks = np.empty(len(y_prob), dtype=float)
    sorted_scores = y_prob[order]
    start = 0
    while start < len(y_prob):
        end = start + 1
        while end < len(y_prob) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        avg_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = avg_rank
        start = end
    rank_sum_pos = ranks[pos].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def average_precision_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    pos_total = int((y_true == 1).sum())
    if pos_total == 0:
        return math.nan
    order = np.argsort(-y_prob, kind="mergesort")
    y_sorted = y_true[order]
    tp_cum = np.cumsum(y_sorted == 1)
    ranks = np.arange(1, len(y_sorted) + 1)
    precision = tp_cum / ranks
    return float(precision[y_sorted == 1].sum() / pos_total)


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (y_prob >= lo) & (y_prob < hi if hi < 1.0 else y_prob <= hi)
        if not mask.any():
            continue
        ece += mask.mean() * abs(float(y_true[mask].mean()) - float(y_prob[mask].mean()))
    return float(ece)


def fixed_operating_points(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    thresholds = np.unique(np.r_[0.0, y_prob, 1.0])
    rows = []
    for threshold in thresholds:
        pred = (y_prob >= threshold).astype(int)
        tn, fp, fn, tp = confusion_counts(y_true, pred)
        sens = safe_div(tp, tp + fn)
        spec = safe_div(tn, tn + fp)
        rows.append((threshold, sens, spec))
    out: dict[str, float] = {}
    for target in (0.90, 0.95):
        valid = [r for r in rows if not math.isnan(r[2]) and r[2] >= target]
        if valid:
            threshold, sens, _ = max(valid, key=lambda r: (r[1], -r[0]))
            out[f"sensitivity_at_{int(target*100)}_specificity"] = sens
            out[f"threshold_at_{int(target*100)}_specificity"] = threshold
        else:
            out[f"sensitivity_at_{int(target*100)}_specificity"] = math.nan
            out[f"threshold_at_{int(target*100)}_specificity"] = math.nan
        valid = [r for r in rows if not math.isnan(r[1]) and r[1] >= target]
        if valid:
            threshold, _, spec = max(valid, key=lambda r: (r[2], r[0]))
            out[f"specificity_at_{int(target*100)}_sensitivity"] = spec
            out[f"threshold_at_{int(target*100)}_sensitivity"] = threshold
        else:
            out[f"specificity_at_{int(target*100)}_sensitivity"] = math.nan
            out[f"threshold_at_{int(target*100)}_sensitivity"] = math.nan
    return out


def compute_metrics(y_true_in: Iterable[float], y_prob_in: Iterable[float], threshold: float = 0.5) -> dict[str, float]:
    y_true = np.asarray(list(y_true_in), dtype=float)
    y_prob = np.asarray(list(y_prob_in), dtype=float)
    mask = np.isfinite(y_true) & np.isfinite(y_prob)
    y_true = y_true[mask].astype(int)
    y_prob = y_prob[mask]
    y_pred = (y_prob >= threshold).astype(int)
    out: dict[str, float] = {k: math.nan for k in METRIC_ORDER}
    out["threshold_used"] = threshold
    out["n_units"] = int(len(y_true))
    if len(y_true) == 0 or len(np.unique(y_true)) < 2:
        return out
    tn, fp, fn, tp = confusion_counts(y_true, y_pred)
    sensitivity = safe_div(tp, tp + fn)
    specificity = safe_div(tn, tn + fp)
    ppv = safe_div(tp, tp + fp)
    npv = safe_div(tn, tn + fn)
    out.update(
        {
            "roc_auc": roc_auc_binary(y_true, y_prob),
            "auprc": average_precision_binary(y_true, y_prob),
            "accuracy": safe_div(tp + tn, tp + tn + fp + fn),
            "balanced_accuracy": np.nanmean([sensitivity, specificity]),
            "sensitivity": sensitivity,
            "specificity": specificity,
            "ppv": ppv,
            "npv": npv,
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
            "progressors_detected": int(tp),
            "progressors_missed": int(fn),
            "false_positives_per_detected_progressor": safe_div(fp, tp),
            "brier_score": float(np.mean((y_prob - y_true) ** 2)),
            "ece": expected_calibration_error(y_true, y_prob),
        }
    )
    out.update(fixed_operating_points(y_true, y_prob))
    return out


def bootstrap_cis(df: pd.DataFrame, n_boot: int, seed: int) -> dict[str, float]:
    metrics = ["roc_auc", "auprc", "sensitivity", "specificity", "ppv", "npv"]
    out = {f"{m}_ci_low": math.nan for m in metrics}
    out.update({f"{m}_ci_high": math.nan for m in metrics})
    if n_boot <= 0 or df.empty:
        return out
    rng = np.random.default_rng(seed)
    values = {m: [] for m in metrics}
    idx = np.arange(len(df))
    y_all = pd.to_numeric(df["y_true"], errors="coerce").to_numpy(dtype=float)
    p_all = pd.to_numeric(df["y_prob"], errors="coerce").to_numpy(dtype=float)
    for _ in range(n_boot):
        sample_idx = rng.choice(idx, size=len(idx), replace=True)
        y_true = y_all[sample_idx]
        y_prob = p_all[sample_idx]
        mask = np.isfinite(y_true) & np.isfinite(y_prob)
        y_true = y_true[mask].astype(int)
        y_prob = y_prob[mask]
        if len(y_true) == 0 or len(np.unique(y_true)) < 2:
            continue
        y_pred = (y_prob >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_counts(y_true, y_pred)
        row = {
            "roc_auc": roc_auc_binary(y_true, y_prob),
            "auprc": average_precision_binary(y_true, y_prob),
            "sensitivity": safe_div(tp, tp + fn),
            "specificity": safe_div(tn, tn + fp),
            "ppv": safe_div(tp, tp + fp),
            "npv": safe_div(tn, tn + fn),
        }
        for metric, value in row.items():
            if np.isfinite(value):
                values[metric].append(value)
    for metric, vals in values.items():
        if vals:
            out[f"{metric}_ci_low"] = float(np.percentile(vals, 2.5))
            out[f"{metric}_ci_high"] = float(np.percentile(vals, 97.5))
    return out


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
        f"Endpoint: `{ENDPOINT}`.",
        f"Clinical definition: {CLINICAL_DEFINITION}.",
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
    relevant_warnings = [w for w in warnings if w.severity in {"WARN", "SKIP"}]
    lines.extend(["", "## Notes", ""])
    if analysis_set == "early_prediction_only":
        lines.append("- Excludes prediction rows joined to master rows with `DaysFromCurrentToEvent == 0`.")
    else:
        lines.append("- Includes all labelled prediction rows in the selected final-candidate LGD2+ files.")
    lines.append("- Threshold-dependent metrics use default threshold `0.5`; fixed operating point columns are in the CSV.")
    lines.append("- Bootstrap confidence intervals are reported for patient-level aggregations; biopsy/sample rows keep CI columns blank.")
    if relevant_warnings:
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
        for w in warnings:
            lines.append(f"| `{w.result_id}` | `{w.severity}` | {w.message} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = experiment_root(args.experiment_root)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    full_manifest = pd.read_csv(args.manifest).fillna("")
    manifest = load_manifest(Path(args.manifest), args.endpoint, args.include_status)
    master = load_master(root, manifest, args.endpoint)
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
        pred, join_key = join_master(pred, master)
        if pred["patient_id"].isna().any():
            n = int(pred["patient_id"].isna().sum())
            warnings.append(WarningRow(result_id, "SKIP", f"{n} rows lack patient_id after join; skipped."))
            continue
        if pred["y_true"].isna().any():
            n = int(pred["y_true"].isna().sum())
            warnings.append(WarningRow(result_id, "WARN", f"{n} rows with missing labels were dropped."))
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
                    analysis_df = analysis_df[analysis_df["DaysFromCurrentToEvent"].ne(0)].copy()
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
                    metrics["n_patients"] = int(agg_df["patient_id"].nunique(dropna=True))
                    patient_labels = agg_df.groupby("patient_id")["y_true"].max()
                    metrics["n_positive_patients"] = int((patient_labels == 1).sum())
                    metrics["n_negative_patients"] = int((patient_labels == 0).sum())
                    if aggregation.startswith("patient_"):
                        metrics.update(bootstrap_cis(agg_df[["y_true", "y_prob"]], args.bootstrap, args.seed))
                    else:
                        metrics.update(bootstrap_cis(agg_df[["y_true", "y_prob"]], 0, args.seed))
                    row = {
                        "result_id": result_id,
                        "analysis_set": analysis_set,
                        "aggregation": aggregation,
                        "endpoint": args.endpoint,
                        "clinical_definition": CLINICAL_DEFINITION,
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

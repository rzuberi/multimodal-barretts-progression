#!/usr/bin/env python
"""Select LGD2+ interpretation cases from external saved predictions.

Builds a per-patient wide table (CNV-only / image-only / early-fusion probability
for the same patient) from the locked LGD2+ campaign, then selects cases for the
interpretation categories A-I. Patient-level first (patient_max), with a
representative sample row per patient taken from the primary fusion model.

Only lightweight derived summaries are written. External absolute paths
(/scratchc/...) are reduced to basenames; no raw data is emitted.
"""

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
from barrett.evaluation.io import (
    join_master,
    load_master,
    load_predictions,
    normalize_key,
    resolve_files,
)
from barrett.labels.endpoints import LGD2_CLINICAL_DEFINITION, LGD2_ENDPOINT

DEFAULT_OUTPUT_DIR = Path("reports/thesis_ch1")
MANIFEST_PATH = Path("docs/final_results_manifest.csv")

# Probability thresholds (task section 4).
THR_DEFAULT = 0.5
THR_HIGH = 0.75
THR_LOW = 0.25
THR_DISAGREE = 0.4

# Extra master columns needed for case context (grade, timing, paths, next label).
DETAIL_COLS = [
    "SampleID",
    "CNVAbsPath",
    "ImageAbsPath",
    "CurrentGradeNorm",
    "NextBiopsyLabel",
    "MonthsBeforeLastBiopsy",
]

# Model specifications: (short name, manifest result_id, prediction glob, group filter).
# Globs are relative to the experiment root.
CAMPAIGN = "data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2"
MODELS = {
    "cnv": dict(
        result_id="lgd2_cnv_core",
        glob=f"{CAMPAIGN}/cnv_anchor/runs/cnv/all_samples/core_binary/cv/"
        "predictions_all_samples_cnv_random_forest_windows_armdiff_plus_arms_plus_cx_"
        "NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv",
        filter={"model_name": "cnv_random_forest"},
    ),
    "image": dict(
        result_id="lgd2_image_uni2",
        glob=f"{CAMPAIGN}/uni2/runs/image/all_samples/core_gpu/cv/"
        "predictions_all_samples_abmil_NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv",
        filter={"model_name": "abmil"},
    ),
    "fusion": dict(
        result_id="lgd2_early_fusion_uni2",
        glob=f"{CAMPAIGN}/uni2/runs/multimodal/all_samples/core_gpu/cv/"
        "predictions_all_samples_early_mean_mlp_windows_armdiff_plus_arms_plus_cx_"
        "NextBiopsyProgression_LGD2plus_k0_uniform_epca0_rep01_fold{1..5}.csv",
        filter={"model_name": "early_mean_mlp"},
    ),
    "fusion_gigapath": dict(
        result_id="lgd2_early_fusion_gigapath",
        glob=f"{CAMPAIGN}/gigapath/runs/multimodal/all_samples/core_gpu/cv/"
        "predictions_all_samples_early_mean_mlp_windows_armdiff_plus_arms_plus_cx_"
        "NextBiopsyProgression_LGD2plus_k0_uniform_epca0_rep01_fold{1..5}.csv",
        filter={"model_name": "early_mean_mlp"},
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument(
        "--experiment-root",
        default=os.environ.get("BARRETTS_EXPERIMENT_ROOT"),
        help="Root for external relative paths. Defaults to repo parent.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def experiment_root(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value).expanduser().resolve()
    return REPO_ROOT.parent.resolve()


def basename(path: object) -> object:
    if pd.isna(path) or str(path) in {"", "nan"}:
        return pd.NA
    return Path(str(path)).name


def load_detail(root: Path, manifest_path: Path) -> pd.DataFrame:
    """Per-sample context keyed by both sample_key and cnv_key (basenames only)."""
    cohort_rows = pd.read_csv(manifest_path).fillna("")
    cohort_path = cohort_rows.loc[
        cohort_rows["result_id"].eq("lgd2_primary_cohort"), "external_result_path"
    ].iloc[0]
    path = root / cohort_path
    header = pd.read_csv(path, nrows=0).columns.tolist()
    usecols = [c for c in DETAIL_COLS if c in header]
    df = pd.read_csv(path, usecols=usecols)
    df["sample_key"] = normalize_key(df["SampleID"])
    df["cnv_key"] = normalize_key(df["CNVAbsPath"].map(basename))
    df["slide_basename"] = df["ImageAbsPath"].map(basename) if "ImageAbsPath" in df else pd.NA
    df["cnv_basename"] = df["CNVAbsPath"].map(basename) if "CNVAbsPath" in df else pd.NA
    df = df.rename(
        columns={
            "CurrentGradeNorm": "current_grade",
            "NextBiopsyLabel": "next_biopsy_label",
            "MonthsBeforeLastBiopsy": "months_before_last_biopsy",
        }
    )
    keep = [
        "current_grade",
        "next_biopsy_label",
        "months_before_last_biopsy",
        "slide_basename",
        "cnv_basename",
    ]
    return df, keep


def merge_detail(pred: pd.DataFrame, detail: pd.DataFrame, keep: list[str]) -> pd.DataFrame:
    """Attach per-sample context; join on cnv_key first, fall back to sample_key."""
    by_cnv = detail.dropna(subset=["cnv_key"]).drop_duplicates("cnv_key").set_index("cnv_key")
    merged = pred.merge(by_cnv[keep], left_on="sample_key", right_index=True, how="left")
    if merged[keep].isna().all().all():
        by_sample = (
            detail.dropna(subset=["sample_key"]).drop_duplicates("sample_key").set_index("sample_key")
        )
        merged = pred.merge(by_sample[keep], left_on="sample_key", right_index=True, how="left")
    return merged


def load_model_predictions(
    root: Path, master: pd.DataFrame, detail: pd.DataFrame, keep: list[str], spec: dict
) -> pd.DataFrame:
    files = resolve_files(root, spec["glob"])
    if not files:
        return pd.DataFrame()
    pred = load_predictions(files)
    if pred.empty:
        return pd.DataFrame()
    for col, val in spec["filter"].items():
        if col in pred.columns:
            pred = pred[pred[col].astype(str) == val]
    pred, _ = join_master(pred, master)
    pred = pred.dropna(subset=["patient_id", "y_true", "y_prob"]).copy()
    pred = merge_detail(pred, detail, keep)
    return pred


def patient_table(pred: pd.DataFrame, early_only: bool) -> pd.DataFrame:
    """patient_max probability + representative (argmax-prob) sample per patient."""
    df = pred
    if early_only:
        df = exclude_current_event_rows(df)
    if df.empty:
        return pd.DataFrame()
    df = df.sort_values("y_prob", ascending=False)
    rep = df.drop_duplicates("patient_id").set_index("patient_id")
    prob = df.groupby("patient_id")["y_prob"].max()
    label = df.groupby("patient_id")["y_true"].max()
    out = pd.DataFrame(
        {
            "prob": prob,
            "y_true": label,
            "rep_sample_id": rep["sample_id"] if "sample_id" in rep else pd.NA,
            "rep_biopsy_id": rep["biopsy_id"] if "biopsy_id" in rep else pd.NA,
            "rep_days_to_event": rep["DaysFromCurrentToEvent"],
            "rep_grade": rep.get("current_grade"),
            "rep_next_label": rep.get("next_biopsy_label"),
            "rep_months": rep.get("months_before_last_biopsy"),
            "rep_slide": rep.get("slide_basename"),
            "rep_cnv": rep.get("cnv_basename"),
        }
    )
    return out


def any_at_event(pred: pd.DataFrame) -> pd.Series:
    ev = pred.assign(_ev=pred["DaysFromCurrentToEvent"].eq(0))
    return ev.groupby("patient_id")["_ev"].any()


def build_wide(preds: dict[str, pd.DataFrame], early_only: bool) -> pd.DataFrame:
    tabs = {name: patient_table(p, early_only) for name, p in preds.items() if not p.empty}
    if "fusion" not in tabs or tabs["fusion"].empty:
        return pd.DataFrame()
    base = tabs["fusion"].add_prefix("fusion_")
    base = base.rename(columns={"fusion_y_true": "y_true"})
    # representative context comes from fusion model
    ctx = {c: f"fusion_{c}" for c in ["rep_sample_id", "rep_biopsy_id", "rep_days_to_event",
                                       "rep_grade", "rep_next_label", "rep_months", "rep_slide", "rep_cnv"]}
    for name, tab in tabs.items():
        if name == "fusion":
            continue
        base[f"{name}_prob"] = tab["prob"]
    wide = base.reset_index().rename(columns={"index": "patient_id"})
    ren = {
        "fusion_prob": "fusion_prob",
        "fusion_rep_sample_id": "rep_sample_id",
        "fusion_rep_biopsy_id": "rep_biopsy_id",
        "fusion_rep_days_to_event": "rep_days_to_event",
        "fusion_rep_grade": "rep_grade",
        "fusion_rep_next_label": "rep_next_label",
        "fusion_rep_months": "rep_months",
        "fusion_rep_slide": "rep_slide",
        "fusion_rep_cnv": "rep_cnv",
    }
    wide = wide.rename(columns=ren)
    wide["analysis_set"] = "early_prediction_only" if early_only else "all_samples"
    return wide


def pred_class(prob: float, thr: float = THR_DEFAULT) -> int:
    return int(prob >= thr) if pd.notna(prob) else -1


def select_cases(wide: pd.DataFrame, at_event: pd.Series, clin_thr: float | None) -> list[dict]:
    """Assign cases to categories A-I. Returns list of case dicts."""
    w = wide.copy()
    w["at_event"] = w["patient_id"].map(at_event).fillna(False)
    cases: list[dict] = []
    seen: dict[str, set] = {}

    def take(cat: str, rows: pd.DataFrame, reason: str, n: int, sort_col: str, ascending: bool):
        picked = rows.sort_values(sort_col, ascending=ascending)
        count = 0
        for _, r in picked.iterrows():
            if count >= n:
                break
            cases.append(_case_row(cat, r, reason, clin_thr))
            count += 1

    pos = w[w["y_true"].eq(1)]
    neg = w[w["y_true"].eq(0)]
    has_cnv = "cnv_prob" in w.columns
    has_img = "image_prob" in w.columns

    # A. True positives detected early: high fusion prob at a PRE-EVENT biopsy
    # (representative sample days>0 => real positive lead time). A progressor may
    # also have a separate at-event biopsy; that does not disqualify it here.
    pos_days = pd.to_numeric(pos.get("rep_days_to_event"), errors="coerce")
    a = pos[(pos["fusion_prob"] >= THR_HIGH) & (pos_days > 0)]
    if len(a) < 3:  # fall back to high-prob TP with missing timing, never at-event
        a = pos[(pos["fusion_prob"] >= THR_HIGH) & (pos_days.ne(0))]
    take("A_true_positive_early", a, "TP: future progressor flagged high-risk with positive lead time", 5,
         "fusion_prob", False)

    # B. False negatives / missed progressors (low fusion prob)
    b = pos[pos["fusion_prob"] <= THR_LOW]
    if len(b) < 3:
        b = pos[pos["fusion_prob"] < THR_DEFAULT]
    take("B_false_negative", b, "FN: progressor the fusion model missed", 5, "fusion_prob", True)

    # C. False positives / high-risk non-progressors
    c = neg[neg["fusion_prob"] >= THR_HIGH]
    if len(c) < 3:
        c = neg[neg["fusion_prob"] >= THR_DEFAULT]
    take("C_false_positive", c, "FP: non-progressor flagged high-risk", 5, "fusion_prob", False)

    # D. True negatives / confident low-risk non-progressors
    d = neg[neg["fusion_prob"] <= THR_LOW]
    take("D_true_negative", d, "TN: confidently low-risk non-progressor", 3, "fusion_prob", True)

    if has_cnv and has_img:
        # E. CNV-rescue: cnv correct, image wrong, fusion correct/moved right
        e = w[
            (np.sign(w["cnv_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
            & (np.sign(w["image_prob"] - THR_DEFAULT) != np.sign(w["y_true"] - 0.5))
            & (np.sign(w["fusion_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
        ]
        take("E_cnv_rescue", e, "CNV correct, image wrong, fusion recovers", 3,
             "cnv_prob", False)

        # F. Histology-rescue: image correct, cnv wrong, fusion correct
        f = w[
            (np.sign(w["image_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
            & (np.sign(w["cnv_prob"] - THR_DEFAULT) != np.sign(w["y_true"] - 0.5))
            & (np.sign(w["fusion_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
        ]
        take("F_histology_rescue", f, "Image correct, CNV wrong, fusion recovers", 3,
             "image_prob", False)

        # G. Fusion-hurt: a unimodal model correct but fusion wrong
        uni_correct = (
            (np.sign(w["cnv_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
            | (np.sign(w["image_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
        )
        g = w[uni_correct & (np.sign(w["fusion_prob"] - THR_DEFAULT) != np.sign(w["y_true"] - 0.5))]
        take("G_fusion_hurt", g, "A unimodal model correct but fusion wrong", 3,
             "fusion_prob", True)

        # H. Modality-agreement high confidence (all three correct)
        all_correct = (
            (np.sign(w["cnv_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
            & (np.sign(w["image_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
            & (np.sign(w["fusion_prob"] - THR_DEFAULT) == np.sign(w["y_true"] - 0.5))
        )
        h_pos = w[all_correct & w["y_true"].eq(1)]
        h_neg = w[all_correct & w["y_true"].eq(0)]
        take("H_agree_positive", h_pos, "All modalities agree correctly (progressor)", 3,
             "fusion_prob", False)
        take("H_agree_negative", h_neg, "All modalities agree correctly (non-progressor)", 3,
             "fusion_prob", True)

        # I. Modality-disagreement: cnv vs image differ strongly
        i = w[(w["cnv_prob"] - w["image_prob"]).abs() >= THR_DISAGREE]
        take("I_modality_disagreement", i, "CNV and image probabilities disagree strongly", 5,
             "fusion_prob", False)
    return cases


def _case_row(cat: str, r: pd.Series, reason: str, clin_thr: float | None) -> dict:
    fp = r.get("fusion_prob")
    patient_at_event = bool(r.get("at_event", False))
    days = pd.to_numeric(r.get("rep_days_to_event"), errors="coerce")
    if pd.isna(days):
        case_timing = "missing"
    elif days == 0:
        case_timing = "at_event"
    else:
        case_timing = "pre_event"
    return {
        "case_category": cat,
        "patient_id": r["patient_id"],
        "biopsy_id": r.get("rep_biopsy_id"),
        "sample_id": r.get("rep_sample_id"),
        "slide_id": r.get("rep_slide"),
        "cnv_id": r.get("rep_cnv"),
        "current_grade": r.get("rep_grade"),
        "next_biopsy_label": r.get("rep_next_label"),
        "days_from_current_to_event": r.get("rep_days_to_event"),
        "months_before_last_biopsy": r.get("rep_months"),
        "true_lgd2_label": int(r["y_true"]) if pd.notna(r["y_true"]) else pd.NA,
        "cnv_only_prob": r.get("cnv_prob"),
        "image_only_prob": r.get("image_prob"),
        "early_fusion_prob": fp,
        "early_fusion_gigapath_prob": r.get("fusion_gigapath_prob"),
        "pred_class_at_0p5": pred_class(fp),
        "pred_class_at_clinical_thr": pred_class(fp, clin_thr) if clin_thr is not None else pd.NA,
        "clinical_threshold": clin_thr if clin_thr is not None else pd.NA,
        "analysis_set": r.get("analysis_set"),
        "case_timing": case_timing,
        "patient_has_at_event_biopsy": patient_at_event,
        "timing_available": bool(pd.notna(days)),
        "reason_selected": reason,
        "slide_external_ref": r.get("rep_slide"),
        "cnv_external_ref": r.get("rep_cnv"),
        "interpretation_output": "MISSING (needs regeneration)",
    }


def clinical_threshold(metrics_csv: Path) -> float | None:
    """Fusion model's threshold_at_90_specificity (patient_max, all_samples) if present."""
    if not metrics_csv.exists():
        return None
    m = pd.read_csv(metrics_csv)
    sel = m[
        m["result_id"].eq("lgd2_early_fusion_uni2")
        & m["aggregation"].eq("patient_max")
        & m["model_key"].str.contains("early_mean_mlp;", na=False)
    ]
    if sel.empty or "threshold_at_90_specificity" not in sel:
        return None
    val = pd.to_numeric(sel["threshold_at_90_specificity"], errors="coerce").dropna()
    return float(val.iloc[0]) if len(val) else None


def write_markdown(cases: pd.DataFrame, out: Path) -> None:
    lines = [
        "# LGD2+ Interpretation Case Selection",
        "",
        f"Endpoint: `{LGD2_ENDPOINT}`.",
        f"Clinical definition: {LGD2_CLINICAL_DEFINITION}.",
        "Primary model for selection: `lgd2_early_fusion_uni2` (`early_mean_mlp`), patient_max.",
        "Modality comparison: `lgd2_cnv_core` (CNV) and `lgd2_image_uni2` abmil (image).",
        "",
        f"Thresholds: default {THR_DEFAULT}; high-confidence >= {THR_HIGH}; "
        f"low-confidence <= {THR_LOW}; strong disagreement |CNV-image| >= {THR_DISAGREE}.",
        "",
        "## Cases per category",
        "",
        "| category | n | patient_ids |",
        "|---|---:|---|",
    ]
    for cat, grp in cases.groupby("case_category"):
        pids = ", ".join(str(p) for p in grp["patient_id"].tolist())
        lines.append(f"| {cat} | {len(grp)} | {pids} |")
    lines += [
        "",
        "## Selected cases",
        "",
        "| category | patient | grade | next label | days_to_event | true | CNV p | image p | fusion p | at 0.5 | set | case timing |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    def f(v):
        if pd.isna(v):
            return ""
        return f"{float(v):.3f}" if isinstance(v, float) else str(v)

    for _, r in cases.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    r["case_category"],
                    str(r["patient_id"]),
                    str(r["current_grade"]) if pd.notna(r["current_grade"]) else "",
                    str(r["next_biopsy_label"]) if pd.notna(r["next_biopsy_label"]) else "",
                    f(r["days_from_current_to_event"]),
                    str(r["true_lgd2_label"]),
                    f(r["cnv_only_prob"]),
                    f(r["image_only_prob"]),
                    f(r["early_fusion_prob"]),
                    str(r["pred_class_at_0p5"]),
                    str(r["analysis_set"]),
                    str(r["case_timing"]),
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- Selection prioritises `early_prediction_only` (excludes `DaysFromCurrentToEvent == 0`).",
        "- `all_samples` cases are added only where a category is under-filled by early-prediction patients.",
        "- At-event cases (days == 0) are detection examples only, never early-prediction examples.",
        "- All interpretation outputs are MISSING for LGD2+ and require regeneration "
        "(see `lgd2_interpretation_regeneration_plan.md`).",
        "- External references are basenames only; no absolute paths or raw data are emitted.",
    ]
    out.write_text("\n".join(lines) + "\n")


def write_warnings(warnings: list[str], out: Path) -> None:
    lines = ["# LGD2+ Interpretation Case Selection Warnings", "", "| severity | message |", "|---|---|"]
    if not warnings:
        lines.append("| OK | No warnings. |")
    else:
        for w in warnings:
            lines.append(f"| {w} |")
    out.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    root = experiment_root(args.experiment_root)
    manifest_path = Path(args.manifest)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    master = load_master(root, manifest_path, LGD2_ENDPOINT)
    detail, keep = load_detail(root, manifest_path)

    preds: dict[str, pd.DataFrame] = {}
    for name, spec in MODELS.items():
        p = load_model_predictions(root, master, detail, keep, spec)
        if p.empty:
            warnings.append(f"WARN | {name} ({spec['result_id']}): no predictions resolved; skipped.")
        preds[name] = p

    if preds.get("fusion") is None or preds["fusion"].empty:
        raise RuntimeError("Primary fusion model predictions missing; cannot select cases.")

    # gigapath fusion is an extra probability column keyed by patient, not a selection driver
    fus_giga = preds.pop("fusion_gigapath", pd.DataFrame())

    at_event = any_at_event(preds["fusion"])
    clin_thr = clinical_threshold(out_dir / "lgd2_patient_level_metrics_all_samples.csv")

    # Build early-prediction-only and all-samples wide tables.
    wide_early = build_wide(preds, early_only=True)
    wide_all = build_wide(preds, early_only=False)

    # attach gigapath fusion prob (all_samples patient_max) as reference column
    if not fus_giga.empty:
        giga = patient_table(fus_giga, early_only=False)["prob"]
        for wtab in (wide_early, wide_all):
            if not wtab.empty:
                wtab["fusion_gigapath_prob"] = wtab["patient_id"].map(giga)

    # Prefer early-prediction cases; fill under-filled categories from all_samples.
    cases_early = pd.DataFrame(select_cases(wide_early, at_event, clin_thr)) if not wide_early.empty else pd.DataFrame()
    cases_all = pd.DataFrame(select_cases(wide_all, at_event, clin_thr)) if not wide_all.empty else pd.DataFrame()

    frames = []
    used_patients: set = set()
    min_per_cat = {
        "A_true_positive_early": 3, "B_false_negative": 3, "C_false_positive": 3,
        "D_true_negative": 2, "E_cnv_rescue": 2, "F_histology_rescue": 2,
        "G_fusion_hurt": 2, "H_agree_positive": 2, "H_agree_negative": 2,
        "I_modality_disagreement": 3,
    }
    all_cats = list(min_per_cat)
    for cat in all_cats:
        early_rows = cases_early[cases_early["case_category"].eq(cat)] if not cases_early.empty else pd.DataFrame()
        picked = early_rows.copy()
        if len(picked) < min_per_cat[cat] and not cases_all.empty:
            extra = cases_all[
                cases_all["case_category"].eq(cat)
                & ~cases_all["patient_id"].isin(picked["patient_id"])
            ]
            need = min_per_cat[cat] - len(picked)
            picked = pd.concat([picked, extra.head(need)], ignore_index=True)
        if picked.empty:
            warnings.append(f"WARN | category {cat}: no cases found under current thresholds.")
        frames.append(picked)

    cases = pd.concat([f for f in frames if not f.empty], ignore_index=True) if any(not f.empty for f in frames) else pd.DataFrame()
    if cases.empty:
        raise RuntimeError("No cases selected.")

    # stable case_id
    cases.insert(0, "case_id", [f"{r.case_category}_{i:02d}" for i, r in enumerate(cases.itertuples(), 1)])

    # column order
    col_order = [
        "case_id", "case_category", "patient_id", "biopsy_id", "sample_id", "slide_id", "cnv_id",
        "current_grade", "next_biopsy_label", "days_from_current_to_event", "months_before_last_biopsy",
        "true_lgd2_label", "cnv_only_prob", "image_only_prob", "early_fusion_prob",
        "early_fusion_gigapath_prob", "pred_class_at_0p5", "pred_class_at_clinical_thr",
        "clinical_threshold", "analysis_set", "case_timing", "patient_has_at_event_biopsy",
        "timing_available", "reason_selected", "slide_external_ref", "cnv_external_ref",
        "interpretation_output",
    ]
    cases = cases[[c for c in col_order if c in cases.columns]]

    csv_path = out_dir / "lgd2_interpretation_case_selection.csv"
    cases.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    write_markdown(cases, out_dir / "lgd2_interpretation_case_selection.md")

    n_early = int((cases["analysis_set"] == "early_prediction_only").sum())
    n_atevent = int((cases["case_timing"] == "at_event").sum())
    n_pre = int((cases["case_timing"] == "pre_event").sum())
    n_missing = int((cases["case_timing"] == "missing").sum())
    warnings.append(
        f"INFO | {len(cases)} cases; {n_early} early-prediction-only, "
        f"{len(cases) - n_early} all-samples; timing: {n_pre} pre-event, "
        f"{n_atevent} at-event, {n_missing} missing."
    )
    if clin_thr is None:
        warnings.append("INFO | No fixed clinical threshold found in metrics CSV; only 0.5 used.")
    warnings.append("INFO | Case CSV holds pseudonymous patient IDs and basename references; add to no-data allowlist.")
    write_warnings(warnings, out_dir / "lgd2_interpretation_case_selection_warnings.md")

    print(f"Wrote {len(cases)} cases to {csv_path}")
    print(f"early_prediction_only={n_early} all_samples={len(cases)-n_early} "
          f"pre_event={n_pre} at_event={n_atevent} timing_missing={n_missing}")
    for cat, grp in cases.groupby("case_category"):
        print(f"  {cat}: {len(grp)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Patient-level paired model comparisons for LGD2+ (shared-index bootstrap).

Reads saved OOF predictions referenced by the manifest, aggregates to patient_max,
and reports paired (a - b) deltas with percentile 95% CIs for the core contrasts.
No model training. Prespecified vs model-selected contrasts are labelled distinctly.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.cohort_filters import exclude_current_event_rows  # noqa: E402
from barrett.evaluation.aggregation import aggregate_predictions  # noqa: E402
from barrett.evaluation.io import (  # noqa: E402
    join_master, load_master, load_predictions, resolve_files,
)
from barrett.evaluation.paired_comparison import compare  # noqa: E402
from barrett.labels.endpoints import LGD2_ENDPOINT  # noqa: E402

MANIFEST = Path("docs/final_results_manifest.csv")
OUT_DIR = Path("reports/thesis_ch1")

# (result_id, prediction-row filter). Best-* reps are model-selected (labelled below).
CNV = ("lgd2_cnv_core", {})
IMG_UNI2 = ("lgd2_image_uni2", {"model_name": "abmil"})
EARLY_UNI2 = ("lgd2_early_fusion_uni2", {"model_name": "early_mean_mlp"})
INTER_REP = ("lgd2_intermediate_fusion_gigapath", {"model_name": "intermediate_abmil_cnv"})
LATE_UNI2_MEAN = ("lgd2_late_fusion_uni2", {"fusion_method": "mean"})
LATE_BEST = ("lgd2_late_fusion_virchow2", {"fusion_method": "mean"})

CONTRASTS = [
    ("image_uni2_abmil - cnv_only", IMG_UNI2, CNV, "prespecified"),
    ("early_fusion_uni2 - cnv_only", EARLY_UNI2, CNV, "prespecified"),
    ("intermediate_fusion(best) - cnv_only", INTER_REP, CNV, "model_selected"),
    ("late_fusion_uni2_mean - cnv_only", LATE_UNI2_MEAN, CNV, "prespecified"),
    ("late_fusion(best) - cnv_only", LATE_BEST, CNV, "model_selected"),
    ("early_fusion_uni2 - image_uni2_abmil", EARLY_UNI2, IMG_UNI2, "prespecified"),
    ("early_fusion_uni2 - late_fusion_uni2_mean", EARLY_UNI2, LATE_UNI2_MEAN, "prespecified"),
]


def get_scores(spec, manifest, master, root, analysis_set):
    result_id, filt = spec
    row = manifest.loc[manifest["result_id"].eq(result_id)]
    if row.empty:
        raise SystemExit(f"manifest row not found: {result_id}")
    row = row.iloc[0]
    files = resolve_files(root, str(row["prediction_file"]))
    pred = load_predictions(files)
    for col, val in filt.items():
        pred = pred[pred[col].astype(str) == str(val)].copy()
    pred, _ = join_master(pred, master)
    pred = pred.dropna(subset=["patient_id", "y_true", "y_prob"]).copy()
    if analysis_set == "early_prediction_only":
        pred = exclude_current_event_rows(pred)
    agg = aggregate_predictions(pred, "patient_max").dropna(subset=["unit_id", "y_true", "y_prob"])
    if agg["unit_id"].duplicated().any():
        raise SystemExit(f"{result_id} {filt}: duplicate patients after aggregation")
    return pd.DataFrame({
        "patient_id": agg["unit_id"].to_numpy(),
        "y_true": agg["y_true"].to_numpy(),
        "y_prob": agg["y_prob"].to_numpy(),
    })


def fmt(x):
    return "" if x is None or pd.isna(x) else f"{x:+.3f}"


def write_md(rows, analysis_set, path):
    lines = [
        f"# LGD2+ Paired Patient-Level Model Differences - {analysis_set}",
        "",
        f"Endpoint: `{LGD2_ENDPOINT}`. Patient-level `patient_max`, shared-index bootstrap.",
        "Delta = (model_a - model_b). AUPRC/AUC: positive favours a. Brier: NEGATIVE favours a (lower is better).",
        "CIs are percentile 95%. Sign-prob is a two-sided bootstrap sign probability, not a frequentist p-value.",
        "",
        "| contrast | type | n (pos/neg) | dAUPRC (95% CI) | dAUC (95% CI) | dBrier (95% CI) | valid frac |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['contrast']} | {r['contrast_type']} | {r['n_patients']} ({r['n_positive']}/{r['n_negative']}) "
            f"| {fmt(r['delta_auprc'])} ({fmt(r['delta_auprc_ci_low'])}, {fmt(r['delta_auprc_ci_high'])}) "
            f"| {fmt(r['delta_roc_auc'])} ({fmt(r['delta_roc_auc_ci_low'])}, {fmt(r['delta_roc_auc_ci_high'])}) "
            f"| {fmt(r['delta_brier'])} ({fmt(r['delta_brier_ci_low'])}, {fmt(r['delta_brier_ci_high'])}) "
            f"| {r['valid_fraction']:.2f} |"
        )
    lines += ["", "Model-selected contrasts (best-of) are optimistic; interpret their CIs with that caveat.",
              "Where a delta CI crosses zero, do not claim superiority."]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment-root", default=os.environ.get("BARRETTS_EXPERIMENT_ROOT"))
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--output-dir", default=str(OUT_DIR))
    args = ap.parse_args()
    root = Path(args.experiment_root).resolve() if args.experiment_root else REPO_ROOT.parent.resolve()
    manifest = pd.read_csv(args.manifest).fillna("")
    master = load_master(root, Path(args.manifest), LGD2_ENDPOINT)
    out_dir = Path(args.output_dir)
    warnings = []

    for analysis_set in ["all_samples", "early_prediction_only"]:
        rows = []
        cache = {}
        for name, a_spec, b_spec, ctype in CONTRASTS:
            try:
                for spec in (a_spec, b_spec):
                    key = (spec[0], tuple(sorted(spec[1].items())), analysis_set)
                    if key not in cache:
                        cache[key] = get_scores(spec, manifest, master, root, analysis_set)
                a = cache[(a_spec[0], tuple(sorted(a_spec[1].items())), analysis_set)]
                b = cache[(b_spec[0], tuple(sorted(b_spec[1].items())), analysis_set)]
                res = compare(a, b, n_boot=args.n_boot, seed=args.seed)
                res["contrast"], res["contrast_type"] = name, ctype
                rows.append(res)
            except Exception as exc:  # record, do not abort the whole run
                warnings.append(f"{analysis_set} | {name} | {type(exc).__name__}: {exc}")
        df = pd.DataFrame(rows)
        df.to_csv(out_dir / f"lgd2_paired_model_differences_{analysis_set}.csv", index=False)
        write_md(rows, analysis_set, out_dir / f"lgd2_paired_model_differences_{analysis_set}.md")

    wl = ["# LGD2+ Paired Model Difference Warnings", ""]
    wl += [f"- {w}" for w in warnings] or ["- None."]
    (out_dir / "lgd2_paired_model_difference_warnings.md").write_text("\n".join(wl) + "\n")
    print(f"Paired comparisons written; warnings={len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

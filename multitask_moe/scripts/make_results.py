#!/usr/bin/env python
"""Per-(task, backbone) result tables + cross-task summary grid.

Mirrors scripts/28_make_lgd2_final_pre_event_results.py (reuses
barrett.evaluation.metrics / paired_comparison / tables) and extends it with the
`moe` family, both backbones, and a cross-task grid reproducing the March deck's
"How well do we detect progression" table (ROC AUC + specificity@90%-sensitivity).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.metrics import compute_metrics, confusion_counts, safe_div  # noqa: E402
from barrett.evaluation.paired_comparison import compare  # noqa: E402

BASE = Path("/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/multitask_moe_20260721")
TASKS = ["ever_progress", "at_risk_3y", "next_biopsy_progression"]
BACKBONES = ["uni2", "gigapath"]
FAMILIES = ["cnv_only", "image_only", "early_fusion", "intermediate_fusion",
            "coattention_fusion", "moe", "late_mean", "late_stack_logit"]
CONTRASTS = [("moe", "cnv_only"), ("moe", "image_only"), ("late_mean", "cnv_only"),
             ("intermediate_fusion", "cnv_only"), ("image_only", "cnv_only")]


def _patient_max(frame, prob="y_prob"):
    return frame.groupby(["patient_id", "outer_fold"], as_index=False).agg(
        y_true=("y_true", "max"), y_prob=(prob, "max"))


def _spec_at_sens(y_true, y_prob, target_sens=0.90):
    """Specificity at the lowest threshold achieving >= target sensitivity."""
    y_true = np.asarray(y_true, int)
    order = np.argsort(-np.asarray(y_prob, float))
    yt = y_true[order]
    P, N = int(yt.sum()), int((yt == 0).sum())
    if P == 0 or N == 0:
        return float("nan")
    tp = np.cumsum(yt)
    fp = np.cumsum(yt == 0)
    sens = tp / P
    spec = 1 - fp / N
    ok = np.where(sens >= target_sens)[0]
    return float(spec[ok[0]]) if len(ok) else float("nan")


def _cross_fitted_ops(frame, output_root, family):
    parts = []
    for fold in range(1, 6):
        patient = _patient_max(frame[frame["outer_fold"].eq(fold)])
        meta = json.loads((output_root / family / f"fold{fold}" / "fold_metadata.json").read_text())
        thr = float(meta["validation_threshold"]["threshold"])
        patient["y_pred"] = (patient["y_prob"] >= thr).astype(int)
        parts.append(patient)
    d = pd.concat(parts, ignore_index=True)
    tn, fp, fn, tp = confusion_counts(d["y_true"].to_numpy(), d["y_pred"].to_numpy())
    return {"sensitivity": safe_div(tp, tp + fn), "specificity": safe_div(tn, tn + fp),
            "ppv": safe_div(tp, tp + fp), "npv": safe_div(tn, tn + fn),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def _process(task, backbone, reports_dir, n_boot):
    output_root = BASE / task / "train" / backbone
    oof = output_root / "oof"
    patient_frames, rows = {}, []
    for family in FAMILIES:
        path = oof / f"{family}_oof_predictions.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, dtype={"row_key": str})
        patient = _patient_max(frame)
        patient_frames[family] = patient
        disc = compute_metrics(patient["y_true"], patient["y_prob"], threshold=0.5)
        ops = _cross_fitted_ops(frame, output_root, family)
        rows.append({"task": task, "backbone": backbone, "model_family": family,
                     "n_patients": len(patient), "n_positive_patients": int(patient["y_true"].sum()),
                     "auprc": disc["auprc"], "roc_auc": disc["roc_auc"], "brier_score": disc["brier_score"],
                     "spec_at_sens90": _spec_at_sens(patient["y_true"], patient["y_prob"]), **ops})
    if not rows:
        return None, None
    metrics = pd.DataFrame(rows).sort_values(["auprc", "roc_auc"], ascending=[False, False]).reset_index(drop=True)
    metrics.insert(0, "rank", np.arange(1, len(metrics) + 1))

    paired = []
    for i, (a, b) in enumerate(CONTRASTS):
        if a in patient_frames and b in patient_frames:
            res = compare(patient_frames[a][["patient_id", "y_true", "y_prob"]],
                          patient_frames[b][["patient_id", "y_true", "y_prob"]],
                          n_boot=n_boot, seed=20260721 + i)
            paired.append({"task": task, "backbone": backbone, "model_a": a, "model_b": b, **res})
    reports_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(reports_dir / f"metrics_{task}_{backbone}.csv", index=False)
    if paired:
        pd.DataFrame(paired).to_csv(reports_dir / f"paired_{task}_{backbone}.csv", index=False)
    return metrics, pd.DataFrame(paired) if paired else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reports-dir", default=str(REPO_ROOT / "multitask_moe" / "reports"))
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--tasks", default=",".join(TASKS),
                    help="comma list of tasks to score (default the built-in three; add "
                         "next_biopsy_highrisk / at_risk_3y_censored etc. once collected)")
    args = ap.parse_args()
    reports_dir = Path(args.reports_dir)
    tasks = [t for t in args.tasks.split(",") if t]

    all_metrics = []
    for task in tasks:
        for backbone in BACKBONES:
            m, _ = _process(task, backbone, reports_dir, args.bootstrap)
            if m is not None:
                all_metrics.append(m)
    if not all_metrics:
        print("no results yet")
        return 1
    combined = pd.concat(all_metrics, ignore_index=True)
    combined.to_csv(reports_dir / "all_metrics.csv", index=False)

    # Cross-task grid (best backbone per family), ROC AUC (spec@sens90) — deck style.
    # Show the FULL family set (no gaps) so the best model per task is always visible;
    # the deck's 5-family subset hid early_fusion/coattention/late_stack, one of which
    # (early_fusion) is the best model on ever_progress.
    grid_families = ["image_only", "cnv_only", "early_fusion", "intermediate_fusion",
                     "coattention_fusion", "moe", "late_mean", "late_stack_logit"]
    grid = []
    for task in tasks:
        row = {"task": task}
        sub = combined[combined["task"] == task]
        for fam in grid_families:
            fam_rows = sub[sub["model_family"] == fam]
            if len(fam_rows):
                best = fam_rows.sort_values("roc_auc", ascending=False).iloc[0]
                row[fam] = f"{best['roc_auc']:.2f} ({best['spec_at_sens90']:.2f})"
            else:
                row[fam] = "NA"
        # Best family per task ranked by AUPRC (the primary metric; breaks ROC ties,
        # e.g. ever_progress where early_fusion and late_mean are tied on ROC at 0.82).
        best_ap = sub.sort_values("auprc", ascending=False).iloc[0]
        row["best_by_auprc"] = f"{best_ap['model_family']} ({best_ap['auprc']:.3f})"
        grid.append(row)
    grid_df = pd.DataFrame(grid)
    grid_df.to_csv(reports_dir / "cross_task_grid.csv", index=False)
    lines = ["# Cross-task detection grid — ROC AUC (spec@sens90)", "",
             "Patient-level, nested 5-fold CV. Best backbone per family shown. "
             "Cells: ROC AUC (specificity@90%-sensitivity).",
             "Final column: best family per task ranked by AUPRC (the primary metric; breaks ROC ties).", "",
             "| " + " | ".join(grid_df.columns) + " |",
             "| " + " | ".join(["---"] * len(grid_df.columns)) + " |"]
    for r in grid_df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(v) for v in r) + " |")
    (reports_dir / "cross_task_grid.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(grid_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

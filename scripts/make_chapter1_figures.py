#!/usr/bin/env python
"""Regenerate the Chapter 1 figure set from allowlisted summary CSVs.

This script reads ONLY the small, de-identified summary tables under
``reports/thesis_ch1/`` (aggregate metrics, paired-difference CIs, cohort counts).
It never touches patient-level data, WSIs, or CNV matrices, so it runs anywhere
without cluster access or the private dataset.

Outputs (written next to the source CSVs, git-ignored as images):
    fig_main_model_comparison.png    - AUPRC + ROC AUC bar comparison
    fig_paired_differences_forest.png- paired deltas vs CNV-only with 95% CIs
    fig_cohort_flow.png              - strict pre-event cohort derivation
    fig_operating_points.png         - sensitivity/specificity/PPV/NPV bars

Usage:
    python scripts/make_chapter1_figures.py [--reports-dir reports/thesis_ch1]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- consistent, colour-vision-safe palette threaded across all figures -------
FOCAL = "#1b5e9c"   # headline model (late mean)
BASE = "#9e9e9e"    # CNV-only baseline
OTHER = "#b8cbe0"   # remaining models

DISPLAY_NAMES = {
    "cnv_only": "CNV only",
    "image_only": "Image (UNI2 ABMIL)",
    "early_fusion": "Early fusion",
    "intermediate_fusion": "Intermediate fusion",
    "coattention_fusion": "Co-attention",
    "late_mean": "Late mean",
    "late_stack_logit": "Late stack-logit",
}


def _bar_color(model: str) -> str:
    if model == "late_mean":
        return FOCAL
    if model == "cnv_only":
        return BASE
    return OTHER


def _style() -> None:
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def fig_main_comparison(comp: pd.DataFrame, out: Path) -> Path:
    comp = comp.copy()
    comp["disp"] = comp["model_family"].map(DISPLAY_NAMES).fillna(comp["model_family"])
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))
    for ax, metric, label, xmax in [
        (axes[0], "auprc", "Patient-level AUPRC", 0.72),
        (axes[1], "roc_auc", "Patient-level ROC AUC", 0.9),
    ]:
        order = comp.sort_values(metric, ascending=True)
        y = np.arange(len(order))
        cols = [_bar_color(m) for m in order.model_family]
        ax.barh(y, order[metric], color=cols, edgecolor="white", height=0.7)
        base = comp.loc[comp.model_family == "cnv_only", metric].iloc[0]
        ax.axvline(base, color=BASE, ls="--", lw=1.1, zorder=0)
        ax.set_yticks(y)
        ax.set_yticklabels(order.disp)
        ax.set_xlabel(label)
        ax.set_xlim(0, xmax)
    axes[0].set_title("Late mean ranks highest on AUPRC", loc="left")
    axes[1].set_title("Consistent ordering on ROC AUC", loc="left")
    fig.text(0.5, 1.005,
             "Multimodal Barrett's LGD2+ progression — patient-level discrimination "
             "(5-fold patient-disjoint CV, n=150)",
             ha="center", va="bottom", fontsize=8, fontweight="bold")
    fig.text(0.99, -0.02, "Higher = better. Dashed line = CNV-only baseline.",
             ha="right", fontsize=5.5, color="#555")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_paired_forest(paired: pd.DataFrame, out: Path) -> Path:
    prim = paired[paired.model_b == "cnv_only"].copy()
    prim["disp"] = prim["model_a"].map(DISPLAY_NAMES).fillna(prim["model_a"])
    prim = prim.sort_values("delta_auprc")
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.4), sharey=True)
    specs = [("delta_auprc", "ΔAUPRC", "higher = better"),
             ("delta_roc_auc", "ΔROC AUC", "higher = better"),
             ("delta_brier", "ΔBrier", "lower = better")]
    for ax, (m, lab, dirn) in zip(axes, specs):
        lo, hi, est = prim[m + "_ci_low"], prim[m + "_ci_high"], prim[m]
        excl0 = ~((lo <= 0) & (hi >= 0))
        cols = np.where(excl0, FOCAL, BASE)
        for i, (e, l, h, cc) in enumerate(zip(est, lo, hi, cols)):
            ax.plot([l, h], [i, i], color=cc, lw=1.6, zorder=2)
            ax.plot(e, i, "o", color=cc, ms=5, zorder=3)
        ax.axvline(0, color="#333", lw=0.9, zorder=1)
        ax.set_xlabel(lab)
        ax.set_title(dirn, loc="left", fontsize=6, color="#555")
    axes[0].set_yticks(np.arange(len(prim)))
    axes[0].set_yticklabels(prim.disp)
    fig.text(0.5, 1.02,
             "Paired differences vs CNV-only baseline (95% bootstrap CI, patient-level, n=150)",
             ha="center", fontsize=8, fontweight="bold")
    fig.text(0.5, 0.965, "Blue = 95% CI excludes zero;  grey = CI includes zero",
             ha="center", fontsize=5.8, color="#555")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_cohort_flow(flow: pd.DataFrame, out: Path) -> Path:
    def _row(stage, col):
        m = flow.loc[flow.stage == stage, col]
        return int(m.iloc[0]) if len(m) and pd.notna(m.iloc[0]) else 0
    all_rows = (_row("all_rows", "rows"), _row("all_rows", "biopsies"), _row("all_rows", "patients"))
    final = (_row("strict_pre_event_eligible", "rows"),
             _row("strict_pre_event_eligible", "biopsies"),
             _row("strict_pre_event_eligible", "patients"))
    pos = (_row("eligible_positive_rows", "rows"), _row("eligible_positive_rows", "patients"))
    excl = [("Endpoint not evaluable", "excluded:endpoint_not_evaluable"),
            ("Current biopsy at LGD2+ event", "excluded:at_event"),
            ("Post first LGD2+ event", "excluded:post_event")]
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    ax.axis("off")
    box = dict(boxstyle="round,pad=0.5", fc="#eaf1f8", ec=FOCAL, lw=1.3)
    ax.text(0.30, 0.82, f"All eligible-schema rows\n{all_rows[0]} rows · {all_rows[1]} biopsies · {all_rows[2]} patients",
            ha="center", va="center", bbox=box, fontsize=7.5)
    ax.text(0.30, 0.16,
            f"Strict pre-event cohort\n{final[0]} rows · {final[1]} biopsies · {final[2]} patients\n"
            f"({pos[0]} positive rows / {pos[1]} progressor patients)",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.5", fc=FOCAL, ec=FOCAL),
            color="white", fontsize=7.5, fontweight="bold")
    ax.annotate("", xy=(0.30, 0.30), xytext=(0.30, 0.70),
                arrowprops=dict(arrowstyle="-|>", color=FOCAL, lw=1.5))
    lines = "\n".join(f"  • {label}: {_row(key, 'rows')} / {_row(key, 'patients')}"
                      for label, key in excl)
    ax.text(0.72, 0.50, "Excluded (rows / patients):\n" + lines, ha="left", va="center",
            bbox=dict(boxstyle="round,pad=0.4", fc="#f7f2ea", ec="#b07d2a", lw=1.0), fontsize=6.8)
    ax.annotate("", xy=(0.55, 0.50), xytext=(0.32, 0.50),
                arrowprops=dict(arrowstyle="-|>", color="#b07d2a", lw=1.2))
    ax.set_title("Strict pre-event LGD2+ cohort derivation", fontsize=8, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0.02, 0.95)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_operating_points(comp: pd.DataFrame, out: Path) -> Path:
    mo = comp.copy()
    mo["disp"] = mo["model_family"].map(DISPLAY_NAMES).fillna(mo["model_family"])
    mo = mo.sort_values("auprc", ascending=False)
    fig, axes = plt.subplots(1, 4, figsize=(9.8, 3.4), sharey=True)
    for ax, (m, lab) in zip(axes, [("sensitivity", "Sensitivity"), ("specificity", "Specificity"),
                                   ("ppv", "PPV"), ("npv", "NPV")]):
        cols = [_bar_color(k) for k in mo.model_family]
        ax.barh(np.arange(len(mo)), mo[m], color=cols, edgecolor="white", height=0.72)
        ax.set_xlabel(lab)
        ax.set_xlim(0, 1.0)
    axes[0].set_yticks(np.arange(len(mo)))
    axes[0].set_yticklabels(mo.disp)
    fig.text(0.5, 1.03,
             "Clinical operating points at cross-fitted inner-validation threshold (n=150)",
             ha="center", fontsize=7.8, fontweight="bold")
    fig.text(0.5, 0.965, "Blue = late mean (headline);  grey = CNV-only baseline",
             ha="center", fontsize=5.8, color="#555")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reports-dir", default="reports/thesis_ch1",
                    help="Directory holding the allowlisted summary CSVs.")
    args = ap.parse_args()
    _style()
    R = Path(args.reports_dir)
    comp = pd.read_csv(R / "lgd2_final_pre_event_model_comparison.csv")
    paired = pd.read_csv(R / "lgd2_final_pre_event_paired_differences.csv")
    flow = pd.read_csv(R / "lgd2_final_pre_event_cohort_flow.csv")
    made = [
        fig_main_comparison(comp, R / "fig_main_model_comparison.png"),
        fig_paired_forest(paired, R / "fig_paired_differences_forest.png"),
        fig_cohort_flow(flow, R / "fig_cohort_flow.png"),
        fig_operating_points(comp, R / "fig_operating_points.png"),
    ]
    for p in made:
        print(f"wrote {p}")


if __name__ == "__main__":
    main()

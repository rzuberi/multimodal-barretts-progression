#!/usr/bin/env python
"""Package the LGD2+ modality-ablation (feature-shuffle) evidence into a thesis table.

Reads existing per-sample out-of-fold predictions from the
``campaign_lgd2_h200_patient_signal_lgd2_20260319`` shuffle campaign (baseline,
shuffle_image, shuffle_cnv, shuffle_both), recomputes patient-max metrics with
the CLEAN repo helpers, and writes a small comparison table. No model is rerun.

Feature shuffling permutes a modality across patients while holding the sample
set fixed, so a drop under shuffle is SUPPORTING evidence that the model relies
on that modality -- not causal proof. Image shuffling is the direct test of the
histology contribution.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.aggregation import aggregate_predictions
from barrett.evaluation.metrics import compute_metrics

CAMPAIGN_SUBPATH = (
    "data/foundation_grid_runs/campaign_lgd2_h200_patient_signal_lgd2_20260319"
    "/patchselect/uni2_signal"
)
CONDITIONS = ["baseline", "shuffle_image", "shuffle_cnv", "shuffle_both"]
SHUFFLE_CONDITIONS = ["shuffle_image", "shuffle_cnv", "shuffle_both"]
MODELS = ["coattn_abmil_cnv", "early_mean_mlp", "early_mean_mlp_timev1"]
ENDPOINT = "NextBiopsyProgression_LGD2plus"
PRED_TEMPLATE = (
    "predictions_all_samples_{model}_windows_armdiff_plus_arms_plus_cx"
    "_{endpoint}_k0_uniform_epca0_rep01_fold{fold}.csv"
)
FOLDS = [1, 2, 3, 4, 5]
# Lower is better -> a positive (baseline - shuffle) delta means shuffle got WORSE.
METRICS = ["auprc", "roc_auc", "brier_score"]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reports/thesis_ch1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment-root",
        default=os.environ.get("BARRETTS_EXPERIMENT_ROOT"),
        help="Root for external relative paths. Defaults to repo parent.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def experiment_root(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value).expanduser().resolve()
    return REPO_ROOT.parent.resolve()


def load_condition_model(cv_dir: Path, model: str) -> tuple[pd.DataFrame, list[str]]:
    """Load and concat the 5 per-fold prediction CSVs for one model/condition."""
    frames, missing = [], []
    for fold in FOLDS:
        path = cv_dir / PRED_TEMPLATE.format(model=model, endpoint=ENDPOINT, fold=fold)
        if not path.exists():
            missing.append(str(path))
            continue
        frames.append(pd.read_csv(path))
    if missing:
        return pd.DataFrame(), missing
    return pd.concat(frames, ignore_index=True), []


def patient_max_metrics(pred: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    agg = aggregate_predictions(pred, "patient_max")
    agg = agg.dropna(subset=["unit_id", "y_true", "y_prob"]).copy()
    return compute_metrics(agg["y_true"], agg["y_prob"]), agg


def main() -> int:
    args = parse_args()
    root = experiment_root(args.experiment_root)
    campaign = root / CAMPAIGN_SUBPATH
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    blockers: list[str] = []
    rows: list[dict] = []
    # sample_id set per model, from baseline, to check identity across conditions.
    baseline_sets: dict[str, frozenset] = {}
    patient_counts: dict[tuple[str, str], tuple[int, int, int]] = {}

    for model in MODELS:
        for condition in CONDITIONS:
            cv_dir = campaign / condition / "cv"
            pred, missing = load_condition_model(cv_dir, model)
            if missing:
                blockers.append(
                    f"{model}/{condition}: missing prediction files: {missing}"
                )
                continue
            required = {"sample_id", "patient_id", "fold", "y_true", "y_prob"}
            have = set(pred.columns)
            if not required.issubset(have):
                blockers.append(
                    f"{model}/{condition}: missing columns {sorted(required - have)} "
                    f"in {cv_dir}"
                )
                continue
            sample_set = frozenset(pred["sample_id"].astype(str))
            if condition == "baseline":
                baseline_sets[model] = sample_set
            metrics, agg = patient_max_metrics(pred)
            patient_counts[(model, condition)] = (
                int(agg["patient_id"].nunique()),
                int((agg.groupby("patient_id")["y_true"].max() == 1).sum()),
                int((agg.groupby("patient_id")["y_true"].max() == 0).sum()),
            )
            rows.append(
                {
                    "model": model,
                    "condition": condition,
                    "endpoint": ENDPOINT,
                    "aggregation": "patient_max",
                    "n_samples": int(len(pred)),
                    "n_patients": int(agg["patient_id"].nunique()),
                    "n_positive_patients": patient_counts[(model, condition)][1],
                    **{m: metrics[m] for m in METRICS},
                }
            )

    # Identity check: every shuffle condition must share baseline's sample set.
    for model in MODELS:
        base = baseline_sets.get(model)
        if base is None:
            continue
        for condition in SHUFFLE_CONDITIONS:
            cv_dir = campaign / condition / "cv"
            pred, missing = load_condition_model(cv_dir, model)
            if missing or "sample_id" not in pred.columns:
                continue
            this_set = frozenset(pred["sample_id"].astype(str))
            if this_set != base:
                warnings.append(
                    f"{model}: sample_id set for {condition} differs from baseline "
                    f"(baseline n={len(base)}, {condition} n={len(this_set)}). "
                    "Deltas for this model are NOT a valid matched comparison."
                )

    if not rows:
        _write_blocked(out_dir, campaign, blockers, warnings)
        print("BLOCKED: no valid metric rows. See warnings file.")
        return 1

    results = pd.DataFrame(rows)

    # Deltas: baseline minus each shuffle, per model, for each metric.
    delta_rows: list[dict] = []
    for model in results["model"].unique():
        sub = results[results["model"] == model].set_index("condition")
        if "baseline" not in sub.index:
            warnings.append(f"{model}: no baseline row; deltas skipped.")
            continue
        model_blocked = any(model in w and "NOT a valid" in w for w in warnings)
        for condition in SHUFFLE_CONDITIONS:
            if condition not in sub.index:
                continue
            row = {"model": model, "comparison": f"baseline_minus_{condition}"}
            for m in METRICS:
                row[f"delta_{m}"] = float(sub.loc["baseline", m] - sub.loc[condition, m])
            row["matched_sample_set"] = not model_blocked
            delta_rows.append(row)
    deltas = pd.DataFrame(delta_rows)

    results.to_csv(out_dir / "lgd2_modality_ablation_comparison.csv", index=False)
    (out_dir / "lgd2_modality_ablation_comparison.md").write_text(
        _make_markdown(results, deltas, campaign)
    )
    (out_dir / "lgd2_modality_ablation_warnings.md").write_text(
        _make_warnings(warnings, blockers)
    )
    print(f"Wrote {len(results)} metric rows and {len(deltas)} delta rows to {out_dir}")
    print(f"Warnings: {len(warnings)}  Blockers: {len(blockers)}")
    return 0


def _fmt(v: object) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    try:
        return f"{float(v):+.3f}" if isinstance(v, float) else str(v)
    except Exception:
        return str(v)


def _make_markdown(results: pd.DataFrame, deltas: pd.DataFrame, campaign: Path) -> str:
    lines = [
        "# LGD2+ Modality Ablation (feature-shuffle) - patient_max",
        "",
        f"Endpoint: `{ENDPOINT}`. Aggregation: patient_max. "
        "Evaluation: 5-fold patient-disjoint out-of-fold predictions.",
        f"Source campaign: `{campaign}`.",
        "",
        "Feature shuffling permutes a modality across patients while the sample set is "
        "held fixed. A metric drop under shuffle is **supporting** evidence that the "
        "model relies on that modality, not causal proof. **shuffle_image is the direct "
        "test of the histology contribution.**",
        "",
        "## Patient-max metrics by model and condition",
        "",
        "| model | condition | n_patients | n_pos | AUPRC | ROC AUC | Brier |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, r in results.iterrows():
        lines.append(
            "| " + " | ".join([
                str(r["model"]), str(r["condition"]), str(r["n_patients"]),
                str(r["n_positive_patients"]),
                f"{r['auprc']:.3f}", f"{r['roc_auc']:.3f}", f"{r['brier_score']:.3f}",
            ]) + " |"
        )
    lines += [
        "",
        "## Deltas (baseline minus shuffle)",
        "",
        "Positive AUPRC/AUC delta = shuffle performed worse than baseline (modality "
        "helped). For Brier (lower is better) a NEGATIVE delta = shuffle worse.",
        "",
        "| model | comparison | dAUPRC | dROC_AUC | dBrier | matched_set |",
        "|---|---|---:|---:|---:|:--:|",
    ]
    for _, r in deltas.iterrows():
        lines.append(
            "| " + " | ".join([
                str(r["model"]), str(r["comparison"]),
                f"{r['delta_auprc']:+.3f}", f"{r['delta_roc_auc']:+.3f}",
                f"{r['delta_brier_score']:+.3f}", "yes" if r["matched_sample_set"] else "NO",
            ]) + " |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- Metrics recomputed with `barrett.evaluation.metrics.compute_metrics` and "
        "`barrett.evaluation.aggregation.aggregate_predictions` (patient_max).",
        "- Sample sets verified identical across conditions per model; see warnings file.",
        "- No model was retrained; predictions are the saved out-of-fold campaign outputs.",
    ]
    return "\n".join(lines) + "\n"


def _make_warnings(warnings: list[str], blockers: list[str]) -> str:
    lines = ["# LGD2+ Modality Ablation Warnings", ""]
    if blockers:
        lines += ["## Blockers", ""]
        lines += [f"- {b}" for b in blockers]
        lines.append("")
    lines += ["## Warnings", ""]
    if warnings:
        lines += [f"- {w}" for w in warnings]
    else:
        lines.append("- None. All conditions share identical sample sets per model.")
    return "\n".join(lines) + "\n"


def _write_blocked(out_dir: Path, campaign: Path, blockers, warnings) -> None:
    msg = (
        "# LGD2+ Modality Ablation - BLOCKED\n\n"
        "No valid patient-level comparison could be built. Manual review required.\n\n"
        f"Campaign path: `{campaign}`\n\n## Blockers\n\n"
        + "\n".join(f"- {b}" for b in blockers)
        + "\n"
    )
    (out_dir / "lgd2_modality_ablation_comparison.md").write_text(msg)
    (out_dir / "lgd2_modality_ablation_comparison.csv").write_text(
        "model,condition,status\n"
    )
    (out_dir / "lgd2_modality_ablation_warnings.md").write_text(
        _make_warnings(warnings, blockers)
    )


if __name__ == "__main__":
    raise SystemExit(main())

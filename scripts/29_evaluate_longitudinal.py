#!/usr/bin/env python
"""Paired evaluation: landmarking longitudinal model vs frozen single-timepoint baselines.

Pools the longitudinal out-of-fold (OOF) predictions written by
``27_run_longitudinal_outer_fold.py`` across all five outer folds. Each landmark
is one biopsy row, so the longitudinal OOF covers the same biopsy ``sample_id``
set as the frozen Chapter 1 baseline OOF tables. Both the longitudinal OOF and
each baseline OOF are first aggregated to patient level with patient-max (the
baseline evaluation protocol), then the two patient-level tables are joined on
``patient_id`` and paired bootstrap confidence intervals are computed for the
metric deltas (longitudinal minus baseline) on AUPRC, ROC AUC and Brier.

The longitudinal model predicts the SAME endpoint over the SAME biopsy rows as
the baselines and both are reduced to the SAME patients, so "does adding history
help?" is a paired test: the bootstrap resamples patients and recomputes both
models' patient-level metrics on each resample, so the CI reflects the paired
difference rather than two independent estimates.

Outputs (written under --output-dir, small CSVs safe to commit via the guard
allowlist):
  longitudinal_vs_baselines_patient_metrics.csv  — point metrics per model
  longitudinal_paired_deltas.csv                 — delta + 95% bootstrap CI per baseline/metric

Usage:
    python scripts/29_evaluate_longitudinal.py \
        --longitudinal-root <output root with longitudinal/foldN/> \
        --baseline-oof-dir  <release>/training_final_nested_cv_v1/oof \
        --output-dir        reports/longitudinal
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

BASELINE_FAMILIES = ["cnv_only", "image_only", "late_mean", "intermediate_fusion"]
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20260713


def patient_max(frame: pd.DataFrame, prob_col: str = "y_prob") -> pd.DataFrame:
    """Aggregate biopsy-level predictions to one row per patient (max risk)."""
    return (
        frame.groupby("patient_id", as_index=False)
        .agg(y_true=("y_true", "max"), y_prob=(prob_col, "max"))
    )


def _metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    out = {
        "auprc": float(average_precision_score(y_true, y_prob)),
        "brier": float(brier_score_loss(y_true, y_prob)),
    }
    out["roc_auc"] = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float("nan")
    return out


def load_longitudinal_oof(root: Path) -> pd.DataFrame:
    """Concatenate longitudinal per-fold outer_test_predictions into one OOF table."""
    parts = []
    for fold_dir in sorted((root / "longitudinal").glob("fold*")):
        path = fold_dir / "outer_test_predictions.csv"
        if not path.exists():
            raise SystemExit(f"missing longitudinal fold output: {path}")
        df = pd.read_csv(path, dtype={"sample_id": str})
        parts.append(df)
    if not parts:
        raise SystemExit(f"no longitudinal fold outputs under {root}/longitudinal")
    oof = pd.concat(parts, ignore_index=True)
    if oof["sample_id"].duplicated().any():
        raise SystemExit("duplicate sample_id across longitudinal folds — OOF must be disjoint")
    return oof


def paired_bootstrap(
    patients: pd.DataFrame,
    prob_a: str,
    prob_b: str,
    metric: str,
    n_boot: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float, float]:
    """Paired bootstrap of (metric_a - metric_b), resampling patients with replacement.

    Returns (point_delta, ci_low, ci_high) at 95%.
    """
    rng = np.random.default_rng(seed)
    y = patients["y_true"].to_numpy(dtype=int)
    a = patients[prob_a].to_numpy(dtype=float)
    b = patients[prob_b].to_numpy(dtype=float)

    def _m(yy, pp):
        if metric == "auprc":
            return average_precision_score(yy, pp)
        if metric == "roc_auc":
            return roc_auc_score(yy, pp) if len(np.unique(yy)) > 1 else np.nan
        return brier_score_loss(yy, pp)

    point = float(_m(y, a) - _m(y, b))
    n = len(y)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yy = y[idx]
        if len(np.unique(yy)) < 2:
            continue
        deltas.append(float(_m(yy, a[idx]) - _m(yy, b[idx])))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return point, float(lo), float(hi)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--longitudinal-root", required=True)
    parser.add_argument("--baseline-oof-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--prob-col", default="y_prob",
                        help="baseline probability column (y_prob or y_prob_calibrated)")
    args = parser.parse_args()

    long_root = Path(args.longitudinal_root).resolve()
    oof_dir = Path(args.baseline_oof_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    longitudinal = load_longitudinal_oof(long_root)
    long_patient = patient_max(longitudinal, "y_prob")
    long_patient = long_patient.rename(columns={"y_prob": "prob_longitudinal"})

    # point metrics table (patient level), longitudinal first
    metric_rows = []
    lm = _metrics(long_patient["y_true"].to_numpy(), long_patient["prob_longitudinal"].to_numpy())
    metric_rows.append({"model": "longitudinal", "n_patients": int(len(long_patient)), **lm})

    delta_rows = []
    for family in BASELINE_FAMILIES:
        path = oof_dir / f"{family}_oof_predictions.csv"
        if not path.exists():
            print(f"[skip] baseline family not found: {path}")
            continue
        base = pd.read_csv(path, dtype={"sample_id": str})
        base_patient = patient_max(base, args.prob_col).rename(columns={"y_prob": f"prob_{family}"})

        base_only = _metrics(base_patient["y_true"].to_numpy(), base_patient[f"prob_{family}"].to_numpy())
        metric_rows.append({"model": family, "n_patients": int(len(base_patient)), **base_only})

        # paired join at patient level (same patients across both models)
        merged = long_patient.merge(
            base_patient[["patient_id", f"prob_{family}"]], on="patient_id", how="inner"
        )
        if len(merged) != len(long_patient) or len(merged) != len(base_patient):
            print(f"[warn] {family}: patient overlap {len(merged)} vs "
                  f"long {len(long_patient)} base {len(base_patient)}")
        for metric in ("auprc", "roc_auc", "brier"):
            point, lo, hi = paired_bootstrap(
                merged.rename(columns={"prob_longitudinal": "A", f"prob_{family}": "B"}),
                "A", "B", metric,
            )
            delta_rows.append({
                "baseline": family, "metric": metric,
                "delta_longitudinal_minus_baseline": round(point, 4),
                "ci95_low": round(lo, 4), "ci95_high": round(hi, 4),
                "excludes_zero": bool(lo > 0 or hi < 0),
                "n_patients": int(len(merged)),
            })

    metrics_df = pd.DataFrame(metric_rows)
    deltas_df = pd.DataFrame(delta_rows)
    metrics_path = out_dir / "longitudinal_vs_baselines_patient_metrics.csv"
    deltas_path = out_dir / "longitudinal_paired_deltas.csv"
    metrics_df.to_csv(metrics_path, index=False)
    deltas_df.to_csv(deltas_path, index=False)

    print(json.dumps({
        "n_longitudinal_patients": int(len(long_patient)),
        "n_longitudinal_landmarks": int(len(longitudinal)),
        "metrics_csv": str(metrics_path),
        "deltas_csv": str(deltas_path),
    }, indent=2))
    print("\n=== patient-level metrics ===")
    print(metrics_df.to_string(index=False))
    print("\n=== paired deltas (longitudinal - baseline) ===")
    print(deltas_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

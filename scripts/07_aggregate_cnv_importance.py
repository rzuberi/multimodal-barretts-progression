#!/usr/bin/env python
"""Aggregate per-fold CNV feature importances into a cross-validated ranking.

Reads ``cnv_feature_importance.csv`` from each outer fold of the frozen
``cnv_only`` release and produces a mean (+/- std) importance table across the
5 patient-disjoint folds, plus per-fold rank stability. Output is an
aggregate-only table (feature name + importance statistics) with NO patient
data — safe to commit under reports/thesis_ch1/ and to transfer off-cluster.

The ``cnv_only`` model is a scikit-learn Pipeline
(SimpleImputer -> StandardScaler -> PCA -> RandomForestClassifier); the
importances exported per fold are RandomForest impurity importances mapped back
to the original genomic features (chromosome arms / windows).

Usage (on the cluster, from repo root):
    export BARRETTS_EXPERIMENT_ROOT=/mnt/scratche/.../barretts_training
    python scripts/07_aggregate_cnv_importance.py \
        --out reports/thesis_ch1/lgd2_cnv_feature_importance_aggregated.csv
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_RELEASE = (
    "analysis/chapter1_lgd2_final_pre_event_20260713_final/"
    "training_final_nested_cv_v1/cnv_only"
)


def load_folds(cnv_only_dir: Path) -> pd.DataFrame:
    frames = []
    for fold in sorted(cnv_only_dir.glob("fold*")):
        f = fold / "cnv_feature_importance.csv"
        if not f.exists():
            continue
        df = pd.read_csv(f)
        df = df.rename(columns={df.columns[0]: "feature", df.columns[1]: "importance"})
        df["fold"] = fold.name
        df["rank"] = df["importance"].rank(ascending=False, method="min").astype(int)
        frames.append(df[["feature", "importance", "fold", "rank"]])
    if not frames:
        raise FileNotFoundError(f"no cnv_feature_importance.csv under {cnv_only_dir}")
    return pd.concat(frames, ignore_index=True)


def aggregate(long: pd.DataFrame) -> pd.DataFrame:
    g = long.groupby("feature")
    out = pd.DataFrame({
        "importance_mean": g["importance"].mean(),
        "importance_std": g["importance"].std(ddof=1),
        "importance_min": g["importance"].min(),
        "importance_max": g["importance"].max(),
        "rank_mean": g["rank"].mean(),
        "rank_best": g["rank"].min(),
        "n_folds": g["importance"].count(),
    }).reset_index()
    out = out.sort_values("importance_mean", ascending=False).reset_index(drop=True)
    out.insert(0, "overall_rank", np.arange(1, len(out) + 1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    root = os.environ.get("BARRETTS_EXPERIMENT_ROOT", "")
    ap.add_argument("--cnv-only-dir", default=str(Path(root) / DEFAULT_RELEASE) if root else "",
                    help="Path to the frozen cnv_only release dir (defaults under $BARRETTS_EXPERIMENT_ROOT).")
    ap.add_argument("--out", default="reports/thesis_ch1/lgd2_cnv_feature_importance_aggregated.csv")
    args = ap.parse_args()
    if not args.cnv_only_dir:
        ap.error("set $BARRETTS_EXPERIMENT_ROOT or pass --cnv-only-dir")
    long = load_folds(Path(args.cnv_only_dir))
    agg = aggregate(long)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(out, index=False)
    print(f"wrote {out}  ({len(agg)} features across {long['fold'].nunique()} folds)")
    print("top 15 by mean impurity importance:")
    print(agg.head(15).to_string(index=False))


if __name__ == "__main__":
    main()

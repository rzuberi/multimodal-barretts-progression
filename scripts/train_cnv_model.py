#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a headless elastic-net CNV classifier from a sample-by-feature CSV."
    )
    parser.add_argument("--train_csv", required=True, help="Training CSV with one row per sample.")
    parser.add_argument("--output_dir", required=True, help="Directory to write model and metrics.")
    parser.add_argument("--label_col", required=True, help="Binary label column.")
    parser.add_argument("--id_col", default="sample_id", help="Sample identifier column.")
    parser.add_argument("--group_col", default=None, help="Optional grouping column, for example patient_id.")
    parser.add_argument(
        "--feature_cols",
        default=None,
        help="Optional comma-separated list of feature columns. Default: all numeric columns except id/label/group.",
    )
    parser.add_argument(
        "--positive_class",
        default=None,
        help="Optional positive class label if label_col is not already 0/1.",
    )
    parser.add_argument("--cv_folds", type=int, default=5, help="Number of CV folds. Default: 5.")
    parser.add_argument("--random_seed", type=int, default=7, help="Random seed for CV.")
    parser.add_argument("--l1_ratio", type=float, default=0.5, help="Elastic-net l1_ratio. Default: 0.5.")
    parser.add_argument("--c_value", type=float, default=1.0, help="Inverse regularization strength. Default: 1.0.")
    parser.add_argument("--max_iter", type=int, default=5000, help="Maximum optimizer iterations. Default: 5000.")
    return parser.parse_args()


def _resolve_feature_columns(df: pd.DataFrame, args: argparse.Namespace) -> List[str]:
    if args.feature_cols:
        feature_cols = [c.strip() for c in str(args.feature_cols).split(",") if c.strip()]
    else:
        exclude = {args.id_col, args.label_col}
        if args.group_col:
            exclude.add(args.group_col)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c not in exclude]
    if not feature_cols:
        raise ValueError("No feature columns resolved. Pass --feature_cols or provide numeric CNV columns.")
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError("Requested feature columns missing from CSV: %s" % ", ".join(missing))
    return feature_cols


def _encode_binary_target(series: pd.Series, positive_class: Optional[str]) -> Tuple[np.ndarray, Dict[str, str]]:
    clean = series.copy()
    if clean.isna().any():
        raise ValueError("Label column contains missing values.")
    unique_vals = list(pd.unique(clean))
    if len(unique_vals) != 2:
        raise ValueError("Binary classification requires exactly 2 unique labels; found %d." % len(unique_vals))
    if positive_class is None:
        if set(unique_vals) == {0, 1} or set(unique_vals) == {"0", "1"}:
            positive_class = "1"
        else:
            positive_class = str(sorted([str(v) for v in unique_vals])[1])
    y = (clean.astype(str) == str(positive_class)).astype(int).to_numpy()
    if y.min() == y.max():
        raise ValueError("Resolved labels collapse to a single class. Check --positive_class.")
    class_map = {
        "negative_class": str(next(v for v in unique_vals if str(v) != str(positive_class))),
        "positive_class": str(positive_class),
    }
    return y, class_map


def _build_pipeline(args: argparse.Namespace) -> Pipeline:
    clf = LogisticRegression(
        penalty="elasticnet",
        solver="saga",
        l1_ratio=float(args.l1_ratio),
        C=float(args.c_value),
        class_weight="balanced",
        max_iter=int(args.max_iter),
        random_state=int(args.random_seed),
    )
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("clf", clf),
        ]
    )


def _choose_splitter(y: np.ndarray, groups: Optional[pd.Series], n_splits: int, seed: int):
    if groups is not None:
        n_groups = int(groups.astype(str).nunique())
        if n_groups < n_splits:
            raise ValueError("group_col has only %d unique groups but cv_folds=%d." % (n_groups, n_splits))
        return "group_kfold", GroupKFold(n_splits=n_splits)
    return "stratified_kfold", StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)


def _cv_predictions(
    x: pd.DataFrame,
    y: np.ndarray,
    sample_ids: pd.Series,
    groups: Optional[pd.Series],
    pipeline: Pipeline,
    n_splits: int,
    seed: int,
) -> pd.DataFrame:
    split_name, splitter = _choose_splitter(y=y, groups=groups, n_splits=n_splits, seed=seed)
    records = []
    if split_name == "group_kfold":
        split_iter = splitter.split(x, y, groups=groups.astype(str))
    else:
        split_iter = splitter.split(x, y)
    for fold_idx, (train_idx, test_idx) in enumerate(split_iter, start=1):
        x_train = x.iloc[train_idx]
        x_test = x.iloc[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]
        model = pipeline
        model.fit(x_train, y_train)
        score = model.predict_proba(x_test)[:, 1]
        pred = (score >= 0.5).astype(int)
        fold_df = pd.DataFrame(
            {
                "fold": fold_idx,
                "sample_id": sample_ids.iloc[test_idx].astype(str).to_numpy(),
                "y_true": y_test.astype(int),
                "y_score": score.astype(float),
                "y_pred": pred.astype(int),
            }
        )
        if groups is not None:
            fold_df["group_id"] = groups.iloc[test_idx].astype(str).to_numpy()
        records.append(fold_df)
    return pd.concat(records, ignore_index=True)


def _metric_summary(pred_df: pd.DataFrame) -> dict:
    y_true = pred_df["y_true"].astype(int).to_numpy()
    y_score = pred_df["y_score"].astype(float).to_numpy()
    y_pred = pred_df["y_pred"].astype(int).to_numpy()
    summary = {
        "n_eval": int(len(pred_df)),
        "n_pos": int(y_true.sum()),
        "n_neg": int((1 - y_true).sum()),
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "average_precision": float(average_precision_score(y_true, y_score)),
        "balanced_accuracy_at_0p5": float(balanced_accuracy_score(y_true, y_pred)),
    }
    per_fold = []
    for fold, fold_df in pred_df.groupby("fold", sort=True):
        fy = fold_df["y_true"].astype(int).to_numpy()
        fs = fold_df["y_score"].astype(float).to_numpy()
        fp = fold_df["y_pred"].astype(int).to_numpy()
        per_fold.append(
            {
                "fold": int(fold),
                "n_eval": int(len(fold_df)),
                "roc_auc": float(roc_auc_score(fy, fs)) if len(np.unique(fy)) == 2 else None,
                "average_precision": float(average_precision_score(fy, fs)),
                "balanced_accuracy_at_0p5": float(balanced_accuracy_score(fy, fp)),
            }
        )
    summary["per_fold"] = per_fold
    return summary


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.train_csv)
    if args.id_col not in df.columns:
        raise ValueError("id_col '%s' not found." % args.id_col)
    if args.label_col not in df.columns:
        raise ValueError("label_col '%s' not found." % args.label_col)
    if args.group_col and args.group_col not in df.columns:
        raise ValueError("group_col '%s' not found." % args.group_col)

    feature_cols = _resolve_feature_columns(df=df, args=args)
    model_df = df[[args.id_col, args.label_col] + ([args.group_col] if args.group_col else []) + feature_cols].copy()
    model_df = model_df.dropna(axis=0).reset_index(drop=True)
    if model_df.empty:
        raise ValueError("No complete rows remain after dropping missing values.")

    x = model_df[feature_cols].astype(float)
    y, class_map = _encode_binary_target(model_df[args.label_col], positive_class=args.positive_class)
    groups = model_df[args.group_col] if args.group_col else None
    sample_ids = model_df[args.id_col].astype(str)

    pipeline = _build_pipeline(args)
    pred_df = _cv_predictions(
        x=x,
        y=y,
        sample_ids=sample_ids,
        groups=groups,
        pipeline=pipeline,
        n_splits=int(args.cv_folds),
        seed=int(args.random_seed),
    )
    metrics = _metric_summary(pred_df)

    final_model = _build_pipeline(args)
    final_model.fit(x, y)
    artifact = {
        "model": final_model,
        "feature_columns": feature_cols,
        "id_col": args.id_col,
        "label_col": args.label_col,
        "group_col": args.group_col,
        "class_map": class_map,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_train_rows": int(len(model_df)),
        "n_features": int(len(feature_cols)),
    }

    joblib.dump(artifact, out_dir / "model.joblib")
    pred_df.to_csv(out_dir / "cv_predictions.csv", index=False)
    (out_dir / "feature_columns.txt").write_text("\n".join(feature_cols) + "\n")
    (out_dir / "train_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (out_dir / "training_metadata.json").write_text(
        json.dumps(
            {
                "train_csv": str(Path(args.train_csv).resolve()),
                "id_col": args.id_col,
                "label_col": args.label_col,
                "group_col": args.group_col,
                "class_map": class_map,
                "cv_folds": int(args.cv_folds),
                "random_seed": int(args.random_seed),
                "l1_ratio": float(args.l1_ratio),
                "c_value": float(args.c_value),
                "max_iter": int(args.max_iter),
                "n_rows_after_dropna": int(len(model_df)),
                "n_features": int(len(feature_cols)),
            },
            indent=2,
        )
        + "\n"
    )

    print("[train_cnv_model] wrote %s" % str(out_dir))
    print("[train_cnv_model] roc_auc=%.4f ap=%.4f bal_acc=%.4f" % (
        metrics["roc_auc"],
        metrics["average_precision"],
        metrics["balanced_accuracy_at_0p5"],
    ))


if __name__ == "__main__":
    main()

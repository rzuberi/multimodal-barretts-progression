#!/usr/bin/env python3

import argparse
from pathlib import Path

import joblib
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run headless inference with a trained CNV model artifact."
    )
    parser.add_argument("--model_path", required=True, help="Path to model.joblib from train_cnv_model.py.")
    parser.add_argument("--input_csv", required=True, help="Input CSV with one row per sample.")
    parser.add_argument("--output_csv", required=True, help="Prediction CSV output path.")
    parser.add_argument("--id_col", default=None, help="Optional sample identifier column. Defaults to training artifact id_col.")
    parser.add_argument("--threshold", type=float, default=0.5, help="Probability threshold for hard calls. Default: 0.5.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = joblib.load(args.model_path)
    model = artifact["model"]
    feature_cols = list(artifact["feature_columns"])
    default_id_col = artifact.get("id_col", "sample_id")
    id_col = args.id_col or default_id_col
    class_map = artifact.get("class_map", {})

    df = pd.read_csv(args.input_csv)
    if id_col not in df.columns:
        raise ValueError("id_col '%s' not found in input CSV." % id_col)
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError("Input CSV is missing feature columns: %s" % ", ".join(missing))

    pred_df = df[[id_col] + feature_cols].copy().dropna(axis=0).reset_index(drop=True)
    if pred_df.empty:
        raise ValueError("No complete rows remain after dropping missing values.")

    x = pred_df[feature_cols].astype(float)
    score = model.predict_proba(x)[:, 1]
    y_pred = (score >= float(args.threshold)).astype(int)

    out = pd.DataFrame(
        {
            id_col: pred_df[id_col].astype(str),
            "positive_class_probability": score.astype(float),
            "predicted_label": y_pred.astype(int),
        }
    )
    if class_map:
        out["positive_class_name"] = class_map.get("positive_class")
        out["negative_class_name"] = class_map.get("negative_class")

    out_path = Path(args.output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print("[predict_cnv_model] wrote %s" % str(out_path))


if __name__ == "__main__":
    main()

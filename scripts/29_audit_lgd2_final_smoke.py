#!/usr/bin/env python
"""Audit the required fold-1 final-model smoke runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.training.artifacts import validate_fold_directory  # noqa: E402
from barrett.evaluation.tables import markdown_table  # noqa: E402


FAMILIES = (
    "cnv_only", "image_only", "early_fusion", "intermediate_fusion", "coattention_fusion",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--reports-dir", default=str(REPO_ROOT / "reports/thesis_ch1"))
    args = parser.parse_args()
    release = Path(args.release_root).resolve()
    output = Path(args.output_root).resolve()
    reports = Path(args.reports_dir)
    manifest = pd.read_csv(release / "training_manifest_v2.csv", dtype={"sample_id": str})
    expected = manifest[manifest["fold_id_rep01"].eq(1)].copy()
    rows = []
    for family in FAMILIES:
        directory = output / family / "fold1"
        problems, predictions = validate_fold_directory(directory, expected, family, 1)
        completion = {}
        if (directory / "fold_completion.json").exists():
            try:
                completion = json.loads((directory / "fold_completion.json").read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        if predictions is not None:
            if not np.isfinite(predictions["y_prob"]).all():
                problems.append("non-finite probabilities")
            if predictions["y_prob"].nunique() < 2:
                problems.append("constant probabilities")
        assignments_path = directory / "inner_fold_assignments.csv"
        if assignments_path.exists():
            assignments = pd.read_csv(assignments_path)
            if assignments["patient_id"].duplicated().any():
                problems.append("patient duplicated in inner-fold assignments")
            if set(assignments["patient_id"].astype(str)) & set(expected["patient_id"].astype(str)):
                problems.append("outer-test patient present in inner-fold assignments")
        rows.append({
            "model_family": family,
            "outer_fold": 1,
            "status": "PASS" if not problems else "FAIL",
            "expected_rows": len(expected),
            "prediction_rows": len(predictions) if predictions is not None else 0,
            "expected_patients": expected["patient_id"].nunique(),
            "prediction_patients": predictions["patient_id"].nunique() if predictions is not None else 0,
            "selected_configuration_id": completion.get("selected_configuration_id", ""),
            "probability_min": predictions["y_prob"].min() if predictions is not None else np.nan,
            "probability_max": predictions["y_prob"].max() if predictions is not None else np.nan,
            "problems": "; ".join(problems),
        })
    table = pd.DataFrame(rows)
    reports.mkdir(parents=True, exist_ok=True)
    table.to_csv(reports / "lgd2_final_training_smoke_audit.csv", index=False)
    passed = int(table["status"].eq("PASS").sum())
    lines = [
        "# LGD2+ Final Training Smoke Audit", "",
        f"Gate status: **{'PASS' if passed == len(FAMILIES) else 'INCOMPLETE'}** ({passed}/{len(FAMILIES)} families).",
        "", markdown_table(table, list(table.columns)), "",
        "Folds 2-5 must not be launched until every requested family passes.",
    ]
    (reports / "lgd2_final_training_smoke_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    warnings = table.loc[table["status"].ne("PASS"), ["model_family", "problems"]]
    warning_lines = ["# LGD2+ Final Training Smoke Warnings", ""]
    if warnings.empty:
        warning_lines.append("None.")
    else:
        warning_lines.extend(
            f"- `{row.model_family}`: {row.problems or 'missing/incomplete artifacts'}"
            for row in warnings.itertuples()
        )
    (reports / "lgd2_final_training_smoke_warnings.md").write_text(
        "\n".join(warning_lines) + "\n", encoding="utf-8"
    )
    print(f"smoke gate: {passed}/{len(FAMILIES)} PASS")
    return 0 if passed == len(FAMILIES) else 1


if __name__ == "__main__":
    raise SystemExit(main())

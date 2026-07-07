#!/usr/bin/env python
"""Summarise lightweight external LGD2+ CNV interpretation outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.cnv_interpretation import summarize_cnv_interpretation
from barrett.evaluation.tables import markdown_table

DEFAULT_CASES = Path("reports/thesis_ch1/lgd2_final_interpretation_case_subset.csv")
DEFAULT_OUT_DIR = Path("reports/thesis_ch1")
DEFAULT_EXTERNAL = Path("analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--external-output-dir", default=str(DEFAULT_EXTERNAL))
    parser.add_argument("--top-windows-csv", default="")
    parser.add_argument("--top-genes-csv", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    return parser.parse_args()


def write_markdown(summary: pd.DataFrame, warnings: list[str], path: Path) -> None:
    recurrent = []
    if "top_genes" in summary:
        genes = []
        for value in summary["top_genes"].dropna().astype(str):
            if value != "MISSING":
                genes.extend([x.strip() for x in value.split(";") if x.strip()])
        if genes:
            recurrent = pd.Series(genes).value_counts().head(10).index.tolist()
    lines = [
        "# LGD2+ CNV Interpretation Summary",
        "",
        "This summary reads lightweight external CNV interpretation outputs if present. It does not copy raw CNV matrices, checkpoints, SHAP arrays, or large figures into Git.",
        "",
        "## Selected cases",
        "",
        markdown_table(
            summary,
            [
                "case_id",
                "case_category",
                "cnv_id",
                "cnv_probability",
                "fusion_probability",
                "cnv_prediction_correct",
                "fusion_prediction_correct",
                "top_cnv_windows",
                "top_genes",
                "warnings",
            ],
        ),
        "",
        "## Recurrent regions / genes",
        "",
    ]
    if recurrent:
        lines.extend(f"- {gene}" for gene in recurrent)
    else:
        lines.append("- Not available yet; external top-window/top-gene outputs are missing.")
    lines.extend(
        [
            "",
            "## CNV-only versus fusion-supported cases",
            "",
            "- Probability-level CNV/fusion correctness is included in the table.",
            "- Region-level comparison requires regenerated external top-window/top-gene outputs.",
            "",
            "## Limitations",
            "",
            "- Missing rows mean the external CNV interpretation stage has not been run or its outputs were not supplied.",
            "- Gene/window summaries are lightweight derivatives only; raw CNV matrices and model artefacts remain external.",
            "",
            "## Warnings",
            "",
        ]
    )
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    case_warnings = summary.loc[summary["warnings"].astype(str).ne(""), ["case_id", "warnings"]]
    if not case_warnings.empty:
        for _, row in case_warnings.iterrows():
            lines.append(f"- {row['case_id']}: {row['warnings']}")
    if not warnings and case_warnings.empty:
        lines.append("- None.")
    path.write_text("\n".join(lines) + "\n")


def write_warnings(warnings: list[str], summary: pd.DataFrame, path: Path) -> None:
    lines = ["# LGD2+ CNV Interpretation Warnings", "", "| scope | warning |", "|---|---|"]
    if warnings:
        for warning in warnings:
            lines.append(f"| global | {warning} |")
    for _, row in summary.iterrows():
        if str(row["warnings"]):
            lines.append(f"| {row['case_id']} | {row['warnings']} |")
    if len(lines) == 3:
        lines.append("| none | No warnings. |")
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = pd.read_csv(args.cases)
    summary, warnings = summarize_cnv_interpretation(
        cases=cases,
        output_dir=Path(args.external_output_dir),
        top_windows_csv=Path(args.top_windows_csv) if args.top_windows_csv else None,
        top_genes_csv=Path(args.top_genes_csv) if args.top_genes_csv else None,
    )
    summary.to_csv(out_dir / "lgd2_cnv_interpretation_summary.csv", index=False)
    write_markdown(summary, warnings, out_dir / "lgd2_cnv_interpretation_summary.md")
    write_warnings(warnings, summary, out_dir / "lgd2_cnv_interpretation_warnings.md")
    print(f"Wrote {len(summary)} CNV interpretation summary rows to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


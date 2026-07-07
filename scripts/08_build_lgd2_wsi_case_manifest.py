#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from barrett.evaluation.histology_interpretation import (  # noqa: E402
    EXTERNAL_HISTOLOGY_ROOT,
    build_wsi_case_manifest,
)


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals = [str(row.get(c, "")).replace("\n", " ").replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _write_markdown(df: pd.DataFrame, warnings: list[str], out_path: Path) -> None:
    lines = [
        "# LGD2+ WSI Case Manifest",
        "",
        "Lightweight manifest for the 8 selected LGD2+ thesis interpretation cases. "
        "It references external WSI feature/checkpoint locations but does not copy slides, tiles, features, or checkpoints into Git.",
        "",
        f"- Cases: {len(df)}",
        f"- Early-prediction-only cases: {int(df['is_early_prediction_only'].sum()) if 'is_early_prediction_only' in df else 'NA'}",
        f"- At-event cases: {int(df['is_at_event'].sum()) if 'is_at_event' in df else 'NA'}",
        f"- Cases with feature refs: {int(df['feature_path_ref'].astype(str).ne('').sum()) if 'feature_path_ref' in df else 'NA'}",
        f"- Cases with warnings: {int(df['warnings'].astype(str).ne('').sum()) if 'warnings' in df else 'NA'}",
        "",
        "## Case Table",
        "",
    ]
    keep = [
        "case_id",
        "case_category",
        "patient_id",
        "slide_basename",
        "feature_model",
        "fold",
        "image_model",
        "fusion_model",
        "is_early_prediction_only",
        "warnings",
    ]
    lines.append(_markdown_table(df[[c for c in keep if c in df.columns]]))
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- None at manifest-build level.")
    case_warnings = df[df["warnings"].astype(str).ne("")]
    if not case_warnings.empty:
        lines.append("")
        lines.append("## Case-Level Warnings")
        lines.append("")
        for _, r in case_warnings.iterrows():
            lines.append(f"- `{r['case_id']}`: {r['warnings']}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_warnings(warnings: list[str], df: pd.DataFrame, out_path: Path) -> None:
    lines = ["# LGD2+ WSI Case Manifest Warnings", ""]
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- No manifest-build warnings.")
    case_warnings = df[df["warnings"].astype(str).ne("")]
    if not case_warnings.empty:
        lines.extend(["", "## Case-Level Warnings", ""])
        for _, r in case_warnings.iterrows():
            lines.append(f"- `{r['case_id']}`: {r['warnings']}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build lightweight LGD2+ WSI interpretation case manifest.")
    p.add_argument("--case-csv", default="reports/thesis_ch1/lgd2_final_interpretation_case_subset.csv")
    p.add_argument("--final-results-manifest", default="docs/final_results_manifest.csv")
    p.add_argument("--external-root", default="..", help="External training/result root containing data/ and analysis/.")
    p.add_argument("--feature-index-csv", default="", help="Optional external feature index CSV.")
    p.add_argument("--external-output-root", default=EXTERNAL_HISTOLOGY_ROOT)
    p.add_argument("--output-dir", default="reports/thesis_ch1")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = pd.read_csv(args.case_csv)
    manifest = pd.read_csv(args.final_results_manifest)
    df, warnings = build_wsi_case_manifest(
        cases=cases,
        final_manifest=manifest,
        external_root=args.external_root,
        feature_index_csv=args.feature_index_csv,
        external_output_root=args.external_output_root,
    )
    csv_path = out_dir / "lgd2_wsi_case_manifest.csv"
    md_path = out_dir / "lgd2_wsi_case_manifest.md"
    warn_path = out_dir / "lgd2_wsi_case_manifest_warnings.md"
    df.to_csv(csv_path, index=False)
    _write_markdown(df, warnings, md_path)
    _write_warnings(warnings, df, warn_path)
    print(f"Wrote {len(df)} WSI case rows to {out_dir}")


if __name__ == "__main__":
    main()

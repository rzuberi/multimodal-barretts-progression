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
    summarize_histology_outputs,
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
        "# LGD2+ Histology Interpretation Summary",
        "",
        "This summary reads lightweight external histology interpretation outputs when present. "
        "It does not copy WSI files, tile images, feature tensors, checkpoints, or large attention maps into Git.",
        "",
        f"- Cases: {len(df)}",
        f"- Cases with top-patch refs: {int(df['top_patch_refs'].astype(str).ne('MISSING').sum()) if 'top_patch_refs' in df else 'NA'}",
        f"- Cases with attention summaries: {int(df['attention_summary'].astype(str).ne('MISSING').sum()) if 'attention_summary' in df else 'NA'}",
        f"- Cases with warnings: {int(df['warnings'].astype(str).ne('').sum()) if 'warnings' in df else 'NA'}",
        "",
        "## Selected Cases",
        "",
    ]
    keep = [
        "case_id",
        "case_category",
        "patient_id",
        "slide_id",
        "image_probability",
        "fusion_probability",
        "top_patches_generated",
        "attention_tile_scores_generated",
        "heatmaps_overlays_generated",
        "top_patch_refs",
        "attention_summary",
        "warnings",
    ]
    lines.append(_markdown_table(df[[c for c in keep if c in df.columns]]))
    lines.extend(["", "## Interpretation Sentences", ""])
    for _, r in df.iterrows():
        lines.append(f"- {r['histology_interpretation_sentence']}")
    lines.extend(["", "## Global Warnings", ""])
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- None.")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_warnings(df: pd.DataFrame, warnings: list[str], out_path: Path) -> None:
    lines = ["# LGD2+ Histology Interpretation Warnings", ""]
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- No global warnings.")
    case_warnings = df[df["warnings"].astype(str).ne("")]
    if not case_warnings.empty:
        lines.extend(["", "## Case-Level Warnings", ""])
        for _, r in case_warnings.iterrows():
            lines.append(f"- `{r['case_id']}`: {r['warnings']}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarise LGD2+ histology interpretation outputs if present.")
    p.add_argument("--wsi-case-manifest", default="reports/thesis_ch1/lgd2_wsi_case_manifest.csv")
    p.add_argument("--external-output-dir", default=EXTERNAL_HISTOLOGY_ROOT)
    p.add_argument("--top-patch-csv", default="")
    p.add_argument("--attention-csv", default="")
    p.add_argument("--output-dir", default="reports/thesis_ch1")
    p.add_argument("--output-prefix", default="lgd2_histology_interpretation")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(args.wsi_case_manifest)
    df, warnings = summarize_histology_outputs(
        manifest=manifest,
        output_dir=args.external_output_dir,
        top_patch_csv=args.top_patch_csv or None,
        attention_csv=args.attention_csv or None,
    )
    prefix = str(args.output_prefix).rstrip("_")
    csv_path = out_dir / f"{prefix}_summary.csv"
    md_path = out_dir / f"{prefix}_summary.md"
    warn_path = out_dir / f"{prefix}_warnings.md"
    df.to_csv(csv_path, index=False)
    _write_markdown(df, warnings, md_path)
    _write_warnings(df, warnings, warn_path)
    print(f"Wrote {len(df)} histology interpretation summary rows to {out_dir}")


if __name__ == "__main__":
    main()

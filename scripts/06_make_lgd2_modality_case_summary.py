#!/usr/bin/env python
"""Summarize probability-only modality dependence for selected LGD2+ cases."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.interpretation import summarize_modality_cases
from barrett.evaluation.tables import markdown_table

DEFAULT_INPUT = Path("reports/thesis_ch1/lgd2_final_interpretation_case_subset.csv")
DEFAULT_OUT_DIR = Path("reports/thesis_ch1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = pd.read_csv(args.input)
    summary = summarize_modality_cases(cases)
    csv_path = out_dir / "lgd2_modality_case_summary.csv"
    md_path = out_dir / "lgd2_modality_case_summary.md"
    summary.to_csv(csv_path, index=False)
    columns = [
        "case_id",
        "category",
        "cnv_prob",
        "image_prob",
        "fusion_prob",
        "fusion_minus_cnv",
        "fusion_minus_image",
        "abs_cnv_image_disagreement",
        "dominant_modality_hint",
        "fusion_helped",
        "fusion_hurt",
        "all_modalities_agree",
        "case_interpretation_sentence",
    ]
    md_path.write_text(
        "# LGD2+ Modality Case Summary\n\n"
        "Probability-only interpretation for the final selected thesis-figure subset. "
        "No heavy data, WSI tiles, checkpoints, or external outputs are read.\n\n"
        + markdown_table(summary, columns)
        + "\n"
    )
    print(f"Wrote {len(summary)} modality summary rows to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


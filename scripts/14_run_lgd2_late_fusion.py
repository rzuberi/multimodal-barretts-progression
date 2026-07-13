#!/usr/bin/env python
"""Reproduce LGD2+ late-fusion OOF predictions from external CNV + image files.

Reads saved out-of-fold predictions (campaign schema) and writes standardized
late-fusion predictions to an EXTERNAL output directory. Does not train models.

Example:
  python scripts/14_run_lgd2_late_fusion.py \
    --cnv-glob "$ROOT/.../cnv/.../predictions_*_fold*.csv" \
    --image-glob "$ROOT/.../uni2/.../predictions_all_samples_abmil_*_fold*.csv" \
    --output-dir "$ROOT/data/lgd2_late_fusion_20260713/uni2"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.evaluation.late_fusion import run_late_fusion  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cnv-glob", action="append", required=True, help="CNV OOF prediction glob(s). Repeatable.")
    p.add_argument("--image-glob", action="append", required=True, help="Image OOF prediction glob(s). Repeatable.")
    p.add_argument("--output-dir", required=True, help="External output dir (must be outside the clean repo).")
    p.add_argument("--seed", type=int, default=20260304)
    args = p.parse_args()
    dest = run_late_fusion(args.cnv_glob, args.image_glob, Path(args.output_dir), seed=args.seed)
    print(f"Wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Emit an image_mil-format training manifest from the frozen cohort + splits (Phase 8 input).

Bridges the frozen strict-pre-event matched cohort and immutable outer splits to the
external training stack (image_mil.data.load_manifest / get_cv_split), which expects
columns: sample_id, patient_id, condition, y_progressor, fold_id_rep<NN>. Written
EXTERNALLY next to the cohort release. No heavy data enters Git.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.labels.endpoints import LGD2_ENDPOINT  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release-dir", required=True)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--output-name", default="training_manifest_v2.csv")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    rel = Path(args.release_dir).resolve()
    manifest = pd.read_csv(rel / "matched_manifest.csv")
    splits = pd.read_csv(rel / "patient_splits.csv")

    fold_col = f"fold_id_rep{args.rep:02d}"
    m = manifest.merge(splits[["patient_id", "outer_fold"]], on="patient_id", how="left", validate="many_to_one")
    if m["outer_fold"].isna().any():
        raise SystemExit(f"{int(m['outer_fold'].isna().sum())} rows without a fold; aborting")
    out = pd.DataFrame({
        "sample_id": m["canonical_row_key"].astype(str),
        "canonical_row_key": m["canonical_row_key"].astype(str),
        "patient_id": m["patient_id"].astype(str),
        "biopsy_id": m["biopsy_id"].astype(str),
        "slide_id": m["slide_id"].astype(str),
        "slide_ref": m["slide_ref"].astype(str),
        "cnv_id": m["cnv_id"].astype(str),
        "source_cnv_feature_id": m["cnv_id"].astype(str),
        "strict_pre_event_eligible": m["strict_pre_event_eligible"].astype(bool),
        "DaysToNextBiopsy": pd.to_numeric(m["DaysToNextBiopsy"], errors="coerce"),
        "condition": "all_samples",
        "y_progressor": pd.to_numeric(m[LGD2_ENDPOINT], errors="coerce").astype("Int64"),
        fold_col: pd.to_numeric(m["outer_fold"], errors="coerce").astype("Int64"),
    })
    if out["y_progressor"].isna().any():
        raise SystemExit("null y_progressor in eligible rows; aborting")
    if out["sample_id"].duplicated().any():
        raise SystemExit("duplicate canonical sample_id in training manifest; aborting")
    dest = rel / args.output_name
    if dest.exists() and not args.overwrite:
        raise SystemExit(f"{dest} exists; pass --overwrite")
    tmp = dest.with_suffix(".tmp"); out.to_csv(tmp, index=False); tmp.replace(dest)
    (rel / (Path(args.output_name).stem + "_meta.json")).write_text(json.dumps({
        "rows": int(len(out)), "patients": int(out["patient_id"].nunique()),
        "positives": int((out["y_progressor"] == 1).sum()),
        "fold_col": fold_col, "folds": sorted(int(x) for x in out[fold_col].dropna().unique()),
    }, indent=2))
    print(f"training_manifest rows={len(out)} patients={out['patient_id'].nunique()} "
          f"positives={int((out['y_progressor']==1).sum())} fold_col={fold_col}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

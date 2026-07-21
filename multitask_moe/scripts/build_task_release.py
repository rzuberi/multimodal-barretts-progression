#!/usr/bin/env python
"""Build a per-task training release by RE-LABELLING the frozen pre-event cohort.

All three tasks share the frozen 707-row / 150-patient matched cohort and its
already-built CNV / UNI2 / GigaPath feature views (identical rows -> clean paired
comparison, no re-embedding). This script writes, into an external per-task
release dir:
  * training_manifest_v2.csv  (script-21 schema, y_progressor = the task label)
  * patient_splits.csv        (patient-disjoint 5-fold, stratified on the task label)
  * symlinks to the frozen feature_views/ and pre_event_cohort.csv

`next_biopsy_progression` simply symlinks the frozen release verbatim (its
manifest/splits already encode that endpoint and produced the Chapter-1 results).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.splits import make_patient_folds  # noqa: E402

FROZEN = Path("/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/"
              "analysis/chapter1_lgd2_final_pre_event_20260713_final")


def _symlink(src: Path, dst: Path) -> None:
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    dst.symlink_to(src)


def _reuse_frozen(out_release: Path) -> None:
    out_release.mkdir(parents=True, exist_ok=True)
    for name in ["training_manifest_v2.csv", "patient_splits.csv", "pre_event_cohort.csv",
                 "matched_manifest.csv", "feature_views"]:
        _symlink(FROZEN / name, out_release / name)
    print(f"next_biopsy_progression: symlinked frozen release -> {out_release}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--label-column", required=True)
    ap.add_argument("--out-release", required=True)
    ap.add_argument("--seed", type=int, default=20260721)
    ap.add_argument("--reuse-frozen", action="store_true",
                    help="symlink the frozen release verbatim (next_biopsy_progression)")
    ap.add_argument("--censor-underfollowed", action="store_true",
                    help="at_risk: drop non-progressor negatives with <3y follow-up")
    args = ap.parse_args()

    out_release = Path(args.out_release).resolve()
    if REPO_ROOT == out_release or REPO_ROOT in out_release.parents:
        raise SystemExit("release must be external to Git")
    if args.reuse_frozen:
        _reuse_frozen(out_release)
        return 0

    mm = pd.read_csv(FROZEN / "matched_manifest.csv", low_memory=False, dtype={"canonical_row_key": str})
    co = pd.read_csv(FROZEN / "pre_event_cohort.csv", low_memory=False)
    co["SampleID"] = co["SampleID"].astype(str)
    label_by_sample = co.set_index("SampleID")[args.label_column]
    followup = co.set_index("SampleID")["MonthsBeforeLastBiopsy"] if "MonthsBeforeLastBiopsy" in co else None
    progressor = co.set_index("SampleID")["Progressor_label"] if "Progressor_label" in co else None

    mm["canonical_row_key"] = mm["canonical_row_key"].astype(str)
    mm["y"] = pd.to_numeric(mm["canonical_row_key"].map(label_by_sample), errors="coerce")

    n_total = len(mm)
    audit = {"task": args.task, "label_column": args.label_column, "n_matched_rows": n_total}

    eligible = mm["y"].notna()
    n_nan = int((~eligible).sum())
    # Under-followed-negative exposure (reported; dropped only with --censor-underfollowed).
    underfollowed = pd.Series(False, index=mm.index)
    if followup is not None and progressor is not None:
        fu = pd.to_numeric(mm["canonical_row_key"].map(followup), errors="coerce")
        prog = pd.to_numeric(mm["canonical_row_key"].map(progressor), errors="coerce")
        underfollowed = (mm["y"] == 0) & (prog == 0) & (fu < 36)
    audit["n_label_nan_excluded"] = n_nan
    audit["n_underfollowed_negatives"] = int((underfollowed & eligible).sum())
    audit["censor_underfollowed"] = bool(args.censor_underfollowed)
    if args.censor_underfollowed:
        eligible = eligible & ~underfollowed

    sub = mm[eligible].copy()
    sub["y_progressor"] = sub["y"].astype(int)

    # Patient-disjoint 5-fold, stratified on the task label (patient = max over rows).
    labels = sub.groupby("patient_id")["y_progressor"].max().rename("patient_label").reset_index()
    folds = make_patient_folds(labels, n_folds=5, seed=args.seed)
    sub = sub.merge(folds[["patient_id", "outer_fold"]], on="patient_id", how="left", validate="many_to_one")
    if sub["outer_fold"].isna().any():
        raise SystemExit("rows without a fold after split")

    manifest = pd.DataFrame({
        "sample_id": sub["canonical_row_key"].astype(str),
        "canonical_row_key": sub["canonical_row_key"].astype(str),
        "patient_id": sub["patient_id"].astype(str),
        "biopsy_id": sub["biopsy_id"].astype(str),
        "slide_id": sub["slide_id"].astype(str),
        "slide_ref": sub["slide_ref"].astype(str),
        "cnv_id": sub["cnv_id"].astype(str),
        "source_cnv_feature_id": sub["cnv_id"].astype(str),
        "strict_pre_event_eligible": sub["strict_pre_event_eligible"].astype(bool),
        "DaysToNextBiopsy": pd.to_numeric(sub["DaysToNextBiopsy"], errors="coerce"),
        "condition": "all_samples",
        "y_progressor": sub["y_progressor"].astype("Int64"),
        "fold_id_rep01": pd.to_numeric(sub["outer_fold"], errors="coerce").astype("Int64"),
    })

    out_release.mkdir(parents=True, exist_ok=True)
    _symlink(FROZEN / "feature_views", out_release / "feature_views")
    _symlink(FROZEN / "pre_event_cohort.csv", out_release / "pre_event_cohort.csv")
    _symlink(FROZEN / "matched_manifest.csv", out_release / "matched_manifest.csv")
    manifest.to_csv(out_release / "training_manifest_v2.csv", index=False)
    folds.to_csv(out_release / "patient_splits.csv", index=False)

    audit.update({
        "n_rows": int(len(manifest)), "n_patients": int(manifest["patient_id"].nunique()),
        "n_positive_rows": int((manifest["y_progressor"] == 1).sum()),
        "n_positive_patients": int((folds["patient_label"] == 1).sum()),
        "fold_sizes": {int(f): int((manifest["fold_id_rep01"] == f).sum()) for f in sorted(manifest["fold_id_rep01"].dropna().unique())},
        "fold_positive_patients": {int(f): int(((folds["outer_fold"] == f) & (folds["patient_label"] == 1)).sum())
                                   for f in sorted(folds["outer_fold"].unique())},
    })
    (out_release / "task_cohort_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

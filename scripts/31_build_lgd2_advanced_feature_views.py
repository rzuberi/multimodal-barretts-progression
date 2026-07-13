#!/usr/bin/env python
"""Build external-only temporal manifest and canonical foundation-model indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.feature_views import canonical_uni2_index  # noqa: E402
from barrett.training.artifacts import reject_repo_output  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--source-root", required=True)
    args = parser.parse_args()
    release = Path(args.release_root).resolve()
    source = Path(args.source_root).resolve()
    reject_repo_output(release, REPO_ROOT)
    matched = pd.read_csv(release / "matched_manifest.csv", dtype={"canonical_row_key": str})
    for foundation in ("gigapath", "virchow2"):
        source_index = pd.read_csv(
            source / foundation / "runs/image/all_samples/core_gpu/index/virchow2_index.csv",
            dtype={"sample_id": str},
        )
        canonical = canonical_uni2_index(
            matched,
            source_index,
            remap_rules=[{"from": "/scratchc/", "to": "/mnt/scratche/slow/"}],
        )
        target = release / "feature_views" / foundation / f"{foundation}_index.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        canonical.to_csv(target, index=False)

    base = pd.read_csv(release / "training_manifest_v2.csv", dtype={"sample_id": str})
    cohort = pd.read_csv(release / "pre_event_cohort.csv", dtype={"SampleID": str})
    temporal_columns = [
        "SampleID", "Date", "DaysSincePreviousBiopsy", "CurrentGradeInt", "LGDStreakSoFar",
        "DaysFromCurrentToEvent",
    ]
    temporal = cohort[temporal_columns].drop_duplicates("SampleID")
    advanced = base.merge(temporal, left_on="sample_id", right_on="SampleID", how="left", validate="one_to_one")
    advanced = advanced.drop(columns="SampleID")
    if len(advanced) != len(base) or set(advanced["sample_id"]) != set(base["sample_id"]):
        raise SystemExit("advanced manifest changed the frozen row set")
    if advanced["Date"].isna().any():
        raise SystemExit("advanced manifest has missing collection dates")
    manifest_path = release / "training_manifest_advanced_v1.csv"
    advanced.to_csv(manifest_path, index=False)
    payload = {
        "status": "PASS", "rows": len(advanced), "patients": advanced["patient_id"].nunique(),
        "folds": sorted(advanced["fold_id_rep01"].unique().tolist()),
        "base_manifest_sha256": sha256(release / "training_manifest_v2.csv"),
        "advanced_manifest_sha256": sha256(manifest_path),
        "future_timing_as_input": False,
        "foundation_indexes": {
            name: str(release / "feature_views" / name / f"{name}_index.csv")
            for name in ("gigapath", "uni2", "virchow2")
        },
    }
    (release / "advanced_feature_view_metadata.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

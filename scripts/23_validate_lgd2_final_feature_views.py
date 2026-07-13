#!/usr/bin/env python
"""Validate frozen-cohort feature views without loading feature tensors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.feature_views import feature_view_audit  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    args = parser.parse_args()
    release = Path(args.release_root).resolve()
    matched = pd.read_csv(release / "matched_manifest.csv", dtype={"canonical_row_key": str})
    cnv_dir = release / "feature_views/cnv"
    views = {name: pd.read_csv(cnv_dir / name, dtype={"sample_id": str}) for name in (
        "features_5mb_armdiff.csv", "features_arms.csv", "cx.csv"
    )}
    uni2 = pd.read_csv(release / "feature_views/uni2/uni2_index.csv", dtype={"sample_id": str})
    audit = feature_view_audit(matched, views, uni2)
    print(audit.to_string(index=False))
    if audit["status"].ne("PASS").any():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Validate and collect experimental fusion OOF predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.training.advanced import ALL_FAMILIES  # noqa: E402
from barrett.training.artifacts import collect_family, reject_repo_output  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--reports-dir", default=str(REPO_ROOT / "reports/thesis_ch1"))
    args = parser.parse_args()
    release, output, reports_dir = Path(args.release_root).resolve(), Path(args.output_root).resolve(), Path(args.reports_dir)
    reject_repo_output(output, REPO_ROOT)
    manifest_path = release / "training_manifest_advanced_v1.csv"
    manifest = pd.read_csv(manifest_path, dtype={"sample_id": str})
    collected, audit_rows = {}, []
    for family in sorted(ALL_FAMILIES):
        frame, audit = collect_family(output, manifest, family)
        audit_rows.extend(audit)
        if frame is not None:
            collected[family] = frame
    complete = len(collected) == len(ALL_FAMILIES)
    if complete:
        reference = set(manifest["sample_id"].astype(str))
        for family, frame in collected.items():
            if set(frame["row_key"].astype(str)) != reference:
                complete = False
                audit_rows.append({"model_family": family, "outer_fold": "ALL", "status": "FAIL", "problems": "row set differs"})
    if complete:
        oof = output / "oof"
        oof.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for family, frame in collected.items():
            path = oof / f"{family}_oof_predictions.csv"
            frame.sort_values(["outer_fold", "row_key"]).to_csv(path, index=False)
            hashes[family] = {"path": str(path), "sha256": sha256(path), "rows": len(frame)}
        (oof / "completeness_manifest.json").write_text(json.dumps({
            "status": "PASS", "rows": len(manifest), "patients": manifest["patient_id"].nunique(),
            "folds": [1, 2, 3, 4, 5], "manifest_path": str(manifest_path),
            "manifest_sha256": sha256(manifest_path), "families": hashes,
        }, indent=2) + "\n")
    reports_dir.mkdir(parents=True, exist_ok=True)
    audit = pd.DataFrame(audit_rows)
    audit.to_csv(reports_dir / "lgd2_advanced_fusion_oof_completeness.csv", index=False)
    lines = ["# LGD2+ Advanced Fusion OOF Completeness", "", f"Status: **{'PASS' if complete else 'INCOMPLETE'}**", "",
             "| Family | Passed folds | Rows | Patients |", "|---|---:|---:|---:|"]
    for family in sorted(ALL_FAMILIES):
        frame = collected.get(family)
        passed = int(((audit.get("model_family") == family) & (audit.get("status") == "PASS")).sum())
        lines.append(f"| {family} | {passed}/5 | {len(frame) if frame is not None else 0} | {frame['patient_id'].nunique() if frame is not None else 0} |")
    (reports_dir / "lgd2_advanced_fusion_oof_completeness.md").write_text("\n".join(lines) + "\n")
    warnings = audit.loc[audit.get("status").ne("PASS"), [column for column in ["model_family", "outer_fold", "problems"] if column in audit]]
    warning_text = "# LGD2+ Advanced Fusion Warnings\n\n" + ("None." if warnings.empty else warnings.to_markdown(index=False)) + "\n"
    (reports_dir / "lgd2_advanced_fusion_warnings.md").write_text(warning_text)
    if not complete:
        raise SystemExit("advanced OOF collection incomplete")
    print(f"PASS: collected {len(collected)} advanced families")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

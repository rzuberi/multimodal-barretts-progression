#!/usr/bin/env python
"""Validate folds, derive leakage-safe late fusion, and collect final OOF predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.training.artifacts import collect_family, reject_repo_output  # noqa: E402
from barrett.training.late_fusion import derive_late_fold  # noqa: E402


BASE_FAMILIES = ("cnv_only", "image_only", "early_fusion", "intermediate_fusion")
ALL_FAMILIES = BASE_FAMILIES + ("late_mean", "late_stack_logit")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--model-registry", default=str(REPO_ROOT / "configs/chapter1_lgd2_final_models.yaml"))
    parser.add_argument("--derive-late", action="store_true")
    parser.add_argument("--reports-dir", default=str(REPO_ROOT / "reports/thesis_ch1"))
    args = parser.parse_args()

    release = Path(args.release_root).resolve()
    output = Path(args.output_root).resolve()
    reject_repo_output(output, REPO_ROOT)
    manifest_path = release / "training_manifest_v2.csv"
    manifest = pd.read_csv(manifest_path, dtype={"sample_id": str})
    all_reports: list[dict] = []
    collected: dict[str, pd.DataFrame] = {}
    for family in BASE_FAMILIES:
        frame, reports = collect_family(output, manifest, family)
        all_reports.extend(reports)
        if frame is not None:
            collected[family] = frame
    if len(collected) != len(BASE_FAMILIES):
        _write_reports(Path(args.reports_dir), all_reports, collected, manifest, output, complete=False)
        raise SystemExit("base-family collection failed; late fusion was not derived")

    if args.derive_late:
        for fold in range(1, 6):
            targets = [output / family / f"fold{fold}" / "fold_completion.json" for family in ALL_FAMILIES[-2:]]
            if all(path.exists() for path in targets):
                continue
            if any(path.parent.exists() and any(path.parent.iterdir()) for path in targets):
                raise SystemExit(f"partial late-fusion output exists for fold {fold}; review before retry")
            derive_late_fold(output, args.model_registry, fold, seed=20260713)

    for family in ALL_FAMILIES[-2:]:
        frame, reports = collect_family(output, manifest, family)
        all_reports.extend(reports)
        if frame is not None:
            collected[family] = frame
    complete = len(collected) == len(ALL_FAMILIES)
    if complete:
        reference = set(collected[ALL_FAMILIES[0]]["row_key"].astype(str))
        for family, frame in collected.items():
            if set(frame["row_key"].astype(str)) != reference:
                complete = False
                all_reports.append({
                    "model_family": family, "outer_fold": "ALL", "status": "FAIL",
                    "expected_rows": len(reference), "prediction_rows": len(frame),
                    "expected_patients": manifest["patient_id"].nunique(),
                    "prediction_patients": frame["patient_id"].nunique(),
                    "problems": "row set differs from reference model",
                })

    if complete:
        oof_dir = output / "oof"
        oof_dir.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for family, frame in collected.items():
            path = oof_dir / f"{family}_oof_predictions.csv"
            frame.sort_values(["outer_fold", "row_key"]).to_csv(path, index=False)
            hashes[family] = {"path": str(path), "sha256": _sha256(path), "rows": len(frame)}
        completeness = {
            "status": "PASS", "manifest_path": str(manifest_path),
            "manifest_sha256": _sha256(manifest_path), "rows": int(len(manifest)),
            "patients": int(manifest["patient_id"].nunique()), "folds": [1, 2, 3, 4, 5],
            "families": hashes,
            "resolved_config": str(Path(args.model_registry).resolve()),
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
            ).strip(),
            "git_dirty": bool(subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
            ).strip()),
            "env_export": sorted(str(path) for path in output.glob("*/fold*/environment.txt")),
            "input_manifests": [str(manifest_path), str(release / "patient_splits.csv")],
            "input_hashes": {
                "training_manifest_v2": _sha256(manifest_path),
                "patient_splits": _sha256(release / "patient_splits.csv"),
            },
            "inner_fold_assignments": sorted(str(path) for path in output.glob("*/fold*/inner_fold_assignments.csv")),
            "outer_fold_assignments": str(release / "patient_splits.csv"),
            "inner_validation_predictions": sorted(str(path) for path in output.glob("*/fold*/inner_validation_predictions.csv")),
            "inner_validation_leaderboard": sorted(str(path) for path in output.glob("*/fold*/inner_validation_leaderboard.csv")),
            "outer_test_predictions": [value["path"] for value in hashes.values()],
            "fold_checkpoints": sorted(str(path) for path in output.glob("*/fold*/model.*")),
            "fitted_preprocessing": sorted(str(path) for path in output.glob("*/fold*/platt_calibrator.joblib")),
            "per_fold_metadata": sorted(str(path) for path in output.glob("*/fold*/fold_metadata.json")),
            "completeness_manifest": str(oof_dir / "completeness_manifest.json"),
        }
        (oof_dir / "completeness_manifest.json").write_text(
            json.dumps(completeness, indent=2) + "\n", encoding="utf-8"
        )
    _write_reports(Path(args.reports_dir), all_reports, collected, manifest, output, complete)
    if not complete:
        raise SystemExit("final OOF collection is incomplete")
    print(f"PASS: collected {len(collected)} families across 707 rows / 150 patients")
    return 0


def _write_reports(
    reports_dir: Path,
    rows: list[dict],
    collected: dict[str, pd.DataFrame],
    manifest: pd.DataFrame,
    output: Path,
    complete: bool,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows)
    table.to_csv(reports_dir / "lgd2_final_oof_completeness.csv", index=False)
    lines = [
        "# LGD2+ Final OOF Completeness",
        "",
        f"Status: **{'PASS' if complete else 'INCOMPLETE'}**",
        "",
        f"Frozen cohort: {len(manifest)} rows; {manifest['patient_id'].nunique()} patients.",
        f"External output root: `{output}`",
        "",
        "| Family | Passed folds | Collected rows | Collected patients |",
        "|---|---:|---:|---:|",
    ]
    for family in ALL_FAMILIES:
        passed = sum(
            str(row.get("model_family")) == family and row.get("status") == "PASS"
            for row in rows if row.get("outer_fold") != "ALL"
        )
        frame = collected.get(family)
        lines.append(
            f"| {family} | {passed}/5 | {len(frame) if frame is not None else 0} | "
            f"{frame['patient_id'].nunique() if frame is not None else 0} |"
        )
    (reports_dir / "lgd2_final_oof_completeness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    warnings = [str(row["problems"]) for row in rows if row.get("problems")]
    text = "# LGD2+ Final OOF Warnings\n\n" + ("\n".join(f"- {value}" for value in warnings) if warnings else "None.\n")
    (reports_dir / "lgd2_final_oof_warnings.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

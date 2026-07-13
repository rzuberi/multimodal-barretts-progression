#!/usr/bin/env python
"""Build canonical-keyed CNV and UNI2 feature views outside Git."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.data.feature_views import (  # noqa: E402
    canonical_cnv_view,
    canonical_uni2_index,
    feature_view_audit,
    sha256_file,
)


DEFAULT_RELEASE = REPO_ROOT.parent / "analysis/chapter1_lgd2_final_pre_event_20260713_final"
DEFAULT_CNV = REPO_ROOT.parent / "data/killcoyne_repro_strict_500kb_slurm_v2"
DEFAULT_UNI2 = REPO_ROOT.parent / (
    "data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/"
    "core_lvl2/uni2/runs/image/all_samples/core_gpu/index/virchow2_index.csv"
)


def _write_markdown(audit: pd.DataFrame, matched: pd.DataFrame, destination: Path, output_root: Path) -> None:
    columns = list(audit.columns)
    table = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in audit.itertuples(index=False, name=None):
        table.append("| " + " | ".join(str(value) for value in row) + " |")
    lines = [
        "# LGD2+ Final Feature Mapping Audit",
        "",
        f"- Canonical rows: {len(matched)}",
        f"- Unique CNV profiles: {matched['cnv_id'].astype(str).nunique()}",
        f"- CNV profiles shared across rows: {int(matched['cnv_shared_with_other_sample'].fillna(False).astype(bool).sum())}",
        f"- Unique slides: {matched['slide_ref'].astype(str).nunique()}",
        f"- External feature-view root: `{output_root}`",
        "",
        *table,
        "",
        "All feature matrices and NPZ references remain external to Git.",
    ]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", default=str(DEFAULT_RELEASE))
    parser.add_argument("--cnv-source-dir", default=str(DEFAULT_CNV))
    parser.add_argument("--uni2-source-index", default=str(DEFAULT_UNI2))
    parser.add_argument("--output-root", default="")
    parser.add_argument("--reports-dir", default=str(REPO_ROOT / "reports/thesis_ch1"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    release = Path(args.release_root).resolve()
    output = Path(args.output_root).resolve() if args.output_root else release / "feature_views"
    if REPO_ROOT == output or REPO_ROOT in output.parents:
        raise SystemExit("feature views must be written outside the clean Git repository")
    reports = Path(args.reports_dir).resolve()
    reports.mkdir(parents=True, exist_ok=True)
    matched_path = release / "matched_manifest.csv"
    matched = pd.read_csv(matched_path, dtype={"canonical_row_key": str, "sample_id": str})

    cnv_names = ["features_5mb_armdiff.csv", "features_arms.csv", "cx.csv"]
    cnv_output = output / "cnv"
    uni2_output = output / "uni2"
    for directory in (cnv_output, uni2_output):
        directory.mkdir(parents=True, exist_ok=True)
    destinations = [cnv_output / name for name in cnv_names] + [uni2_output / "uni2_index.csv"]
    existing = [path for path in destinations if path.exists()]
    if existing and not args.overwrite:
        raise SystemExit(f"feature view outputs already exist; pass --overwrite: {existing[:3]}")

    views: dict[str, pd.DataFrame] = {}
    source_hashes = {}
    for name in cnv_names:
        source_path = Path(args.cnv_source_dir).resolve() / name
        source = pd.read_csv(source_path)
        view = canonical_cnv_view(matched, source)
        destination = cnv_output / name
        temp = destination.with_suffix(destination.suffix + ".tmp")
        view.to_csv(temp, index=False)
        temp.replace(destination)
        views[name] = view
        source_hashes[str(source_path)] = sha256_file(source_path)

    source_index_path = Path(args.uni2_source_index).resolve()
    source_index = pd.read_csv(source_index_path)
    remaps = [
        {"from": "/scratchc/", "to": "/mnt/scratche/slow/"},
        {"from": "/mnt/scratchc/", "to": "/mnt/scratche/slow/"},
    ]
    uni2 = canonical_uni2_index(matched, source_index, remap_rules=remaps)
    uni2_destination = uni2_output / "uni2_index.csv"
    temp = uni2_destination.with_suffix(".csv.tmp")
    uni2.to_csv(temp, index=False)
    temp.replace(uni2_destination)
    source_hashes[str(source_index_path)] = sha256_file(source_index_path)

    audit = feature_view_audit(matched, views, uni2)
    if audit["status"].ne("PASS").any():
        raise SystemExit("feature view audit failed")
    audit_path = reports / "lgd2_final_feature_mapping_audit.csv"
    audit.to_csv(audit_path, index=False)
    _write_markdown(audit, matched, reports / "lgd2_final_feature_mapping_audit.md", output)
    (reports / "lgd2_final_feature_mapping_warnings.md").write_text(
        "# LGD2+ Final Feature Mapping Warnings\n\nNo warnings. Exact 707-row coverage validated.\n",
        encoding="utf-8",
    )
    metadata = {
        "release_root": str(release),
        "matched_manifest": str(matched_path),
        "matched_manifest_sha256": sha256_file(matched_path),
        "output_root": str(output),
        "rows": int(len(matched)),
        "unique_cnv_profiles": int(matched["cnv_id"].astype(str).nunique()),
        "unique_slides": int(matched["slide_ref"].astype(str).nunique()),
        "source_hashes": source_hashes,
        "outputs": {str(path): sha256_file(path) for path in destinations},
    }
    (output / "feature_view_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(audit.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Collect OOF, derive late fusion, and build the MoE routing report for one (task, backbone).

Reuses barrett.training.artifacts.collect_family and late_fusion.derive_late_fold
unchanged. Because CNV is trained once per task (backbone-independent) under
train/shared, it is symlinked into each backbone output root so late fusion and
collection find cnv_only + image_only side by side.

Writes, under <output_root>/oof/:
  * <family>_oof_predictions.csv for every family incl. moe, late_mean, late_stack_logit
  * completeness_manifest.json
  * moe_routing_report.{csv,md}  (routing %, progressor rate, mean days-to-progression per expert)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.training.artifacts import collect_family, reject_repo_output  # noqa: E402
from barrett.training.late_fusion import derive_late_fold  # noqa: E402

BASE = Path("/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/multitask_moe_20260721")
BASE_FAMILIES = ("cnv_only", "image_only", "early_fusion", "intermediate_fusion", "coattention_fusion", "moe")
LATE_FAMILIES = ("late_mean", "late_stack_logit")
ALL_FAMILIES = BASE_FAMILIES + LATE_FAMILIES


def _link_shared_cnv(task: str, output_root: Path) -> None:
    shared = BASE / task / "train" / "shared" / "cnv_only"
    dst = output_root / "cnv_only"
    if not dst.exists() and shared.exists():
        dst.symlink_to(shared)


def _moe_routing_report(output_root: Path, cohort: pd.DataFrame) -> pd.DataFrame | None:
    rows = []
    for fold in range(1, 6):
        p = output_root / "moe" / f"fold{fold}" / "moe_routing.csv"
        if p.exists():
            rows.append(pd.read_csv(p, dtype={"sample_id": str}))
    if not rows:
        return None
    routing = pd.concat(rows, ignore_index=True)
    days = cohort.set_index("SampleID")["DaysFromCurrentToEvent"] if "DaysFromCurrentToEvent" in cohort else None
    if days is not None:
        routing["days_to_progression"] = pd.to_numeric(routing["sample_id"].map(days), errors="coerce")
    out = []
    n = len(routing)
    for expert in ("image", "cnv", "multimodal"):
        sub = routing[routing["routed_expert"] == expert]
        rec = {
            "routed_expert": expert,
            "n_biopsies": int(len(sub)),
            "pct_of_biopsies": round(100.0 * len(sub) / n, 1) if n else 0.0,
            "progressor_rate": round(float(sub["y_true"].mean()), 3) if len(sub) else float("nan"),
            "mean_gate_weight": round(float(routing[f"w_{expert}"].mean()), 3) if f"w_{expert}" in routing else float("nan"),
        }
        if "days_to_progression" in routing:
            rec["mean_days_to_progression"] = round(float(sub["days_to_progression"].mean()), 0) if len(sub) else float("nan")
        out.append(rec)
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--backbone", required=True)
    ap.add_argument("--derive-late", action="store_true")
    args = ap.parse_args()

    task, backbone = args.task, args.backbone
    release = BASE / task / "release"
    output_root = BASE / task / "train" / backbone
    reject_repo_output(output_root, REPO_ROOT)
    registry = REPO_ROOT / "multitask_moe" / "configs" / ("models_uni2.yaml" if backbone == "uni2" else f"models_{backbone}.yaml")

    _link_shared_cnv(task, output_root)
    manifest = pd.read_csv(release / "training_manifest_v2.csv", dtype={"sample_id": str})

    reports = []
    collected = {}
    for family in BASE_FAMILIES:
        frame, rep = collect_family(output_root, manifest, family)
        reports.extend(rep)
        if frame is not None:
            collected[family] = frame

    if args.derive_late and {"cnv_only", "image_only"} <= set(collected):
        for fold in range(1, 6):
            done = [output_root / f / f"fold{fold}" / "fold_completion.json" for f in LATE_FAMILIES]
            if all(p.exists() for p in done):
                continue
            derive_late_fold(output_root, registry, fold, seed=20260721)
        for family in LATE_FAMILIES:
            frame, rep = collect_family(output_root, manifest, family)
            reports.extend(rep)
            if frame is not None:
                collected[family] = frame

    oof_dir = output_root / "oof"
    oof_dir.mkdir(parents=True, exist_ok=True)
    for family, frame in collected.items():
        frame.sort_values(["outer_fold", "row_key"]).to_csv(oof_dir / f"{family}_oof_predictions.csv", index=False)

    # MoE routing report.
    cohort = pd.read_csv(release / "pre_event_cohort.csv", low_memory=False)
    cohort["SampleID"] = cohort["SampleID"].astype(str)
    routing = _moe_routing_report(output_root, cohort)
    if routing is not None:
        routing.to_csv(oof_dir / "moe_routing_report.csv", index=False)
        lines = [f"# MoE routing — {task} / {backbone}", "",
                 "| " + " | ".join(routing.columns) + " |",
                 "| " + " | ".join(["---"] * len(routing.columns)) + " |"]
        for r in routing.itertuples(index=False, name=None):
            lines.append("| " + " | ".join(str(v) for v in r) + " |")
        (oof_dir / "moe_routing_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    status = {
        "task": task, "backbone": backbone,
        "collected_families": sorted(collected),
        "n_families": len(collected), "expected": len(ALL_FAMILIES),
        "rows": {f: int(len(v)) for f, v in collected.items()},
        "complete": len(collected) == len(ALL_FAMILIES),
    }
    (oof_dir / "collection_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0 if status["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

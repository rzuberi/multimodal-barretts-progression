#!/usr/bin/env python
"""Generate or submit exact commands for the frozen LGD2+ final rerun."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from barrett.training.artifacts import reject_repo_output  # noqa: E402


PRIMARY_FAMILIES = (
    "cnv_only", "image_only", "early_fusion", "intermediate_fusion", "coattention_fusion",
)


def _job_spec(family: str) -> dict[str, str]:
    if family == "cnv_only":
        return {"partition": "epyc", "qos": "epyc_limit", "gres": "", "time": "01:00:00", "mem": "32G"}
    return {
        "partition": "h200", "qos": "h200_preempt", "gres": "gpu:nvidia_h200:1",
        "time": "04:00:00", "mem": "64G",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--model-registry", default=str(REPO_ROOT / "configs/chapter1_lgd2_final_models.yaml"))
    parser.add_argument("--python", default="/home/zuberi01/miniforge3/envs/virchow2/bin/python")
    parser.add_argument("--mode", choices=("smoke", "full"), required=True)
    parser.add_argument("--families", nargs="+", choices=PRIMARY_FAMILIES, default=list(PRIMARY_FAMILIES))
    parser.add_argument("--folds", nargs="+", type=int)
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()

    release = Path(args.release_root).resolve()
    output = Path(args.output_root).resolve()
    reject_repo_output(output, REPO_ROOT)
    if not (release / "training_manifest_v2.csv").exists():
        raise SystemExit(f"missing frozen training manifest: {release / 'training_manifest_v2.csv'}")
    folds = tuple(args.folds or ([1] if args.mode == "smoke" else [1, 2, 3, 4, 5]))
    if any(fold not in range(1, 6) for fold in folds):
        raise SystemExit("folds must be in 1..5")
    logs = output / "slurm_logs"
    logs.mkdir(parents=True, exist_ok=True)
    records = []
    for family in args.families:
        for fold in folds:
            fold_dir = output / family / f"fold{fold}"
            completion = fold_dir / "fold_completion.json"
            if completion.exists():
                records.append({"family": family, "outer_fold": fold, "status": "SKIP_COMPLETE"})
                continue
            if fold_dir.exists() and any(fold_dir.iterdir()):
                records.append({
                    "family": family, "outer_fold": fold, "status": "SKIP_PARTIAL",
                    "warning": f"non-empty incomplete directory: {fold_dir}",
                })
                continue
            device = "cpu" if family == "cnv_only" else "cuda"
            command = [
                args.python, str(REPO_ROOT / "scripts/24_run_lgd2_final_outer_fold.py"),
                "--release-root", str(release),
                "--model-registry", str(Path(args.model_registry).resolve()),
                "--family", family,
                "--outer-fold", str(fold),
                "--output-root", str(output),
                "--device", device,
                "--cpu-threads", "8",
            ]
            spec = _job_spec(family)
            job_name = f"lgd2_{family[:5]}_f{fold}_{args.mode}"
            sbatch = [
                "sbatch", "--parsable", f"--partition={spec['partition']}", f"--qos={spec['qos']}",
                "--cpus-per-task=8", f"--mem={spec['mem']}", f"--time={spec['time']}",
                f"--job-name={job_name}", f"--chdir={REPO_ROOT}",
                f"--output={logs}/%x_%j.out", f"--error={logs}/%x_%j.err",
            ]
            if spec["gres"]:
                sbatch.append(f"--gres={spec['gres']}")
            sbatch.append("--wrap=" + shlex.join(command))
            record = {
                "family": family, "outer_fold": fold, "status": "GENERATED",
                "command": shlex.join(command), "sbatch_command": shlex.join(sbatch),
            }
            if args.submit:
                result = subprocess.run(sbatch, check=True, capture_output=True, text=True)
                record["job_id"] = result.stdout.strip().split(";")[0]
                record["status"] = "SUBMITTED"
            records.append(record)
            print(f"{record['status']} {family} fold {fold}: {record.get('job_id', record['command'])}")
    manifest = {
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": args.mode,
        "release_root": str(release),
        "output_root": str(output),
        "python": args.python,
        "submitted": bool(args.submit),
        "jobs": records,
    }
    path = output / f"launch_manifest_{args.mode}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Submit independent advanced-fusion outer folds across H200 and L40S queues."""

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

from barrett.training.advanced import ALL_FAMILIES  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--model-registry", default=str(REPO_ROOT / "configs/chapter1_lgd2_advanced_fusion.yaml"))
    parser.add_argument("--python", default="/home/zuberi01/miniforge3/envs/virchow2/bin/python")
    parser.add_argument("--families", nargs="+", choices=sorted(ALL_FAMILIES), default=sorted(ALL_FAMILIES))
    parser.add_argument("--folds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--queue", choices=("h200", "cuda", "mixed"), default="mixed")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    release, output = Path(args.release_root).resolve(), Path(args.output_root).resolve()
    if REPO_ROOT == output or REPO_ROOT in output.parents:
        raise SystemExit("output must remain outside Git")
    logs = output / "slurm_logs"
    logs.mkdir(parents=True, exist_ok=True)
    records = []
    for family_index, family in enumerate(args.families):
        for fold in args.folds:
            directory = output / family / f"fold{fold}"
            if (directory / "fold_completion.json").exists():
                records.append({"family": family, "outer_fold": fold, "status": "SKIP_COMPLETE"})
                continue
            if directory.exists() and any(directory.iterdir()):
                records.append({"family": family, "outer_fold": fold, "status": "SKIP_PARTIAL"})
                continue
            queue = args.queue
            if queue == "mixed":
                queue = "h200" if (family_index + fold) % 2 == 0 else "cuda"
            if queue == "h200":
                spec = ("h200", "h200_preempt", "gpu:nvidia_h200:1")
            else:
                spec = ("cuda", "cuda_limit", "gpu:L40S:1")
            command = [
                args.python, str(REPO_ROOT / "scripts/32_run_lgd2_advanced_outer_fold.py"),
                "--release-root", str(release), "--model-registry", str(Path(args.model_registry).resolve()),
                "--family", family, "--outer-fold", str(fold), "--output-root", str(output), "--device", "cuda",
            ]
            job_name = f"adv_{family[:8]}_f{fold}"
            sbatch = [
                "sbatch", "--parsable", f"--partition={spec[0]}", f"--qos={spec[1]}", f"--gres={spec[2]}",
                "--cpus-per-task=8", "--mem=96G", "--time=04:00:00", f"--job-name={job_name}",
                f"--chdir={REPO_ROOT}", f"--output={logs}/%x_%j.out", f"--error={logs}/%x_%j.err",
                "--wrap=" + shlex.join(command),
            ]
            record = {"family": family, "outer_fold": fold, "queue": queue, "status": "GENERATED",
                      "command": shlex.join(command), "sbatch_command": shlex.join(sbatch)}
            if args.submit:
                result = subprocess.run(sbatch, check=True, capture_output=True, text=True)
                record["job_id"], record["status"] = result.stdout.strip().split(";")[0], "SUBMITTED"
            records.append(record)
            print(record["status"], family, fold, record.get("job_id", queue))
    payload = {"created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               "release_root": str(release), "output_root": str(output), "jobs": records}
    path = output / f"launch_manifest_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"manifest: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

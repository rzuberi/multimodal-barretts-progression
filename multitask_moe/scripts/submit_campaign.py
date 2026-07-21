#!/usr/bin/env python
"""Submit the multitask/MoE training campaign as self-deduplicating sbatch jobs.

For every work-unit (task, backbone, family, fold) this submits ONE copy to
EVERY healthy node in the unit's lane partition(s). Each copy runs
``slurm/run_unit.sh``, which claims the unit atomically so it executes exactly
once across all nodes; duplicates self-cancel. Re-running this orchestrator is
safe: units already queued (squeue name match) or finished (.done marker) are
skipped, so it doubles as a resume tool.

Default is a DRY RUN (prints the plan, submits nothing). Pass --submit to submit.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PYTHON = "/home/zuberi01/miniforge3/envs/virchow2/bin/python"
OUTPUT_BASE = Path(
    "/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/multitask_moe_20260721"
)
RUNNER = REPO_ROOT / "multitask_moe" / "scripts" / "train_outer_fold.py"
WRAPPER = REPO_ROOT / "multitask_moe" / "slurm" / "run_unit.sh"

TASKS = ["ever_progress", "at_risk_3y", "next_biopsy_progression"]
BACKBONES = ["uni2", "gigapath"]
NEURAL_FAMILIES = ["image_only", "early_fusion", "intermediate_fusion", "coattention_fusion", "moe"]
CNV_FAMILY = "cnv_only"
FOLDS = [1, 2, 3, 4, 5]
ACCOUNT = "fmlab"

# Lane -> partitions and per-partition sbatch resource spec.
LANES = {
    "gpu": {
        "partitions": ["h200", "cuda"],
        "gres": {"h200": "gpu:nvidia_h200:1", "cuda": "gpu:L40S:1"},
        "qos": {"h200": "h200_preempt"},
        "cpus": 8, "mem": "64G", "time": "06:00:00", "max_nodes": None,
    },
    "cpu": {
        "partitions": ["epyc"],
        "gres": {},
        "qos": {"epyc": "epyc_limit"},
        "cpus": 16, "mem": "32G", "time": "08:00:00", "max_nodes": 8,
    },
}
_BAD_STATE = ("down", "drain", "drng", "fail", "boot", "maint", "unk", "resv", "na")


def registry_for(backbone: str) -> Path:
    name = "models_uni2.yaml" if backbone in ("uni2", "shared") else f"models_{backbone}.yaml"
    return REPO_ROOT / "multitask_moe" / "configs" / name


def healthy_nodes(partition: str) -> list[str]:
    out = subprocess.run(["sinfo", "-h", "-p", partition, "-N", "-o", "%N|%t"],
                         capture_output=True, text=True).stdout
    nodes = []
    for line in out.splitlines():
        if "|" not in line:
            continue
        node, state = line.split("|", 1)
        state = state.strip().lower()
        if any(bad in state for bad in _BAD_STATE):
            continue
        if node not in nodes:
            nodes.append(node)
    return nodes


def job_exists(job_name: str) -> bool:
    out = subprocess.run(["squeue", "-u", "zuberi01", "-h", "-n", job_name, "-o", "%i"],
                         capture_output=True, text=True).stdout
    return bool(out.strip())


def iter_units():
    """Yield dicts describing each work-unit."""
    for task in TASKS:
        release = OUTPUT_BASE / task / "release"
        for fold in FOLDS:
            # CNV is backbone-independent -> single 'shared' bucket, CPU lane.
            yield {
                "task": task, "backbone": "shared", "family": CNV_FAMILY, "fold": fold,
                "lane": "cpu", "release": release, "registry": registry_for("shared"),
                "output_root": OUTPUT_BASE / task / "train" / "shared", "device": "cpu",
            }
            for backbone in BACKBONES:
                for family in NEURAL_FAMILIES:
                    yield {
                        "task": task, "backbone": backbone, "family": family, "fold": fold,
                        "lane": "gpu", "release": release, "registry": registry_for(backbone),
                        "output_root": OUTPUT_BASE / task / "train" / backbone, "device": "cuda",
                    }


def unit_id(u: dict) -> str:
    return f"{u['task']}__{u['backbone']}__{u['family']}__f{u['fold']}"


def write_cmd(u: dict, state_dir: Path) -> Path:
    lane = LANES[u["lane"]]
    cmd = (
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        f"cd {REPO_ROOT}\n"
        f"{ENV_PYTHON} {RUNNER} \\\n"
        f"  --release-root {u['release']} \\\n"
        f"  --model-registry {u['registry']} \\\n"
        f"  --family {u['family']} --outer-fold {u['fold']} \\\n"
        f"  --output-root {u['output_root']} \\\n"
        f"  --device {u['device']} --cpu-threads {lane['cpus']} --resume\n"
    )
    cmd_file = state_dir / f"{unit_id(u)}.cmd"
    cmd_file.write_text(cmd, encoding="utf-8")
    return cmd_file


def sbatch_for(u: dict, node: str, partition: str, state_dir: Path, log_dir: Path) -> list[str]:
    lane = LANES[u["lane"]]
    uid = unit_id(u)
    cmd = ["sbatch", "--parsable", "-J", f"barrett_mm_{uid}",
           "-A", ACCOUNT, "-p", partition, "-w", node,
           "--cpus-per-task", str(lane["cpus"]), "--mem", lane["mem"], "--time", lane["time"],
           "-o", str(log_dir / f"{uid}__{node}.out"), "-e", str(log_dir / f"{uid}__{node}.err")]
    if partition in lane["qos"]:
        cmd += ["--qos", lane["qos"][partition]]
    if partition in lane["gres"]:
        cmd += ["--gres", lane["gres"][partition]]
    cmd += ["--wrap", f"bash {WRAPPER} {state_dir} {uid}"]
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--submit", action="store_true", help="actually submit (default: dry run)")
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--backbones", default=",".join(BACKBONES))
    ap.add_argument("--families", default="all", help="'all' or comma list incl cnv_only/moe")
    ap.add_argument("--folds", default=",".join(str(f) for f in FOLDS))
    ap.add_argument("--lanes", default="gpu,cpu")
    ap.add_argument("--max-nodes-per-unit", type=int, default=0, help="0 = all healthy nodes")
    args = ap.parse_args()

    want_tasks = set(args.tasks.split(","))
    want_backbones = set(args.backbones.split(",")) | {"shared"}
    want_folds = {int(x) for x in args.folds.split(",")}
    want_lanes = set(args.lanes.split(","))
    want_families = None if args.families == "all" else set(args.families.split(","))

    state_dir = OUTPUT_BASE / "state"
    log_dir = OUTPUT_BASE / "slurm_logs"
    if args.submit:
        state_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)

    node_cache: dict[str, list[str]] = {}
    n_units = n_jobs = n_skipped_done = n_skipped_queued = 0
    for u in iter_units():
        if u["task"] not in want_tasks or u["fold"] not in want_folds or u["lane"] not in want_lanes:
            continue
        if u["backbone"] not in want_backbones:
            continue
        if want_families is not None and u["family"] not in want_families:
            continue
        uid = unit_id(u)
        done = state_dir / f"{uid}.done"
        if done.exists():
            n_skipped_done += 1
            continue
        if job_exists(f"barrett_mm_{uid}"):
            n_skipped_queued += 1
            continue
        n_units += 1
        lane = LANES[u["lane"]]
        nodes: list[str] = []
        for part in lane["partitions"]:
            if part not in node_cache:
                node_cache[part] = healthy_nodes(part)
            nodes += [(part, n) for n in node_cache[part]]
        cap = args.max_nodes_per_unit or lane.get("max_nodes") or 0
        if cap and cap > 0:
            nodes = nodes[:cap]
        if not args.submit:
            print(f"[dry] {uid}  lane={u['lane']}  -> {len(nodes)} node-copies")
            n_jobs += len(nodes)
            continue
        write_cmd(u, state_dir)
        for part, node in nodes:
            cmd = sbatch_for(u, node, part, state_dir, log_dir)
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                n_jobs += 1
            else:
                print(f"[submit-error] {uid}@{node}: {res.stderr.strip()[:200]}")

    action = "submitted" if args.submit else "planned"
    print(f"\nunits {action}: {n_units}  node-copies {action}: {n_jobs}  "
          f"skipped(done)={n_skipped_done}  skipped(queued)={n_skipped_queued}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

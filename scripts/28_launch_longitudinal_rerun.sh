#!/usr/bin/env bash
# Launch the landmarking longitudinal model across all five outer folds on SLURM.
#
# Each fold is one GPU job (nested inner-CV + final retrain + outer-test predict).
# Data stays on the cluster; outputs are written under $OUTPUT_ROOT, which MUST be
# outside the Git tree. Run this from the repo root on the cluster login node.
#
# Env activation uses the training env (virchow2) so the frozen UNI2/CNV feature
# views load exactly as in the Chapter 1 rerun.
#
# Usage:
#   RELEASE_ROOT=<frozen release dir> OUTPUT_ROOT=<scratch out> \
#     bash scripts/28_launch_longitudinal_rerun.sh [--smoke] [--fold N]
#
# --smoke : submit only fold 1 with a 1-candidate / 2-epoch config (sanity check).
# --fold N: submit only outer fold N (1..5).
set -euo pipefail

: "${RELEASE_ROOT:?set RELEASE_ROOT to the frozen release dir}"
: "${OUTPUT_ROOT:?set OUTPUT_ROOT to a scratch output dir outside Git}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-virchow2}"
PARTITION="${PARTITION:-h200}"
ACCOUNT="${ACCOUNT:-fmlab}"
CONDA_SH="${CONDA_SH:-$HOME/miniforge3/etc/profile.d/conda.sh}"

SMOKE=""
FOLDS="1 2 3 4 5"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke) SMOKE="--smoke"; FOLDS="1"; shift ;;
    --fold) FOLDS="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUTPUT_ROOT/slurm_logs"

for fold in $FOLDS; do
  job_name="long_fold${fold}${SMOKE:+_smoke}"
  sbatch \
    --job-name="$job_name" \
    --partition="$PARTITION" \
    --account="$ACCOUNT" \
    --gres=gpu:1 \
    --cpus-per-task=8 \
    --mem=64G \
    --time=08:00:00 \
    --output="$OUTPUT_ROOT/slurm_logs/${job_name}_%j.out" \
    --error="$OUTPUT_ROOT/slurm_logs/${job_name}_%j.err" \
    --wrap="set -euo pipefail; \
      source '$CONDA_SH'; conda activate '$ENV_NAME'; \
      cd '$REPO_ROOT'; \
      python scripts/27_run_longitudinal_outer_fold.py \
        --release-root '$RELEASE_ROOT' \
        --output-root '$OUTPUT_ROOT' \
        --outer-fold $fold \
        --device auto $SMOKE --overwrite"
  echo "submitted $job_name"
done

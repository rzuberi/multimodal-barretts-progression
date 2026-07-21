#!/usr/bin/env bash
# Self-deduplicating work-unit wrapper for the multitask/MoE campaign.
#
# The orchestrator submits one copy of each work-unit to EVERY node in the
# lane's partition(s). Each copy runs this wrapper, which guarantees the unit
# executes exactly once across all nodes and all re-submissions:
#
#   1. if a completion marker exists -> exit 0 (work already finished).
#   2. atomically claim the unit with `mkdir` (atomic on Lustre). If the claim
#      fails, another node already owns it -> self-cancel (exit 0), unless the
#      owning job is dead (stale claim) in which case we reclaim.
#   3. the winner best-effort cancels the sibling copies still PENDING on other
#      nodes, runs the command from the unit spec, and on success writes the
#      completion marker. A trap always releases the claim so failures can retry.
#
# Args: $1 = state dir (shared Lustre), $2 = unit_id
set -uo pipefail

STATE_DIR="$1"
UNIT_ID="$2"
DONE_MARKER="$STATE_DIR/$UNIT_ID.done"
CLAIM_DIR="$STATE_DIR/$UNIT_ID.claim"
CMD_FILE="$STATE_DIR/$UNIT_ID.cmd"
OWNER_FILE="$CLAIM_DIR/owner"
JOB_NAME="barrett_mm_$UNIT_ID"
SELF_JOB="${SLURM_JOB_ID:-nojob}"
HOST="$(hostname -s)"

log() { echo "[$(date +%H:%M:%S)] [$HOST/$SELF_JOB] $*"; }

if [[ -f "$DONE_MARKER" ]]; then
  log "already complete ($UNIT_ID) -> exit"; exit 0
fi

try_claim() {
  if mkdir "$CLAIM_DIR" 2>/dev/null; then
    echo "$HOST:$SELF_JOB:$(date +%s)" > "$OWNER_FILE"
    return 0
  fi
  return 1
}

if ! try_claim; then
  owner="$(cat "$OWNER_FILE" 2>/dev/null || echo unknown)"
  owner_job="$(echo "$owner" | cut -d: -f2)"
  # Stale-claim recovery: if the owning job is no longer in the queue, reclaim.
  if [[ "$owner_job" =~ ^[0-9]+$ ]] && [[ -z "$(squeue -h -j "$owner_job" -o '%i' 2>/dev/null)" ]]; then
    log "stale claim from dead job $owner_job -> reclaiming"
    rm -rf "$CLAIM_DIR"
    if ! try_claim; then log "lost reclaim race -> self-cancel"; exit 0; fi
  else
    log "already claimed by $owner -> self-cancel"; exit 0
  fi
fi

# We own the claim. Always release it on exit so a failed unit can be retried.
trap 'rmdir "$CLAIM_DIR" 2>/dev/null || rm -rf "$CLAIM_DIR" 2>/dev/null || true' EXIT
log "claimed $UNIT_ID"

# Drop sibling copies still queued on other nodes (best effort).
scancel --name "$JOB_NAME" --state=PENDING 2>/dev/null || true

if [[ ! -f "$CMD_FILE" ]]; then
  log "missing command file $CMD_FILE -> abort"; exit 2
fi

log "running: $(cat "$CMD_FILE")"
bash "$CMD_FILE"
rc=$?
if [[ $rc -eq 0 ]]; then
  touch "$DONE_MARKER"
  log "unit complete ($UNIT_ID)"
else
  log "unit FAILED rc=$rc ($UNIT_ID) -> claim released for retry"
fi
exit $rc

#!/usr/bin/env bash
# Regenerate the Chapter 1 result tables and figures from the frozen release.
#
# Two tiers:
#   (1) NO-DATA tier  - figures + no-data check. Runs anywhere from the repo
#                       alone (only reads allowlisted reports/thesis_ch1/*.csv).
#   (2) CLUSTER tier  - table regeneration from the frozen OOF release. Requires
#                       $BARRETTS_EXPERIMENT_ROOT and the private dataset; run on
#                       the CRUK CI cluster with the `erin` conda env active.
#
# Usage:
#   scripts/run_all.sh figures     # tier 1 only (default)
#   scripts/run_all.sh tables      # tier 2 (needs cluster + env vars)
#   scripts/run_all.sh all         # both
set -euo pipefail
cd "$(dirname "$0")/.."   # repo root
MODE="${1:-figures}"
PY="${PYTHON:-python}"

run_figures() {
  echo ">> [no-data] regenerating Chapter 1 figures from summary CSVs"
  "$PY" scripts/make_chapter1_figures.py
  echo ">> [no-data] verifying no patient data is tracked"
  bash scripts/assert_no_data_tracked.sh
}

run_tables() {
  : "${BARRETTS_EXPERIMENT_ROOT:?set BARRETTS_EXPERIMENT_ROOT to the training root on the cluster}"
  : "${BARRETTS_MASTER_CSV:?set BARRETTS_MASTER_CSV to the canonical master CSV}"
  echo ">> [cluster] BARRETTS_EXPERIMENT_ROOT=$BARRETTS_EXPERIMENT_ROOT"
  echo ">> [cluster] collecting final OOF predictions"
  "$PY" scripts/27_collect_lgd2_final_oof.py
  echo ">> [cluster] building pre-event results (model comparison + paired differences)"
  "$PY" scripts/28_make_lgd2_final_pre_event_results.py
  echo ">> [cluster] cohort table"
  "$PY" scripts/03_make_cohort_table.py
  echo ">> [cluster] main results table"
  "$PY" scripts/04_make_main_results_table.py
  echo ">> [cluster] patient detection metrics"
  "$PY" scripts/02_recompute_patient_detection_metrics.py
  echo ">> [cluster] selecting interpretation cases"
  "$PY" scripts/30_select_lgd2_final_interpretation_cases.py
  echo ">> [cluster] aggregating CNV feature importance across folds"
  "$PY" scripts/07_aggregate_cnv_importance.py
  echo "NOTE: scripts/05_make_early_prediction_table.py and"
  echo "      scripts/06_make_interpretability_summary.py are not yet written"
  echo "      (see docs/final_results_manifest.md 'Planned but NOT yet written')."
}

case "$MODE" in
  figures) run_figures ;;
  tables)  run_tables ;;
  all)     run_tables; run_figures ;;
  *) echo "usage: $0 {figures|tables|all}" >&2; exit 2 ;;
esac
echo ">> done ($MODE)"

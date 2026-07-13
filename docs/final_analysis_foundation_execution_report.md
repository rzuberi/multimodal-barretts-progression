# Final Analysis Foundation — Execution Report

## 1. Outcome
**Partially complete (by design).** Phases 0–7 (the analysis-ready foundation) are complete,
tested, and all 12 readiness gates PASS. Phase 8 (the GPU model rerun) is **launch-prepared
but not submitted**: the frozen training manifest loads into the real training stack with
patient-disjoint folds, but two training INPUTS are not yet resolved for the frozen cohort
(CNV feature-source dir; UNI2 feature index). Per the plan, jobs were NOT launched on
unvalidated/mismatched feature sources. No final model metrics are produced.

## 2. Git state
- Starting: `main` @ `1d56fb3`.
- Branch: `chapter1-final-analysis-foundation`.
- Phase 1 commit: `5cfbf0c`. Final commit + push/merge: recorded in outer `current_update.md`.

## 3. Files added/modified (clean repo)
- Added: `src/barrett/labels/lgd2.py`, `src/barrett/data/pre_event.py`,
  `src/barrett/data/matched_cohort.py`, `src/barrett/data/splits.py`,
  `src/barrett/evaluation/nested_selection.py`, `src/barrett/evaluation/output_contract.py`,
  `src/barrett/evaluation/cross_fitted_thresholds.py`,
  `scripts/17_build_lgd2_pre_event_cohort.py`, `scripts/18_build_or_validate_lgd2_patient_splits.py`,
  `scripts/19_validate_lgd2_training_artifacts.py`, `scripts/20_validate_lgd2_final_rerun_readiness.py`,
  `scripts/21_build_training_manifest.py`,
  `configs/chapter1_lgd2_final_analysis.yaml`, `docs/schemas/lgd2_oof_prediction_schema.md`,
  tests `test_lgd2_pre_event.py`, `test_splits_matched.py`, `test_nested_selection.py`,
  `test_output_contract.py`, `test_cross_fitted_thresholds.py`, and the report/audit files below.
- Modified: `.gitignore`, `scripts/assert_no_data_tracked.sh` (allowlist the new cohort-flow CSV).

## 4. Endpoint validation
- Rule: current-event `CurrentGradeInt>=3 OR (==2 AND LGDStreakSoFar>=2)`; next-biopsy positive
  `NextBiopsyLabel>=3 OR (==2 AND LGDStreakSoFar>=1)`.
- Stored `NextBiopsyProgression_LGD2plus` agrees with the derived two-LGD endpoint on **all 921
  evaluable rows (0 disagreements)**.
- Deviation recorded: canonical `EventDate` uses an **LGDx3** rule (10/38 event patients disagree,
  max 1139 days). Not used; event boundary derived from the timeline under the locked two-LGD rule.

## 5. Temporal cohort (audit anchors recomputed)
959 rows / 160 patients; 614 (Progressor==0) and 20 (Progressor==1) missing event days; 172 days==0;
endpoint 231 pos / 690 neg / 38 missing. Exclusion flow:

| stage | rows | patients |
|---|---|---|
| all | 959 | 160 |
| endpoint not evaluable | 38 | 17 |
| at-event | 183 | 40 |
| post-event | 31 | 7 |
| **strict pre-event eligible** | **707** | **150** |

## 6. Matched modelling unit
Canonical row key = `SampleID`; 707 unique units, 0 duplicate keys, 1:1 sample→CNV and
sample→image. 12 CNV profiles shared across samples (multi-slide biopsies) — flagged, not dropped.
Model-input equality across primary families: **equal (707 keys)**.

## 7. Split release
Deterministic 5-fold patient-disjoint (seed 20260713, stratified). 30 patients/fold, 10 pos / 20 neg
each. Row counts per fold: 174/130/138/121/144. Validation: no cross-fold patient, all 5 folds present,
both classes per fold.

## 8. Nested selection
Library `nested_selection.py` implemented + tested: inner patient-disjoint folds from outer-training
only; patient_max before ranking; rank AUPRC→AUC→Brier→configuration_id; full leaderboard retained;
fails closed if any outer-test patient enters inner predictions. (Applied during Phase 8, not yet run.)

## 9. Thresholding/calibration
Library `cross_fitted_thresholds.py` implemented + tested: threshold selected on inner-validation
patients only, applied unchanged to the outer-test fold, pooled confusion; primary criterion =
validation threshold at 90% specificity; calibrator fit on validation only. Tests prove test labels
never influence threshold/calibration.

## 10. Artifact contract
`output_contract.py` + `scripts/19` + `docs/schemas/lgd2_oof_prediction_schema.md`: 25 required
prediction columns, 15 required run-artifact keys; validators fail closed on duplicate keys,
incomplete folds, missing patient IDs, label/prob out of range, model-input inequality, missing
artifacts. (Enforced on Phase 8 outputs when they exist.)

## 11. Readiness gates
`reports/thesis_ch1/lgd2_final_rerun_readiness.md`: **12/12 PASS** — endpoint agreement, cohort not
blocked, strict-pre-event derived, at/post-event excluded, gate A (matched row-set equality), gate B
(single frozen split), enough pos/neg per fold, leakage+contract tests (23 passed), release external
to Git, no raw data tracked, non-overwrite behaviour, candidate registry present.

## 12. Training execution
**Not launched.** The training manifest (`training_manifest.csv`, 707 rows / 150 patients / 107
positives) loads via `image_mil.data.load_manifest`; all 5 folds verified patient-disjoint. Task
registry blocker RESOLVED (created `tasks_chapter1_lgd2_final.json`; endpoint resolves as binary).
Remaining input blockers (exact commands in `docs/final_analysis_foundation_launch_commands.md`):
1. CNV feature-source dir covering the 707 frozen samples (existing `features_*.csv` are a different
   killcoyne cohort — sample_ids do not match).
2. UNI2 feature index for image/fusion families.
External run root reserved: `analysis/chapter1_lgd2_final_pre_event_20260713_final/training/`.
No Slurm jobs submitted (would train on mismatched features).

## 13. Final metrics
Not available — the rerun has not run. Developmental metrics remain valid as references only.

## 14. Interpretability artifacts retained
Not yet — produced by the Phase 8 rerun (CNV estimators/importances, ABMIL checkpoints/attention,
fusion checkpoints). Case categories must be re-selected from final OOF predictions (strict pre-event
cohort differs from the developmental all-samples cohort), not reused.

## 15. Tests and no-data guard
- `pytest`: **122 passed** (erin env), incl. 30 new for this foundation.
- `py_compile`: OK on all new Python.
- `assert_no_data_tracked.sh`: OK. Cohort/manifest/split CSVs are EXTERNAL; only the small
  `lgd2_final_*` summary CSV/MDs are tracked (allowlisted).

## 16. Deviations and unresolved blockers
- Canonical `EventDate` (LGDx3) unused; event boundary derived from timeline (two-LGD). Documented.
- Phase 8 submission blocked on CNV feature-source + UNI2 feature index resolution (Section 12).
- Cross-fitted thresholding library built but only exercised on toy data (applied at Phase 8).

## 17. Scientific consequence
The analysis foundation is frozen: a deterministic strict pre-event LGD2+ cohort (707 rows / 150
patients), one immutable 5-fold patient split, leakage-safe selection/threshold/contract machinery,
and a validated bridge into the training stack. Nothing about model performance can be claimed yet.
The strongest permitted conclusion remains reserved for after a validated internal rerun and uses
LGD2+ neoplastic-progression wording (not cancer/OAC), with no external-validity claim.

## 18. Exact next command
Resolve the CNV feature-source dir (prereq 1), then run the CNV-only block in
`docs/final_analysis_foundation_launch_commands.md`; validate each completed run with `scripts/19`
before deriving any metric.

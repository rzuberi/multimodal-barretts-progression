# Final Analysis Foundation Implementation Plan

## Instruction to the executing coding agent

Implement this plan end to end. Do not merely audit or propose changes. Work incrementally, preserve existing external results, and stop before expensive training unless every readiness gate below passes.

At completion, write a separate execution report to:

`docs/final_analysis_foundation_execution_report.md`

The report is mandatory. It must state exactly what was implemented, what was run, external output paths, cohort and split counts, test results, training/job status, failures, deviations from this plan, and remaining work. Do not mark a phase complete without evidence.

## Objective

Create one analysis-ready foundation for the Barrett Chapter 1 comparison:

> Does adding histopathology to CNV improve prediction of future LGD2+ neoplastic progression in patients with Barrett's oesophagus?

The final workflow must prevent repeated cycles of discovering missing identifiers, predictions, thresholds, checkpoints, or interpretation artifacts after training. It must freeze the cohort, temporal eligibility, folds, model-selection rules, output schema, and retained artifacts before one controlled final model rerun.

Existing results remain developmental evidence and regression references. Do not delete or overwrite them.

## Locked scientific decisions

- Endpoint: `NextBiopsyProgression_LGD2plus`.
- Clinical definition: next biopsy is HGD/IMC/OAC, or it completes two consecutive LGD biopsies.
- Primary analysis: strictly pre-event future prediction.
- Primary evaluation: five-fold patient-disjoint outer cross-validation.
- Primary reporting level: patient.
- Primary aggregation: `patient_max`.
- Supplementary reporting: `patient_mean`, biopsy-level, and sample/slide-level.
- Primary metric: patient-level AUPRC.
- Secondary metrics: patient-level ROC AUC and Brier score.
- Clinical metrics: sensitivity, specificity, PPV, NPV, balanced accuracy, TP, FP, TN, FN, progressors detected/missed, and false positives per detected progressor.
- Main comparison cohort: identical eligible matched sample rows and patients for every model.
- Hyperparameter and architecture selection: outer-training/inner-validation data only; never outer-test data.
- Intermediate-fusion selection: pooled inner-validation predictions only, not pooled outer-test predictions.
- Primary clinical thresholds: selected from inner validation and applied unchanged to the corresponding outer test fold.
- Pooled test-derived thresholds: exploratory only.
- LGD3+: supplementary/legacy only.
- LOPO: not primary.
- Heavy data, predictions, checkpoints, features, and interpretation arrays remain external to Git.

## Critical temporal clarification

Do not implement a blanket rule that drops every row with missing `DaysFromCurrentToEvent`.

In the current canonical table, missing event timing is expected for non-progressors because they do not have an event date. A lightweight inspection on 2026-07-13 found:

- 959 rows and 160 patients;
- 614/614 rows with `Progressor_label == 0` have missing `DaysFromCurrentToEvent`;
- 20 rows with `Progressor_label == 1` have missing `DaysFromCurrentToEvent`;
- 172 rows have `DaysFromCurrentToEvent == 0`;
- `NextBiopsyProgression_LGD2plus` has 231 positive, 690 negative, and 38 missing rows.

Recompute and document these counts. They are audit anchors, not hard-coded acceptance values.

The endpoint is next-biopsy progression. Temporal eligibility must therefore be derived from the clinical sequence and dates, not inferred from missingness alone.

## Assumed strict pre-event rule

Implement this rule unless direct file evidence proves a safer equivalent. Record any deviation.

A sample row is primary-analysis eligible only when all of the following hold:

1. `NextBiopsyProgression_LGD2plus` is non-null and binary.
2. `NextBiopsyLabel` is known.
3. The next biopsy is demonstrably later than the current biopsy:
   - preferably `NextBiopsyDate > Date`; and
   - `DaysToNextBiopsy > 0` when available.
4. The current biopsy is before the patient's first LGD2+ event.
5. The current biopsy does not already meet the LGD2+ event definition.
6. Both required modalities and all validated matching identifiers exist.
7. The row belongs to the frozen identical-sample comparison set.

Derive current-event status directly:

```text
is_lgd2_event_at_current =
    CurrentGradeInt >= 3
    OR (CurrentGradeInt == 2 AND LGDStreakSoFar >= 2)
```

Derive the next-biopsy endpoint independently and compare it with the stored column:

```text
derived_NextBiopsyProgression_LGD2plus = 1
    if NextBiopsyLabel >= 3
    OR (NextBiopsyLabel == 2 AND LGDStreakSoFar >= 1)
```

The stored and freshly derived endpoint must agree on every evaluable row. Fail the readiness gate on disagreement.

For patients with an LGD2+ event, derive or validate the first event date from the full clinical biopsy timeline before intersecting with modality availability. Exclude current-event and post-event rows. For patients without an event, a missing event date is valid; retain rows when the next-biopsy target and temporal order are known.

If the full clinical timeline needed to derive the first LGD2+ event is unavailable, do not silently approximate it from matched rows. Use the canonical `EventDate` only after validating that it was generated with the locked two-LGD rule. Otherwise mark the cohort release blocked.

## External and repository boundaries

Clean Git repository:

`multimodal-barretts-progression/`

Current external canonical input:

`data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`

Current developmental campaign:

`data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`

Create a new timestamped external root for the final foundation and rerun. Suggested form:

`analysis/chapter1_lgd2_final_pre_event_<YYYYMMDD_HHMMSS>/`

Never write the new cohort, split tables, raw OOF predictions, checkpoints, feature matrices, tile scores, or large interpretation outputs inside the clean Git repository. Git may contain scripts, schemas, configuration templates, hashes, compact metric tables, and Markdown reports only.

## Phase 0: establish provenance and working state

1. Read:
   - `PROJECT_STATE.md`;
   - `docs/full_integration_execution_report_20260713.md`;
   - `docs/data_contract.md`;
   - `docs/final_results_manifest.csv`;
   - `configs/chapter1_lgd2.yaml`;
   - existing model migration and experiment plans.
2. Confirm the clean repo is on `main`, inspect `git status`, and preserve unrelated changes.
3. Detect the correct Python environments. Use the repository's tested lightweight environment for tests and the model-specific environment for training. Record executable paths and package versions.
4. Inventory the source scripts that generated:
   - the canonical LGD2+ master;
   - existing patient folds;
   - CNV-only models;
   - UNI2 ABMIL;
   - early fusion;
   - intermediate fusion;
   - late fusion.
5. Hash all source inputs and scripts used for the new release.

Deliverable:

- `reports/thesis_ch1/lgd2_final_foundation_provenance.md`

## Phase 1: make endpoint and temporal eligibility reproducible

Add reusable, tested code under the clean package. Suggested files:

- `src/barrett/labels/lgd2.py`
- `src/barrett/data/pre_event.py`
- `scripts/17_build_lgd2_pre_event_cohort.py`

Required functionality:

1. Recompute the LGD2+ current-event rule and next-biopsy endpoint from source columns.
2. Parse and validate `Date`, `NextBiopsyDate`, `EventDate`, `DaysToNextBiopsy`, and `DaysFromCurrentToEvent` without guessing malformed values.
3. Derive at least these flags:
   - `endpoint_evaluable`;
   - `next_biopsy_is_future`;
   - `is_lgd2_event_at_current`;
   - `is_post_lgd2_event`;
   - `strict_pre_event_eligible`;
   - `timing_evidence_source`;
   - `exclusion_reason`.
4. Distinguish valid no-event missingness from unresolved event timing.
5. Verify that dates and day differences agree within an explicitly documented tolerance.
6. Fail on stored-versus-derived endpoint disagreement.
7. Produce an external versioned cohort release and metadata JSON containing source hashes, code hash, row counts, patient counts, endpoint counts, exclusion counts, and generation command.
8. Never overwrite an existing release without an explicit flag. Use atomic writes.

Create lightweight Git summaries:

- `reports/thesis_ch1/lgd2_final_pre_event_cohort_flow.csv`
- `reports/thesis_ch1/lgd2_final_pre_event_cohort_flow.md`
- `reports/thesis_ch1/lgd2_final_pre_event_timing_audit.md`
- `reports/thesis_ch1/lgd2_final_pre_event_warnings.md`

The cohort flow must report counts by row, biopsy, and patient for every exclusion stage. It must separately report at-event, post-event, endpoint-missing, next-biopsy-date-missing, non-positive next-biopsy interval, unresolved event timing, missing image, missing CNV, and unsafe/duplicate matching.

## Phase 2: freeze the exact matched comparison set

Build one external sample manifest used by every primary model.

Required columns:

- `cohort_release_id`;
- `sample_id`;
- `patient_id`;
- `biopsy_id`;
- `slide_id` and slide basename/reference;
- `cnv_id` and CNV basename/reference;
- endpoint and timing fields;
- `strict_pre_event_eligible`;
- modality availability;
- canonical row key;
- exclusion reason;
- source-table hash.

Requirements:

1. Enforce one canonical comparison row per validated modelling unit.
2. Explicitly resolve or reject duplicated CNV-slide pairings.
3. Verify CNV-only, image-only, and every fusion family consume the same canonical row keys.
4. Use the matched multimodal cohort for the main CNV baseline. A broader CNV-only cohort may be supplementary but must never be placed in the primary paired comparison.
5. Produce a machine-readable equality check between model input manifests.

Lightweight outputs:

- `reports/thesis_ch1/lgd2_final_matched_cohort_audit.csv`
- `reports/thesis_ch1/lgd2_final_matched_cohort_audit.md`
- `reports/thesis_ch1/lgd2_final_model_input_equality.md`

Readiness gate A passes only if endpoint derivation, temporal eligibility, matching, and exact row-set equality all pass.

## Phase 3: create one immutable outer split release

Add:

- `src/barrett/data/splits.py`
- `scripts/18_build_or_validate_lgd2_patient_splits.py`
- `configs/chapter1_lgd2_final_analysis.yaml`

Split rules:

1. Create exactly five outer folds at patient level.
2. Derive patient labels as the maximum endpoint value across that patient's eligible rows, consistent with `patient_max` reporting.
3. Use one deterministic, documented seed. Do not search multiple seeds for the most favourable balance.
4. Stratify patient outcomes where feasible.
5. Assign all biopsies, samples, slides, and CNVs from a patient to one outer fold.
6. Record fold patient/positive/negative/sample/biopsy counts.
7. Hash and freeze the patient-to-fold CSV externally.
8. Refuse training if a patient appears in more than one outer fold or if any model uses a different assignment.

Because the strict pre-event cohort differs from the developmental all-samples cohort, treat this as a new versioned split release. Do not silently reuse old fold files. Compare old and new assignments only for documentation.

Add tests for determinism, patient disjointness, five-fold completeness, class presence, and row-to-patient propagation.

Lightweight outputs:

- `reports/thesis_ch1/lgd2_final_split_audit.csv`
- `reports/thesis_ch1/lgd2_final_split_audit.md`
- `reports/thesis_ch1/lgd2_final_split_warnings.md`

Readiness gate B passes only if all model families use the same frozen outer split manifest.

## Phase 4: freeze the final model and selection registry

Add:

- `configs/chapter1_lgd2_final_models.yaml`
- `src/barrett/evaluation/nested_selection.py`

Primary families:

1. CNV-only: the locked core CNV random-forest representation.
2. Histology-only: UNI2 features with ABMIL.
3. Early fusion: UNI2 plus the locked CNV representation, including `early_mean_mlp` as a candidate or fixed architecture.
4. Intermediate fusion: a small, explicitly listed candidate set.
5. Late fusion:
   - prespecified arithmetic mean;
   - validation-trained logistic stacker.

Co-attention may be supplementary unless it passes the same nested-selection, artifact, and input-equality requirements. Foundation-model, magnification, tile-size, clinical-augmentation, and broad architecture sweeps are supplementary and must not be searched during primary outer-test evaluation.

Nested-selection rules:

1. For each outer fold, create patient-disjoint inner folds from outer-training patients only.
2. Fit preprocessing and candidate models independently inside each inner training fold.
3. Pool inner held-out patient predictions for that outer fold.
4. Aggregate inner held-out predictions using `patient_max` before model selection.
5. Rank candidates by:
   - highest patient-level AUPRC;
   - then highest ROC AUC;
   - then lowest Brier score;
   - then a deterministic configuration-name tie break.
6. Save the complete validation leaderboard, not only the winner.
7. Select intermediate fusion from pooled inner-validation predictions only.
8. Retrain the selected configuration on the full outer-training set, then evaluate the outer-test fold exactly once.
9. Outer-test results must never alter the candidate choice for that fold.
10. For late `stack_logit`, train the meta-model on outer-training inner-OOF base-model predictions. Never train it on outer-test predictions.

The final report must distinguish:

- prespecified/fixed models;
- nested-selected model families;
- supplementary post-hoc selected models.

Add unit tests proving that outer-test rows cannot enter selection, preprocessing, calibration, threshold selection, or the late-fusion stacker.

Readiness gate C passes only when leakage tests pass and every primary candidate set is fixed in configuration.

## Phase 5: implement the analysis-ready artifact contract

Add:

- `src/barrett/evaluation/output_contract.py`
- `scripts/19_validate_lgd2_training_artifacts.py`
- a JSON Schema or documented CSV schema under `docs/schemas/`.

Every outer-test prediction row must contain:

- `run_id`;
- `cohort_release_id` and cohort hash;
- `split_release_id` and split hash;
- `model_family`, `model_name`, `configuration_id`;
- `feature_model`, `fusion_type`, and CNV representation;
- `outer_fold`;
- canonical row key;
- patient, biopsy, sample, slide, and CNV identifiers;
- `y_true`;
- raw logit where available;
- raw probability;
- calibrated probability if calibration is enabled;
- eligibility/timing fields;
- checkpoint/config/preprocessor references;
- seed and software-environment reference.

Every run must also retain externally:

- exact resolved YAML/JSON configuration;
- source Git commit and dirty-state indicator;
- environment/package export;
- input manifests and hashes;
- outer and inner fold assignments;
- inner validation predictions and leaderboard;
- outer-test predictions;
- fold checkpoints;
- fitted preprocessing objects;
- training logs and failure state;
- per-fold run metadata;
- completeness manifest with file sizes and hashes.

Model-specific artifacts:

- CNV: ordered feature names/windows, fitted estimator, feature importance and/or coefficients, preprocessing state, genomic build, bin resolution, and window-to-gene mapping reference.
- ABMIL: checkpoint, slide/feature index, attention/tile identifiers sufficient to regenerate selected-case outputs, feature model and extraction metadata.
- Early/intermediate/co-attention: checkpoints plus both modality identifiers and any available attention/gating outputs.
- Late fusion: base prediction references and fitted stacker coefficients/intercept for each outer fold.

Fail closed on duplicate prediction keys, incomplete fold coverage, missing patient IDs, label disagreements, model input inequality, or missing required artifacts.

Readiness gate D passes only when a toy run from each family satisfies the schema and artifact validator.

## Phase 6: replace post-hoc primary thresholds

Add:

- `src/barrett/evaluation/cross_fitted_thresholds.py`
- tests and reporting integration.

For each outer fold and model:

1. Aggregate pooled inner-validation predictions to patient level using `patient_max`.
2. Select thresholds on those validation patients only.
3. Apply each selected threshold unchanged to the corresponding outer-test patients.
4. Pool outer-test confusion counts across folds.

Report:

- default threshold `0.5`;
- validation-selected threshold for a prespecified criterion;
- sensitivity at validation-selected 90% and 95% specificity;
- specificity at validation-selected 90% and 95% sensitivity.

Choose and document one primary clinical operating criterion before outer-test analysis. Safest default: validation threshold targeting 90% specificity, with sensitivity and false-positive burden reported on outer-test patients. If the target cannot be achieved in a validation fold, use a deterministic conservative fallback and record it.

Keep current pooled-OOF post-hoc threshold results as exploratory and label them clearly. Do not overwrite them.

If probability calibration is used, fit the calibrator on inner-OOF validation predictions only and apply it to the outer test fold. Report raw and calibrated Brier/calibration separately.

Readiness gate E passes only if tests demonstrate that threshold and calibration fitting never see outer-test labels.

## Phase 7: final readiness review before compute

Add:

- `scripts/20_validate_lgd2_final_rerun_readiness.py`
- `reports/thesis_ch1/lgd2_final_rerun_readiness.csv`
- `reports/thesis_ch1/lgd2_final_rerun_readiness.md`

The validator must check:

- endpoint agreement;
- strict pre-event eligibility;
- no current/post-event rows;
- no unresolved target timing in the primary cohort;
- exact model row-set equality;
- patient-disjoint outer and inner folds;
- complete candidate registry;
- no test-data selection paths;
- output directories outside Git;
- output non-overwrite behavior;
- artifact schema support;
- model runtime environments;
- feature/checkpoint/input references;
- enough positive and negative patients in each outer and inner split;
- no raw data tracked by Git.

Do not launch expensive jobs unless every required gate is `PASS`. If a gate fails, stop, write the failure and exact remediation to the mandatory execution report, and do not weaken the gate to make it pass.

## Phase 8: controlled final rerun

Only after the readiness report passes, run the locked primary model matrix on the same strict pre-event cohort and split release.

Required run order:

1. CNV-only baseline.
2. UNI2 ABMIL image-only baseline.
3. Early fusion.
4. Intermediate fusion with nested validation selection.
5. Late fusion mean.
6. Late fusion validation-trained stacker.
7. Optional co-attention supplementary run only after primary models complete.

Operational requirements:

- Run one outer fold/job shard at a time or use transparent Slurm arrays.
- Save partial successful folds without treating incomplete runs as final.
- Never overwrite developmental campaigns.
- Use a new external run root.
- Record Slurm job IDs, commands, environments, resource requests, wall time, exit status, and failed folds.
- Retry only diagnosed technical failures; do not alter model settings based on outer-test performance.
- Do not run additional architecture searches after viewing test results.

If compute cannot be completed in the coding-agent session, the agent must still create exact launch and collection commands, submit jobs if permitted, and record live job IDs/status. It must not claim the rerun is complete until all five outer folds and artifact validations pass.

## Phase 9: derive final results only from frozen OOF artifacts

Extend the clean reporting scripts so they consume the new run manifest rather than hard-coded result paths.

Primary result table:

- CNV-only;
- image-only UNI2 ABMIL;
- early fusion;
- nested-selected intermediate fusion;
- late fusion mean;
- late fusion stacker.

For each model report patient-level:

- AUPRC with paired bootstrap CI;
- ROC AUC with paired bootstrap CI;
- Brier score with paired bootstrap CI;
- validation-derived clinical operating-point metrics;
- threshold 0.5 metrics;
- patient, positive, and negative counts;
- TP, FP, TN, FN;
- detected and missed progressors;
- false positives per detected progressor.

Primary contrasts:

- early fusion minus CNV-only;
- intermediate fusion minus CNV-only;
- late mean minus CNV-only;
- late stacker minus CNV-only.

Contextual contrasts:

- image-only minus CNV-only;
- fusion models minus image-only;
- early versus late fusion.

Use shared-patient paired bootstrap resampling. Never compare metrics computed on different patient sets.

Create new, clearly versioned reports rather than overwriting developmental reports until the final rerun is accepted. Update `docs/final_results_manifest.csv`, `PROJECT_STATE.md`, and the README only after final validation.

## Phase 10: interpretation readiness from the final models

The final rerun must remove the current interpretation artifact gaps.

Required minimum:

- Persist CNV estimators and ordered feature/window definitions for all outer folds.
- Export lightweight fold-specific CNV feature importance tables externally.
- Validate the genomic build and create/reference a compatible window-to-gene map.
- Retain ABMIL checkpoints and attention regeneration metadata.
- Retain fusion checkpoints and enough modality information to perform case-level ablation.
- Regenerate interpretation only for selected cases after final OOF predictions determine their categories.

Do not reuse existing case categories automatically: cases may change classification under the strict pre-event rerun. Re-select cases from final OOF predictions.

Model-internal fusion attribution is supplementary. Probability-level modality ablation remains acceptable supporting evidence, but it must not be described as causal attribution.

## Required tests

Use toy/synthetic data only in Git tests. At minimum test:

- LGD2 current-event derivation;
- two-consecutive-LGD next-biopsy rule;
- HGD/IMC/OAC endpoint positives;
- valid non-progressor missing event date retained;
- at-event and post-event exclusion;
- missing or non-positive next-biopsy timing exclusion;
- stored-versus-derived label disagreement fails;
- duplicate/many-to-many modality matching fails;
- exact row-set equality across models;
- deterministic patient splits;
- outer and inner patient disjointness;
- validation-only intermediate selection;
- late stacker fold purity;
- preprocessing fit isolation;
- cross-fitted threshold isolation;
- artifact-schema validation;
- incomplete folds rejected;
- external-output and no-overwrite guards;
- no-data tracking guard.

Run:

- `py_compile` on all changed Python;
- the full lightweight test suite;
- toy end-to-end cohort/split/selection/artifact validation;
- `./scripts/assert_no_data_tracked.sh`.

## Required documentation updates

Update only after implementation evidence exists:

- `README.md`;
- `PROJECT_STATE.md`;
- `docs/data_contract.md`;
- `docs/experiment_plan.md`;
- `docs/final_results_manifest.csv` and `.md`;
- `configs/chapter1_lgd2.yaml` or replace it with the new locked final-analysis config;
- timing/threshold limitations reports.

The documentation must explicitly distinguish:

- developmental all-samples results;
- developmental at-event-excluded results;
- final strict pre-event nested-CV results;
- supplementary post-hoc analyses;
- external validation, which remains absent unless separately performed.

## Mandatory execution report structure

Write `docs/final_analysis_foundation_execution_report.md` with these sections:

1. **Outcome**: complete, partially complete, or blocked.
2. **Git state**: starting commit, branch, final commit, push/merge status.
3. **Files added/modified**.
4. **Endpoint validation**: exact rule, disagreements, resolution.
5. **Temporal cohort**: complete exclusion flow and final row/biopsy/patient/class counts.
6. **Matched modelling unit**: duplicate/matching/equality results.
7. **Split release**: seed, hashes, fold counts, leakage checks.
8. **Nested selection**: candidates, validation metrics, selected configuration per outer fold.
9. **Thresholding/calibration**: exact validation-only procedure.
10. **Artifact contract**: files required and completeness by model/fold.
11. **Readiness gates**: A-E and final validator results.
12. **Training execution**: commands, job IDs, environments, fold status, external output root.
13. **Final metrics**: only if all required outer folds are complete and validated.
14. **Interpretability artifacts retained**.
15. **Tests and no-data guard**.
16. **Deviations and unresolved blockers**.
17. **Scientific consequence**: what can and cannot now be claimed.
18. **Exact next command** if anything remains incomplete.

Do not write vague statements such as "validated" without paths, hashes, counts, or test names.

## Definition of done

This implementation is complete only when:

1. A deterministic strict pre-event LGD2+ cohort release exists externally.
2. Its endpoint and temporal derivation are reproducible and fully audited.
3. Every primary model uses identical canonical rows and patients.
4. One immutable five-fold patient split release is used by every model.
5. Model and hyperparameter selection uses only inner validation within each outer fold.
6. Intermediate fusion is selected from pooled inner-validation predictions, never test results.
7. Primary operating thresholds are validation-derived and cross-fitted.
8. Every model emits the complete standard artifact schema.
9. The locked model suite has five complete, validated outer-test folds, or the execution report clearly marks compute as incomplete.
10. Final tables can be recreated from saved OOF outputs without loading checkpoints or retraining.
11. CNV and histology interpretation artifacts required for selected-case regeneration have been retained externally.
12. Tests and the no-data guard pass.
13. The mandatory execution report contains verifiable evidence for every completed item.

## Scientific wording after completion

Even if the internal final rerun is successful, the strongest permitted conclusion is:

> In this matched internal cohort, adding histopathology to CNV improved patient-level prediction of future next-biopsy LGD2+ neoplastic progression under patient-disjoint nested cross-validation.

Do not call the endpoint cancer/OAC progression. Do not claim external generalisability, clinical utility, or causal modality contribution without external validation and appropriately designed evidence.

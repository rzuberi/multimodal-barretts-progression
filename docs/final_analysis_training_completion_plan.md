# Final Analysis Training Completion Plan

## Instruction to the executing coding agent

Execute this plan. This is the completion stage after
`docs/final_analysis_foundation_execution_report.md`.

Do not stop after another audit, readiness framework, or generic command plan. The intended end state is a validated five-fold strict pre-event rerun with complete out-of-fold predictions for the locked unimodal and fusion models, followed by final patient-level comparisons.

Write a separate mandatory execution report to:

`docs/final_analysis_training_completion_execution_report.md`

Update it throughout execution. If compute remains running or blocked, state that plainly, include job IDs and the exact next command, and use `PARTIAL` rather than `COMPLETE`.

## Current state

The analysis foundation exists and is frozen externally at:

`analysis/chapter1_lgd2_final_pre_event_20260713_final/`

It currently contains:

- `pre_event_cohort.csv`;
- `matched_manifest.csv`;
- `patient_splits.csv`;
- `row_to_fold.csv`;
- `training_manifest.csv`;
- `tasks_chapter1_lgd2_final.json`;
- release metadata.

Current cohort:

- 707 strict pre-event modelling rows;
- 150 patients;
- five patient-disjoint folds;
- 30 patients per fold;
- 10 positive and 20 negative patients per fold.

No final model rerun has occurred. Existing performance results are developmental references only.

## Critical problems to fix before training

### 1. Feature identifier mismatch

The frozen `training_manifest.csv` currently uses numeric canonical `SampleID` values as `sample_id`. Existing CNV feature tables and UNI2 indexes use CNV-style identifiers such as `SLX-...`.

Do not conclude that features are absent merely because these columns differ. Trace the mapping through:

- canonical `SampleID`;
- `CNVAbsPath` and its canonical basename/sample token;
- `ImageAbsPath` and slide basename;
- existing feature-table `sample_id`;
- existing UNI2 index `sample_id` and `image_basename`.

Build explicit external feature views keyed by the canonical modelling-row identifier. Do not replace the canonical key with a CNV identifier because 12 CNV profiles are shared by multiple modelling rows.

### 2. Legacy image/fusion test leakage

The legacy `image_mil.train.train_one_fold` uses the supplied test loader during every epoch for early stopping. The old outer-test fold therefore acts as validation data.

This is not acceptable for the final rerun. Refactor the final runner to have three distinct sets:

- inner/final training;
- inner validation or outer-training-only early-stopping validation;
- outer test, evaluated once after training is complete.

The outer-test fold must not be used for epoch selection, early stopping, thresholding, calibration, preprocessing, or architecture selection.

### 3. Legacy CNV tuning is sample-level

The legacy CNV random-forest tuner uses `StratifiedKFold` on rows. Multiple rows from one patient may therefore cross inner folds.

Replace this with patient-disjoint inner folds. Candidate ranking must use pooled inner held-out predictions aggregated with `patient_max`, with AUPRC as the primary metric.

### 4. No real frozen model registry

`configs/chapter1_lgd2_final_analysis.yaml` freezes the analysis, but it is not a complete model/hyperparameter registry. Create the missing registry before running any outer-test model.

### 5. New evaluation libraries are not connected to real trainers

`nested_selection.py`, `cross_fitted_thresholds.py`, and `output_contract.py` are tested only on toy data. Integrate them into the actual final training and collection workflow.

## Locked scientific protocol

- Endpoint: `NextBiopsyProgression_LGD2plus`.
- Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
- Cohort: frozen 707-row strict pre-event matched cohort.
- Outer evaluation: frozen five-fold patient-disjoint CV.
- Primary aggregation: patient maximum probability.
- Primary metric: patient-level AUPRC.
- Secondary metrics: ROC AUC and Brier score.
- Primary clinical threshold: selected on inner validation to target 90% specificity, then applied unchanged to the outer test fold.
- Reference threshold: 0.5.
- Every primary model must receive the same 707 canonical modelling rows and 150 patients.
- All preprocessing and model selection must be fitted using outer-training patients only.
- Intermediate fusion must be fixed or selected using pooled inner-validation predictions, never pooled outer-test predictions.
- Main contrasts are paired on identical patients.

## Phase 1: resolve canonical feature mappings

Add:

- `src/barrett/data/feature_views.py`
- `scripts/22_build_lgd2_final_feature_views.py`
- `scripts/23_validate_lgd2_final_feature_views.py`

### CNV feature view

Start from the feature sources used by the successful developmental campaign. The old run metadata identifies:

- `data/killcoyne_repro_strict_500kb_slurm_v2/features_5mb_armdiff.csv`;
- `data/killcoyne_repro_strict_500kb_slurm_v2/features_arms.csv`;
- `data/killcoyne_repro_strict_500kb_slurm_v2/cx.csv`.

Despite the directory name, the developmental LGD2 campaign reported 940 CNV samples and trained on these sources. Validate their provenance and mapping rather than rejecting them based on direct comparison with numeric `SampleID`.

For each frozen modelling row:

1. Derive the CNV feature key using the same canonicalisation logic as `image_mil.cnv_variants` and the developmental campaign.
2. Match `CNVAbsPath` to exactly one feature row in each required source.
3. Confirm the three sources agree on key coverage.
4. Create external filtered/adapted feature files whose `sample_id` is the canonical modelling key used by the frozen manifest.
5. Duplicate feature values only when the canonical table intentionally contains multiple slide/sample rows sharing one CNV profile. Record this explicitly.
6. Preserve the original CNV feature key in `source_cnv_feature_id`.
7. Preserve feature order and write feature-name hashes.
8. Do not impute missing profiles. Require 707/707 coverage.

The adapted CNV files must remain external under:

`analysis/chapter1_lgd2_final_pre_event_20260713_final/feature_views/cnv/`

### UNI2 feature index

The developmental UNI2 index already exists at:

`data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/runs/image/all_samples/core_gpu/index/virchow2_index.csv`

The filename is generic legacy naming; its rows point to UNI2 embeddings with feature dimension 1536.

For each frozen modelling row:

1. Match using validated CNV key plus image basename, or directly using `ImageAbsPath` basename and the source UNI2 manifest.
2. Require exactly one NPZ reference for the canonical modelling row.
3. Create an external index whose `sample_id` is the canonical modelling key.
4. Retain `source_feature_sample_id`, `image_basename`, `npz_path`, `n_instances`, `feat_dim`, and status.
5. Resolve legacy `/scratchc` paths using the established path-remap mechanism.
6. Check path existence and index metadata without copying tensors.
7. Require 707/707 index coverage, `status=ok`, and a consistent feature dimension.

Write the adapted index under:

`analysis/chapter1_lgd2_final_pre_event_20260713_final/feature_views/uni2/uni2_index.csv`

### Mapping audit

Create lightweight reports:

- `reports/thesis_ch1/lgd2_final_feature_mapping_audit.csv`
- `reports/thesis_ch1/lgd2_final_feature_mapping_audit.md`
- `reports/thesis_ch1/lgd2_final_feature_mapping_warnings.md`

Report canonical rows, unique CNV profiles, shared profiles, unique slides, CNV coverage, UNI2 coverage, duplicate mappings, missing mappings, feature dimensions, and source hashes.

Feature gate passes only with exact 707/707 coverage for both modalities and no ambiguous mappings.

## Phase 2: correct and freeze the training manifest

Update `scripts/21_build_training_manifest.py` or replace it with a version that emits both identifiers:

- `sample_id`: canonical modelling identifier used consistently by all adapted feature views;
- `canonical_row_key`;
- `source_cnv_feature_id`;
- `source_image_feature_id`;
- patient/biopsy/slide/CNV identifiers;
- label;
- outer fold;
- timing and eligibility fields.

Validate that:

- there are 707 unique canonical row keys;
- the manifest does not collapse shared CNV profiles;
- all five folds remain patient-disjoint;
- every row exists in both adapted feature views;
- labels agree with the cohort release;
- no at-event or post-event row is present.

Write a new versioned manifest rather than silently changing the existing file. Record its hash in the model registry and run metadata.

## Phase 3: migrate the minimum final model code

The clean repository now has a concrete rerun requirement, so migrate only the model definitions and training utilities required for the locked final models. Do not copy campaign launch code wholesale.

Add as needed:

- `src/barrett/models/cnv.py`
- `src/barrett/models/image_mil.py`
- `src/barrett/models/early_fusion.py`
- `src/barrett/models/intermediate_fusion.py`
- `src/barrett/training/data.py`
- `src/barrett/training/loops.py`
- `src/barrett/training/inner_cv.py`
- `src/barrett/training/artifacts.py`
- package `__init__.py` files.

Source behavior from:

- `scripts/run_mil_cnv_only_cv.py`;
- `image_mil/models.py`;
- `image_mil/multimodal.py`;
- `image_mil/train.py`;
- `image_mil/train_multimodal.py`;
- `scripts/run_mil_cv.py`;
- `scripts/run_mil_multimodal_cv.py`.

Requirements:

1. Preserve the mathematical architecture of the developmental comparators.
2. Separate model definitions from HPC paths and CLI globals.
3. Add toy tensor compatibility tests comparing old and migrated model outputs after loading identical weights where feasible.
4. Implement explicit train/validation/test APIs.
5. Outer-test data must never be passed to the training loop until final prediction.
6. Save raw logits and probabilities.
7. Make all seeds explicit.
8. Fit PCA, scaling, class weighting, and any feature selection using training patients only.
9. Save fitted preprocessing objects externally.
10. Do not introduce new architectures during migration.

If full migration would alter behavior or cannot be validated, create a thin final runner around the existing model definitions but replace the leaking training loop. Document the dependency. Do not use the old leaking loop for convenience.

## Phase 4: create the real model registry

Create:

`configs/chapter1_lgd2_final_models.yaml`

It must include exact, finite candidates and all hyperparameters. At minimum:

### CNV-only

- Family: `cnv_only`.
- Model: `cnv_random_forest`.
- Representation: `windows_armdiff_plus_arms_plus_cx`.
- PCA/scaling behavior matching the developmental baseline.
- A small deterministic RF candidate grid or a prespecified fixed configuration.
- Patient-disjoint inner validation.

Do not retain the legacy row-level random search. If a grid is used, list every candidate in YAML and rank using patient-level inner-validation AUPRC.

### Image-only

- Family: `image_only`.
- Feature model: UNI2, level 2, existing 1536-dimensional features.
- Model: ABMIL.
- Fixed architecture.
- Fixed optimizer/loss settings declared in YAML.
- Epoch count or early-stopping epoch determined without outer-test data.

### Early fusion

- Family: `early_fusion`.
- Model: `early_mean_mlp`.
- Same UNI2 and CNV representations as the unimodal baselines.
- Fixed architecture and finite hyperparameter candidates.

### Intermediate fusion

- Family: `intermediate_fusion`.
- Base architecture: `intermediate_abmil_cnv`.
- Freeze a small candidate set before outer-test runs.
- Candidate differences may include only justified training hyperparameters, such as learning rate, regularisation, or a documented hidden dimension.
- Maximum four candidates unless the execution report justifies more.
- Select independently within each outer fold using pooled inner-validation patient predictions.
- If only one defensible configuration exists, mark the model `prespecified_fixed`; do not call it the selected best model.

### Late fusion

- `late_mean`: arithmetic mean of matching CNV and image outer-test probabilities; no fitted parameters.
- `late_stack_logit`: logistic meta-model trained only on inner-OOF base predictions from outer-training patients.

### Supplementary only

- Co-attention may be added only after all primary models complete.
- Do not add foundation sweeps, magnification sweeps, clinical augmentation, or additional CNV resolutions to the primary run.

The registry must include a `role` field (`PRIMARY_FIXED`, `PRIMARY_NESTED_SELECTED`, or `SUPPLEMENTARY`) and a unique `configuration_id` for every candidate.

## Phase 5: implement a single final outer-fold runner

Add:

`scripts/24_run_lgd2_final_outer_fold.py`

CLI requirements:

```text
--release-root
--model-registry
--family
--outer-fold
--output-root
--resume
```

Optional explicit runtime flags are acceptable, but resolved settings must come from the frozen registry and be saved.

For each outer fold:

1. Load the frozen manifest and feature views.
2. Identify outer-training and outer-test patients from the frozen split.
3. Create deterministic patient-disjoint inner folds from outer-training patients.
4. Train/evaluate each candidate across inner folds.
5. Save every inner held-out prediction.
6. Aggregate to patient level with `patient_max` for candidate ranking.
7. Select the winning candidate using `nested_selection.py`.
8. Derive a final epoch/training schedule from inner validation only. A safe default for neural models is the median best epoch across inner folds.
9. Retrain the selected model on all outer-training rows for that fixed number of epochs without consulting outer-test outcomes.
10. Predict the outer test fold once.
11. Save checkpoint, preprocessor, validation leaderboard, inner OOF predictions, outer-test predictions, logs, and metadata.
12. Validate outputs against `output_contract.py` before reporting fold success.

For late fusion:

- Require validated CNV and image predictions for the same outer fold and exact row keys.
- Train stack-logit using inner OOF base predictions, not outer-test predictions.
- Save stacker coefficients/intercept and training-patient hashes.

Fail the fold if any model has missing rows, duplicate keys, patient leakage, feature mismatch, or artifact-contract failure.

## Phase 6: connect cross-fitted thresholds and calibration

During each outer-fold run:

1. Use the selected model's pooled inner-validation patient predictions.
2. Select the target-90%-specificity threshold.
3. Apply it unchanged to outer-test patient predictions.
4. Save threshold, achieved validation specificity, fallback status, and outer-test confusion counts.
5. Also evaluate threshold 0.5.

Calibration:

- Raw probabilities and raw Brier score are mandatory.
- If calibration is enabled, use one prespecified method, fitted only on pooled inner-validation predictions.
- Given the modest patient count, default to Platt scaling unless evidence supports isotonic calibration.
- Save calibrated probabilities separately.
- Do not replace raw probabilities.

Add integration tests that spy on patient IDs and prove no outer-test patient reaches selection, early stopping, threshold fitting, calibration, or preprocessing.

## Phase 7: build exact launch and monitoring tools

Add:

- `scripts/25_launch_lgd2_final_rerun.sh` or Python equivalent;
- `scripts/26_monitor_lgd2_final_rerun.py`;
- `scripts/27_collect_lgd2_final_oof.py`.

The launch tool must:

- use the frozen release and registry;
- create one external output root;
- refuse output paths inside Git;
- refuse overwriting completed folds;
- generate exact commands before submission;
- support one-fold smoke mode;
- submit primary families in dependency order;
- record Slurm job IDs and commands.

Recommended order:

1. CNV-only fold 1 smoke.
2. Image-only fold 1 smoke.
3. Early-fusion fold 1 smoke.
4. Intermediate-fusion fold 1 smoke including inner selection.
5. Validate all smoke artifacts.
6. Submit remaining outer folds for CNV, image, early, and intermediate.
7. Run late mean and stack-logit after base-model predictions complete.

Use the known model environment only after import/runtime validation. Do not install or alter environments automatically.

## Phase 8: smoke-test gate

Before full submission, require successful fold-1 runs for CNV, image, early fusion, and intermediate fusion.

Smoke acceptance criteria:

- all expected inner folds completed;
- no patient leakage;
- no outer-test use during training;
- validation leaderboard exists;
- selected configuration is recorded;
- outer-test predictions contain every expected fold-1 canonical row exactly once;
- checkpoint and preprocessor exist;
- output schema passes;
- probabilities are finite and non-constant;
- no missing features;
- output remains external;
- logs contain no ignored exceptions.

Create:

- `reports/thesis_ch1/lgd2_final_training_smoke_audit.csv`
- `reports/thesis_ch1/lgd2_final_training_smoke_audit.md`
- `reports/thesis_ch1/lgd2_final_training_smoke_warnings.md`

Do not launch folds 2-5 until this gate passes for all primary trained families.

## Phase 9: execute and complete the five-fold rerun

Run all five outer folds for:

- CNV-only random forest;
- image-only UNI2 ABMIL;
- early fusion `early_mean_mlp`;
- intermediate fusion;
- late fusion mean;
- late fusion stack-logit.

The executing agent must monitor jobs and collect results. A submitted job is not a completed model.

For case-specific failures:

- diagnose and retry only the failed fold;
- do not change scientific hyperparameters based on test performance;
- record every retry and reason.

For pipeline-wide failures:

- stop dependent jobs;
- fix the common cause;
- rerun the smoke gate if behavior changed.

Do not run supplementary co-attention until all required primary folds pass.

## Phase 10: collect and validate final OOF predictions

`scripts/27_collect_lgd2_final_oof.py` must:

1. Require five validated outer folds per primary family.
2. Concatenate outer-test rows only.
3. Reject duplicate canonical row keys.
4. Reject missing expected rows.
5. Verify each patient occurs in one outer fold.
6. Verify identical row and patient sets across every family.
7. Verify labels and folds against the frozen release.
8. Preserve raw logits/probabilities and calibrated probabilities separately.
9. Write a completeness JSON with hashes.

Expected per-family OOF coverage is 707 canonical rows and 150 patients unless a documented correction creates a new frozen release. Never silently evaluate differing subsets.

Create lightweight completeness reports:

- `reports/thesis_ch1/lgd2_final_oof_completeness.csv`
- `reports/thesis_ch1/lgd2_final_oof_completeness.md`
- `reports/thesis_ch1/lgd2_final_oof_warnings.md`

## Phase 11: generate final patient-level results

Add or update a manifest-driven script:

`scripts/28_make_lgd2_final_pre_event_results.py`

Generate new versioned reports, not overwrites of developmental outputs:

- `lgd2_final_pre_event_patient_metrics.csv/.md`;
- `lgd2_final_pre_event_model_comparison.csv/.md`;
- `lgd2_final_pre_event_paired_differences.csv/.md`;
- `lgd2_final_pre_event_cross_fitted_operating_points.csv/.md`;
- warnings and interpretation summary.

Primary patient-level metrics:

- AUPRC;
- ROC AUC;
- Brier score;
- sensitivity, specificity, PPV, NPV;
- balanced accuracy;
- TP, FP, TN, FN;
- detected/missed progressors;
- false positives per detected progressor;
- threshold used and validation fallback status;
- calibration/ECE where valid.

Primary contrasts with shared-patient bootstrap CIs:

- early fusion minus CNV-only;
- intermediate fusion minus CNV-only;
- late mean minus CNV-only;
- late stack-logit minus CNV-only.

Contextual contrasts:

- image-only minus CNV-only;
- each fusion model minus image-only;
- early versus intermediate and late fusion.

Rank by AUPRC first, then AUC, then Brier and false-positive burden. Do not declare superiority where paired confidence intervals include zero.

## Phase 12: retain interpretation-ready final artifacts

For the final CNV folds, retain externally:

- fitted estimator;
- ordered feature names;
- PCA/scaler where used;
- feature importance or permutation importance calculated without test-label tuning;
- genomic coordinates/build;
- compatible window-to-gene map reference.

For image/fusion folds, retain externally:

- checkpoints;
- UNI2 index and feature metadata;
- attention regeneration configuration;
- modality input identifiers;
- late stacker coefficients;
- optional fusion gating/ablation outputs.

After final OOF results exist, reselect interpretation cases. Do not assume the eight developmental cases retain the same TP/FN/rescue categories.

Histology and CNV interpretation regeneration is a subsequent stage, but the final rerun is incomplete if the artifacts required to perform it were not retained.

## Phase 13: update repository state only after evidence exists

Update:

- `PROJECT_STATE.md`;
- `README.md`;
- `docs/final_results_manifest.csv` and `.md`;
- `docs/experiment_plan.md`;
- `docs/data_contract.md`;
- timing/threshold limitation reports.

Clearly label old reports as developmental and the new strict pre-event nested-CV reports as final candidates.

Do not remove historical reports. Avoid contradictory active claims.

## Tests required

Use toy data for Git tests. Add at minimum:

- canonical ID to CNV-feature mapping;
- canonical ID to UNI2-index mapping;
- shared CNV profile does not collapse canonical rows;
- ambiguous mapping fails;
- missing feature fails;
- migrated model tensor-shape tests;
- old/new model compatibility tests where feasible;
- explicit train/validation/test separation;
- outer test never used for early stopping;
- patient-disjoint CNV tuning;
- patient-level inner candidate ranking;
- final epoch derived from inner validation only;
- late stacker trained without outer-test rows;
- full output-contract integration;
- five-fold OOF completeness;
- identical model row sets;
- cross-fitted threshold integration;
- external output and non-overwrite guards.

Run:

- `py_compile` for all changed Python;
- full lightweight `pytest` suite;
- one-fold real smoke tests;
- artifact validators;
- `./scripts/assert_no_data_tracked.sh`.

## Mandatory execution report

Write `docs/final_analysis_training_completion_execution_report.md` with:

1. Outcome: `COMPLETE`, `PARTIAL`, or `BLOCKED`.
2. Starting/final commits and branch/push/merge state.
3. Feature mapping sources and exact coverage.
4. Canonical manifest identity strategy.
5. Model registry and every candidate configuration.
6. Changes made to remove outer-test early stopping.
7. Changes made to enforce patient-disjoint CNV tuning.
8. Smoke-test results.
9. Slurm commands, job IDs, status and runtime.
10. Fold-by-fold completion matrix for every model.
11. Selected intermediate configuration per outer fold and validation metrics.
12. Validation-derived threshold per model/fold.
13. OOF completeness and equality checks.
14. Final metrics and paired contrasts, only if complete.
15. Artifact inventory for interpretation.
16. Tests and no-data guard.
17. Failures, retries and deviations.
18. What can and cannot scientifically be claimed.
19. Exact next command if incomplete.

Do not call the work complete when jobs are merely submitted, when any fold is missing, when models use different patients, or when final outputs fail the artifact contract.

## Definition of done

The task is complete only when:

1. CNV and UNI2 feature views cover all 707 frozen rows without ambiguity.
2. The corrected training manifest preserves every canonical modelling row.
3. The exact finite model registry is committed.
4. Outer-test data is absent from training, early stopping, selection, preprocessing, thresholding and calibration.
5. CNV inner tuning is patient-disjoint.
6. Fold-1 smoke runs pass for CNV, image, early and intermediate models.
7. All five folds complete for every primary family.
8. Late mean and stack-logit are built leakage-safely.
9. Final OOF predictions have identical 707-row/150-patient coverage across models.
10. Patient-level metrics, paired CIs and cross-fitted clinical metrics are generated.
11. Required checkpoints, preprocessors and interpretation artifacts remain externally available.
12. Tests and no-data guard pass.
13. The mandatory execution report contains paths, hashes, counts, job IDs and evidence.

## Permitted final scientific wording

Only after all definition-of-done items pass:

> In this matched internal cohort, adding histopathology to CNV improved patient-level prediction of future next-biopsy LGD2+ neoplastic progression under patient-disjoint nested cross-validation.

Qualify this according to paired confidence intervals. Do not call the endpoint cancer/OAC progression, do not claim that fusion helps every patient, and do not claim external generalisability without an external cohort.

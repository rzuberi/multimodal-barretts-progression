# LGD2+ Outer-Test OOF Prediction Schema

One CSV row per (model, outer fold, canonical row). Defined and enforced by
`src/barrett/evaluation/output_contract.py` (`REQUIRED_PREDICTION_COLUMNS`).
Validate with `scripts/19_validate_lgd2_training_artifacts.py`.

## Required columns

| Column | Type | Description |
|---|---|---|
| `run_id` | str | Unique final-rerun identifier. |
| `cohort_release_id` | str | Frozen strict pre-event cohort release id. |
| `cohort_hash` | str | Hash of the cohort release. |
| `split_release_id` | str | Frozen five-fold outer split release id. |
| `split_hash` | str | Hash of the split release. |
| `model_family` | str | e.g. cnv_only, histology_only, early_fusion, intermediate_fusion, late_fusion. |
| `model_name` | str | Concrete model instance name (unique per family/config). |
| `configuration_id` | str | Selected configuration id for this fold. |
| `feature_model` | str | Feature backbone (e.g. UNI2, none). |
| `fusion_type` | str | none / early / intermediate / late_mean / late_stack. |
| `cnv_representation` | str | CNV feature representation id. |
| `outer_fold` | int | Outer fold index (0..expected_folds-1). |
| `row_key` | str | Canonical modelling-unit row key (frozen comparison set). |
| `patient_id` | str | Patient identifier (never null). |
| `biopsy_id` | str | Biopsy identifier. |
| `sample_id` | str | Sample identifier. |
| `slide_id` | str | Slide identifier / reference. |
| `cnv_id` | str | CNV identifier / reference. |
| `y_true` | int | Endpoint label, in {0,1}. |
| `y_prob` | float | Raw predicted probability, in [0,1]. |
| `strict_pre_event_eligible` | bool | Strict pre-event primary-analysis eligibility. |
| `checkpoint_ref` | str | Reference to the fold checkpoint. |
| `config_ref` | str | Reference to the resolved config. |
| `seed` | int | Seed used for this fold. |
| `env_ref` | str | Reference to the environment/package export. |

## Optional / nullable columns

| Column | Type | Description |
|---|---|---|
| `y_logit` | float\|null | Raw logit where available. |
| `y_prob_calibrated` | float\|null | Calibrated probability when calibration is enabled. |

## Validation rules (fail closed)

- All required columns present.
- No duplicate `(model_name, outer_fold, row_key)` keys.
- No missing `patient_id`.
- Every model covers all `expected_folds` outer folds.
- `y_true` in {0,1}; `y_prob` in [0,1] and non-null.
- Across models, the set of `row_key` values must be identical
  (`validate_model_input_equality`).
- The run completeness manifest must resolve all
  `REQUIRED_RUN_ARTIFACT_KEYS` (`validate_run_completeness`).

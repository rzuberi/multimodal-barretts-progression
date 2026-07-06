# Data Contract

No data files are stored here. This document defines the minimum external table needed to continue.

## Minimum Master Cohort Columns

Required identifiers:

- `PatientID`
- `BiopsyID_int`
- `SampleID`
- `ImageAbsPath`
- `CNVAbsPath`

Required labels:

- `Progressor_label`
- `CurrentGradeNorm`
- `CurrentGradeInt`
- `NextBiopsyLabel`
- final endpoint column, either `NextBiopsyProgression_LGD2plus` or `NextBiopsyProgression_LGD3plus`

Required timing:

- `Date`
- `NextBiopsyDate`
- `DaysToNextBiopsy`
- `EventDate`
- `EventType`
- `DaysFromCurrentToEvent`
- `MonthsBeforeLastBiopsy`
- `AtRisk_1y`
- `AtRisk_2y`
- `AtRisk_3y`
- `AtRisk_4y`
- `AtRisk_5y`

Required cohort flags to generate:

- `has_image`
- `has_cnv`
- `included_in_multimodal_cohort`
- `included_in_cnv_only_cohort`
- `is_at_event`
- `is_early_prediction_sample`
- `exclusion_reason`

Required split/evaluation fields:

- `patient_id_for_split`
- `heldout_patient_id` for LOPO predictions
- `fold_id` only for non-LOPO CV analyses

## Early-Prediction Filter

The audit did not find one final reusable early-prediction condition. The proposed filter is:

```text
keep rows where Progressor_label == 0
or rows where Progressor_label == 1 and DaysFromCurrentToEvent > 0
```

For strict next-biopsy prediction, also require a known next-biopsy label:

```text
NextBiopsyLabel is not null
```

## Endpoint Rules To Lock

LGD3+ audited rule:

```text
NextBiopsyProgression_LGD3plus = 1
if NextBiopsyLabel >= 3
or NextBiopsyLabel == 2 and LGDStreakSoFar >= 2
```

LGD2+ strict next-biopsy table exists externally, but the final endpoint choice remains open.

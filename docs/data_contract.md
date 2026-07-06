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
- primary endpoint column: `NextBiopsyProgression_LGD2plus`
- supplementary endpoint column, when available: `NextBiopsyProgression_LGD3plus`

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
- `fold_id` for primary 5-fold patient-disjoint CV
- `heldout_patient_id` only for supplementary LOPO analyses

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

## Primary Endpoint Rule

LGD2+ is locked as primary:

```text
NextBiopsyProgression_LGD2plus = 1
if the next biopsy is HGD/IMC/OAC
or the next biopsy satisfies the second consecutive LGD event rule
```

Operationally, this corresponds to HGD/IMC/OAC or two consecutive LGD biopsies.

## Supplementary Endpoint Rule

LGD3+ audited rule:

```text
NextBiopsyProgression_LGD3plus = 1
if NextBiopsyLabel >= 3
or NextBiopsyLabel == 2 and LGDStreakSoFar >= 2
```

LGD3+ is retained only as supplementary / legacy / interpretability-supporting.

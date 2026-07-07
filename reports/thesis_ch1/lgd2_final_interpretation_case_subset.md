# LGD2+ Final Interpretation Case Subset

Eight lightweight case rows selected for the first thesis-figure interpretation regeneration stage.
Selection prioritised early-prediction-only, non-at-event cases with slide/CNV identifiers and all CNV/image/fusion probabilities available.

| case_id | category | patient_id | current_grade | DaysFromCurrentToEvent | true_label | CNV_probability | image_probability | early_fusion_probability | prediction_correctness_cnv | prediction_correctness_image | prediction_correctness_early_fusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_01 | A_true_positive_early | PR1/WSH/049 | NDBE | 730 | 1 | 0.423 | 0.954 | 0.993 | wrong | correct | correct |
| A_true_positive_early_02 | A_true_positive_early | PR1/BED/060 | LGD | 365 | 1 | 0.448 | 0.964 | 0.993 | wrong | correct | correct |
| B_false_negative_07 | B_false_negative | AHM1146 | NDBE | 396 | 1 | 0.527 | 0.104 | 0.285 | correct | wrong | wrong |
| C_false_positive_12 | C_false_positive | AD0594 | NDBE |  | 0 | 0.563 | 0.937 | 0.947 | wrong | wrong | wrong |
| E_cnv_rescue_19 | E_cnv_rescue | PR1/HIN/043 | NDBE |  | 1 | 0.529 | 0.462 | 0.947 | correct | wrong | correct |
| F_histology_rescue_24 | F_histology_rescue | PR1/BED/037 | NDBE | 1096 | 1 | 0.328 | 0.956 | 0.925 | wrong | correct | correct |
| G_fusion_hurt_26 | G_fusion_hurt | PR1/HIN/072 | ID | 646 | 1 | 0.105 | 0.860 | 0.375 | wrong | correct | wrong |
| I_modality_disagreement_37 | I_modality_disagreement | PR1/PTB/070 | LGD | 365 | 1 | 0.451 | 0.975 | 0.939 | wrong | correct | correct |

## Category coverage

- A_true_positive_early: 2
- B_false_negative: 1
- C_false_positive: 1
- E_cnv_rescue: 1
- F_histology_rescue: 1
- G_fusion_hurt: 1
- I_modality_disagreement: 1

## Notes

- References are basenames/IDs only; no raw WSI, CNV matrix, checkpoint, feature tensor, or mounted private path is committed.
- Interpretation outputs remain missing and require external regeneration.

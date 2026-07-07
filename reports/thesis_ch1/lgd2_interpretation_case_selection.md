# LGD2+ Interpretation Case Selection

Endpoint: `NextBiopsyProgression_LGD2plus`.
Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
Primary model for selection: `lgd2_early_fusion_uni2` (`early_mean_mlp`), patient_max.
Modality comparison: `lgd2_cnv_core` (CNV) and `lgd2_image_uni2` abmil (image).

Thresholds: default 0.5; high-confidence >= 0.75; low-confidence <= 0.25; strong disagreement |CNV-image| >= 0.4.

## Cases per category

| category | n | patient_ids |
|---|---:|---|
| A_true_positive_early | 5 | PR1/WSH/049, PR1/BED/060, PR1/WSH/081, AHM1110, AHM0952 |
| B_false_negative | 5 | AH0328, AHM1146, AHM0896, PR1/ADH/069, AHM1557 |
| C_false_positive | 5 | AHM1807, AD0594, PR1/HIN/064, AD0644, AHM1813 |
| D_true_negative | 3 | AHM0844, AHM1318, AHM0722 |
| E_cnv_rescue | 3 | PR1/HIN/043, AD0169, AHM1939 |
| F_histology_rescue | 3 | PR1/PTB/070, PR1/BED/060, PR1/BED/037 |
| G_fusion_hurt | 3 | AHM1146, PR1/HIN/072, AD0775X |
| H_agree_negative | 3 | AHM0844, AHM1318, AHM0722 |
| H_agree_positive | 3 | PR1/WSH/081, PR1/HIN/044, AHM1110 |
| I_modality_disagreement | 5 | PR1/WSH/049, PR1/BED/060, AHM0753, PR1/PTB/070, AHM0268 |

## Selected cases

| category | patient | grade | next label | days_to_event | true | CNV p | image p | fusion p | at 0.5 | set | case timing |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| A_true_positive_early | PR1/WSH/049 | NDBE | 0.0 | 730.000 | 1 | 0.423 | 0.954 | 0.993 | 1 | early_prediction_only | pre_event |
| A_true_positive_early | PR1/BED/060 | LGD | 2.0 | 365.000 | 1 | 0.448 | 0.964 | 0.993 | 1 | early_prediction_only | pre_event |
| A_true_positive_early | PR1/WSH/081 | ID | 3.0 | 365.000 | 1 | 0.610 | 0.863 | 0.992 | 1 | early_prediction_only | pre_event |
| A_true_positive_early | AHM1110 | ID | 2.0 | 778.000 | 1 | 0.575 | 0.888 | 0.960 | 1 | early_prediction_only | pre_event |
| A_true_positive_early | AHM0952 | NDBE | 3.0 | 788.000 | 1 | 0.609 | 0.751 | 0.955 | 1 | early_prediction_only | pre_event |
| B_false_negative | AH0328 | LGD | 2.0 | 179.000 | 1 | 0.286 | 0.471 | 0.153 | 0 | early_prediction_only | pre_event |
| B_false_negative | AHM1146 | NDBE | 4.0 | 396.000 | 1 | 0.527 | 0.104 | 0.285 | 0 | early_prediction_only | pre_event |
| B_false_negative | AHM0896 | NDBE | 4.0 | 850.000 | 1 | 0.362 | 0.206 | 0.324 | 0 | early_prediction_only | pre_event |
| B_false_negative | PR1/ADH/069 | ID | 0.0 | 885.000 | 1 | 0.471 | 0.445 | 0.352 | 0 | early_prediction_only | pre_event |
| B_false_negative | AHM1557 | NDBE | 0.0 |  | 1 | 0.350 | 0.401 | 0.358 | 0 | early_prediction_only | missing |
| C_false_positive | AHM1807 | LGD | 0.0 |  | 0 | 0.474 | 0.702 | 0.956 | 1 | early_prediction_only | missing |
| C_false_positive | AD0594 | NDBE | 2.0 |  | 0 | 0.563 | 0.937 | 0.947 | 1 | early_prediction_only | missing |
| C_false_positive | PR1/HIN/064 | LGD | 1.0 |  | 0 | 0.377 | 0.798 | 0.895 | 1 | early_prediction_only | missing |
| C_false_positive | AD0644 | ID | 1.0 |  | 0 | 0.514 | 0.896 | 0.826 | 1 | early_prediction_only | missing |
| C_false_positive | AHM1813 | NDBE | 0.0 |  | 0 | 0.451 | 0.634 | 0.817 | 1 | early_prediction_only | missing |
| D_true_negative | AHM0844 | NDBE | 0.0 |  | 0 | 0.319 | 0.042 | 0.045 | 0 | early_prediction_only | missing |
| D_true_negative | AHM1318 | NDBE | 0.0 |  | 0 | 0.298 | 0.252 | 0.048 | 0 | early_prediction_only | missing |
| D_true_negative | AHM0722 | NDBE | 0.0 |  | 0 | 0.147 | 0.259 | 0.060 | 0 | early_prediction_only | missing |
| E_cnv_rescue | PR1/HIN/043 | NDBE | 4.0 |  | 1 | 0.529 | 0.462 | 0.947 | 1 | early_prediction_only | missing |
| E_cnv_rescue | AD0169 | NDBE | 0.0 |  | 0 | 0.492 | 0.896 | 0.480 | 0 | early_prediction_only | missing |
| E_cnv_rescue | AHM1939 | NDBE | 2.0 |  | 0 | 0.490 | 0.631 | 0.421 | 0 | early_prediction_only | missing |
| F_histology_rescue | PR1/PTB/070 | LGD | 3.0 | 365.000 | 1 | 0.451 | 0.975 | 0.939 | 1 | early_prediction_only | pre_event |
| F_histology_rescue | PR1/BED/060 | LGD | 2.0 | 365.000 | 1 | 0.448 | 0.964 | 0.993 | 1 | early_prediction_only | pre_event |
| F_histology_rescue | PR1/BED/037 | NDBE | 3.0 | 1096.000 | 1 | 0.328 | 0.956 | 0.925 | 1 | early_prediction_only | pre_event |
| G_fusion_hurt | AHM1146 | NDBE | 4.0 | 396.000 | 1 | 0.527 | 0.104 | 0.285 | 0 | early_prediction_only | pre_event |
| G_fusion_hurt | PR1/HIN/072 | ID | 3.0 | 646.000 | 1 | 0.105 | 0.860 | 0.375 | 0 | early_prediction_only | pre_event |
| G_fusion_hurt | AD0775X | ID | 0.0 | 1696.000 | 1 | 0.515 | 0.789 | 0.435 | 0 | early_prediction_only | pre_event |
| H_agree_positive | PR1/WSH/081 | ID | 3.0 | 365.000 | 1 | 0.610 | 0.863 | 0.992 | 1 | early_prediction_only | pre_event |
| H_agree_positive | PR1/HIN/044 | NDBE | 3.0 |  | 1 | 0.560 | 0.914 | 0.989 | 1 | early_prediction_only | missing |
| H_agree_positive | AHM1110 | ID | 2.0 | 778.000 | 1 | 0.575 | 0.888 | 0.960 | 1 | early_prediction_only | pre_event |
| H_agree_negative | AHM0844 | NDBE | 0.0 |  | 0 | 0.319 | 0.042 | 0.045 | 0 | early_prediction_only | missing |
| H_agree_negative | AHM1318 | NDBE | 0.0 |  | 0 | 0.298 | 0.252 | 0.048 | 0 | early_prediction_only | missing |
| H_agree_negative | AHM0722 | NDBE | 0.0 |  | 0 | 0.147 | 0.259 | 0.060 | 0 | early_prediction_only | missing |
| I_modality_disagreement | PR1/WSH/049 | NDBE | 0.0 | 730.000 | 1 | 0.423 | 0.954 | 0.993 | 1 | early_prediction_only | pre_event |
| I_modality_disagreement | PR1/BED/060 | LGD | 2.0 | 365.000 | 1 | 0.448 | 0.964 | 0.993 | 1 | early_prediction_only | pre_event |
| I_modality_disagreement | AHM0753 | LGD | 2.0 | 539.000 | 1 | 0.525 | 0.955 | 0.941 | 1 | early_prediction_only | pre_event |
| I_modality_disagreement | PR1/PTB/070 | LGD | 3.0 | 365.000 | 1 | 0.451 | 0.975 | 0.939 | 1 | early_prediction_only | pre_event |
| I_modality_disagreement | AHM0268 | LGD | 3.0 | 357.000 | 1 | 0.482 | 0.903 | 0.938 | 1 | early_prediction_only | pre_event |

## Notes

- Selection prioritises `early_prediction_only` (excludes `DaysFromCurrentToEvent == 0`).
- `all_samples` cases are added only where a category is under-filled by early-prediction patients.
- At-event cases (days == 0) are detection examples only, never early-prediction examples.
- All interpretation outputs are MISSING for LGD2+ and require regeneration (see `lgd2_interpretation_regeneration_plan.md`).
- External references are basenames only; no absolute paths or raw data are emitted.

# LGD2+ WSI Case Manifest

Lightweight manifest for the 8 selected LGD2+ thesis interpretation cases. It references external WSI feature/checkpoint locations but does not copy slides, tiles, features, or checkpoints into Git.

- Cases: 8
- Early-prediction-only cases: 8
- At-event cases: 0
- Cases with feature refs: 8
- Cases with warnings: 0

## Case Table

| case_id | case_category | patient_id | slide_basename | feature_model | fold | image_model | fusion_model | is_early_prediction_only | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_01 | A_true_positive_early | PR1/WSH/049 | PS01 8837 2A B2326.ndpi | uni2 | 2 | abmil | early_mean_mlp | True |  |
| A_true_positive_early_02 | A_true_positive_early | PR1/BED/060 | 13H 20009427 B1 PR1 BED 060 B2842 1.ndpi | uni2 | 2 | abmil | early_mean_mlp | True |  |
| B_false_negative_07 | B_false_negative | AHM1146 | S09 26616 2 1 G3497.ndpi | uni2 | 3 | abmil | early_mean_mlp | True |  |
| C_false_positive_12 | C_false_positive | AD0594 | S05 28850 2 1 G3497.ndpi | uni2 | 2 | abmil | early_mean_mlp | True |  |
| E_cnv_rescue_19 | E_cnv_rescue | PR1/HIN/043 | PS14.52598 P3628 1 B2506 11.ndpi | uni2 | 4 | abmil | early_mean_mlp | True |  |
| F_histology_rescue_24 | F_histology_rescue | PR1/BED/037 | 11H 11088 B2819.ndpi | uni2 | 2 | abmil | early_mean_mlp | True |  |
| G_fusion_hurt_26 | G_fusion_hurt | PR1/HIN/072 | PS14 58170 4 PR1 HIN 072 B2842 1.ndpi | uni2 | 1 | abmil | early_mean_mlp | True |  |
| I_modality_disagreement_37 | I_modality_disagreement | PR1/PTB/070 | H14 19755 A1 B2819.ndpi | uni2 | 2 | abmil | early_mean_mlp | True |  |

## Warnings

- None at manifest-build level.

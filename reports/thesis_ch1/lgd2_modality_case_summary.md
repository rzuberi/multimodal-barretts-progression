# LGD2+ Modality Case Summary

Probability-only interpretation for the final selected thesis-figure subset. No heavy data, WSI tiles, checkpoints, or external outputs are read.

| case_id | category | cnv_prob | image_prob | fusion_prob | fusion_minus_cnv | fusion_minus_image | abs_cnv_image_disagreement | dominant_modality_hint | fusion_helped | fusion_hurt | all_modalities_agree | case_interpretation_sentence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_01 | A_true_positive_early | 0.423 | 0.954 | 0.993 | 0.570 | 0.039 | 0.531 | fusion_closer_to_image | True | False | False | Fusion is correct where at least one unimodal model is wrong. |
| A_true_positive_early_02 | A_true_positive_early | 0.448 | 0.964 | 0.993 | 0.545 | 0.030 | 0.515 | fusion_closer_to_image | True | False | False | Fusion is correct where at least one unimodal model is wrong. |
| B_false_negative_07 | B_false_negative | 0.527 | 0.104 | 0.285 | -0.242 | 0.181 | 0.423 | fusion_closer_to_image | False | True | False | Fusion is wrong despite at least one correct unimodal model. |
| C_false_positive_12 | C_false_positive | 0.563 | 0.937 | 0.947 | 0.384 | 0.010 | 0.374 | fusion_closer_to_image | False | False | True | All modalities agree on the risk class. |
| E_cnv_rescue_19 | E_cnv_rescue | 0.529 | 0.462 | 0.947 | 0.419 | 0.485 | 0.066 | modalities_similar | True | False | False | Fusion is correct where at least one unimodal model is wrong. |
| F_histology_rescue_24 | F_histology_rescue | 0.328 | 0.956 | 0.925 | 0.597 | -0.031 | 0.627 | fusion_closer_to_image | True | False | False | Fusion is correct where at least one unimodal model is wrong. |
| G_fusion_hurt_26 | G_fusion_hurt | 0.105 | 0.860 | 0.375 | 0.271 | -0.485 | 0.755 | fusion_closer_to_cnv | False | True | False | Fusion is wrong despite at least one correct unimodal model. |
| I_modality_disagreement_37 | I_modality_disagreement | 0.451 | 0.975 | 0.939 | 0.488 | -0.036 | 0.524 | fusion_closer_to_image | True | False | False | Fusion is correct where at least one unimodal model is wrong. |

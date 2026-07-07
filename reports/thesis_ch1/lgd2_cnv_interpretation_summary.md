# LGD2+ CNV Interpretation Summary

This summary reads lightweight external CNV interpretation outputs if present. It does not copy raw CNV matrices, checkpoints, SHAP arrays, or large figures into Git.

## Selected cases

| case_id | case_category | cnv_id | cnv_probability | fusion_probability | cnv_prediction_correct | fusion_prediction_correct | top_cnv_windows | top_genes | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_01 | A_true_positive_early | SLX-12451.D712_D501 | 0.423 | 0.993 | wrong | correct | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |
| A_true_positive_early_02 | A_true_positive_early | SLX-12455.D701_D504 | 0.448 | 0.993 | wrong | correct | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |
| B_false_negative_07 | B_false_negative | SLX-13692.D703_D508 | 0.527 | 0.285 | correct | wrong | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |
| C_false_positive_12 | C_false_positive | SLX-13692.D711_D505 | 0.563 | 0.947 | wrong | wrong | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |
| E_cnv_rescue_19 | E_cnv_rescue | SLX-12451.D710_D506 | 0.529 | 0.947 | correct | correct | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |
| F_histology_rescue_24 | F_histology_rescue | SLX-12455.D710_D507 | 0.328 | 0.925 | wrong | correct | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |
| G_fusion_hurt_26 | G_fusion_hurt | SLX-12455.D705_D507 | 0.105 | 0.375 | wrong | wrong | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |
| I_modality_disagreement_37 | I_modality_disagreement | SLX-12455.D707_D507 | 0.451 | 0.939 | wrong | correct | MISSING | MISSING | Missing external CNV interpretation outputs for this case. |

## Recurrent regions / genes

- Not available yet; external top-window/top-gene outputs are missing.

## CNV-only versus fusion-supported cases

- Probability-level CNV/fusion correctness is included in the table.
- Region-level comparison requires regenerated external top-window/top-gene outputs.

## Limitations

- Missing rows mean the external CNV interpretation stage has not been run or its outputs were not supplied.
- Gene/window summaries are lightweight derivatives only; raw CNV matrices and model artefacts remain external.

## Warnings

- External CNV interpretation output directory not found: analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance
- A_true_positive_early_01: Missing external CNV interpretation outputs for this case.
- A_true_positive_early_02: Missing external CNV interpretation outputs for this case.
- B_false_negative_07: Missing external CNV interpretation outputs for this case.
- C_false_positive_12: Missing external CNV interpretation outputs for this case.
- E_cnv_rescue_19: Missing external CNV interpretation outputs for this case.
- F_histology_rescue_24: Missing external CNV interpretation outputs for this case.
- G_fusion_hurt_26: Missing external CNV interpretation outputs for this case.
- I_modality_disagreement_37: Missing external CNV interpretation outputs for this case.

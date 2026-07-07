# LGD2+ Histology Interpretation Summary

This summary reads lightweight external histology interpretation outputs when present. It does not copy WSI files, tile images, feature tensors, checkpoints, or large attention maps into Git.

- Cases: 8
- Cases with top-patch refs: 0
- Cases with attention summaries: 0
- Cases with warnings: 8

## Selected Cases

| case_id | case_category | patient_id | slide_id | image_probability | fusion_probability | top_patches_generated | attention_tile_scores_generated | heatmaps_overlays_generated | top_patch_refs | attention_summary | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_01 | A_true_positive_early | PR1/WSH/049 | PS01 8837 2A B2326.ndpi | 0.9540758728981018 | 0.9934176206588744 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |
| A_true_positive_early_02 | A_true_positive_early | PR1/BED/060 | 13H 20009427 B1 PR1 BED 060 B2842 1.ndpi | 0.9635841250419616 | 0.9931897521018982 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |
| B_false_negative_07 | B_false_negative | AHM1146 | S09 26616 2 1 G3497.ndpi | 0.1040728092193603 | 0.2848115861415863 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |
| C_false_positive_12 | C_false_positive | AD0594 | S05 28850 2 1 G3497.ndpi | 0.9372631311416626 | 0.9474844932556152 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |
| E_cnv_rescue_19 | E_cnv_rescue | PR1/HIN/043 | PS14.52598 P3628 1 B2506 11.ndpi | 0.4624266326427459 | 0.9472943544387816 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |
| F_histology_rescue_24 | F_histology_rescue | PR1/BED/037 | 11H 11088 B2819.ndpi | 0.955672323703766 | 0.9251195788383484 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |
| G_fusion_hurt_26 | G_fusion_hurt | PR1/HIN/072 | PS14 58170 4 PR1 HIN 072 B2842 1.ndpi | 0.859920084476471 | 0.3750661611557007 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |
| I_modality_disagreement_37 | I_modality_disagreement | PR1/PTB/070 | H14 19755 A1 B2819.ndpi | 0.9751919507980348 | 0.9389178156852722 | False | False | False | MISSING | MISSING | Missing external histology interpretation outputs for this case. |

## Interpretation Sentences

- A_true_positive_early_01: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.9540758728981018, 0.9934176206588744).
- A_true_positive_early_02: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.9635841250419616, 0.9931897521018982).
- B_false_negative_07: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.1040728092193603, 0.2848115861415863).
- C_false_positive_12: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.9372631311416626, 0.9474844932556152).
- E_cnv_rescue_19: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.4624266326427459, 0.9472943544387816).
- F_histology_rescue_24: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.955672323703766, 0.9251195788383484).
- G_fusion_hurt_26: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.859920084476471, 0.3750661611557007).
- I_modality_disagreement_37: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.9751919507980348, 0.9389178156852722).

## Global Warnings

- External histology output directory not found: analysis/lgd2_interpretation_regeneration_20260707/histology

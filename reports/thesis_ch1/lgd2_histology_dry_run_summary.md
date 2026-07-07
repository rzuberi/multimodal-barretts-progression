# LGD2+ Histology Interpretation Summary

This summary reads lightweight external histology interpretation outputs when present. It does not copy WSI files, tile images, feature tensors, checkpoints, or large attention maps into Git.

- Cases: 2
- Cases with top-patch refs: 2
- Cases with attention summaries: 0
- Cases with warnings: 0

## Selected Cases

| case_id | case_category | patient_id | slide_id | image_probability | fusion_probability | command_run | command_success | top_patches_generated | tile_scores_generated | attention_scores_generated | heatmap_generated | overlay_generated | number_of_top_patches | number_of_tiles_scored | top_patch_refs | attention_summary | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_02 | A_true_positive_early | PR1/BED/060 | 13H 20009427 B1 PR1 BED 060 B2842 1.ndpi | 0.9635841250419616 | 0.9931897521018982 | True | True | True | True | True | True | True | 1 | 256 | A_true_positive_early/PR1_BED_060__SLX-12455.D701_D504__fold2/top_tiles_grid.png | MISSING |  |
| B_false_negative_07 | B_false_negative | AHM1146 | S09 26616 2 1 G3497.ndpi | 0.1040728092193603 | 0.2848115861415863 | True | True | True | True | True | True | True | 1 | 256 | B_false_negative/AHM1146__SLX-13692.D703_D508__fold3/top_tiles_grid.png | MISSING |  |

## Interpretation Sentences

- A_true_positive_early_02: regenerated histology outputs highlight A_true_positive_early/PR1_BED_060__SLX-12455.D701_D504__fold2/top_tiles_grid.png; compare image probability 0.9635841250419616 with fusion probability 0.9931897521018982.
- B_false_negative_07: regenerated histology outputs highlight B_false_negative/AHM1146__SLX-13692.D703_D508__fold3/top_tiles_grid.png; compare image probability 0.1040728092193603 with fusion probability 0.2848115861415863.

## Global Warnings

- None.

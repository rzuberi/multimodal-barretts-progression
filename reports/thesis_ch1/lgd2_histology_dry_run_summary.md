# LGD2+ Histology Interpretation Summary

This summary reads lightweight external histology interpretation outputs when present. It does not copy WSI files, tile images, feature tensors, checkpoints, or large attention maps into Git.

- Cases: 2
- Cases with top-patch refs: 0
- Cases with attention summaries: 0
- Cases with warnings: 2

## Selected Cases

| case_id | case_category | patient_id | slide_id | image_probability | fusion_probability | command_run | command_success | top_patches_generated | tile_scores_generated | attention_scores_generated | heatmap_generated | overlay_generated | number_of_top_patches | number_of_tiles_scored | top_patch_refs | attention_summary | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_true_positive_early_02 | A_true_positive_early | PR1/BED/060 | 13H 20009427 B1 PR1 BED 060 B2842 1.ndpi | 0.9635841250419616 | 0.9931897521018982 | True | False | False | False | False | False | False |  |  | MISSING | MISSING | Missing external histology interpretation outputs for this case.; Command failed before WSI/feature/checkpoint loading: ModuleNotFoundError: No module named 'torch' |
| B_false_negative_07 | B_false_negative | AHM1146 | S09 26616 2 1 G3497.ndpi | 0.1040728092193603 | 0.2848115861415863 | False | False | False | False | False | False | False |  |  | MISSING | MISSING | Missing external histology interpretation outputs for this case.; Not attempted because first dry-run case failed. |

## Interpretation Sentences

- A_true_positive_early_02: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.9635841250419616, 0.9931897521018982).
- B_false_negative_07: LGD2+ histology outputs are not regenerated yet; current evidence is limited to image/fusion probabilities (0.1040728092193603, 0.2848115861415863).

## Global Warnings

- External histology output directory not found: ../analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi

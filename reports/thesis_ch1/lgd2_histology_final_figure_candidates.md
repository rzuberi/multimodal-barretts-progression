# LGD2+ Histology Final Figure Candidates

All 8 selected LGD2+ ABMIL histology interpretation cases are retained as Chapter 1 figure candidates for later final selection during writing.

Heavy outputs remain external. Git tracks only this lightweight candidate manifest; it does not contain WSI files, tile images, heatmaps, feature tensors, checkpoints, or full tile-score dumps.

External output root:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/`

Per-case candidate image files: `top_tiles_grid.png`, `bottom_tiles_grid.png`, `heatmap_overlay.png`, `heatmap_overlay_shuffle.png`.

## Candidate Cases

| case_id | category | patient_id | true_label | image_prob | fusion_prob | tiles | status | external_output_ref |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `A_true_positive_early_01` | `A_true_positive_early` | `PR1/WSH/049` | `1` | `0.954` | `0.993` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/A_true_positive_early/PR1_WSH_049__SLX-12451.D712_D501__fold2` |
| `A_true_positive_early_02` | `A_true_positive_early` | `PR1/BED/060` | `1` | `0.964` | `0.993` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/A_true_positive_early/PR1_BED_060__SLX-12455.D701_D504__fold2` |
| `B_false_negative_07` | `B_false_negative` | `AHM1146` | `1` | `0.104` | `0.285` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/B_false_negative/AHM1146__SLX-13692.D703_D508__fold3` |
| `C_false_positive_12` | `C_false_positive` | `AD0594` | `0` | `0.937` | `0.947` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/C_false_positive/AD0594__SLX-13692.D711_D505__fold2` |
| `E_cnv_rescue_19` | `E_cnv_rescue` | `PR1/HIN/043` | `1` | `0.462` | `0.947` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/E_cnv_rescue/PR1_HIN_043__SLX-12451.D710_D506__fold4` |
| `F_histology_rescue_24` | `F_histology_rescue` | `PR1/BED/037` | `1` | `0.956` | `0.925` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/F_histology_rescue/PR1_BED_037__SLX-12455.D710_D507__fold2` |
| `G_fusion_hurt_26` | `G_fusion_hurt` | `PR1/HIN/072` | `1` | `0.860` | `0.375` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/G_fusion_hurt/PR1_HIN_072__SLX-12455.D705_D507__fold1` |
| `I_modality_disagreement_37` | `I_modality_disagreement` | `PR1/PTB/070` | `1` | `0.975` | `0.939` | `256` | `INCLUDE_FOR_LATER_SELECTION` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/I_modality_disagreement/PR1_PTB_070__SLX-12455.D707_D507__fold2` |

## Use In Chapter Drafting

- Include all 8 cases as the current histology interpretation candidate pool.
- Choose final thesis panels later once the full Chapter 1 narrative, CNV interpretation, and fusion case-story requirements are clear.
- Prefer the visually strongest subset for main figures; move remaining valid cases to supplementary material if useful.
- Do not make biological claims from these image manifests alone; use clinician/pathology review and matched CNV/fusion evidence before final interpretation.

## Current Recommendation

Retain all 8 as candidates. Next missing interpretation work is LGD2+ CNV windows/genes and fusion/composite case summaries for the same case set.

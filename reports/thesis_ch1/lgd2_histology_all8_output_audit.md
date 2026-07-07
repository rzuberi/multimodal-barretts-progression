# LGD2+ Histology All-8 Output Audit

- Cases audited: 8
- Structurally valid cases: 8
- Failed cases: 0

## Case Status

| case_id | category | valid | tiles_scored | top_score_range | output_ref |
| --- | --- | --- | --- | --- | --- |
| `A_true_positive_early_01` | `A_true_positive_early` | `True` | `256` | `0.0119531; 0.011362263; 0.011329324; 0.011317418; 0.011065992` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/A_true_positive_early/PR1_WSH_049__SLX-12451.D712_D501__fold2` |
| `A_true_positive_early_02` | `A_true_positive_early` | `True` | `256` | `0.04553629; 0.044974424; 0.032111093; 0.02829201; 0.026603399` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/A_true_positive_early/PR1_BED_060__SLX-12455.D701_D504__fold2` |
| `B_false_negative_07` | `B_false_negative` | `True` | `256` | `0.01266778; 0.011998858; 0.011351064; 0.0109072095; 0.010797691` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/B_false_negative/AHM1146__SLX-13692.D703_D508__fold3` |
| `C_false_positive_12` | `C_false_positive` | `True` | `256` | `0.031084266; 0.02795765; 0.027039673; 0.026914874; 0.026739066` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/C_false_positive/AD0594__SLX-13692.D711_D505__fold2` |
| `E_cnv_rescue_19` | `E_cnv_rescue` | `True` | `256` | `0.04644224; 0.039828185; 0.034539554; 0.026262792; 0.02582529` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/E_cnv_rescue/PR1_HIN_043__SLX-12451.D710_D506__fold4` |
| `F_histology_rescue_24` | `F_histology_rescue` | `True` | `256` | `0.04520655; 0.041244384; 0.03707991; 0.033216745; 0.023280129` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/F_histology_rescue/PR1_BED_037__SLX-12455.D710_D507__fold2` |
| `G_fusion_hurt_26` | `G_fusion_hurt` | `True` | `256` | `0.031467002; 0.027484288; 0.02278748; 0.02139542; 0.020030105` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/G_fusion_hurt/PR1_HIN_072__SLX-12455.D705_D507__fold1` |
| `I_modality_disagreement_37` | `I_modality_disagreement` | `True` | `256` | `0.057571203; 0.047479805; 0.043931946; 0.04367443; 0.043125942` | `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training/analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/I_modality_disagreement/PR1_PTB_070__SLX-12455.D707_D507__fold2` |

## Notes

- Audits parse `metadata.json` and `tile_scores.csv` and verify PNG files can be opened by PIL.
- No images, tile grids, heatmaps, overlays, or full tile-score dumps are committed to Git.

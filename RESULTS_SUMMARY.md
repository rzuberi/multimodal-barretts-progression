# Results Summary

## Core baseline findings

- Stable public leaderboard rows: `315`
- Complete rows: `304`
- Task leaders: `20` multimodal, `1` image
- Canonical progression headline: `NextBiopsyProgression_LGD3plus` multimodal `0.854` vs image `0.834`

The baseline evidence still lives in:

- [data_snapshots/headline_task_auc_comparison.csv](data_snapshots/headline_task_auc_comparison.csv)
- [data_snapshots/task_leaders.csv](data_snapshots/task_leaders.csv)
- [data_snapshots/model_leaderboard_binary_auc.csv](data_snapshots/model_leaderboard_binary_auc.csv)

## Additional experiment highlights

- AtRisk no-leak EPYC relaunch: best MoE AUCs were `0.8468` (`AtRisk_1y`), `0.8168` (`AtRisk_3y`), and `0.8391` (`AtRisk_5y`)
- Aggregation study: multimodal led `NextBiopsyProgression_LGD3plus` at biopsy (`0.848`) and patient (`0.886`) level, while image led `Progressor_label` at biopsy (`0.795`) and patient (`0.915`) level
- Critical next-biopsy evaluation: patient-level AUCs were modest across all model groups, with best MoE at `0.601`
- Distance-to-progression study: image reached the farthest horizon (`-5+`), CNV had the largest never-caught fraction (`48.3%`), multimodal reduced that to `20.7%`
- Modality-weight study: `Progressor_label` showed negative correlation between days-to-progression and image weight (`rho=-0.2069`, `p=0.0491`)

New derived public tables:

- [data_snapshots/atrisk_noleak_headline_models.csv](data_snapshots/atrisk_noleak_headline_models.csv)
- [data_snapshots/critical_biopsy_headline.csv](data_snapshots/critical_biopsy_headline.csv)
- [data_snapshots/biopsy_patient_aggregation_best.csv](data_snapshots/biopsy_patient_aggregation_best.csv)
- [data_snapshots/distance_to_progression_summary.csv](data_snapshots/distance_to_progression_summary.csv)
- [data_snapshots/modality_weight_shift_summary.csv](data_snapshots/modality_weight_shift_summary.csv)

## Main interpretation

The updated public record supports a narrower and more defensible claim than a generic “multimodal always wins” story. Multimodal models remain strongest on several canonical progression tasks, but endpoint definition, aggregation level, and derived expert routing all materially change which model family looks best.

## Figures

- [figures/figure1_baseline_headline_auc.png](figures/figure1_baseline_headline_auc.png)
- [figures/figure3_atrisk_noleak_auc.png](figures/figure3_atrisk_noleak_auc.png)
- [figures/figure4_biopsy_patient_aggregation_auc.png](figures/figure4_biopsy_patient_aggregation_auc.png)
- [figures/figure5_critical_biopsy_false_negatives.png](figures/figure5_critical_biopsy_false_negatives.png)
- [figures/figure6_distance_to_progression.png](figures/figure6_distance_to_progression.png)
- [figures/figure7_modality_weight_shift.png](figures/figure7_modality_weight_shift.png)

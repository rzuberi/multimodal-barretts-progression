# Results Summary

## New Patient-Level Headline

The strongest new public headline is the corrected strict patient-level next-biopsy endpoint:

- endpoint: `NextBiopsyProgression_LGD2plus`
- best multimodal: `0.926`
- best image-only: `0.865`
- best CNV-only: `0.854`
- best routing / MoE: `0.887`

Source:

- [data_snapshots/strict_lgd2_patient_level_headline.csv](data_snapshots/strict_lgd2_patient_level_headline.csv)

## Data-Efficiency Result

For `Progressor_label`, reduced pathology input still preserved the patient-level signal:

- best image-only baseline: `0.879`
- best full multimodal baseline: `0.922`
- best reduced-patch multimodal: `0.927`
- best simplified CNV-only model: `0.869`

Source:

- [data_snapshots/progressor_patient_level_data_efficiency.csv](data_snapshots/progressor_patient_level_data_efficiency.csv)

## Modality-Ablation Result

Strict patient-level ablations support a real multimodal contribution:

- `NextBiopsyProgression_LGD2plus`: baseline `0.926`, shuffle image `0.861`, shuffle CNV `0.888`, shuffle both `0.727`
- `Progressor_label`: baseline `0.918`, shuffle image `0.878`, shuffle CNV `0.879`, shuffle both `0.704`

Source:

- [data_snapshots/strict_lgd2_patient_level_modality_ablation.csv](data_snapshots/strict_lgd2_patient_level_modality_ablation.csv)

## Earlier Public Material Still In Repo

The repo still includes the earlier aggregate-only public snapshot:

- [data_snapshots/headline_task_auc_comparison.csv](data_snapshots/headline_task_auc_comparison.csv)
- [data_snapshots/atrisk_noleak_headline_models.csv](data_snapshots/atrisk_noleak_headline_models.csv)
- [data_snapshots/biopsy_patient_aggregation_best.csv](data_snapshots/biopsy_patient_aggregation_best.csv)
- [data_snapshots/distance_to_progression_summary.csv](data_snapshots/distance_to_progression_summary.csv)
- [data_snapshots/modality_weight_shift_summary.csv](data_snapshots/modality_weight_shift_summary.csv)

## Main Interpretation

The updated public record supports a simple story:

1. Under a stricter patient-level progression rule, a plain multimodal model still performs best.
2. For at least one patient-level endpoint, reduced pathology input can work almost as well or slightly better than the full-pathology baseline.
3. Image and CNV are not redundant, because ablating both causes a much larger drop than ablating either one alone.

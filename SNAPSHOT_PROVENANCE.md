# Data Boundary And Provenance

## Scope

This repo is a public, aggregate-only summary of the Barrett's multimodal modelling programme. It is intended to preserve the key result tables, figures, and high-level experimental comparisons without exposing any patient-level material.

## Checked-in aggregate sources used for the refresh

Campaign summaries:

- [source_aggregates/campaigns/lgd3plus_fullcoverage_global_results_summary.csv](source_aggregates/campaigns/lgd3plus_fullcoverage_global_results_summary.csv)
- [source_aggregates/campaigns/lgd3plus_fullcoverage_best_model_per_condition.csv](source_aggregates/campaigns/lgd3plus_fullcoverage_best_model_per_condition.csv)
- [source_aggregates/campaigns/cnv_masked_alltasks_global_results_summary.csv](source_aggregates/campaigns/cnv_masked_alltasks_global_results_summary.csv)
- [source_aggregates/campaigns/cnv_masked_alltasks_best_model_per_condition.csv](source_aggregates/campaigns/cnv_masked_alltasks_best_model_per_condition.csv)

Report-level aggregates:

- [source_aggregates/reports/atrisk_noleak_top_models.csv](source_aggregates/reports/atrisk_noleak_top_models.csv)
- [source_aggregates/reports/critical_biopsy_sample_level.csv](source_aggregates/reports/critical_biopsy_sample_level.csv)
- [source_aggregates/reports/critical_biopsy_patient_level.csv](source_aggregates/reports/critical_biopsy_patient_level.csv)
- [source_aggregates/reports/biopsy_patient_aggregation_combined.csv](source_aggregates/reports/biopsy_patient_aggregation_combined.csv)
- [source_aggregates/reports/progressor_detection_horizon_summary.csv](source_aggregates/reports/progressor_detection_horizon_summary.csv)
- [source_aggregates/reports/progressor_never_caught_summary.csv](source_aggregates/reports/progressor_never_caught_summary.csv)
- [source_aggregates/reports/fusion_rescue_hurt_counts.csv](source_aggregates/reports/fusion_rescue_hurt_counts.csv)
- [source_aggregates/reports/modality_weight_binned_stats.csv](source_aggregates/reports/modality_weight_binned_stats.csv)
- [source_aggregates/reports/modality_weight_spearman.csv](source_aggregates/reports/modality_weight_spearman.csv)

## Explicit exclusions

Not included in this public repo:

- any `derived_master.csv`
- any row-level prediction exports
- any patient-level detail files
- trajectory files containing case-level sequences
- any report artifact with patient identifiers embedded in the table body

Examples of excluded internal artifact types:

- `patients_*`
- `*_detail.csv`
- `group_membership_*`
- `preprogression_*`
- `focus_cases_*`

## Why some analyses appear only in aggregate form

Some internal reports were scientifically useful but unsafe to publish verbatim. For those analyses, only a de-identified aggregate reduction was carried over. Two examples:

- fusion rescue or hurt analysis: only group counts were retained

## Rebuild path

The repo is runnable at the public aggregate layer:

```bash
pip install -r requirements.txt
python3 scripts/build_public_snapshot.py
```

This regenerates:

- derived CSV summaries in [data_snapshots](data_snapshots)
- static figures in [figures](figures)

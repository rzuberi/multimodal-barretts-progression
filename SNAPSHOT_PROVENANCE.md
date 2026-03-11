# Snapshot Provenance

## Public version boundary

- Last public commit before this refresh: `5f986668aa7919fb2b38c4738e22bd5beb9093fe`
- Commit date: `2026-03-04 20:51:28 UTC`
- Branch status before this refresh: `HEAD` matched `origin/main`
- Baseline snapshot stored in this repo: `2026-03-04T20:14:40Z`

The March 11, 2026 update preserves that baseline and adds aggregate-safe results produced between March 4 and March 10, 2026.

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
- [source_aggregates/reports/progressor_union_label_summary.csv](source_aggregates/reports/progressor_union_label_summary.csv)
- [source_aggregates/reports/post_local_grade_shift_summary.csv](source_aggregates/reports/post_local_grade_shift_summary.csv)
- [source_aggregates/reports/post_snapshot_experiment_log.csv](source_aggregates/reports/post_snapshot_experiment_log.csv)

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
- post-local grade comparison: only cohort-level counts were retained

## Rebuild path

The repo is runnable at the public aggregate layer:

```bash
pip install -r requirements.txt
python3 scripts/build_public_snapshot.py
```

This regenerates:

- derived CSV summaries in [data_snapshots](data_snapshots)
- static figures in [figures](figures)
- update metadata in [data_snapshots/update_metadata.json](data_snapshots/update_metadata.json)

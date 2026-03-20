# Multimodal Barrett's Progression

## Very Short Explanation

This project is about trying to tell which Barrett's oesophagus patients look more likely to get worse over time. We use two kinds of information from the same biopsy visit: patterns from histopathology images and patterns from copy-number DNA data. The goal is not to replace doctors, but to see whether combining these signals can help identify higher-risk patients earlier.

## What This Public Repo Contains

This GitHub repo is aggregate-only. It contains summary tables, figures, and short writeups, but it does not contain patient identifiers, row-level predictions, slide embeddings, or private master tables.

Included:

- aggregate leaderboard tables
- de-identified patient-level summary tables
- static figures and narrative interpretation

Excluded:

- patient or sample identifiers
- row-level predictions
- private derived cohort tables
- any file that could reconstruct patient trajectories

## Main Update In This Snapshot

The March 2026 public update adds three things that were not in the earlier public snapshot:

1. A stricter patient-level next-biopsy analysis where progression is defined more conservatively.
2. A patient-level data-efficiency result showing that reduced pathology input can still work well for one endpoint.
3. Patient-level modality-ablation evidence showing that both image and CNV signals matter.

## New Headline Results

### 1) Strict patient-level next-biopsy progression still looks strong

For the corrected strict endpoint `NextBiopsyProgression_LGD2plus`, the best patient-level model was still a plain multimodal model:

- best multimodal: patient AUC `0.926`
- best image-only: patient AUC `0.865`
- best CNV-only: patient AUC `0.854`
- best routing / MoE: patient AUC `0.887`

This is the cleanest current headline because it uses the stricter progression definition and patient-level evaluation.

Source table:

- [data_snapshots/strict_lgd2_patient_level_headline.csv](data_snapshots/strict_lgd2_patient_level_headline.csv)

### 2) For the progressor task, less pathology data can still work

On `Progressor_label`, the best reduced-patch multimodal model slightly exceeded the best full multimodal baseline at patient level:

- best image-only baseline: `0.879`
- best full multimodal baseline: `0.922`
- best reduced-patch multimodal: `0.927`
- best simplified CNV-only model: `0.869`

So the public story here is not just “bigger models on more data win”. For one important patient-level endpoint, a leaner pathology input still kept the signal.

Source table:

- [data_snapshots/progressor_patient_level_data_efficiency.csv](data_snapshots/progressor_patient_level_data_efficiency.csv)

### 3) Modality ablations support a real multimodal signal

Patient-level H200 ablations were rerun under the strict rule. The pattern was:

- `NextBiopsyProgression_LGD2plus`: baseline `0.926`, shuffle image `0.861`, shuffle CNV `0.888`, shuffle both `0.727`
- `Progressor_label`: baseline `0.918`, shuffle image `0.878`, shuffle CNV `0.879`, shuffle both `0.704`

That means both modalities are contributing useful information, and destroying both causes a large collapse in patient-level performance.

Source table:

- [data_snapshots/strict_lgd2_patient_level_modality_ablation.csv](data_snapshots/strict_lgd2_patient_level_modality_ablation.csv)

## Earlier Public Snapshot Still Included

The older public material is still useful and remains in the repo:

- canonical `LGD3plus` next-biopsy snapshot tables
- AtRisk no-leak tables
- biopsy-to-patient aggregation tables
- distance-to-progression and modality-reliance summaries

Those files still matter for the broader story, but they are no longer the cleanest single headline after the stricter patient-level refresh.

## Suggested Reading Order

1. [data_snapshots/strict_lgd2_patient_level_headline.csv](data_snapshots/strict_lgd2_patient_level_headline.csv)
2. [data_snapshots/progressor_patient_level_data_efficiency.csv](data_snapshots/progressor_patient_level_data_efficiency.csv)
3. [data_snapshots/strict_lgd2_patient_level_modality_ablation.csv](data_snapshots/strict_lgd2_patient_level_modality_ablation.csv)
4. [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)
5. [SNAPSHOT_PROVENANCE.md](SNAPSHOT_PROVENANCE.md)

## Older Figures And Tables

The earlier public figures and tables are still available:

- [figures/figure1_baseline_headline_auc.png](figures/figure1_baseline_headline_auc.png)
- [figures/figure3_atrisk_noleak_auc.png](figures/figure3_atrisk_noleak_auc.png)
- [figures/figure4_biopsy_patient_aggregation_auc.png](figures/figure4_biopsy_patient_aggregation_auc.png)
- [figures/figure6_distance_to_progression.png](figures/figure6_distance_to_progression.png)
- [figures/figure7_modality_weight_shift.png](figures/figure7_modality_weight_shift.png)

## Reproducibility

This repo is reproducible at the aggregate-report layer, not at the private data reconstruction layer. The checked-in CSVs and figures are meant to preserve the public scientific summary without exposing private cohort data.

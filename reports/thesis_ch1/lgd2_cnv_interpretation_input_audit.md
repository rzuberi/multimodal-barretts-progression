# LGD2+ CNV Interpretation Input Audit

Audit for the 8 selected LGD2+ interpretation cases. No raw CNV data was copied or modified.

## Selected CNV IDs

- `A_true_positive_early_01`: `SLX-12451.D712_D501` (A_true_positive_early)
- `A_true_positive_early_02`: `SLX-12455.D701_D504` (A_true_positive_early)
- `B_false_negative_07`: `SLX-13692.D703_D508` (B_false_negative)
- `C_false_positive_12`: `SLX-13692.D711_D505` (C_false_positive)
- `E_cnv_rescue_19`: `SLX-12451.D710_D506` (E_cnv_rescue)
- `F_histology_rescue_24`: `SLX-12455.D710_D507` (F_histology_rescue)
- `G_fusion_hurt_26`: `SLX-12455.D705_D507` (G_fusion_hurt)
- `I_modality_disagreement_37`: `SLX-12455.D707_D507` (I_modality_disagreement)

## Required inputs

| input | status | path / basename | safe without copying into Git? | notes |
|---|---|---|---|---|
| selected case CNV IDs | FOUND | SLX-12451.D712_D501; SLX-12455.D701_D504; SLX-13692.D703_D508; SLX-13692.D711_D505; SLX-12451.D710_D506; SLX-12455.D710_D507; SLX-12455.D705_D507; SLX-12455.D707_D507 | yes | Basenames only in selected case subset. |
| CNV prediction files | FOUND | data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/cnv_anchor/runs/cnv/all_samples/core_binary/cv/predictions_all_samples_cnv_random_forest_windows_armdiff_plus_arms_plus_cx_NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv | yes, read-only | Saved probabilities exist and were already used for metrics/case selection. |
| CNV campaign root | FOUND | data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/cnv_anchor | yes, read-only | Primary LGD2+ CNV model family root. |
| CNV feature/window matrix | MISSING / NOT VALIDATED | Not found in audited files | unknown | Required by old importance scripts; do not infer from prediction CSVs. |
| saved CNV model/checkpoint/estimator | MISSING / NOT VALIDATED | Not found in audited files | unknown | cnv_feature_importance.py appears to refit/aggregate via worklists; no simple selected-case saved estimator path was validated. |
| LGD2+ feature importance source | MISSING | MISSING | n/a | Manifest marks LGD2+ CNV interpretability as MISSING. |
| LGD2+ window-to-gene map | MISSING | No selected-case LGD2+ gene map found | n/a | Legacy LGD3+/older maps exist only as support. |
| external output directory | PLANNED | analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance | yes, external only | Directory does not need to exist before the summary loader runs. |
| legacy support file | FOUND | analysis/clinician_figures_nextbiopsyprogression_batch10/cnv_top_genes_batch10_cnv_only.csv | read-only; do not reuse as primary LGD2+ | Legacy/supplementary only. |
| legacy support file | FOUND | analysis/clinician_figures_nextbiopsyprogression_batch10/cnv_top_windows_batch10_cnv_only.csv | read-only; do not reuse as primary LGD2+ | Legacy/supplementary only. |
| legacy support file | FOUND | analysis/cnv_explainability/admin/importance_worklist.csv | read-only; do not reuse as primary LGD2+ | Legacy/supplementary only. |
| legacy support file | FOUND | analysis/cnv_explainability/binmaps/binmap_windows_5mb.csv | read-only; do not reuse as primary LGD2+ | Legacy/supplementary only. |
| legacy support file | FOUND | analysis/cnv_explainability/binmaps/binmap_arm.csv | read-only; do not reuse as primary LGD2+ | Legacy/supplementary only. |

## Warnings

- LGD2+ CNV top-window/top-gene/importance outputs were not found for the selected cases.
- Existing clinician CNV gene/window files are LGD3+/legacy and cannot support primary LGD2+ biological claims.
- `cnv_feature_importance.py` is not a simple no-training selected-case extractor; it supports worklist/row/aggregate modes and imports model-building/fitting utilities.
- Optional CNV regeneration was not run in this stage because required estimator/feature-matrix paths were not validated.

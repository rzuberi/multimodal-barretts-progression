# LGD2+ Interpretation External Run Plan

Final selected subset: `reports/thesis_ch1/lgd2_final_interpretation_case_subset.csv`.

External output root to use for regenerated artefacts:

`analysis/lgd2_interpretation_regeneration_20260707/`

Do not write raw interpretation artefacts into Git. Only reduced summaries should be copied back into `reports/thesis_ch1/`.

## Per-case plan

| case_id | category | CNV outputs | histology outputs | multimodal outputs | external output directory | commit to Git? |
|---|---|---|---|---|---|---|
| `A_true_positive_early_01` | early TP | top windows, genes, CNV profile | top patches, tile-score table, heatmap | probability panel, modality comparison | `analysis/lgd2_interpretation_regeneration_20260707/A_true_positive_early_01/` | summaries only |
| `A_true_positive_early_02` | early TP | top windows, genes, CNV profile | top patches, tile-score table, heatmap | probability panel, modality comparison | `analysis/lgd2_interpretation_regeneration_20260707/A_true_positive_early_02/` | summaries only |
| `B_false_negative_07` | false negative | top windows, genes, CNV profile | top patches, tile-score table, heatmap | missed-progressor panel | `analysis/lgd2_interpretation_regeneration_20260707/B_false_negative_07/` | summaries only |
| `C_false_positive_12` | false positive | top windows, genes, CNV profile | top patches, tile-score table, heatmap | false-positive burden panel | `analysis/lgd2_interpretation_regeneration_20260707/C_false_positive_12/` | summaries only |
| `E_cnv_rescue_19` | CNV rescue | top windows, genes, feature importance | optional top patches | rescue label and probability panel | `analysis/lgd2_interpretation_regeneration_20260707/E_cnv_rescue_19/` | summaries only |
| `F_histology_rescue_24` | histology rescue | optional CNV window audit | top patches, tile-score table, heatmap | rescue label and probability panel | `analysis/lgd2_interpretation_regeneration_20260707/F_histology_rescue_24/` | summaries only |
| `G_fusion_hurt_26` | fusion hurt | CNV windows for correct unimodal signal | histology patches for correct unimodal signal | hurt/fail panel | `analysis/lgd2_interpretation_regeneration_20260707/G_fusion_hurt_26/` | summaries only |
| `I_modality_disagreement_37` | modality disagreement | CNV windows | histology patches | disagreement/arbitration panel | `analysis/lgd2_interpretation_regeneration_20260707/I_modality_disagreement_37/` | summaries only |

## CNV outputs

Target model: `lgd2_cnv_core` / `cnv_random_forest`.

Old LGD3+/legacy scripts to adapt:

- `scripts/cnv_feature_importance.py`
- `scripts/cnv_bins_to_genes.py`
- `scripts/run_cnv_gene_mapping_batch.py`
- `scripts/export_clinician_cnv_window_gene_summaries.py`
- `scripts/run_patientlevel_cnv_shap.py`

Inputs needed:

- selected case `cnv_id` from `lgd2_final_interpretation_case_subset.csv`;
- LGD2+ campaign root from `docs/final_results_manifest.csv`;
- external CNV feature/mask files and trained estimator artefacts.

Outputs:

- top CNV windows;
- window-to-gene maps;
- feature importances / coefficients / SHAP if available;
- CNV profile plot if existing script supports it.

Commit policy:

- top-window/top-gene summary CSV/MD may be committed if small and deidentified;
- CNV matrices, profile plots with private detail, SHAP arrays, and model artefacts stay external.

## Histology outputs

Target model: `lgd2_image_uni2` / `abmil`, plus `lgd2_early_fusion_uni2` / `early_mean_mlp`.

Old LGD3+/legacy scripts to adapt:

- `scripts/build_wsi_explainability_index.py`
- `scripts/build_wsi_case_manifest.py`
- `scripts/run_wsi_explainability_case.py`
- `scripts/launch_wsi_explainability_array.py`
- `scripts/plot_attention_spread_curves.py`
- `scripts/generate_clinician_nextbiopsyprogression_batch.py`

Inputs needed:

- selected case `slide_id` basename;
- external WSI/feature paths from the LGD2+ master cohort;
- external model checkpoint/features for the selected image/fusion models.

Outputs:

- top patches;
- attention/tile-score table;
- heatmap or overlay if supported;
- attention-spread summary.

Commit policy:

- tile-score tables and small aggregate summaries may be committed;
- WSI-derived images, patch tiles, heatmaps, feature tensors, and checkpoints stay external.

## Multimodal outputs

Target model: `lgd2_early_fusion_uni2` / `early_mean_mlp`.

Old scripts to adapt:

- `scripts/analyze_progressor_fusion_rescue_hurt.py`
- `scripts/add_modality_dependence_batch10.py`
- `scripts/generate_clinician_nextbiopsyprogression_batch.py`

Already available in Git:

- CNV/image/fusion probability comparison in `lgd2_modality_case_summary.csv`;
- rescue/hurt/fail category labels in `lgd2_final_interpretation_case_subset.csv`.

Still external:

- modality-dependence score regenerated from model internals;
- composite figure panels with WSI/CNV visual artefacts.

## Lightweight CNV run decision

No CNV interpretation was run in this stage. The relevant scripts require external trained estimator artefacts and feature/mask files; they may be safe later, but the exact command must be validated manually against the LGD2+ campaign before execution.

Candidate command template:

```bash
python scripts/cnv_feature_importance.py \
  --manifest reports/thesis_ch1/lgd2_final_interpretation_case_subset.csv \
  --endpoint NextBiopsyProgression_LGD2plus \
  --model cnv_random_forest \
  --output-root analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance
```

Treat this as a plan, not a verified command.


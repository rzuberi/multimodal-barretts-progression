# LGD2+ Interpretation Regeneration Plan

What needs to be regenerated for the cases selected in
`lgd2_interpretation_case_selection.csv` (endpoint `NextBiopsyProgression_LGD2plus`).

Nothing here has been run. All interpretation outputs for LGD2+ are currently
MISSING (see `lgd2_interpretability_availability.md`). The LGD3+ scripts named below
exist in the training repo and produced the equivalent LGD3+ artefacts; they must be
re-pointed at the LGD2+ campaign and cohort. Every regenerated artefact stays external
or is reduced to a lightweight summary before any commit.

Per-case inputs come from the case CSV columns: `patient_id`, `sample_id`,
`biopsy_id`, `slide_external_ref` (WSI basename), `cnv_external_ref` (CNV basename),
`current_grade`, `days_from_current_to_event`, `case_timing`, and the three
modality probabilities.

External roots (relative to experiment root; do not commit):
- Master cohort: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`
- LGD2+ campaign: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/{uni2,gigapath,cnv_anchor}`

## Histology outputs to regenerate

Applies to image/multimodal cases — categories A, C, F, H, I (any case with a
`slide_external_ref`). Prioritise the primary fusion model `lgd2_early_fusion_uni2`
(`early_mean_mlp`) and its image-only counterpart `lgd2_image_uni2` (`abmil`).

Outputs per case:
- top patches (ranked tile list);
- attention heatmap / slide overlay;
- tile-score table;
- attention-spread summary.

Old scripts likely needed (from the training repo, re-point to the LGD2+ campaign):
- `scripts/build_wsi_explainability_index.py` and `scripts/build_wsi_case_manifest.py` — build the per-case WSI/feature index.
- `scripts/run_wsi_explainability_case.py` / `scripts/launch_wsi_explainability_array.py` — generate top patches + attention heatmaps per case.
- `scripts/plot_attention_spread_curves.py` — attention-spread summary.
- `scripts/generate_clinician_nextbiopsyprogression_batch.py` — clinician-facing selected-case figures.

Per selected case, record: `patient_id`, `sample_id`/`slide_external_ref`, selected
model, external slide/features path, script used. Keep only a lightweight tile-score
CSV / attention-spread summary in Git; heatmaps and patch images stay external.

## CNV outputs to regenerate

Applies to CNV/multimodal cases — categories A, B, E, G, H, I (any case with a
`cnv_external_ref`). Prioritise `lgd2_cnv_core` (`cnv_random_forest`,
`windows_armdiff_plus_arms_plus_cx`) and the fusion CNV branch.

Outputs per case:
- top CNV windows;
- gene maps;
- model coefficients / feature importances (+ optional SHAP);
- CNV profile plot.

Old scripts likely needed:
- `scripts/cnv_feature_importance.py` — per-model window importances / coefficients.
- `scripts/cnv_bins_to_genes.py` / `scripts/run_cnv_gene_mapping_batch.py` / `scripts/export_clinician_cnv_window_gene_summaries.py` — window→gene maps.
- `scripts/run_patientlevel_cnv_shap.py` — patient-level SHAP.
- `scripts/build_cnv_masks.py` / `scripts/cnv_masked_curves.py` — CNV masking evidence.
- `scripts/plot_cnv_attention_spread_curves.py` — CNV region spread.

Per selected case, record: `patient_id`, `cnv_external_ref`/CNV path, selected model,
script used. Keep only a lightweight top-window / top-gene CSV in Git; raw CNV
matrices and profile plots stay external.

## Multimodal outputs to regenerate

Applies to fusion cases — categories E, F, G, H, I especially. For each:
- CNV-only probability (`cnv_only_prob`, present in the case CSV);
- image-only probability (`image_only_prob`, present);
- fusion probability (`early_fusion_prob`, present);
- modality-dependence score (needs regeneration);
- rescue / hurt / fail category (already assigned via `case_category`);
- case-figure plan (side-by-side CNV profile + attention heatmap + probability panel).

Old scripts likely needed:
- `scripts/analyze_progressor_fusion_rescue_hurt.py` — formal rescue/hurt/fail at LGD2+.
- `scripts/add_modality_dependence_batch10.py` — per-case modality-dependence score.
- `scripts/generate_clinician_nextbiopsyprogression_batch.py` — combined case figures.

The three unimodal/fusion probabilities already exist in the case CSV, so the
disagreement and rescue/hurt/fail assignments are reproducible now; only the
per-case modality-dependence score and the composite figures need regeneration.

## Notes

- Regeneration needs external checkpoints and feature tensors — none enter Git.
- Re-point every script from the LGD3+ cohort/campaign to the LGD2+ campaign above; do not reuse LGD3+ artefacts as primary.
- `lgd2_foundation_combo` stays excluded until its `patient_id` join is validated.

# LGD2+ Interpretation Script Adaptation Checklist

No old interpretation script was refactored or run in this stage. This checklist records what must change before LGD2+ regeneration.

| script path | LGD3+/legacy output | inputs required | LGD2+ changes needed | safe to reuse? | heavy-data risk | external output path | status |
|---|---|---|---|---|---|---|---|
| `scripts/build_wsi_explainability_index.py` | WSI/feature lookup index | master cohort, WSI paths, feature roots | point to LGD2+ master/campaign and selected subset | yes, with checks | may expose WSI paths | `analysis/lgd2_interpretation_regeneration_20260707/wsi_index/` | needs minor edits |
| `scripts/build_wsi_case_manifest.py` | per-case WSI manifest | selected cases, master cohort, feature paths | use `lgd2_final_interpretation_case_subset.csv` | yes, with checks | may expose WSI paths | `analysis/lgd2_interpretation_regeneration_20260707/wsi_case_manifest/` | ready after path review |
| `scripts/run_wsi_explainability_case.py` | top patches, attention maps | model checkpoint, features, WSI/slide ID | re-point endpoint/model to LGD2+ `early_mean_mlp`/`abmil` | not directly | patch images/heatmaps | per-case external folder | needs manual review |
| `scripts/launch_wsi_explainability_array.py` | batch WSI explainability | case manifest, scheduler, checkpoints | use selected 8-case manifest only | not directly | large images/logs | `analysis/lgd2_interpretation_regeneration_20260707/wsi_array/` | needs manual review |
| `scripts/plot_attention_spread_curves.py` | attention-spread plots | tile-score outputs | re-point to LGD2+ tile scores | yes, after tile outputs exist | plots may be generated | `analysis/lgd2_interpretation_regeneration_20260707/attention_spread/` | needs upstream outputs |
| `scripts/generate_clinician_nextbiopsyprogression_batch.py` | clinician-facing composite figures | WSI/CNV outputs, probabilities | use LGD2+ selected subset and model labels | not directly | figures/images | `analysis/lgd2_interpretation_regeneration_20260707/composite_figures/` | needs manual review |
| `scripts/cnv_feature_importance.py` | CNV windows/importances | trained CNV model, masks/features | re-point to LGD2+ `cnv_random_forest` and selected cases | maybe | model artefacts/arrays | `analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance/` | needs manual review |
| `scripts/cnv_bins_to_genes.py` | CNV window gene maps | window definitions, gene annotation | use LGD2+ top windows | yes | low if outputs are summaries | `analysis/lgd2_interpretation_regeneration_20260707/cnv_gene_maps/` | ready after top windows |
| `scripts/run_cnv_gene_mapping_batch.py` | batched gene maps | top-window tables | use selected subset windows | yes | low if summaries only | `analysis/lgd2_interpretation_regeneration_20260707/cnv_gene_maps/` | needs minor edits |
| `scripts/export_clinician_cnv_window_gene_summaries.py` | clinician CNV gene summaries | mapped CNV windows | use LGD2+ selected subset | yes | low if summary only | `analysis/lgd2_interpretation_regeneration_20260707/cnv_gene_summaries/` | ready after top windows |
| `scripts/run_patientlevel_cnv_shap.py` | patient-level CNV SHAP | model/checkpoint, features | re-point endpoint/model and selected cases | not directly | SHAP arrays may be large | `analysis/lgd2_interpretation_regeneration_20260707/cnv_shap/` | needs manual review |
| `scripts/build_cnv_masks.py` | CNV mask definitions | CNV feature schema | no case-specific change; confirm LGD2+ mask | yes | low | `analysis/lgd2_interpretation_regeneration_20260707/cnv_masks/` | ready |
| `scripts/cnv_masked_curves.py` | CNV masking curves | predictions/features/model | re-point to LGD2+ selected cases | maybe | arrays/plots | `analysis/lgd2_interpretation_regeneration_20260707/cnv_masked_curves/` | needs manual review |
| `scripts/plot_cnv_attention_spread_curves.py` | CNV region spread plots | CNV importance outputs | use LGD2+ top-window outputs | yes after inputs exist | plots | `analysis/lgd2_interpretation_regeneration_20260707/cnv_region_spread/` | needs upstream outputs |
| `scripts/analyze_progressor_fusion_rescue_hurt.py` | rescue/hurt/fail case report | model predictions, cohort labels | re-point to LGD2+ predictions already summarized | yes | low for CSV summaries | `analysis/lgd2_interpretation_regeneration_20260707/fusion_rescue_hurt/` | ready |
| `scripts/add_modality_dependence_batch10.py` | modality-dependence score | fusion model internals/checkpoints | use selected 8 cases and LGD2+ early-fusion model | not directly | model internals/features | `analysis/lgd2_interpretation_regeneration_20260707/modality_dependence/` | needs manual review |

Scripts that generate WSI-derived images, patch tiles, heatmaps, checkpoints, feature tensors, SHAP arrays, or raw CNV matrices must write only to external folders. Git should receive only small CSV/Markdown summaries.


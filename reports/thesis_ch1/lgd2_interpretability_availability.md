# LGD2+ Interpretability Availability

Audit of existing interpretation evidence for the primary endpoint
`NextBiopsyProgression_LGD2plus` (HGD/IMC/OAC or two consecutive LGD biopsies).

Sources inspected: `docs/final_results_manifest.csv`, `docs/lgd2_completion_audit.md`,
`reports/thesis_ch1/*`. Model prediction/summary files for the locked LGD2+ campaign
`campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251` were checked for the
presence of interpretation outputs (attention/top-patch/CNV region exports).

Bottom line: **no LGD2+-specific interpretation output exists yet.** All histology,
CNV, and multimodal interpretation artefacts found are LGD3+ and must be treated as
legacy/supplementary support only. Manifest rows `lgd2_histology_interpretability`,
`lgd2_cnv_interpretability`, and `lgd2_fusion_help_hurt_fail` are all status `MISSING`.

## Histology interpretation availability

| Model result_id | attention maps | top-patch CSV | tile ranking | slide heatmap | clinician figure | patch scores | attention spread | LGD2+ status |
|---|---|---|---|---|---|---|---|---|
| `lgd2_image_uni2` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_image_gigapath` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_image_virchow2` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_early_fusion_uni2` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_early_fusion_gigapath` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_intermediate_fusion_*` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_coattention_*` | no | no | no | no | no | no | no | MISSING for LGD2+ |

Only sample/patient prediction files (`y_true`, `y_prob`, `y_pred`) exist for these
models. No attention weights, tile scores, or heatmaps are exported at the LGD2+ endpoint.

## CNV interpretation availability

| Model result_id | top CNV windows | gene maps | feature importance | coefficients | SHAP | masks | permutation importance | LGD2+ status |
|---|---|---|---|---|---|---|---|---|
| `lgd2_cnv_core` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_early_fusion_uni2` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| `lgd2_early_fusion_gigapath` | no | no | no | no | no | no | no | MISSING for LGD2+ |
| best multimodal rows | no | no | no | no | no | no | no | MISSING for LGD2+ |

CNV masking evidence exists at the *metric* level (manifest `lgd2_modality_ablation_shuffle`,
`lgd2_cnv_variants`) but no per-case CNV window/gene/importance export tied to the LGD2+ endpoint.

## Multimodal interpretation availability

| Output | LGD2+ status | Notes |
|---|---|---|
| modality-dependence score per case | MISSING for LGD2+ | shuffle/ablation exists at metric level only (`lgd2_modality_ablation_shuffle`) |
| fusion rescue/hurt/fail report | MISSING for LGD2+ | LGD3+ reports exist (see legacy section) |
| image-vs-CNV disagreement cases | MISSING for LGD2+ | derivable from saved predictions (this stage produces it) |
| CNV-only / image-only / multimodal prob per patient | DERIVABLE | saved prediction files exist; `scripts/05_select_lgd2_interpretation_cases.py` builds it |
| selected case tables | MISSING for LGD2+ | produced by this stage |
| confidence/calibration per case | DERIVABLE | probabilities exist; Brier/ECE already at cohort level |

## LGD3+ interpretation outputs usable only as legacy/supplementary support

From manifest `lgd3_interpretability_support` (status `REVIEW_MANUALLY`, endpoint
`NextBiopsyProgression_LGD3plus`) — **do not present as primary LGD2+ interpretation**:

- `analysis/clinician_figures_nextbiopsyprogression_batch10/` — LGD3+ top patches, clinician figures.
- `analysis/explainability/` — LGD3+ histology explainability.
- `analysis/cnv_explainability/` — LGD3+ CNV windows/genes.
- `reports/progressor_fusion_rescue_hurt_*` — LGD3+/older rescue-hurt case reports.
- `reports/modality_weight_time_to_progression_*` — LGD3+/older modality-weight-over-time.

These demonstrate the pipeline can produce the required artefact types, but were computed
on a different endpoint and cohort definition and cannot back LGD2+ claims.

## Missing LGD2+ interpretation outputs

1. Histology attention maps / top-patch CSVs / tile-score tables / slide heatmaps / attention-spread summaries — for `lgd2_image_*`, `lgd2_early_fusion_*`, `lgd2_intermediate_fusion_*`, `lgd2_coattention_*`.
2. CNV top windows / gene maps / feature importances / coefficients / SHAP / masks / permutation importance — for `lgd2_cnv_core` and best multimodal rows.
3. Fusion help/hurt/fail case report and per-case modality-dependence score at the LGD2+ endpoint.
4. Clinician-facing selected-case figures at the LGD2+ endpoint.

## Exact external paths found

Relative to the experiment root (repo parent; do not commit these files):

- Master cohort: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`
- LGD2+ campaign root: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`
- Prediction files (saved `y_prob`, exist for all core models): `.../core_lvl2/{cnv_anchor,uni2,gigapath,virchow2}/runs/{cnv,image,multimodal}/all_samples/*/cv/predictions_all_samples_*_NextBiopsyProgression_LGD2plus_*_fold{1..5}.csv`
- Modality shuffle/ablation support: `data/foundation_grid_runs/campaign_lgd2_h200_patient_signal_lgd2_20260319/patchselect/uni2_signal/{baseline,shuffle_image,shuffle_cnv,shuffle_both}/`
- LGD3+ legacy interpretation (supplementary only): `analysis/clinician_figures_nextbiopsyprogression_batch10/`, `analysis/explainability/`, `analysis/cnv_explainability/`

No interpretation-output path exists for the LGD2+ endpoint.

## Warnings and manual-review items

- All LGD2+ interpretation artefacts require regeneration; none can be reused directly.
- LGD3+ interpretation must be labelled legacy/supplementary in the thesis, never primary.
- `lgd2_foundation_combo` prediction files lack validated `patient_id`; excluded from case selection until the join is validated.
- Master `CNVAbsPath`/`ImageAbsPath` are absolute private paths (`/scratchc/...`); commit only basenames/relative references, never absolute mounts.
- Regeneration requires model checkpoints and feature tensors that are external and must not enter Git.

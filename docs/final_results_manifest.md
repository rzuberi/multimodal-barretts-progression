# Final Results Manifest — Barrett Chapter 1

## Purpose

This manifest links the clean GitHub repository to external HPC cohort/result folders without tracking raw data, WSIs, model checkpoints, large prediction files, or full result directories.

All paths below are external paths relative to the Barrett training root:

`/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training`

The machine-readable companion file is `docs/final_results_manifest.csv`. Future scripts should read that CSV and then load only the external files they need.

## Locked Chapter 1 analysis

- Primary endpoint: `NextBiopsyProgression_LGD2plus`.
- Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
- Primary evaluation: 5-fold patient-disjoint CV.
- Primary reporting level: patient-level.
- Supplementary reporting: biopsy-level and sample/slide-level.
- LGD3+: supplementary / legacy / interpretability-supporting.
- LOPO: not primary for now.

## Main LGD2+ final-candidate results

### Strict pre-event nested-CV rerun

These are the current final candidates. The older campaign rows below remain developmental context.

| result family | external path | OOF predictions | status | intended use |
|---|---|---|---|---|
| CNV-only RF | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/cnv_only/` | `oof/cnv_only_oof_predictions.csv` | `FINAL_CANDIDATE` | Primary baseline |
| UNI2 ABMIL | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/image_only/` | `oof/image_only_oof_predictions.csv` | `FINAL_CANDIDATE` | Image baseline |
| Early fusion | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/early_fusion/` | `oof/early_fusion_oof_predictions.csv` | `FINAL_CANDIDATE` | Main comparison |
| Intermediate fusion | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/intermediate_fusion/` | `oof/intermediate_fusion_oof_predictions.csv` | `FINAL_CANDIDATE` | Main comparison |
| Co-attention fusion | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/coattention_fusion/` | `oof/coattention_fusion_oof_predictions.csv` | `SUPPLEMENTARY` | Post-hoc architecture comparison |
| Late mean | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/late_mean/` | `oof/late_mean_oof_predictions.csv` | `FINAL_CANDIDATE` | Headline point-estimate model |
| Late stack-logit | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_final_nested_cv_v1/late_stack_logit/` | `oof/late_stack_logit_oof_predictions.csv` | `FINAL_CANDIDATE` | Main comparison |

All seven files contain identical 707 rows and 150 patients. Final patient tables are `reports/thesis_ch1/lgd2_final_pre_event_*.csv`; the external completeness manifest records hashes and fold artifacts. Co-attention was retrained after inspection of the prespecified primary results and is therefore supplementary post-hoc evidence.

### Supplementary advanced architecture run

All seven advanced families use the same 707 strict pre-event rows, 150 patients, frozen outer folds, inner-validation model selection, and validation-derived thresholds. They were specified after inspecting the locked primary results and remain `SUPPLEMENTARY`.

| family | feature inputs | external OOF prediction | AUPRC | status |
|---|---|---|---:|---|
| Foundation ensemble | GigaPath + UNI2 + Virchow2 + CNV | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/oof/foundation_ensemble_fusion_oof_predictions.csv` | 0.636 | `SUPPLEMENTARY` |
| Hierarchical patient fusion | UNI2 + CNV + pre-event hierarchy | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/oof/hierarchical_patient_fusion_oof_predictions.csv` | 0.631 | `SUPPLEMENTARY` |
| Optimal-transport fusion | UNI2 + chromosome CNV tokens | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/oof/optimal_transport_fusion_oof_predictions.csv` | 0.565 | `SUPPLEMENTARY` |
| Multitask temporal fusion | UNI2 + CNV | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/oof/multitask_temporal_fusion_oof_predictions.csv` | 0.534 | `SUPPLEMENTARY` |
| Low-rank bilinear fusion | UNI2 + CNV | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/oof/low_rank_bilinear_fusion_oof_predictions.csv` | 0.514 | `SUPPLEMENTARY` |
| CNV-token cross-attention | UNI2 + chromosome CNV tokens | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/oof/cnv_token_cross_attention_oof_predictions.csv` | 0.507 | `SUPPLEMENTARY` |
| Reliability-gated fusion | UNI2 + CNV | `analysis/chapter1_lgd2_final_pre_event_20260713_final/training_advanced_fusion_nested_cv_v1/oof/reliability_gated_fusion_oof_predictions.csv` | 0.502 | `SUPPLEMENTARY` |

The foundation ensemble and hierarchical models were effectively tied with late mean on AUPRC; their paired 95% intervals versus late mean include zero. Heavy OOF predictions and checkpoints remain external.

| result family | status | external path | summary file | prediction file | missing metrics | planned output |
|---|---|---|---|---|---|---|
| Primary LGD2+ cohort | `LEGACY` | `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/` | `derived_master.csv` | n/a | final cohort-flow docs and early-prediction flag | Table 1 cohort flow |
| CNV-only core | `LEGACY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/cnv_anchor/` | `global_results_summary.csv` | `runs/cnv/all_samples/core_binary/cv/predictions_all_samples_cnv_random_forest_windows_armdiff_plus_arms_plus_cx_NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv` | patient AUPRC, Brier/calibration, PPV/NPV, FP/TN, fixed operating points | Main model comparison table |
| CNV variant/resolution sweep | `SUPPLEMENTARY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/cnv_variants/cnv_anchor/` | `global_results_summary.csv` | `runs/cnv/all_samples/variant_binary/cv/predictions_all_samples_*_NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv` | patient-level clinical metrics by variant | Supplementary CNV variant table |
| Image-only Gigapath | `LEGACY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/gigapath/` | `global_results_summary.csv` | `runs/image/all_samples/core_gpu/cv/predictions_all_samples_set_transformer_lite_NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv` | full patient clinical metrics | Main model comparison table |
| Image-only UNI2 | `LEGACY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/uni2/` | `global_results_summary.csv` | `runs/image/all_samples/core_gpu/cv/predictions_all_samples_*_NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv` | full patient clinical metrics | Supplementary foundation image table |
| Image-only Virchow2 | `LEGACY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/virchow2/` | `global_results_summary.csv` | `runs/image/all_samples/core_gpu/cv/predictions_all_samples_*_NextBiopsyProgression_LGD2plus_rep01_fold{1..5}.csv` | full patient clinical metrics | Supplementary foundation image table |
| Early fusion | `LEGACY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/{gigapath,uni2,virchow2}/` | `global_results_summary.csv` | `runs/multimodal/all_samples/core_gpu/cv/predictions_all_samples_early_mean_mlp*_windows_armdiff_plus_arms_plus_cx_NextBiopsyProgression_LGD2plus_k0_uniform_epca0_rep01_fold{1..5}.csv` | full patient clinical metrics | Main/supplementary model comparison |
| Intermediate fusion | `LEGACY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/{gigapath,uni2,virchow2}/` | `global_results_summary.csv` | `runs/multimodal/all_samples/core_gpu/cv/predictions_all_samples_intermediate_abmil_cnv_windows_armdiff_plus_arms_plus_cx_NextBiopsyProgression_LGD2plus_k0_uniform_epca0_rep01_fold{1..5}.csv` | full patient clinical metrics | Main model comparison table |
| Co-attention fusion | `LEGACY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/{gigapath,uni2,virchow2}/` | `global_results_summary.csv` | `runs/multimodal/all_samples/core_gpu/cv/predictions_all_samples_coattn_abmil_cnv_windows_armdiff_plus_arms_plus_cx_NextBiopsyProgression_LGD2plus_k0_uniform_epca0_rep01_fold{1..5}.csv` | full patient clinical metrics | Main/supplementary model comparison |
| Foundation-combo fusion | `REVIEW_MANUALLY` | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/foundation_combo/` | `cv_summary_foundation_combo_fusion.csv` | `cv_predictions_foundation_combo_fusion.csv` | patient IDs and patient metrics need join/review | Supplementary foundation-fusion table |
| Clinical augmentation | `REVIEW_MANUALLY` | `data/foundation_grid_runs/campaign_lgd2_clinical_augmentation_20260319_190949/` | `core_lvl2/*/global_results_summary.csv` | review manually | decide thesis scope; patient clinical metrics | Supplementary clinical covariates table |

## Completed recomputation from existing outputs

The following have been recomputed from saved external prediction files, without retraining, by `scripts/02_recompute_patient_detection_metrics.py`:

- Patient-level clinical metrics with PPV, NPV, TP, FP, TN, FN.
- False-positive burden, including false positives per detected progressor.
- Patient-level confusion matrices.
- Patient-level AUPRC.
- Patient-level Brier score and calibration summaries.
- Sensitivity at fixed specificity and specificity at fixed sensitivity.
- Confidence intervals or fold/bootstrap variability at patient level.
- Early-prediction-only analysis excluding `DaysFromCurrentToEvent == 0`.

Primary input pattern for this recomputation:

`data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/*/runs/*/all_samples/*/cv/predictions_all_samples_*NextBiopsyProgression_LGD2plus*_rep01_fold{1..5}.csv`

The prediction files audited include `sample_id`, `patient_id`, `fold`, `y_true`, `y_pred`, and `y_prob`.

Small generated summaries are tracked under `reports/thesis_ch1/`; raw prediction files remain external.

## Supplementary / legacy result families

| result family | status | external path | thesis use |
|---|---|---|---|
| LGD3+ 5-fold results | `SUPPLEMENTARY` | `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/`; `reports/biopsy_patient_aggregation_20260306_102801/` | Supplementary / legacy endpoint comparison |
| LGD3+ interpretation outputs | `SUPPLEMENTARY` | `analysis/clinician_figures_nextbiopsyprogression_batch10/`; `analysis/explainability/`; `analysis/cnv_explainability/` | Interpretability support only unless regenerated for LGD2+ |
| Killcoyne/CNV reproduction | `LEGACY` | `analysis/killcoyne_paperfaithful_fullsplit_20260427_145056/`; `analysis/fixed_lambda_lopo_truepath_panels_20260428_1048/` | Historical CNV baseline context |
| Survival/time-window outputs | `SUPPLEMENTARY` | `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/` | Supplementary time-window analysis |
| Old 50-fold/smoke/LOPO families | `EXPLORATORY` | `data/virchow2_mil_runs/`; older `data/foundation_grid_runs/campaign_20260226_210057/`; related smoke folders | Do not use for primary claims |

## Missing or partial result families

| item | status | note |
|---|---|---|
| LGD2+ histology attention/top-patch outputs | `SUPPLEMENTARY` | ABMIL interpretation complete for all eight selected cases (external outputs, `pathology` env); selected-case, not cohort-wide. |
| LGD2+ CNV top genes/windows | `MISSING` | Blocked: no persisted estimator/exported LGD2+ importance, no LGD2+ window-to-gene map. LGD3+ legacy is a different endpoint. |
| LGD2+ fusion help/hurt/fail cases | `SUPPLEMENTARY` | Probability-level case interpretation complete for the first three packs; model-internal attribution still missing. |
| LGD2+ late fusion (mean; stack_logit) | `FINAL_CANDIDATE` | Patient-level metrics + paired deltas recomputed for uni2/virchow2/gigapath; rows `lgd2_late_fusion_*`. |
| LGD2+ modality ablation (shuffle image/CNV) | `SUPPLEMENTARY` | Patient-level baseline-minus-shuffle deltas packaged; supporting evidence, not causal proof. |
| LGD2+ tile/magnification comparison | `REVIEW_MANUALLY` | Patch-selection/level evidence exists, but no clean final LGD2+ comparison table was found. |
| Foundation-combo patient-level metrics | `REVIEW_MANUALLY` | Prediction file found, but audited header lacks `patient_id`; join required before patient metrics. |
| Final early-prediction-only results | `FINAL_CANDIDATE` | Generated in `reports/thesis_ch1/lgd2_patient_level_metrics_early_prediction_only.csv`. |

## Next scripts that should consume this manifest

- `scripts/02_recompute_patient_detection_metrics.py`
- `scripts/03_make_cohort_table.py`
- `scripts/04_make_main_results_table.py`
- `scripts/05_make_early_prediction_table.py`
- `scripts/06_make_interpretability_summary.py`
- `scripts/27_collect_lgd2_final_oof.py`
- `scripts/28_make_lgd2_final_pre_event_results.py`
- `scripts/30_select_lgd2_final_interpretation_cases.py`

These scripts should read `docs/final_results_manifest.csv`, resolve external paths under `$BARRETTS_EXPERIMENT_ROOT`, and write any generated outputs outside Git unless they are small documentation summaries.

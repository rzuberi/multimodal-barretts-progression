# Incomplete Results / Gap List — Barrett Chapter 1

Source: `docs/final_results_manifest.csv`.

This file lists thesis-relevant rows that are not complete for the locked Chapter 1 analysis:

- Primary endpoint: `NextBiopsyProgression_LGD2plus`
- Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies
- Primary evaluation: 5-fold patient-disjoint CV
- Primary reporting level: patient-level

## Blocking recomputation

These are required before final Chapter 1 tables.

| result_id | gap | external evidence | next action |
|---|---|---|---|
| `lgd2_patient_metrics_recompute` | Missing patient AUPRC, Brier/calibration, PPV, NPV, FP, TN, fixed operating points, confidence intervals. | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/patient_aggregation/task2_patient_aggregation_metrics.csv`; prediction pattern in manifest. | Run `scripts/02_recompute_patient_detection_metrics.py` from saved predictions. |
| `lgd2_early_prediction_filter` | No final early-prediction-only metrics excluding `DaysFromCurrentToEvent == 0`. | Master cohort has timing column; saved prediction paths exist; no filtered result file found. | Recompute selected final models after filtering current-event samples. |

## Manual review needed

These may be usable, but cannot be treated as final until reviewed.

| result_id | gap | external evidence | next action |
|---|---|---|---|
| `lgd2_foundation_combo` | Prediction file lacks `patient_id` in audited header; patient-level metrics need cohort join. | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/foundation_combo/cv_predictions_foundation_combo_fusion.csv` | Join to cohort by sample ID if valid, then recompute patient metrics. |
| `lgd2_clinical_augmentation` | Clinical covariate scope not decided; final patient clinical metrics missing. | `data/foundation_grid_runs/campaign_lgd2_clinical_augmentation_20260319_190949/core_lvl2/*/global_results_summary.csv` | Decide whether clinical augmentation belongs in Chapter 1; if yes, recompute patient metrics. |
| `lgd2_tile_magnification_comparison` | Clean final LGD2+ tile/magnification comparison table not found. | `data/foundation_grid_runs/campaign_lgd2_patientday_moe_20260318_182454/magnification` | Identify exact summary/prediction files or mark as not completed. |

## Missing primary LGD2+ interpretation

These do not currently exist for the locked LGD2+ endpoint.

| result_id | missing item | available support | next action |
|---|---|---|---|
| `lgd2_histology_interpretability` | LGD2+ attention maps, top patches, clinician-facing histology figures. | LGD3+ support exists under `analysis/clinician_figures_nextbiopsyprogression_batch10/` and `analysis/explainability/`. | Regenerate for LGD2+ selected image/multimodal models. |
| `lgd2_cnv_interpretability` | LGD2+ CNV top windows, gene maps, coefficients/importances. | LGD3+ support exists under `analysis/cnv_explainability/`. | Regenerate for LGD2+ selected CNV and multimodal models. |
| `lgd2_fusion_help_hurt_fail` | LGD2+ true-positive, false-positive, false-negative, image-vs-CNV rescue/hurt/fail cases. | LGD3+ case-analysis support exists, but not primary endpoint. | Build case table from LGD2+ patient-level predictions after recomputation. |

## Final-candidate rows with remaining work

These result families have usable 5-fold LGD2+ outputs, but still need final patient-level metrics, early-prediction filtering, or LGD2+ interpretation before thesis use.

| result_id | remaining work |
|---|---|
| `lgd2_primary_cohort` | Final cohort-flow documentation, early-prediction flag, exclusion reasons. |
| `lgd2_cnv_core` | Patient AUPRC, Brier/calibration, PPV/NPV, FP/TN, fixed operating points; early-prediction sensitivity. |
| `lgd2_image_gigapath` | Patient AUPRC, Brier/calibration, PPV/NPV, FP/TN, fixed operating points; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_image_uni2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_image_virchow2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_early_fusion_gigapath` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_early_fusion_uni2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_early_fusion_virchow2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_intermediate_fusion_gigapath` | Patient AUPRC, Brier/calibration, PPV/NPV, FP/TN, fixed operating points; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_intermediate_fusion_uni2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_intermediate_fusion_virchow2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_coattention_gigapath` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_coattention_uni2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |
| `lgd2_coattention_virchow2` | Full patient clinical metrics; early-prediction sensitivity; LGD2+ interpretation. |

## Not primary, but not final for Chapter 1

These should not block the primary Chapter 1 result table.

| result_id | status | note |
|---|---|---|
| `lgd2_cnv_variants` | `SUPPLEMENTARY` | Needs patient-level clinical metrics by CNV variant if used as a supplementary sensitivity table. |
| `lgd2_modality_ablation_shuffle` | `SUPPLEMENTARY` | Needs full patient clinical metrics for ablation/shuffle claims. |
| `survival_time_window` | `SUPPLEMENTARY` | Useful for time-window analysis, but not the primary binary patient-level detection table. |
| `lgd3_5fold_legacy` | `SUPPLEMENTARY` | Legacy endpoint only; keep separate from primary LGD2+ claims. |
| `lgd3_interpretability_support` | `SUPPLEMENTARY` | Interpretability support only unless regenerated for LGD2+. |
| `killcoyne_cnv_reproduction` | `LEGACY` | Historical CNV context; not aligned to primary LGD2+ endpoint. |
| `fixed_lambda_cnv_lopo` | `LEGACY` | Historical CNV context; not aligned to primary LGD2+ endpoint. |
| `old_50fold_and_smoke` | `EXPLORATORY` | Development history only; do not use for primary thesis claims. |

## Minimum completion order

1. Recompute patient-level detection metrics for selected LGD2+ final models.
2. Recompute early-prediction-only metrics excluding `DaysFromCurrentToEvent == 0`.
3. Finalize cohort-flow/exclusion documentation.
4. Decide whether foundation-combo and clinical augmentation are included or supplementary only.
5. Regenerate LGD2+ interpretability outputs for selected CNV, image, and multimodal models.
6. Build LGD2+ fusion help/hurt/fail case analysis from patient-level predictions.

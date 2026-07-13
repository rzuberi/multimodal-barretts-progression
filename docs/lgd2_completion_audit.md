# LGD2+ Completion Audit

## Locked Specification

- Primary endpoint: `NextBiopsyProgression_LGD2plus`.
- Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
- Primary evaluation: 5-fold patient-disjoint CV.
- Primary reporting level: patient-level.
- Supplementary reporting levels: biopsy-level and sample-level.
- LGD3+ status: supplementary / legacy / interpretability-supporting endpoint.

## What Exists

| Requirement | Status | Evidence |
|---|---|---|
| Matched histology-CNV Barrett's cohort | Exists | `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`: 959 rows, 160 patients, 470 biopsies |
| LGD2+ endpoint table | Exists | `NextBiopsyProgression_LGD2plus`: 231 positive rows, 690 negative rows, 38 missing labels |
| Patient-level LGD2+ labels | Exists | 55 positive and 100 negative labelled patients |
| 5-fold patient-disjoint CV | Exists | Saved prediction files for final LGD2+ campaign have 155 patients and zero patients appearing in multiple folds per checked model |
| CNV-only models | Exists | `core_lvl2/cnv_anchor/global_results_summary.csv`; 5 models, 5/5 folds |
| Histology-only models | Exists | `core_lvl2/{gigapath,uni2,virchow2}/global_results_summary.csv`; `abmil` and `set_transformer_lite`, 5/5 folds |
| Early fusion | Exists | `early_mean_mlp`, `early_mean_mlp_timev1`, 5/5 folds |
| Intermediate fusion | Exists | `intermediate_abmil_cnv`, 5/5 folds |
| Co-attention fusion | Exists | `coattn_abmil_cnv`, 5/5 folds |
| CNV variants/resolutions | Exists | Five variants: `arms_only`, `external_arms_500kb`, `topk_arms_k5`, `windows_armdiff_plus_arms_plus_cx`, `windows_plus_arms` |
| Foundation models | Exists | Gigapath, UNI2, Virchow2 |
| Sample-level metrics | Exists | Global summaries include AUC, AUPRC, balanced accuracy, sensitivity, specificity, Brier, ECE/fixed operating-point metrics |
| Patient-level AUC/sensitivity/specificity | Exists | `core_lvl2/patient_aggregation/task2_patient_aggregation_metrics.csv` |
| Modality shuffling/ablation support | Exists for selected UNI2 multimodal runs | `data/foundation_grid_runs/campaign_lgd2_h200_patient_signal_lgd2_20260319/patchselect/uni2_signal/{baseline,shuffle_image,shuffle_cnv,shuffle_both}/cv/summary_metrics.csv` |
| Saved prediction files for recomputation | Exists | LGD2+ prediction files include `sample_id`, `patient_id`, `fold`, `y_true`, `y_pred`, `y_prob` |

## Primary Candidate Result Paths

- Master table: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`
- Main campaign: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`
- Patient aggregation: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/patient_aggregation/`
- Ablation/shuffle support: `data/foundation_grid_runs/campaign_lgd2_h200_patient_signal_lgd2_20260319/`

## Current Best Patient-Level LGD2+ Rows

From `task2_patient_aggregation_metrics.csv`, using the stored patient aggregation:

| model | AUC | sensitivity | specificity | accuracy | derived PPV | derived NPV | TP | FN | FP | TN | FP per detected progressor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| multimodal/gigapath/intermediate_abmil_cnv, patient_max | 0.887 | 0.927 | 0.590 | 0.710 | 0.554 | 0.937 | 51 | 4 | 41 | 59 | 0.804 |
| image/gigapath/set_transformer_lite, patient_max | 0.829 | 0.891 | 0.590 | 0.697 | 0.544 | 0.908 | 49 | 6 | 41 | 59 | 0.837 |
| cnv/cnv_anchor/cnv_random_forest, patient_max | 0.819 | 0.164 | 0.980 | 0.690 | 0.818 | 0.681 | 9 | 46 | 2 | 98 | 0.222 |

These derived count metrics are useful, but the final table should be regenerated directly from patient-level prediction scores.

## What Is Still Missing

> RESOLVED since this audit (see `PROJECT_STATE.md` for canonical status): the final
> patient-level clinical metric table, calibration/Brier, fixed operating points,
> confidence intervals, and the early-prediction-only analysis are all COMPLETE in
> `reports/thesis_ch1/`. LGD2+ ABMIL histology attention/top-patch interpretation is
> COMPLETE for all eight selected cases. Late fusion is integrated at patient level.
> Genuinely still missing: LGD2+ CNV region/gene interpretation (BLOCKED — needs a
> compute run), model-internal fusion attribution, and a clean tile/magnification table.
> The table below is retained for historical provenance.

| Missing item | Why it matters | Can be done without retraining? |
|---|---|---|
| Final patient-level clinical metric table | Stored patient table lacks AUPRC, Brier/calibration, fixed operating-point metrics, FP/TN columns, PPV/NPV, and false-positive burden | Yes, saved `y_prob` predictions exist |
| Patient-level calibration/Brier | Needed for clinical reporting beyond AUC | Yes |
| Patient-level sensitivity at fixed specificity and specificity at fixed sensitivity | Needed for clinically meaningful operating points | Yes |
| Confidence intervals or fold variability at patient level | Needed to compare modalities rigorously | Yes |
| Final early-prediction-only analysis excluding at-event samples | Separates detection/current-event recognition from future prediction | Likely yes, using master table + predictions |
| LGD2+ histology attention/top-patch figures | Existing interpretation is mostly LGD3+ | Needs new interpretation jobs or figure generation |
| LGD2+ CNV region/gene interpretation tables | Existing CNV interpretation is mostly LGD3+ | Needs new interpretation export |
| LGD2+ fusion rescue/hurt/failure cases | Needed for multimodal biological interpretation | Needs new case analysis |
| Clean tile/magnification comparison table for LGD2+ | Patch-selection/level evidence exists, but no final comparison table was found | Unclear; may need result collation or rerun |
| Final result manifest | Thesis needs exact external paths/scripts/cohort definitions | Yes |

## Not Primary Anymore

- LOPO is not required for the primary result set.
- LGD3+ is not primary; use it only as supplementary / legacy / interpretability-supporting.
- Older 50-fold and smoke families should not be used for primary claims.

## Immediate Next Work

1. Recompute patient-level LGD2+ metrics from saved prediction files for selected final models.
2. Apply the same metric code to biopsy/sample-level supplementary outputs.
3. Decide and run the early-prediction-only supplementary analysis excluding `DaysFromCurrentToEvent == 0`.
4. Generate LGD2+ interpretation outputs or explicitly mark LGD3+ interpretation as legacy support only.
5. Create `docs/final_result_manifest.md` once the exact final external outputs are frozen.

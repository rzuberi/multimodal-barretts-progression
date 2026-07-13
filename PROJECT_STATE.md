# Project State

## Decision State

- Primary endpoint: `NextBiopsyProgression_LGD2plus`.
- Clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
- Primary evaluation: 5-fold patient-disjoint CV.
- Primary reporting level: patient.
- Supplementary reporting levels: biopsy and sample.
- Primary clinical framing: future progression detection, not current diagnosis recognition.
- LGD3+ status: supplementary / legacy / interpretability-supporting endpoint.
- Data storage: external cluster paths only; never GitHub.

## Best Current External Inputs

These paths are references to the cluster experiment folder and are not repository contents.

- Primary LGD2+ strict next-biopsy master: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`
- Primary LGD2+ 5-fold campaign: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`
- Primary LGD2+ patient aggregation: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/patient_aggregation/`
- LGD2+ modality shuffle/ablation support: `data/foundation_grid_runs/campaign_lgd2_h200_patient_signal_lgd2_20260319/`
- LGD3+ legacy master: `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`
- LGD3+ legacy interpretation/report support: `reports/biopsy_patient_aggregation_20260306_102801/`, `reports/progressor_distance_to_progression_20260306_104927/`, `analysis/clinician_figures_nextbiopsyprogression_batch10/`

## Completed

- Patient-level LGD2+ metrics (AUPRC, ROC AUC, Brier/calibration, PPV/NPV, FP/TN, fixed operating points, bootstrap CIs) are computed in `reports/thesis_ch1/lgd2_patient_level_metrics_all_samples.csv`.
- Early-prediction-only sensitivity analysis (excludes `DaysFromCurrentToEvent == 0`) is complete: `reports/thesis_ch1/lgd2_patient_level_metrics_early_prediction_only.csv`.
- Cohort-flow and main model-comparison tables are complete.
- Late fusion (`mean`, `stack_logit`) integrated at patient level for uni2/virchow2/gigapath; see manifest rows `lgd2_late_fusion_*`.
- ABMIL histology interpretation complete for all eight selected LGD2+ cases (external outputs, `pathology` env); no environment blocker remains.
- Probability-level fusion case interpretation complete for the first three case packs (`A_true_positive_early_02`, `B_false_negative_07`, `E_cnv_rescue_19`).

## Remaining Gaps

- LGD2+ CNV top-windows/genes interpretation is BLOCKED: no persisted CNV estimator or exported LGD2+ feature-importance, and no LGD2+ window-to-gene map. LGD3+ legacy outputs are a different endpoint and not valid primary evidence. Unblocking requires a compute run (not lightweight); see `reports/thesis_ch1/lgd2_cnv_interpretation_input_audit.md`.
- Model-internal fusion attribution (beyond probability comparisons) is missing.
- Composite clinician-facing multimodal case figures are missing.
- Clean final tile/magnification LGD2+ comparison table is not yet packaged.
- Foundation-combo needs `patient_id` join validation; clinical-augmentation scope undecided. Both remain `REVIEW_MANUALLY` and are excluded from the primary comparison.

## Repository Principle

Keep this repository small enough that every tracked file has a clear role in the next thesis result set.

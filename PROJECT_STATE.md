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
- Frozen strict pre-event cohort release: 707 matched rows, 150 patients, 693 unique CNV profiles; at-event and post-event rows excluded before splitting.
- Final five-fold patient-disjoint nested-CV rerun complete for CNV-only, UNI2 ABMIL, early fusion, intermediate fusion, late mean, and late stack-logit on identical rows/patients.
- Intermediate configuration selection, thresholds, calibration, preprocessing, and final epoch selection use inner validation only.
- Final OOF contract passes at 707 rows / 150 patients for all six model families.
- Best final-candidate model is late mean: AUPRC 0.630, AUC 0.774, Brier 0.184. CNV-only: 0.538, 0.663, 0.216.
- Paired late-mean minus CNV differences: AUPRC +0.091 (95% CI -0.036 to 0.219), AUC +0.111 (0.002 to 0.219), Brier -0.032 (-0.062 to -0.004).

## Remaining Gaps

- LGD2+ CNV feature-importance interpretation is now AVAILABLE. The July 13 final
  release persisted a `cnv_only` estimator per outer fold (scikit-learn Pipeline:
  impute → scale → PCA(64) → RandomForest), and each fold exported
  `cnv_feature_importance.csv`. `scripts/07_aggregate_cnv_importance.py` aggregates
  the five folds into `reports/thesis_ch1/lgd2_cnv_feature_importance_aggregated.csv`
  (Chapter 1, Fig 1.5). The earlier "BLOCKED / no persisted estimator" note predated
  that run. Remaining CNV-interpretation refinements: a window→gene annotation map and
  (optionally) importances for the multimodal models. LGD3+ legacy outputs remain a
  different endpoint and not valid primary evidence.
- Model-internal fusion attribution (beyond probability comparisons) is missing.
- Composite clinician-facing multimodal case figures are missing.
- Clean final tile/magnification LGD2+ comparison table is not yet packaged.
- Foundation-combo needs `patient_id` join validation; clinical-augmentation scope undecided. Both remain `REVIEW_MANUALLY` and are excluded from the primary comparison.
- Reselect interpretation cases from final strict pre-event OOF predictions; developmental case labels cannot be assumed unchanged.
- Regenerate histology attention and CNV region/gene outputs from the final fold checkpoints for selected cases.
- External validation remains absent. Do not generalise beyond this internal matched cohort.
- The primary paired AUPRC interval includes zero; report a likely multimodal benefit, not definitive superiority.

## Repository Principle

Keep this repository small enough that every tracked file has a clear role in the next thesis result set.

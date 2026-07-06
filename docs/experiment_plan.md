# Experiment Plan

## Primary Aim

Build a coherent Chapter 1 result set for multimodal Barrett's progression prediction using histopathology and CNV.

## Minimum Final Result Set

1. Primary endpoint: `NextBiopsyProgression_LGD2plus`.
2. Primary clinical definition: HGD/IMC/OAC or two consecutive LGD biopsies.
3. Final cohort table outside Git: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`.
3. Patient-level evaluation:
   - primary: 5-fold patient-disjoint CV;
   - biopsy/sample-level metrics: supplementary.
4. Model families:
   - CNV-only baseline;
   - image-only MIL;
   - early fusion;
   - intermediate/co-attention fusion;
   - best selected foundation-model fusion.
5. Clinical detection metrics:
   - ROC AUC;
   - AUPRC;
   - sensitivity;
   - specificity;
   - PPV;
   - NPV;
   - balanced accuracy;
   - Brier/calibration;
   - sensitivity at fixed specificity;
   - specificity at fixed sensitivity;
   - progressors detected and missed;
   - false positives per detected progressor;
   - patient-level confusion matrix.
6. Biological interpretation:
   - histology top patches or attention maps;
   - CNV region/gene rankings;
   - multimodal dependence/rescue/hurt cases.

## Existing Results To Treat As Primary Starting Points

- LGD2+ 5-fold sample-level model campaign: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`.
- LGD2+ patient/biopsy/sample aggregation: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/core_lvl2/patient_aggregation/`.
- LGD2+ modality shuffle/ablation support: `data/foundation_grid_runs/campaign_lgd2_h200_patient_signal_lgd2_20260319/`.

## Existing Results To Treat As Supplementary

- LGD3+ canonical 5-fold CV and patient aggregation.
- LGD3+ distance-to-progression analysis.
- LGD3+ clinician/explainability figures.
- CNV-only Killcoyne-style LOPO baselines.
- Survival/time-window analyses.

## Missing Results

- Patient-level LGD2+ clinical metric table with AUPRC, Brier/calibration, fixed operating-point metrics, PPV, NPV, FP/TN counts, and false-positive burden.
- Early-prediction-only LGD2+ sensitivity analysis excluding `DaysFromCurrentToEvent == 0`.
- LGD2+ interpretation figures.
- Clean final tile/magnification comparison table for LGD2+.
- Final result manifest listing exact external paths for primary and supplementary outputs.

## Obsolete Or Developmental Results

- Older 50-fold result families.
- Smoke runs.
- Result folders with no saved prediction files.
- LGD3+ headline results for primary claims; keep only as supplementary / legacy / interpretation support.

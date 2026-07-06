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

## Known Risks

- Current-event samples are included in primary all-samples LGD2+ results; early-prediction-only analysis remains supplementary/missing.
- Patient-level LGD2+ aggregation exists, but its stored table lacks patient-level AUPRC, Brier/calibration, fixed operating-point metrics, FP/TN counts, PPV/NPV, and false-positive burden.
- LGD2+ interpretation outputs were not found; existing interpretation is mainly LGD3+.
- Tile/magnification testing is not packaged as a clean final LGD2+ result.
- Some supportive outputs mix endpoint/history and should stay legacy or supplementary.

## Repository Principle

Keep this repository small enough that every tracked file has a clear role in the next thesis result set.

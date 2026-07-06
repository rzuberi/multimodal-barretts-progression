# Project State

## Decision State

- Primary endpoint: undecided, LGD2+ versus LGD3+.
- Preferred evaluation: LOPO if computationally feasible; otherwise patient-disjoint CV with explicit justification.
- Primary reporting level: patient.
- Primary clinical framing: future progression detection, not current diagnosis recognition.
- Data storage: external cluster paths only; never GitHub.

## Best Current External Inputs

These paths are references to the cluster experiment folder and are not repository contents.

- LGD3+ canonical master: `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`
- LGD2+ strict next-biopsy master: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`
- LGD3+ canonical 5-fold campaign: `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/`
- LGD2+ 5-fold campaign: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`
- LGD3+ patient aggregation report: `reports/biopsy_patient_aggregation_20260306_102801/`
- LGD3+ distance-to-progression report: `reports/progressor_distance_to_progression_20260306_104927/`

## Known Risks

- Current-event samples are included in some all-samples results.
- LOPO results are incomplete for canonical image and fusion models.
- Existing results mix endpoints, fold regimes, and historical cohorts.
- Some apparent interpretability outputs are endpoint-specific to LGD3+.
- PPV/NPV and patient confusion counts need explicit recomputation.

## Repository Principle

Keep this repository small enough that every tracked file has a clear role in the next thesis result set.

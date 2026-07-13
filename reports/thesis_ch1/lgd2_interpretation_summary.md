# LGD2+ Interpretation Summary (current state)

Current-state summary of the interpretation stage for the primary endpoint. Git
history and dated execution logs hold the historical chronology; this file is not
append-only.

## 1. Endpoint and evaluation
- Endpoint: `NextBiopsyProgression_LGD2plus` (HGD/IMC/OAC or two consecutive LGD biopsies).
- Evaluation: 5-fold patient-disjoint CV; primary reporting patient-level `patient_max`.

## 2. Final selected cases
- Eight LGD2+ interpretation cases were selected (subset in
  `reports/thesis_ch1/lgd2_final_interpretation_case_subset.csv`).

## 3. ABMIL histology status
- Complete for all eight selected cases: external top/bottom tile grids, heatmap
  overlays, shuffled overlays, tile-score CSVs and metadata JSON, using the
  `pathology` environment. Lightweight summary:
  `reports/thesis_ch1/lgd2_histology_all8_interpretation_summary.csv`.

## 4. Manual decision
- All eight cases retained for later figure selection (`INCLUDE_FOR_LATER_SELECTION`).

## 5. Probability-level fusion interpretation
- Complete for the selected cases / first three multimodal case packs
  (`A_true_positive_early_02`, `B_false_negative_07`, `E_cnv_rescue_19`).

## 6. CNV region/gene status
- BLOCKED. No persisted CNV estimator or exported LGD2+ feature importance, and no
  LGD2+ window-to-gene map. LGD3+ legacy outputs are a different endpoint and are not
  valid primary evidence. See `reports/thesis_ch1/lgd2_cnv_interpretation_input_audit.md`.

## 7. Model-internal fusion attribution
- Missing. Only probability-level rescue/hurt/fail assignments exist; no model-internal
  attribution has been produced.

## 8. External output locations
- Histology WSI outputs:
  `analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/NextBiopsyProgression_LGD2plus/all_samples/uni2/abmil/` (external; not in Git).
- The WSI runner lives in the outer experiment tree at `scripts/run_wsi_explainability_case.py`.

## 9. Next actions
- Generate LGD2+ CNV feature-importance externally (compute run) to unblock region/gene interpretation.
- Add model-internal fusion attribution.
- Assemble composite clinician-facing multimodal case figures.

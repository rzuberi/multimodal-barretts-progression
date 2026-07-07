# LGD2+ Interpretation & Case-Selection Stage — Change Summary

Stage: LGD2+ interpretation availability audit + case selection + regeneration plan.
Endpoint: `NextBiopsyProgression_LGD2plus` (HGD/IMC/OAC or two consecutive LGD biopsies).
No model training run. No external result files modified. No raw data committed.

## What was done

1. Audited existing interpretation evidence from `docs/final_results_manifest.csv`,
   `docs/lgd2_completion_audit.md`, and `reports/thesis_ch1/*`. Confirmed all LGD2+
   interpretation outputs are MISSING; only LGD3+ interpretation exists (legacy support).
2. Built a per-patient wide table (CNV-only / image-only / early-fusion probability for
   the same patient) from external saved predictions, using `patient_max` aggregation.
3. Selected 38 cases across categories A–I for histology, CNV, and multimodal
   interpretation, prioritising early-prediction-only cases.
4. Wrote a regeneration plan naming the existing LGD3+ scripts to re-point at LGD2+.
5. Wrote a thesis-facing summary (states interpretation NOT yet regenerated).
6. Added toy-data tests for the selection logic.
7. Allowlisted the new lightweight CSV in the no-data guard and `.gitignore`.

## Files added

- `reports/thesis_ch1/lgd2_interpretability_availability.md` — availability audit; all LGD2+ interpretation MISSING, LGD3+ marked legacy/supplementary; exact external paths listed.
- `scripts/05_select_lgd2_interpretation_cases.py` — case-selection script (external paths only, basenames not absolute mounts).
- `reports/thesis_ch1/lgd2_interpretation_case_selection.csv` — 38-case table (patient/biopsy/sample/slide/cnv ids, grade, timing, three modality probabilities, predicted classes, timing flags, reason, external refs).
- `reports/thesis_ch1/lgd2_interpretation_case_selection.md` — human-readable case summary.
- `reports/thesis_ch1/lgd2_interpretation_case_selection_warnings.md` — warnings / manual-review notes.
- `reports/thesis_ch1/lgd2_interpretation_regeneration_plan.md` — histology / CNV / multimodal outputs to regenerate + old scripts to re-point.
- `reports/thesis_ch1/lgd2_interpretation_summary.md` — thesis-facing summary + priority.
- `tests/test_case_selection.py` — 11 toy tests.
- `reports/thesis_ch1/lgd2_interpretation_stage_changelog.md` — this file.

## Files modified

- `scripts/assert_no_data_tracked.sh` — allowlist the new case CSV.
- `.gitignore` — negation for the new case CSV (matches existing whitelisted-CSV convention).

## Results

### Cases selected (38 total)

| category | n | purpose |
|---|---:|---|
| A true positive early | 5 | progressors flagged early, real lead time 365–788 days, fusion prob 0.96–0.99 |
| B false negative | 5 | missed progressors |
| C false positive | 5 | high-risk non-progressors (FP burden) |
| D true negative | 3 | confident low-risk non-progressors |
| E CNV-rescue | 3 | genomics correct, morphology wrong |
| F histology-rescue | 3 | morphology correct, genomics wrong |
| G fusion-hurt | 3 | unimodal correct, fusion wrong |
| H agreement | 3 + 3 | all modalities agree correctly (positive / negative) |
| I disagreement | 5 | CNV vs image conflict, fusion resolution |

### Timing

- All 38 cases early-prediction-only.
- Representative biopsies: 22 pre-event, 16 timing-missing, 0 at-event.
- No selected case is at-event. Per-case timing in `case_timing`; patient-level context
  in `patient_has_at_event_biopsy` (kept separate to avoid overclaiming).

### Thresholds used

- Default 0.5; high-confidence >= 0.75; low-confidence <= 0.25; strong disagreement |CNV-image| >= 0.4.
- Fusion `threshold_at_90_specificity` (0.610) carried as optional column; 0.5 not replaced.

### Recommended first model to interpret

1. `lgd2_early_fusion_uni2` (`early_mean_mlp`) — strongest early-prediction AUPRC/AUC.
2. `lgd2_cnv_core` (`cnv_random_forest`).
3. `lgd2_image_uni2` (`abmil`).
4. `lgd2_early_fusion_gigapath` — AUC comparison only.
5. `lgd2_foundation_combo` excluded until patient-ID join validated.

### Missing interpretation outputs

All of: histology attention/top-patches/tile-scores/heatmaps/attention-spread;
CNV top-windows/gene-maps/importances/SHAP/profiles; per-case modality-dependence
score + composite fusion figures. Only modality probabilities and rescue/hurt/
disagreement assignments exist now.

### Validation

- `py_compile`: OK on all scripts.
- Tests: 11/11 pass (manual runner; `pytest` not installed in `.conda_mil` env).
- `scripts/05_select_lgd2_interpretation_cases.py`: runs clean, 38 cases.
- `scripts/assert_no_data_tracked.sh`: OK — no forbidden data-like files tracked.

### Notes

- Ran with `../.conda_mil/bin/python` (3.10); default `python3` is 3.6 and cannot run the code.
- Changes staged, not committed.

# LGD2+ Interpretation Summary

Thesis-facing summary of the interpretation stage for the primary endpoint
`NextBiopsyProgression_LGD2plus` (HGD/IMC/OAC or two consecutive LGD biopsies).

**Status: interpretation has NOT been regenerated.** This stage selects cases and
plans regeneration. All LGD2+ interpretation artefacts (attention maps, top patches,
CNV windows/genes, fusion case figures) are still MISSING and must be produced before
any thesis figure is drawn. See `lgd2_interpretability_availability.md` and
`lgd2_interpretation_regeneration_plan.md`.

## Which cases were selected

38 cases selected across the nine categories, all patient-level (patient_max) with a
representative pre-event or timing-missing biopsy per patient. All are drawn from the
`early_prediction_only` set; none of the selected representative biopsies are at-event
(`DaysFromCurrentToEvent == 0`): 22 pre-event, 16 timing-missing, 0 at-event.

| category | n | what it shows |
|---|---:|---|
| A true positive early | 5 | progressors flagged high-risk with real lead time (365–788 days) |
| B false negative | 5 | progressors the fusion model missed |
| C false positive | 5 | non-progressors flagged high-risk (FP burden) |
| D true negative | 3 | confidently low-risk non-progressors |
| E CNV-rescue | 3 | genomics correct where morphology is wrong |
| F histology-rescue | 3 | morphology correct where genomics is wrong |
| G fusion-hurt | 3 | a unimodal model correct but fusion wrong (honest limitation) |
| H modality agreement | 3 + 3 | all modalities agree correctly (positive / negative) |
| I modality disagreement | 5 | CNV vs image disagree strongly; how fusion resolves it |

Concrete detail is in `lgd2_interpretation_case_selection.csv` /
`lgd2_interpretation_case_selection.md`.

## Why each category matters

- A/B/C/D map the confusion matrix onto real patients: who is caught early, who is missed, who is over-called, who is safely cleared.
- E/F isolate when each modality carries the signal — the core multimodal argument.
- G is the honesty check: fusion is not free; some cases get worse.
- H shows robust agreement (the confident, defensible predictions).
- I studies fusion behaviour under conflict, where the model's arbitration matters most.

## Which outputs already exist

- CNV-only, image-only, and early-fusion **probabilities** per patient (in the case CSV).
- Cohort-level metrics and calibration (`lgd2_patient_level_metrics_*`).
- Rescue/hurt/fail and disagreement **assignments** (derived here from saved predictions).

## Which outputs need regeneration

- Histology: top patches, attention heatmaps, tile-score tables, attention-spread summaries.
- CNV: top windows, gene maps, coefficients/importances, SHAP, profile plots.
- Multimodal: per-case modality-dependence score and composite case figures.

## Cases to prioritise for final thesis figures

1. Category A (early true positives) — the headline early-detection claim; strongest, longest-lead-time cases with fusion prob > 0.95.
2. Category E and F (rescue) — one clean CNV-rescue and one clean histology-rescue figure.
3. Category I (disagreement) — one case showing fusion resolving a CNV-vs-image conflict correctly.
4. Category B and G (miss / fusion-hurt) — one each, for an honest limitations panel.

## Final 8-case thesis-figure subset

The final subset is now fixed in `lgd2_final_interpretation_case_subset.csv` /
`lgd2_final_interpretation_case_subset.md`.

Selected categories:

- 2 x `A_true_positive_early`
- 1 x `B_false_negative`
- 1 x `C_false_positive`
- 1 x `E_cnv_rescue`
- 1 x `F_histology_rescue`
- 1 x `G_fusion_hurt`
- 1 x `I_modality_disagreement`

All selected rows are from the `early_prediction_only` analysis set and none are
at-event rows. The selected table stores slide/CNV basenames only, not private mounted
paths.

## Probability-only interpretation already available

`lgd2_modality_case_summary.csv` / `.md` now provide, for each selected case:

- CNV, image, and early-fusion probabilities;
- fusion-minus-unimodal differences;
- absolute CNV-image disagreement;
- dominant modality hint;
- fusion-help / fusion-hurt flags;
- one-sentence probability-level interpretation.

This is not a substitute for biological interpretation, but it is enough to define the
case-study question before regenerating heavy outputs.

## Still requires external regeneration

The following remain external and missing for LGD2+:

- histology top patches, tile-score tables, attention heatmaps/overlays;
- CNV top windows, gene maps, importances/coefficients/SHAP;
- model-internal modality-dependence scores;
- composite clinician-facing figures.

The external run plan is in `lgd2_interpretation_external_run_plan.md`. The old-script
adaptation checklist is in `lgd2_interpretation_script_adaptation_checklist.md`.

## CNV interpretation regeneration status

CNV interpretation has **not** been regenerated yet. The first CNV stage completed here
is an input audit plus a missing-output-safe summary loader.

Ready selected cases:

- `A_true_positive_early_01`
- `A_true_positive_early_02`
- `B_false_negative_07`
- `C_false_positive_12`
- `E_cnv_rescue_19`
- `F_histology_rescue_24`
- `G_fusion_hurt_26`
- `I_modality_disagreement_37`

Expected external output root:

`analysis/lgd2_interpretation_regeneration_20260707/`

Expected CNV outputs:

- per-case top CNV windows;
- per-case top genes/window-to-gene maps;
- feature-importance/coefficient summaries if safely available;
- optional CNV profile plots kept external.

Current generated lightweight files:

- `lgd2_cnv_interpretation_input_audit.md`
- `lgd2_cnv_interpretation_commands.md`
- `lgd2_cnv_interpretation_summary.csv`
- `lgd2_cnv_interpretation_summary.md`
- `lgd2_cnv_interpretation_warnings.md`

The exact command templates are in `lgd2_cnv_interpretation_commands.md`. The key
blocker is that the LGD2+ selected-case CNV feature/model/worklist inputs have not
been validated. Existing top-window/top-gene outputs found on disk are legacy/LGD3+
support only and must not be used as primary LGD2+ evidence.

## Histology interpretation regeneration status

Histology interpretation has **not** been regenerated yet. This stage created the
LGD2+ WSI case manifest, audited inputs, and ran the missing-output-safe summary
loader only.

Ready selected cases:

- `A_true_positive_early_01`
- `A_true_positive_early_02`
- `B_false_negative_07`
- `C_false_positive_12`
- `E_cnv_rescue_19`
- `F_histology_rescue_24`
- `G_fusion_hurt_26`
- `I_modality_disagreement_37`

All 8 selected cases have:

- slide IDs / basenames;
- UNI2 feature references in the external feature index;
- fold-matched `abmil` image checkpoint references;
- fold-matched `early_mean_mlp` fusion checkpoint references;
- early-prediction-only timing with no at-event rows.

No selected case is blocked at the input-reference stage. The missing outputs are the
actual regenerated LGD2+ top patches, tile-score tables, attention heatmaps/overlays,
and attention-spread summaries.

Expected external histology output root:

`analysis/lgd2_interpretation_regeneration_20260707/histology/`

Current generated lightweight files:

- `lgd2_histology_interpretation_input_audit.md`
- `lgd2_histology_interpretation_commands.md`
- `lgd2_wsi_case_manifest.csv`
- `lgd2_wsi_case_manifest.md`
- `lgd2_wsi_case_manifest_warnings.md`
- `lgd2_histology_interpretation_summary.csv`
- `lgd2_histology_interpretation_summary.md`
- `lgd2_histology_interpretation_warnings.md`

The exact command templates are in `lgd2_histology_interpretation_commands.md`.
The legacy WSI runner opens slides, loads feature tensors/checkpoints, and writes
PNG/tile-score outputs, so it must be run externally and not from Git output paths.

## Histology dry-run status

Dry-run cases selected:

- `A_true_positive_early_02`: high-confidence true-positive, `abmil` probability 0.964, early-fusion probability 0.993.
- `B_false_negative_07`: missed progressor, `abmil` probability 0.104, early-fusion probability 0.285.

The WSI explainability command was **not run**. Pre-run validation found that the
raw slide paths required by `run_wsi_explainability_case.py` are not visible in this
shell (`/scratchc/.../*.ndpi` paths do not exist). The selected UNI2 feature files
also need path remapping from legacy `/scratchc` references to the visible slow-scratch
tree before the legacy runner can load them.

No top patches, tile-score tables, heatmap overlays, or tile grids were generated in
this stage. The dry-run output target remains:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/`

Current dry-run files:

- `lgd2_histology_dry_run_cases.csv`
- `lgd2_histology_dry_run_command_check.md`
- `lgd2_histology_dry_run_summary.csv`
- `lgd2_histology_dry_run_summary.md`
- `lgd2_histology_dry_run_warnings.md`

Recommendation: do not run all 8 cases yet. First run from a node/session where the
raw WSI slide tree is mounted, and either restore the legacy `/scratchc` feature paths
or build a dry-run feature index with paths remapped to the visible external feature
files.

## Which model to interpret first

Recommended order (matches manifest thesis priority):

1. `lgd2_early_fusion_uni2` (`early_mean_mlp`) — strongest early-prediction-only AUPRC/AUC; primary interpretation target.
2. `lgd2_cnv_core` (`cnv_random_forest`) — molecular baseline for CNV windows/genes.
3. best validated image-only model, `lgd2_image_uni2` (`abmil`) — histology baseline.
4. `lgd2_early_fusion_gigapath` — only if an AUC comparison is needed (strongest all-samples AUC).
5. Do **not** prioritise `lgd2_foundation_combo` until its `patient_id` join is validated.

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

## Which model to interpret first

Recommended order (matches manifest thesis priority):

1. `lgd2_early_fusion_uni2` (`early_mean_mlp`) — strongest early-prediction-only AUPRC/AUC; primary interpretation target.
2. `lgd2_cnv_core` (`cnv_random_forest`) — molecular baseline for CNV windows/genes.
3. best validated image-only model, `lgd2_image_uni2` (`abmil`) — histology baseline.
4. `lgd2_early_fusion_gigapath` — only if an AUC comparison is needed (strongest all-samples AUC).
5. Do **not** prioritise `lgd2_foundation_combo` until its `patient_id` join is validated.

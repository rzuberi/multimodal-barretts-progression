# LGD2+ Interpretation Summary

Thesis-facing summary of the interpretation stage for the primary endpoint
`NextBiopsyProgression_LGD2plus` (HGD/IMC/OAC or two consecutive LGD biopsies).

**Current status:** LGD2+ ABMIL histology interpretation has now been regenerated
externally for the fixed 8-case subset and structurally validated. CNV interpretation,
fusion-specific interpretation, and composite clinician-facing figures remain missing.
See `lgd2_interpretability_availability.md` and
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

## Histology path-remapping status

The path-remapping/preflight layer has now been added:

- `src/barrett/utils/path_remap.py`
- `configs/path_remap.template.yaml`
- `scripts/10_validate_lgd2_histology_paths.py`

Current audit files:

- `lgd2_histology_path_remap_audit.csv`
- `lgd2_histology_path_remap_audit.md`
- `lgd2_histology_path_remap_warnings.md`

The dry-run audit checked `A_true_positive_early_02` and `B_false_negative_07`.
Both cases are fully resolvable after applying the template fallback remaps:

- raw WSI slide paths resolve after `/scratchc` mount remapping;
- UNI2 feature NPZ paths resolve after Barrett retraining root remapping;
- `abmil` and `early_mean_mlp` checkpoint refs resolve through the external
  `barretts_training/data` candidate root;
- output parent resolves under the external analysis folder.

No WSI was opened, no feature NPZ was loaded, and no checkpoint was loaded. The dry
run should now be attempted only as a case-level external command, starting with
`row_idx 0`, and should still write heavy outputs only under:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/`

## Histology dry-run execution status

The first case-level dry run was attempted after path remapping:

- Case/model attempted: `A_true_positive_early_02` / `abmil`
- Command success: `no`
- Failure: `ModuleNotFoundError: No module named 'torch'`
- Failure happened before WSI opening, feature loading, checkpoint loading, or output generation.

The second selected dry-run case, `B_false_negative_07`, was not attempted because the
first case failed. No top patches, tile-score tables, heatmaps, overlays, or tile grids
were generated.

Current blocker is no longer path resolution; it is the Python environment for the
legacy WSI runner. Runtime preflight in the current environment fails:

- Python: `/home/zuberi01/miniforge3/envs/barretts_multimodal/bin/python`
- missing imports: `torch`, `PIL`, `openslide`
- passing imports: `numpy`, `pandas`

Runtime audit files:

- `lgd2_histology_runtime_env_audit.csv`
- `lgd2_histology_runtime_env_audit.md`
- `lgd2_histology_runtime_env_warnings.md`

The next step is to identify an environment where `torch`, `openslide`, `pandas`,
`numpy`, and `PIL` import cleanly, run `scripts/11_validate_histology_runtime_env.py`
there, then rerun only `row_idx 0` using:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi_case_manifest_fullpaths_remapped.csv`

Do not scale to all 8 cases until `row_idx 0` completes and the external outputs are
summarised successfully.

## Histology environment discovery and row 0 result

Candidate environments tested: 11.

Passing runtime preflight:

- `/home/zuberi01/miniforge3/envs/pathology/bin/python`
- `/home/zuberi01/miniforge3/envs/virchow2/bin/python`
- `/home/zuberi01/miniforge3/envs/erin/bin/python`

Selected environment:

`/home/zuberi01/miniforge3/envs/pathology/bin/python`

Selection reason: it is the most pathology/WSI-aligned passing environment; external
`.conda_mil` timed out during runtime preflight.

Row 0 was attempted with the selected environment:

- case/model: `A_true_positive_early_02` / `abmil`
- success: yes
- generated externally: top tile grid, bottom tile grid, heatmap overlay, shuffled
  heatmap overlay, tile-score CSV, metadata JSON
- `B_false_negative_07`: not attempted

The dry-run summary marks row 0 ready for thesis review at the output-presence level:
top patches, tile scores, and heatmap/overlay outputs were found. Next step is to
inspect row 0 outputs before running the missed-progressor case or all 8 cases.

## Histology dry-run output validation

Row 0 structural validation:

- case/model: `A_true_positive_early_02` / `abmil`
- result: valid
- outputs found externally: top tile grid, bottom tile grid, heatmap overlay, shuffled
  heatmap overlay, tile-score CSV, metadata JSON
- tiles scored: `256`

Because row 0 was structurally valid, the second dry-run case was run:

- case/model: `B_false_negative_07` / `abmil`
- result: success
- structural validation: valid
- outputs found externally: top tile grid, bottom tile grid, heatmap overlay, shuffled
  heatmap overlay, tile-score CSV, metadata JSON
- tiles scored: `256`

Both dry-run cases are ready for manual visual inspection. This confirms the
case-level ABMIL histology interpretation pipeline is functioning for the two selected
dry-run examples, but it does not yet validate the biological content of the images.

Recommendation: manually inspect the two external visual outputs first. If they look
correct, it is reasonable to run the remaining 6 selected cases with the same
`pathology` environment and external output root.

## Histology interpretation regeneration status

Manual visual inspection of the first two dry-run cases was completed and judged valid
enough to proceed. The remaining 6 selected cases were then run one at a time with:

`/home/zuberi01/miniforge3/envs/pathology/bin/python`

All 8 selected LGD2+ cases now have structurally complete external ABMIL histology
outputs:

- `A_true_positive_early_01`
- `A_true_positive_early_02`
- `B_false_negative_07`
- `C_false_positive_12`
- `E_cnv_rescue_19`
- `F_histology_rescue_24`
- `G_fusion_hurt_26`
- `I_modality_disagreement_37`

External output root:

`analysis/lgd2_interpretation_regeneration_20260707/histology/dry_run/wsi/`

Per-case external outputs include:

- `top_tiles_grid.png`
- `bottom_tiles_grid.png`
- `heatmap_overlay.png`
- `heatmap_overlay_shuffle.png`
- `tile_scores.csv`
- `metadata.json`

Lightweight all-8 reports now live in:

- `lgd2_histology_all8_output_audit.csv` / `.md`
- `lgd2_histology_all8_interpretation_summary.csv` / `.md`
- `lgd2_histology_all8_warnings.md`
- `lgd2_histology_all8_execution_log.md`
- `lgd2_histology_case_category_comparison.md`

No WSI files, tile images, heatmaps, overlays, feature tensors, checkpoints, or full
tile-score dumps are committed to Git. Next recommended step: manually inspect all 8
external visual outputs and choose final thesis figures. Do not make biological claims
from the lightweight score summaries alone.

## Histology figure-candidate decision

Manual visual review found all 8 regenerated ABMIL histology outputs acceptable for
the current Chapter 1 candidate pool. All 8 are therefore retained for later final
figure selection while the full chapter narrative is written.

Candidate manifest:

- `lgd2_histology_final_figure_candidates.csv`
- `lgd2_histology_final_figure_candidates.md`

Current decision:

- include all 8 as histology interpretation candidates;
- do not choose the final main-figure subset yet;
- revisit selection after LGD2+ CNV windows/genes and fusion/composite case summaries
  are available;
- use remaining valid cases as supplementary candidates if they do not fit the main
  chapter narrative.

## First multimodal case-study packs

The first lightweight LGD2+ multimodal case-study packs have been assembled for:

- `A_true_positive_early_02`
- `B_false_negative_07`
- `E_cnv_rescue_19`

Fusion probability interpretation is complete for these cases using existing CNV-only, ABMIL image-only, and early-fusion probabilities. Histology panels are available externally for all selected cases and include top/bottom tile grids, heatmap overlays, shuffled overlays, tile-score tables, and metadata JSON.

CNV region/gene interpretation was not generated in this stage. The selected cases have CNV probabilities and CNV IDs, but LGD2+ feature-importance, feature-matrix/model, and window-to-gene-map inputs remain unvalidated. The case packs are therefore ready for thesis drafting at the probability-plus-histology level, with CNV panels marked as pending.

New lightweight files:

- `lgd2_multimodal_case_pack_selection.csv` / `.md`
- `lgd2_fusion_case_interpretation.csv` / `.md`
- `lgd2_case_storyboard_first3.md`
- `lgd2_case_pack_histology_panel_inventory.csv` / `.md`
- `lgd2_case_pack_cnv_input_status.csv` / `.md`
- `lgd2_case_pack_cnv_top_windows.csv` / `.md`
- `lgd2_multimodal_case_figure_plan_first3.md`

## Which model to interpret first

Recommended order (matches manifest thesis priority):

1. `lgd2_early_fusion_uni2` (`early_mean_mlp`) — strongest early-prediction-only AUPRC/AUC; primary interpretation target.
2. `lgd2_cnv_core` (`cnv_random_forest`) — molecular baseline for CNV windows/genes.
3. best validated image-only model, `lgd2_image_uni2` (`abmil`) — histology baseline.
4. `lgd2_early_fusion_gigapath` — only if an AUC comparison is needed (strongest all-samples AUC).
5. Do **not** prioritise `lgd2_foundation_combo` until its `patient_id` join is validated.

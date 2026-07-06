# Barrett LOPO / LGD2+ Follow-up Audit

## Executive summary

- Current named canonical master is LGD3+: `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`.
- Endpoint generation is configurable in `scripts/rebuild_lgd3plus_canonical_union_progressor.py`, with defaults `event_grade_threshold=3`, `lgd_streak_threshold=3`, and `next_biopsy_lgd_streak_threshold=3`.
- Exact LGD3+ next-biopsy rule in canonical metadata: `NextBiopsyLabel>=3 OR (NextBiopsyLabel==2 AND LGDStreakSoFar>=2)`.
- LGD2+ derived tables and 5-fold result folders exist, especially `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv` and `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/`.
- Full canonical 20260304 LGD3+ LOPO results for CNV/image/fusion were not found in audited files; canonical headline results are 5-fold patient-disjoint CV.
- LOPO exists mainly for Killcoyne/CNV reproduction outputs and older Virchow2 MIL checkpoints; reusable MIL LOPO prediction/metric CSVs were not found.
- Canonical master has 172 rows with `DaysFromCurrentToEvent == 0`; these are included in `Progressor_label` and all `AtRisk_1y` to `AtRisk_5y`.
- Patient-level aggregation metrics already exist for LGD3+ 5-fold CV; PPV/NPV and patient confusion matrices are not directly output by the main metric helper.
- Interpretability outputs exist for LGD3+ histology, CNV, and multimodal case figures; LGD2+ interpretability outputs were not found.
- If final thesis endpoint is LGD2+ and evaluation must be LOPO, the clean final result set would require new LOPO jobs plus patient-level detection recomputation.

## 1. LGD2+ versus LGD3+

- Answer: current canonical endpoint is LGD3+ by name and metadata, but endpoint generation is configurable.
- Threshold definition: `scripts/rebuild_lgd3plus_canonical_union_progressor.py:53-88` defines `--event_grade_threshold`, `--lgd_streak_threshold`, `--next_biopsy_lgd_streak_threshold`, and `--next_biopsy_task_name`.
- Exact LGD streak code: `canon_row_event = (gi >= event_grade_threshold) | ((gi == 2) & (lgd >= lgd_streak_threshold))` at `scripts/rebuild_lgd3plus_canonical_union_progressor.py:157-161`.
- Exact next-biopsy code: `next_lgd_needed_before = max(int(next_biopsy_lgd_streak_threshold) - 1, 0)` then `NextBiopsyLabel>=event_grade_threshold` or `NextBiopsyLabel==2 AND LGDStreakSoFar>=next_lgd_needed_before` at `scripts/rebuild_lgd3plus_canonical_union_progressor.py:190-196`.
- Canonical LGD3+ metadata: `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/meta.json` says `NextBiopsyProgression_LGD3plus = 1 if NextBiopsyLabel>=3 OR (NextBiopsyLabel==2 AND LGDStreakSoFar>=2)`.
- LGD2+ derived evidence: `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv` has `NextBiopsyProgression_LGD2plus` with 231 positive, 690 negative, 38 NaN rows; 959 rows, 160 patients.
- Other LGD2/LGD2-like derived folders: `data/derived_nextbiopsy_lgd2_CANONICAL_ONLY_20260318/`, `data/derived_nextbiopsy_lgd3plus_CANONICAL_union_progressor_lgd2_20260318/`.
- LGD2+ result folders exist, e.g. `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/` and `data/foundation_grid_runs/campaign_lgd2_clinical_augmentation_20260319_190949/`, but they are 5-fold CV, not LOPO.
- Switching from LGD3+ to LGD2+ requires regenerating or reselecting the derived master, task registry, split/task manifests, all model results, patient/biopsy aggregation reports, clinical detection reports, and interpretability/case figures for the new endpoint.
- Existing LGD3+ results become obsolete for the main endpoint if LGD2+ is chosen, but remain valid as supplementary/exploratory LGD3+ analyses.
- HGD/IMC/OAC are always counted regardless of LGD streak through `gi >= event_grade_threshold` / `NextBiopsyLabel >= event_grade_threshold`.
- Confidence: High.

## 2. LOPO availability

| model/result type | endpoint | cohort | path | number of folds/patients | metrics | status |
|---|---|---|---|---:|---|---|
| CNV Killcoyne reproduction | Progressor-like | strict 500kb repro v2 | `data/killcoyne_repro_strict_500kb_slurm_v2/consistency_audit_report_20260217.json` | 160 patients in manifest; 940/820/671 samples by condition | AUC by condition: 0.600/0.524/0.187 | obsolete/exploratory |
| CNV Killcoyne paper faithful | Progressor-like | discovery full | `analysis/killcoyne_paperfaithful_discovery_full_20260323_133835/lopo_summary.csv` | 3 conditions; `n_patients` column | AUC 0.780/0.750/0.664 | preliminary/useful baseline |
| CNV Killcoyne paper faithful | Progressor-like | fullsplit | `analysis/killcoyne_paperfaithful_fullsplit_20260427_145056/*/lopo_summary.csv` | per-condition `n_patients` column | AUC 0.801 all, 0.792 exclude HGD/IMC, 0.732 exclude LGD/HGD/IMC | best existing CNV LOPO baseline |
| CNV fixed-lambda panels | Progressor-like | truepath panels | `analysis/fixed_lambda_lopo_truepath_panels_20260428_1048/fixed_lambda_lopo_summary.csv` | `n_patients` column | fixed-lambda LOPO AUC 0.843/0.817/0.799 | useful CNV/panel LOPO |
| CNV/histology-label direct panels | Progressor-like | sample histology panel variants | `analysis/lopo_histology_direct_panels_20260428_1205/summary.csv` | `n_patients` column | sample LOPO AUC 0.843/0.817/0.799 fixed-lambda; 0.821/0.812/0.736 inner-CV | exploratory; not WSI MIL |
| CNV paper repro hg38 | Progressor-like | 50kb/500kb 20260226 | `data/killcoyne_paper_repro_hg38_50kb_20260226_173900/lopo_predictions.csv`, `data/killcoyne_paper_repro_hg38_500kb_20260226_173900/lopo_predictions.csv` | 88 patients, 731 unique samples | saved `y_true`, `y_pred_prob`; no summary in file | obsolete/exploratory |
| Image-only MIL LOPO code | `y_progressor` | old manifest default | `scripts/run_mil_lopo.py`, `image_mil/lopo.py` | one held-out `patient_id` per loop | pooled binary metrics if run | code support only |
| Image-only MIL LOPO artifacts | `y_progressor` | older Virchow2 MIL rerun | `data/virchow2_mil_runs/rerun_20260217_152953/lopo/` | many patient checkpoint files | no CSV/JSON predictions or metrics found | incomplete/obsolete |
| Canonical LGD3+ foundation results | `NextBiopsyProgression_LGD3plus` | 20260304 canonical | `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/` | 5 folds, not LOPO | AUC/AUPRC/sens/spec/Brier in summaries | final 5-fold CV, not LOPO |
| LGD2+ foundation results | `NextBiopsyProgression_LGD2plus` | strict LGD2 canonical | `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/` | 5 folds, not LOPO | AUC/AUPRC/sens/spec/Brier | preliminary/final-candidate CV, not LOPO |
| Survival/time-window | LGD2+ strict next-biopsy | patient-day | `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/survival_summary.csv` | GroupKFold/OoF, not LOPO | c-index, time-dependent AUC | supplementary, not LOPO |

- LOPO code supports image-only MIL (`pool_mean`, `pool_max`, `abmil`) but not audited as supporting late/early/intermediate fusion, co-attention, foundation fusion, or survival LOPO.
- LOPO results for canonical 20260304 LGD3+ cohort: Not found in audited files.
- LOPO results for LGD2+: Not found in audited files.
- Held-out predictions are saved for several CNV LOPO outputs (`lopo_predictions*.csv` with `patient_id`, `sample_id`, `y_true`, `y_pred_prob`). MIL reusable held-out prediction files were not found.

## 3. Limits of LOPO

- Canonical full cohort has 160 patients; full LOPO would require 160 held-out patient evaluations per endpoint/model/condition.
- Manifest condition patient counts: `all_samples` 160, `exclude_hgd_imc` 154, `exclude_lgd_hgd_imc` 151.
- Canonical patient positives: `Progressor_label` has 38 positive patients and 122 negative patients; `NextBiopsyProgression_LGD3plus` evaluable patient labels have 51 positive and 104 negative patients across 155 patients.
- Single-patient folds can be single-class; per-fold AUC is unstable/undefined. `image_mil/lopo.py:63-72` pools all held-out predictions for final metrics.
- `image_mil/lopo.py:37-47` supports full retraining per held-out patient for image-only MIL by calling `train_one_fold`; it is not just evaluation of precomputed predictions.
- Current LOPO code records sample-level predictions and pooled sample-level metrics. Patient-level aggregation before metric calculation is not built into `image_mil/lopo.py`.
- Existing canonical foundation models use 5 patient-disjoint folds, not LOPO. Full LOPO for image/fusion models would need new jobs.
- Existing LOPO warnings/cost notes: no explicit warning file found; cost is implied by one model retrain per patient and chunking args `--chunk_id/--num_chunks` in `scripts/run_mil_lopo.py:40-42`.

## 4. At-event versus early-prediction handling

- Canonical master at-event count: 172 rows, 38 patients, 70 biopsies where `DaysFromCurrentToEvent == 0`.
- All at-event rows have `Progressor_label == 1`.
- At-event rows in `NextBiopsyProgression_LGD3plus`: 93 positive, 75 negative, 4 NaN.
- At-event rows in `AtRisk_1y` to `AtRisk_5y`: all 172 are positive for every year.
- At-event current grades: HGD 84, IMC 36, LGD 33, NDBE 16, ID 2, OAC 1.
- At-event event types: `HGD+` 94 rows, `LGDx3` 78 rows.
- Manifest condition membership: at-event rows remain in `all_samples` 171 joined rows, `exclude_hgd_imc` 51, and `exclude_lgd_hgd_imc` 18; grade-based exclusions do not fully remove all event rows.
- Existing early-prediction-style report: `reports/progressor_distance_to_progression_20260306_104927/summary.md:7-9` defines event as first `CurrentGradeInt >= 3`, excludes the progression biopsy itself, and includes pre-progression `CurrentGradeInt <= 2`.
- Clean LGD3+/LGD2+ early-prediction filter not found as a reusable condition. Simple filter: keep non-progressors plus progressors with `DaysFromCurrentToEvent > 0`; equivalently exclude `DaysFromCurrentToEvent == 0` and, for strict future next-biopsy prediction, require non-null next-biopsy label.
- Existing canonical 5-fold all-samples results include at-event samples. The progressor distance-to-progression report excludes HGD/IMC/OAC progression biopsy itself but is not the full LGD3+ event definition.

## 5. Patient-level clinical detection metrics

- Main metric helper `image_mil/metrics.py:80-121` computes ROC AUC, AUPRC, accuracy, balanced accuracy, sensitivity, specificity, Brier, ECE, sensitivity at specificity 90/95, specificity at sensitivity 90/95, and threshold.
- PPV, NPV, explicit TP/FP/TN/FN, false positives per detected progressor, and confusion matrices are not returned by `binary_metrics`, although `_safe_confusion` exists internally.
- Threshold is fixed at 0.5 in `binary_metrics` by default; CV scripts also expose threshold options, and aggregation report states threshold 0.5.
- Patient-level metrics already exist for canonical LGD3+ 5-fold CV in `reports/biopsy_patient_aggregation_20260306_102801/summary.md`.
- Example patient-level LGD3+ metrics: multimodal `NextBiopsyProgression_LGD3plus` patient_max AUC 0.886, sensitivity 0.922, specificity 0.567, n=155; `Progressor_label` multimodal patient_max AUC 0.902, sensitivity 0.868, specificity 0.787, n=160.
- Detection-oriented outputs exist in `reports/progressor_distance_to_progression_20260306_104927/`, including never-caught patients and distance-to-progression metrics.
- Best script to adapt for patient-level clinical detection metrics: `scripts/evaluate_biopsy_patient_aggregation.py`, adding PPV/NPV/confusion/count outputs and applying the desired early-prediction filter.
- Saved predictions in foundation CV folders and aggregation inputs appear sufficient to recompute patient-level clinical metrics for 5-fold CV. LOPO recomputation requires saved LOPO held-out predictions; these were found for CNV baselines, not canonical image/fusion.

## 6. Biological interpretation outputs

### Histology

- WSI/top-patch outputs exist for LGD3+ in `analysis/explainability/wsi/NextBiopsyProgression_LGD3plus/...`.
- Clinician-facing batch outputs exist at `analysis/clinician_figures_nextbiopsyprogression_batch10/`; `selected_cases.csv` links `patient_id`, `sample_id`, current grade, next biopsy date, model probabilities, and case folders.
- Batch10 attention summaries exist: `analysis/clinician_figures_nextbiopsyprogression_batch10/figures/attention_spread_metrics_summary.csv` and per-case tile-score paths in `attention_spread_metrics_per_case.csv`.
- Histology top patches are available for image-only and multimodal selected cases.
- LGD2+ histology interpretability outputs: Not found in audited files.

### CNV

- CNV explainability root exists: `analysis/cnv_explainability/README.md`.
- CNV masks/importances/gene maps are documented for `NextBiopsyProgression_LGD3plus`, including `analysis/cnv_explainability/importances_aggregated/...`, `masks/...`, and `gene_maps/...`.
- Clinician figures include `analysis/clinician_figures/cnv/top_regions.csv`.
- Batch10 LGD3+ CNV outputs include `cnv_top_windows_batch10_cnv_only.csv`, `cnv_top_genes_batch10_cnv_only.csv`, `cnv_top_windows_batch10_multimodal.csv`, and `cnv_top_genes_batch10_multimodal.csv`.
- Outputs are available for CNV-only and multimodal selected cases. LGD2+ CNV interpretation outputs: Not found in audited files.

### Multimodal

- Modality dependence outputs exist: `analysis/clinician_figures_nextbiopsyprogression_batch10/modality_dependence_batch10.csv` and per-case `modality_dependence.txt`.
- Modality weight/time reports exist: `reports/modality_weight_time_to_progression_20260306_131818/summary.md`.
- Fusion rescue/hurt case-study outputs exist: `reports/progressor_fusion_rescue_hurt_20260306_112609/`, including rescue/hurt/failure CSVs.
- Case-study figures exist for selected true-positive-like next-biopsy progression cases. Systematic TP/FP/FN clinician figures for LGD2+ LOPO were not found.

## 7. Recommended Chapter 1 result set

### Already usable

- Canonical LGD3+ 5-fold patient-disjoint CV headline: `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/`.
- LGD3+ patient/biopsy aggregation: `reports/biopsy_patient_aggregation_20260306_102801/`.
- LGD3+ early/distance-to-progression analysis: `reports/progressor_distance_to_progression_20260306_104927/`.
- LGD3+ clinician/explainability figures: `analysis/clinician_figures_nextbiopsyprogression_batch10/`, `analysis/explainability/`, `analysis/cnv_explainability/`.
- CNV-only LOPO baselines: `analysis/killcoyne_paperfaithful_fullsplit_20260427_145056/` and `analysis/fixed_lambda_lopo_truepath_panels_20260428_1048/`.
- LGD2+ 5-fold CV candidate results: `data/foundation_grid_runs/campaign_lgd2_nextbiopsy_lgd2_refresh_cuda_20260319_142251/` and `data/foundation_grid_runs/campaign_lgd2_clinical_augmentation_20260319_190949/`.

### Needs rerun

- If primary endpoint is LGD2+ with LOPO: rerun CNV-only, image-only, late/early/intermediate fusion, co-attention, and selected foundation-fusion models on `data/derived_nextbiopsy_lgd2_strict_nextbiopsy_CANONICAL_ONLY_20260319/derived_master.csv`.
- If primary endpoint remains LGD3+ with LOPO: rerun the same model set on `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`.
- Generate held-out prediction CSVs with patient IDs for all LOPO model families.
- Recompute patient-level detection metrics with PPV/NPV/confusion matrices and an early-prediction-only filter excluding `DaysFromCurrentToEvent == 0`.
- Regenerate final interpretability/case figures for the chosen endpoint/evaluation setting.

### Optional/supplementary

- Survival/time-window patient-day results: `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/`.
- Killcoyne reproduction and paperfaithful CNV-only LOPO as historical baseline.
- Fusion rescue/hurt and modality dependence reports as biological/clinical interpretation sections.

### Obsolete/exploratory

- Older 50-fold and smoke result families.
- `data/killcoyne_repro_strict_500kb_slurm_v2/` LOPO AUC audit as a final thesis metric.
- `data/virchow2_mil_runs/rerun_20260217_152953/lopo/` because only checkpoints/logs were found, not reusable prediction/metric CSVs.
- LGD3+ results if the final endpoint is explicitly LGD2+.

## Not answerable from audited files

- Whether the thesis final endpoint should be LGD2+ or LGD3+.
- Whether full canonical LOPO jobs exist outside the audited folder tree.
- Whether a final clinical threshold should be fixed at 0.5, fixed specificity, or selected another way.

# Barrett Multimodal Cohort / Experiment Audit

## Executive summary

- Project root confirmed: `/mnt/scratche/slow/fmlab/zuberi01/phd/barretts_retraining/barretts_training`.
- Best current master table found: `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`.
- Main multimodal unit appears to be one row = one slide/sample record with one linked CNV path; 959 rows, 959 unique `ImageAbsPath`, 941 unique `CNVAbsPath`.
- One CNV can map to multiple slides: 15 duplicated `CNVAbsPath` values across 33 rows.
- Patient/biopsy hierarchy is explicit: 160 patients, 470 biopsy IDs, 959 slide/sample rows.
- Splits are manifest-based and patient-disjoint in audited training code; `dataset_manifest.csv` has 10 fold columns.
- Progression endpoint is not one single clean concept: `Progressor_label` is patient-level, while `NextBiopsyProgression_LGD3plus` and `AtRisk_*` use future/current event logic.
- Canonical LGD3+ rebuild script defines event as `CurrentGradeInt>=3 OR (CurrentGradeInt==2 AND LGDStreakSoFar>=threshold)`, i.e. HGD/IMC/OAC plus LGD-streak rule.
- Existing results cover CNV-only, image-only, multimodal early/intermediate/coattention, late/foundation fusion, survival/time-window, and interpretability.
- Most urgent verification: whether `dataset_manifest.csv` plus `derived_master.csv` are the intended thesis-final cohort/split, because older 50-fold and newer 5-fold result families coexist.

## Key files inspected

| path | type | apparent purpose | why it matters |
|---|---|---|---|
| `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv` | CSV | Canonical sample/slide/CNV/task table | Best master cohort table found; 959 rows, 59 columns |
| `data/dataset_master_final_ready_nosplits.csv` | CSV | Older master sample table | Same core 959-row structure, before LGD3+ additions |
| `data/killcoyne_repro_strict_500kb_slurm_v2/dataset_manifest.csv` | CSV | Training manifest with splits | Defines `condition`, `sample_id`, `patient_id`, labels, 10 fold columns |
| `slide_matching.xlsx` | XLSX | Endoscopy/sample/slide matching workbook | Contains `EndoscopySampleID`, `EndoscopyID`, `PatientID`, `PathCaseID`, `Slide file` |
| `configs/tasks_dataset_master.json` | JSON | Task registry | Lists progression, current-grade, next-biopsy, timing tasks |
| `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/tasks_lgd3plus_canonical.json` | JSON | Canonical LGD3+ task registry | Adds `NextBiopsyProgression_LGD3plus`, `NextBiopsyTier3` |
| `image_mil/data.py` | Python | CV split helper | `get_cv_split()` and `assert_patient_disjoint()` prove patient-disjoint split enforcement |
| `scripts/run_mil_cv.py`, `scripts/run_mil_cnv_only_cv.py`, `scripts/run_mil_multimodal_cv.py` | Python | Image/CNV/multimodal CV entry points | Use manifest splits and assert patient disjointness |
| `scripts/rebuild_lgd3plus_canonical_union_progressor.py` | Python | Canonical label rebuild | Documents progressor and LGD3+ event rules |
| `scripts/evaluate_biopsy_patient_aggregation.py` | Python | Sample-to-biopsy/patient aggregation | Shows sample rows are aggregated to biopsy/patient for evaluation |
| `data/virchow2_mil_runs/global_results_summary.csv` | CSV | Older 50-fold model summary | Main pre-canonical inventory of 985 result rows |
| `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/global_results_summary.csv` | CSV | Newer 5-fold canonical results | Main canonical LGD3+ result table, 834 rows |
| `analysis/killcoyne_paper_repro_assessment_20260320.md` | Markdown | Killcoyne reproduction assessment | Distinguishes local/matched cohort from paper cohort |
| `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/summary.md` | Markdown | Patient-day survival summary | Explicit patient-day unit, `GroupKFold` by patient, time-window metrics |
| `analysis/clinical_augmentation_20260319/clinical_leakage_audit.md` | Markdown | Clinical covariate audit | Lists safe clinical variables and excluded leakage variables |

## Answers to the 12 questions

### 1. Exact modelling unit

Answer:
- Best-supported answer: **A. one CNV profile + one matched slide**, with caveat that some CNV profiles are reused across multiple slide rows.
- Canonical master has 959 rows, 959 unique `SampleID`, 959 unique `ImageAbsPath`, and 941 unique `CNVAbsPath`.
- There are 470 biopsy IDs and 160 patients, so the primary model row is below biopsy and patient level.
- Aggregation scripts later collapse sample predictions to biopsy/patient, so aggregation is downstream, not the raw unit.

Evidence:
- `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`: `SampleID`, `PatientID`, `BiopsyID_int`, `ImageAbsPath`, `CNVAbsPath`.
- `scripts/evaluate_biopsy_patient_aggregation.py`: builds `sample_id` from `CNVAbsPath`, then aggregates by `biopsy_key` and `PatientID`.

Confidence: High

Follow-up needed: Confirm thesis should use the canonical 20260304 table rather than `data/dataset_master_final_ready_nosplits.csv`.

### 2. CNV-to-slide matching

Answer:
- Can one CNV match one slide? Yes; most rows are one `CNVAbsPath` plus one `ImageAbsPath`.
- Can one CNV match multiple slides? Yes; 15 duplicated `CNVAbsPath` values across 33 rows.
- Can multiple CNVs match one slide? Not in canonical master; `ImageAbsPath` is unique across 959 rows.
- Are there unmatched CNVs? Not found in audited files as a clean unmatched-CNV manifest.
- Are there unmatched slides? Not found in audited files as a clean unmatched-slide manifest.
- Is matching stored in one clean CSV? No. Operational matching is in `derived_master.csv`; slide metadata is in `slide_matching.xlsx`.

Evidence:
- `derived_master.csv`: `ImageAbsPath`, `CNVAbsPath`, `BiopsyIDMatchType`.
- `slide_matching.xlsx`: `EndoscopySampleID`, `EndoscopyID`, `PatientID`, `PathCaseID`, `EndoscopyDate`, `Block`, `Pathology`, `Slide file`.
- Duplicate CNV examples include multiple `PS02.10762` slide levels sharing `SLX-10722_SLX-11823.D712_D501`.

Confidence: High for matched rows; Low for unmatched universe.

Follow-up needed: Locate a full slide/CNV universe manifest if unmatched counts are needed.

### 3. Patient/timepoint/biopsy hierarchy

Answer:
- Patient ID exists: `PatientID`, `PatientID_real`, `participant_id`.
- Timepoint/endoscopy-like information exists: `Date`, `EndoscopyID` in `slide_matching.xlsx`, `BiopsyIndex`, `BiopsiesTotalForPatient`.
- Biopsy ID exists: `BiopsyID_int`, `BiopsyID_real`; 470 unique biopsy IDs in canonical master.
- Slide ID/path exists: `ImageAbsPath`; `Slide file` in matching workbook.
- CNV/sample ID exists: `CNVAbsPath`; training manifest `sample_id` is the CNV directory basename.
- Timing exists: `MonthsBeforeLastBiopsy`, `DaysFromCurrentToEvent`, `Time_to_progression`, `EventDate`, `NextBiopsyDate`.

Evidence:
- `derived_master.csv`: 160 `PatientID`, 470 `BiopsyID_int`, 959 `ImageAbsPath`.
- `dataset_manifest.csv`: `sample_id`, `patient_id`, `time_to_endpoint_months`.
- `slide_matching.xlsx`: `EndoscopySampleID`, `EndoscopyID`, `PatientID`, `PathCaseID`, `EndoscopyDate`, `Slide file`.

Confidence: High

Follow-up needed: Decide whether `EndoscopyID` from `slide_matching.xlsx` should be merged into the modelling master.

### 4. Train/val/test splitting and leakage risk

Answer:
- Splits are CV folds, not a single train/val/test file.
- `dataset_manifest.csv` defines `fold_id_rep01` to `fold_id_rep10`, plus `fold_id` and `cv_rep`.
- Audited fold columns have zero patients assigned to multiple folds within a condition for reps 1-3.
- Code uses `get_cv_split()` and then `assert_patient_disjoint(train_df, test_df)`.
- Multiple fold regimes coexist: older summaries use 50 folds total (`10 reps x 5 folds`); canonical campaign uses 5 folds.
- Leakage risk: split leakage appears guarded at patient level; label/time leakage is separately discussed in Killcoyne reproduction notes.

Evidence:
- `data/killcoyne_repro_strict_500kb_slurm_v2/dataset_manifest.csv`: `patient_id`, `fold_id_rep01`...`fold_id_rep10`.
- `image_mil/data.py`: `assert_patient_disjoint()`.
- `scripts/run_mil_cv.py`, `scripts/run_mil_cnv_only_cv.py`, `scripts/run_mil_multimodal_cv.py`: call split helper and disjoint assertion.
- `analysis/01_Killcoyne_reproduction/00_master_index.md`: mentions aggregation/time-leakage probes.

Confidence: High for CV split implementation; Medium for all historical results.

Follow-up needed: Verify every headline result used the same manifest SHA if writing final thesis tables.

### 5. Progression definition

Answer:
- Labels: `Progressor_label` is binary 0/1; canonical table has 325 positive rows and 634 negative rows.
- Older `data/dataset_master_final_ready_nosplits.csv` has 420 positive and 539 negative rows, so label definitions changed.
- Endpoint is not OAC-only. Canonical event logic includes `CurrentGradeInt>=3`, where labels show HGD=3, IMC=4, OAC=5.
- LGD3+ logic also includes `CurrentGradeInt==2 AND LGDStreakSoFar>=threshold`.
- `EventType` values in canonical master: `HGD+`, `LGDx3`, and missing for non-progressors.
- Same as Killcoyne? Not documented as identical; Killcoyne reproduction is handled separately.

Evidence:
- `scripts/rebuild_lgd3plus_canonical_union_progressor.py`: `Progressor_label = old_progressor_patient OR canonical_current_biopsy_event_patient`; event rule documented.
- `derived_master.csv`: `Progressor_label`, `EventType`, `CurrentGradeInt`, `LGDStreakSoFar`.
- `analysis/killcoyne_paper_repro_assessment_20260320.md`: says local reproduction does not match paper metrics/cohort exactly.

Confidence: Medium

Follow-up needed: Confirm the clinical endpoint wording for `LGDx3` versus HGD/IMC/OAC in the thesis.

### 6. Diagnosis labels and label mapping

Answer:
- Raw/normalized labels found: `NDBE`, `ID`, `LGD`, `HGD`, `IMC`, `OAC`.
- Canonical counts: NDBE 609, LGD 155, HGD 84, ID 74, IMC 36, OAC 1.
- Numeric mapping found: `CurrentGradeInt` 0=NDBE, 1=ID, 2=LGD, 3=HGD, 4=IMC, 5=OAC.
- Labels are attached at sample/slide row level and can be aggregated to biopsy/patient.
- Binary mappings include `Progressor_label`, `Progress_in_1`...`Progress_in_5`, `AtRisk_1y`...`AtRisk_5y`, `NextBiopsyProgression_LGD3plus`.
- Multiclass mappings include `CurrentGradeInt`, `NextBiopsyLabel`, `NextBiopsyTier3`.

Evidence:
- `derived_master.csv`: `Label`, `CurrentGradeNorm`, `CurrentGradeInt`, `NextBiopsyLabel`.
- `dataset_manifest.csv`: `grade_int`, `pathology_category`.
- `configs/tasks_dataset_master.json`, `tasks_lgd3plus_canonical.json`: task types.
- `scripts/export_patient_biopsy_tables.py`: exports grade and progression fields to biopsy/event tables.

Confidence: High

Follow-up needed: Find original raw pathology text mapping code if exact raw-to-normalized curation needs citation.

### 7. Timing information

Answer:
- Yes, `MonthsBeforeLastBiopsy` exists; canonical master has 268 unique values.
- “Final” appears to mean last biopsy/surveillance endpoint for `MonthsBeforeLastBiopsy`, not necessarily progression.
- Progressor timing columns: `EventDate`, `DaysFromCurrentToEvent`, `Time_to_progression`, `EventType`.
- Non-progressor censoring appears represented by `MonthsBeforeLastBiopsy`; survival summary uses `MonthsBeforeLastBiopsy * 30.44` as censor duration.
- Separate progressor/non-progressor timing rules are implied in survival analysis, but not fully documented in one data dictionary.
- Time-window performance can be computed: `AtRisk_1y`...`AtRisk_5y` and survival `auc_365d`, `auc_730d`, `auc_1095d`, `auc_1826d` exist.

Evidence:
- `derived_master.csv`: `MonthsBeforeLastBiopsy`, `DaysFromCurrentToEvent`, `AtRisk_1y`...`AtRisk_5y`.
- `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/summary.md`: event duration and censor duration definitions.
- `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/survival_summary.csv`: time-dependent AUC columns.

Confidence: Medium

Follow-up needed: Write a one-paragraph data dictionary for “final” before thesis use.

### 8. Post-progression samples

Answer:
- Post-progression samples after event were not found in canonical master by `DaysFromCurrentToEvent < 0`; count is 0.
- At-event samples are present: `DaysFromCurrentToEvent == 0` count is 172.
- Non-progressors have missing `DaysFromCurrentToEvent` in 634 rows.
- Filters excluding advanced/current progression states exist as conditions: `exclude_hgd_imc`, `exclude_lgd_hgd_imc`.
- For next-biopsy progression figures, current biopsy non-progression filter is explicit: `CurrentGradeInt<=2`.
- At-progression samples are not globally removed from all `Progressor_label` modelling; condition-specific exclusions control this.

Evidence:
- `derived_master.csv`: `DaysFromCurrentToEvent`, `CurrentGradeInt`, `EventType`.
- `dataset_manifest.csv`: conditions `all_samples`, `exclude_hgd_imc`, `exclude_lgd_hgd_imc`.
- `analysis/clinician_figures_nextbiopsyprogression_batch10/README.md`: `non-progression filter: CurrentGradeInt<=2`.

Confidence: Medium

Follow-up needed: Decide whether thesis progression-prediction tables should exclude at-event rows by default.

### 9. Comparison to Killcoyne

Answer:
- Yes, there is extensive Killcoyne-style CNV-only reproduction.
- Local full cohort CNV runs use 160 patients / 940 samples and are explicitly not the published paper cohort.
- Discovery-like runs use 88 patients / 731 samples and still do not reproduce paper metrics/risk classes.
- CNV-only model on matched multimodal cohort exists through `dataset_manifest.csv` and `data/virchow2_mil_runs/global_results_summary.csv`.
- Original/paper and matched multimodal cohorts are distinguished in notes and result paths.

Evidence:
- `analysis/killcoyne_paper_repro_assessment_20260320.md`: paper reference, local full cohort, discovery-like cohort, bottom line.
- `analysis/killcoyne_paper_cohort_reconstruction_20260320/summary.md`: discovery/validation reconstruction status.
- `analysis/01_Killcoyne_reproduction/00_master_index.md`: canonical reproduction/audit package.
- `data/killcoyne_paper_repro_hg38_50kb_20260226_173900/summary_metrics.csv`: discovery-like 50kb results.
- `data/virchow2_mil_runs/global_results_summary.csv`: matched multimodal cohort CNV-only rows.

Confidence: High

Follow-up needed: Keep Killcoyne reproduction and multimodal matched-cohort benchmark in separate thesis tables.

### 10. Existing model results

Answer:
- CNV-only: yes.
- Histology-only / CLAM / UNI: image-only MIL results exist; files reference `uni2`, `virchow2`, `gigapath`; CLAM specifically not found in audited result labels.
- Late fusion: yes.
- Early fusion: yes, `early_mean_mlp` and `early_mean_mlp_timev1`.
- Intermediate fusion: yes, `intermediate_abmil_cnv` and `coattn_abmil_cnv`.
- Progression prediction: yes, `Progressor_label`, `Progress_in_*`, `AtRisk_*`, `NextBiopsyProgression_LGD3plus`.
- Current diagnosis / dysplasia classification: yes, `CurrentGradeInt`, `NextBiopsyLabel`, `NextBiopsyTier3`.
- Time-window performance: yes, `AtRisk_*` and survival time-dependent AUC.
- Interpretability outputs: yes, clinician figures, CNV explainability, top patches, calibration, CNV regions.

Evidence:
- See result inventory table below.

Confidence: High

Follow-up needed: Confirm whether any CLAM-specific outputs exist under a name not containing `CLAM`.

### 11. Clinical metadata

Answer:
- Additional clinical metadata exists and was audited.
- Safe features include sex/gender, age at biopsy, Barrett's circumference/maximum, hiatus hernia measures, clinical/research biopsy counts, and prior intervention variables.
- Medication, smoking, and detailed treatment history beyond prior ablation/resection/dilatation were not found in audited safe feature list.
- Clinical covariates appear used in survival analysis and are available for modelling augmentation.
- Leakage audit excludes target/future fields such as current grade, next biopsy label, date of death, future pathology events.

Evidence:
- `analysis/clinical_augmentation_20260319/clinical_feature_columns.txt`.
- `analysis/clinical_augmentation_20260319/clinical_feature_meta.json`.
- `analysis/clinical_augmentation_20260319/clinical_leakage_audit.md`.
- `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/summary.md`: clinical baseline and combined survival models.

Confidence: High

Follow-up needed: Search release manifests if smoking/medication fields are needed.

### 12. Minimum master cohort table

Answer:
- Existing best candidate: `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv`.
- It already has patient ID, biopsy ID, slide path, CNV path, progression labels, diagnosis labels, and timing fields.
- It lacks explicit split columns; merge with `data/killcoyne_repro_strict_500kb_slurm_v2/dataset_manifest.csv` via CNV basename `sample_id`.
- It lacks clean unmatched-slide/unmatched-CNV flags; those require a full slide/CNV universe manifest.
- It lacks explicit `cnv_exists` / `image_exists` booleans, but paths are present and can be checked.
- It lacks a single final `exclusion_reason`; conditions in `dataset_manifest.csv` encode some exclusions.

Evidence:
- `derived_master.csv`: master columns.
- `dataset_manifest.csv`: `condition`, `sample_id`, `patient_id`, `fold_id_rep*`, `grade_int`, `pathology_category`.
- `scripts/export_patient_biopsy_tables.py`: shows planned export names for master-cohort style columns.

Confidence: High

Follow-up needed: Merge canonical master with manifest splits and add file-existence/exclusion columns.

## Result inventory

| model/result type | path | task | cohort/version | split/fold | metrics found | status |
|---|---|---|---|---|---|---|
| CNV-only matched cohort | `data/virchow2_mil_runs/global_results_summary.csv` | `Progressor_label`, `Progress_in_*`, `AtRisk_*`, grade/time tasks | 940 CNV samples / 160 patients manifest | 50 expected folds | AUC, AUPRC, accuracy, sensitivity, specificity, calibration | preliminary/older |
| Image-only MIL | `data/virchow2_mil_runs/global_results_summary.csv` | same task registry | matched multimodal cohort | 50 expected folds | AUC etc. | preliminary/older |
| Multimodal early/intermediate/coattention | `data/virchow2_mil_runs/global_results_summary.csv` | same task registry | matched multimodal cohort | 50 expected folds | AUC etc. | preliminary/older |
| Canonical LGD3+ full coverage | `data/foundation_grid_runs/campaign_lgd3plus_CANONICAL_fullcoverage_20260304_195943/global_results_summary.csv` | `NextBiopsyProgression_LGD3plus`, `Progressor_label`, `AtRisk_*`, current/next grade | canonical 20260304 | 5 folds | AUC/AUPRC/calibration/regression metrics | likely current but needs confirmation |
| Late fusion | `data/virchow2_mil_runs/late_fusion_20260218_094553/cv_summary_metrics_late_fusion.csv` | `Progressor_label` | older matched cohort | CV folds | AUC ~0.73 top all-samples | preliminary |
| Foundation combo fusion smoke | `data/foundation_grid_runs/fusion_smoke_20260226_210743/cv_summary_foundation_combo_fusion.csv` | `Progressor_label` | foundation model fusion | smoke CV | AUC ~0.773 | preliminary |
| Killcoyne CNV reproduction 50kb | `data/killcoyne_paper_repro_hg38_50kb_20260226_173900/summary_metrics.csv` | progressor/non-progressor | discovery-like 88 patients / 731 samples | 50 folds | best mean AUC 0.6762 CV; LOPO 0.7902 in assessment | obsolete for final model, useful baseline |
| Killcoyne CNV reproduction 500kb | `data/killcoyne_paper_repro_hg38_500kb_20260226_173900/summary_metrics.csv` | progressor/non-progressor | discovery-like 88 patients / 731 samples | 50 folds | best mean AUC 0.6776 CV; LOPO 0.7771 in assessment | obsolete/baseline |
| CNV-only optimization | `analysis/cnv_only_optimization_20260505/README.md` | Killcoyne post-QC cohorts | hg19/hg38 optimized CNV-only | LOPO/nested outputs | leaderboard files described | unclear/follow-up |
| Survival/time-window | `analysis/patientday_survival_strict_lgd2_nextbiopsy_20260319_v2/survival_summary.csv` | eventual progression survival | strict LGD2 next-biopsy patient-day | `GroupKFold` by patient | c-index, mean td-AUC, 1/2/3/5y AUC | likely current survival analysis |
| Interpretability: clinician figures | `analysis/clinician_figures/README.md` | `Progressor_label`, `NextBiopsyProgression_LGD3plus` | selected cases | existing checkpoints | AUCs, calibration flags, top patches, CNV regions | presentation/interp |
| Interpretability: next-biopsy batch10 | `analysis/clinician_figures_nextbiopsyprogression_batch10/README.md` | `NextBiopsyProgression_LGD3plus` | selected true-positive cases | existing checkpoints | AUCs, confidence, calibration, modality dependence | presentation/interp |
| CNV explainability | `analysis/cnv_explainability/README.md` | `NextBiopsyProgression_LGD3plus` | CNV masks/top regions | existing outputs | masks, importance, gene maps | exploratory/interp |

## Suggested master cohort table

Use `data/derived_nextbiopsy_lgd3plus_CANONICAL_20260304_154336/derived_master.csv` as the base. It should be merged with `data/killcoyne_repro_strict_500kb_slurm_v2/dataset_manifest.csv` by `sample_id = basename(CNVAbsPath)` to add `condition` and `fold_id_rep*`.

Minimum extra columns to add:

- `slide_id` or normalized slide filename from `ImageAbsPath`
- `cnv_id` from basename of `CNVAbsPath`
- `split_condition` and `fold_id_rep01`...`fold_id_rep10`
- `cnv_exists`
- `image_exists`
- `included_in_cnv_only_cohort`
- `included_in_multimodal_cohort`
- `exclusion_reason`
- `unmatched_cnv_flag`
- `unmatched_slide_flag`

Questions not answerable from audited files:

- Full count of unmatched CNVs.
- Full count of unmatched slides.
- Whether the 20260304 canonical table is thesis-final.
- Exact original raw pathology-to-grade curation trail.
- Whether smoking/medication fields exist outside the audited clinical feature release.

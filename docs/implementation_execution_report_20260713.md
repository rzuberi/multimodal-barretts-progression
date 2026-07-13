# Chapter 1 State Repair and Late-Fusion Integration Report

## Outcome
- overall status: **complete** (CNV interpretation remains BLOCKED by design, documented with exact next command)
- starting commit: `fc22568` (clean repo, branch `main`)
- final commit: see branch tip of `chapter1-late-fusion-integration` (recorded at push)
- branch and push/merge status: branch `chapter1-late-fusion-integration`; push/merge status recorded in the Git section below.

## Documentation corrections
Stale claims corrected:
- "early-prediction-only analysis remains supplementary/missing" — early-prediction-only is COMPLETE.
- "patient table lacks AUPRC/Brier/PPV/NPV/FP-TN/operating points" — all COMPLETE with bootstrap CIs.
- "LGD2+ interpretation outputs were not found" / "biological interpretation outputs were not found" — ABMIL histology COMPLETE for all 8 cases; probability-level fusion interpretation complete for first 3 packs.
- "do not run all 8 cases yet" — RESOLVED (relabelled as historical provenance).
- generated caveat "LGD2+ interpretability outputs are still missing" — replaced (via script 04) with a precise status line.
Files updated:
- `PROJECT_STATE.md` (Known Risks → Completed + Remaining Gaps).
- `README.md` (interpretation line).
- `docs/final_results_manifest.md` (status table: histology COMPLETE, fusion PARTIAL, late fusion COMPLETE, early-prediction COMPLETE; CNV still MISSING/BLOCKED).
- `docs/lgd2_completion_audit.md` (RESOLVED banner; historical table retained).
- `reports/thesis_ch1/lgd2_interpretation_summary.md` (superseded "do not run all 8" note).
- `reports/thesis_ch1/lgd2_results_interpretation.md` + `lgd2_table_generation_warnings.md` (regenerated via scripts 04/02).
- outer `current_updare.md` renamed to `current_update.md` and rewritten as a current handover (operational; not tracked in clean repo). Unsupported `environment.yml` claim removed.
Unresolved documentation conflicts: none identified after a targeted stale-text rescan.

## Late-fusion code migration
- source files migrated (logic only, path-independent): outer `scripts/run_late_fusion_cv.py`, `scripts/lgd2_late_fusion_prep.py`.
- clean files added: `src/barrett/evaluation/late_fusion.py`, `scripts/14_run_lgd2_late_fusion.py`, `tests/test_late_fusion.py`.
- fold-purity / leakage safeguards: `stack_logit` fits only on other folds of the same condition/rep; `merge_oof` rejects label disagreements and any patient crossing held-out folds; single-class training folds fall back to mean with a recorded `stack_note`.
- output guard: `run_late_fusion` refuses to write inside the clean repo (except temp/test dirs).
- sklearn imported lazily inside the stacking function.
- environment used: `erin` (`/home/zuberi01/miniforge3/envs/erin/bin/python`) because `barretts_multimodal` lacks scikit-learn. No packages installed, no envs altered. External late-fusion jobs were NOT rerun to prove the code (existing outputs used; toy tests validate the logic).

## Manifest integration
- result IDs added: `lgd2_late_fusion_uni2`, `lgd2_late_fusion_virchow2`, `lgd2_late_fusion_gigapath` (schema unchanged; 26 columns).
- external paths used: `data/lgd2_late_fusion_20260713/<enc>/` with `cv_summary_metrics_late_fusion.csv` and `cv_predictions_late_fusion.csv`.
- methods included: `mean`, `stack_logit`. Excluded embedded `cnv_only`, `img_only` (they have canonical manifest rows).

## Cohort and join validation
| result_id | method | rows(sample) | patients | positive | negative | folds | multi-fold patients | duplicates | join key | status |
|---|---|---|---|---|---|---|---|---|---|---|
| lgd2_late_fusion_uni2 | mean/stack | 903 | 155 | 55 | 100 | 5 | 0 | 0 | prediction.patient_id; sample_id->basename(CNVAbsPath) | OK |
| lgd2_late_fusion_virchow2 | mean/stack | 903 | 155 | 55 | 100 | 5 | 0 | 0 | prediction.patient_id; sample_id->basename(CNVAbsPath) | OK |
| lgd2_late_fusion_gigapath | mean/stack | 903 | 155 | 55 | 100 | 5 | 0 | 0 | prediction.patient_id; sample_id->basename(CNVAbsPath) | OK |

No SKIP/WARN warnings were emitted for any late-fusion row (no missing patient IDs, no label disagreements, no multi-fold patients, no duplicates). Early-prediction filter removed 165 sample rows; early-prediction patient counts 150/50/100.

## Patient-level results: all samples (patient_max, threshold 0.5)
| encoder | method | AUPRC | ROC AUC | sensitivity | specificity | PPV | NPV | TP | FP | TN | FN | Brier | FP/detected |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uni2 | mean | 0.781 | 0.864 | 0.691 | 0.820 | 0.679 | 0.828 | 38 | 18 | 82 | 17 | 0.170 | 0.474 |
| uni2 | stack_logit | 0.741 | 0.827 | 0.436 | 0.940 | 0.800 | 0.752 | 24 | 6 | 94 | 31 | 0.165 | 0.250 |
| virchow2 | mean | 0.796 | 0.876 | 0.745 | 0.870 | 0.759 | 0.861 | 41 | 13 | 87 | 14 | 0.169 | 0.317 |
| virchow2 | stack_logit | 0.772 | 0.846 | 0.491 | 0.930 | 0.794 | 0.769 | 27 | 7 | 93 | 28 | 0.162 | 0.259 |
| gigapath | mean | 0.728 | 0.834 | 0.818 | 0.700 | 0.600 | 0.875 | 45 | 30 | 70 | 10 | 0.171 | 0.667 |
| gigapath | stack_logit | 0.568 | 0.759 | 0.218 | 0.800 | 0.375 | 0.650 | 12 | 20 | 80 | 43 | 0.195 | 1.667 |

## Patient-level results: early prediction only (patient_max, threshold 0.5)
| encoder | method | AUPRC | ROC AUC | sensitivity | specificity | PPV | NPV | TP | FP | TN | FN | Brier | FP/detected |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uni2 | mean | 0.689 | 0.811 | 0.580 | 0.820 | 0.617 | 0.796 | 29 | 18 | 82 | 21 | 0.179 | 0.621 |
| uni2 | stack_logit | 0.654 | 0.771 | 0.380 | 0.940 | 0.760 | 0.752 | 19 | 6 | 94 | 31 | 0.175 | 0.316 |
| virchow2 | mean | 0.680 | 0.791 | 0.600 | 0.870 | 0.698 | 0.813 | 30 | 13 | 87 | 20 | 0.184 | 0.433 |
| virchow2 | stack_logit | 0.652 | 0.757 | 0.380 | 0.930 | 0.731 | 0.750 | 19 | 7 | 93 | 31 | 0.180 | 0.368 |
| gigapath | mean | 0.608 | 0.754 | 0.600 | 0.700 | 0.500 | 0.778 | 30 | 30 | 70 | 20 | 0.192 | 1.000 |
| gigapath | stack_logit | 0.507 | 0.689 | 0.180 | 0.800 | 0.310 | 0.661 | 9 | 20 | 80 | 41 | 0.211 | 2.222 |

## Comparison with locked headline
- Headline unchanged: `lgd2_early_fusion_uni2` (`early_mean_mlp`) remains strongest by AUPRC in both analysis sets (all-samples patient_max AUPRC 0.849; early-prediction 0.764). Best late fusion (virchow2, mean, AUPRC 0.796 all-samples) does not exceed it. No material contradiction to record.
- Mean vs stacked: simple probability `mean` beats fold-pure `stack_logit` on every encoder and both analysis sets. Stacking mainly trades sensitivity for specificity (e.g. uni2 all-samples sens 0.436 vs 0.691). Do not present stacking as the stronger late-fusion variant.
- Analysis-set consistency: conclusions are consistent between all-samples and early-prediction-only.
- Confidence-interval caveat: bootstrap CIs are in the patient-level CSVs and overlap substantially across fusion strategies; differences among fusion variants and against early fusion are not claimed as statistically significant on point estimates alone.

## Regression checks
- Existing (non-late-fusion) patient-level rows: **unchanged**. Max absolute difference across all 90 pre-existing rows vs commit `fc22568` = 0.000e+00 in both analysis sets; no existing keys dropped. The only additions are 30 late-fusion rows per analysis set (3 encoders × 2 methods × 5 aggregations).

## CNV interpretation status
- Inputs validated: fold-level CNV prediction probabilities for the three packs (A→fold2, B→fold3, E→fold4); genome build for the gene map (GRCh38, GENCODE v46).
- Missing (BLOCKERS): no persisted CNV estimator or exported LGD2+ feature-importance; no LGD2+ feature/window matrix as a standalone input; no LGD2+ window-to-gene map; the planned external `.../cnv_feature_importance/` directory does not exist. LGD3+ legacy importance is a different endpoint (task-conditioned) and is not valid primary LGD2+ evidence.
- Outputs generated: none (correctly kept BLOCKED; no results manufactured).
- Exact next command (run externally, writes outside Git; requires the validated LGD2+ task registry):
  ```bash
  python scripts/cnv_feature_importance.py --mode build_worklist \
    --out_root analysis/lgd2_interpretation_regeneration_20260707/cnv_feature_importance \
    --task_registry <LGD2_TASK_REGISTRY> \
    --worklist_csv .../cnv_feature_importance/admin/importance_worklist.csv
  # then --mode row per row, --mode aggregate; then cnv_bins_to_genes.py with
  # data/reference/gencode.v46.annotation.gtf.gz; finally:
  python scripts/07_summarise_lgd2_cnv_interpretation.py
  ```
  If a precomputed LGD2+ top-windows/importance CSV is supplied into that directory, `scripts/07_summarise_lgd2_cnv_interpretation.py` alone unblocks the summary with no refit.

## Tests and safety
- commands run: `pytest -q` (erin env); `py_compile` on all changed/new Python; `git diff --check`; `./scripts/assert_no_data_tracked.sh`.
- results: pytest **58 passed** (incl. 7 new late-fusion tests). py_compile OK. `git diff --check` clean (fixed stray `\r` line endings in 3 appended manifest rows). `assert_no_data_tracked.sh`: OK, no forbidden data-like files tracked.
- pytest availability: available in `erin`; not in `barretts_multimodal`.
- confirmation heavy files stayed external: all late-fusion predictions/summaries remain under `data/lgd2_late_fusion_20260713/` (external); only small allowlisted summary CSVs/MDs under `reports/thesis_ch1/` are tracked.

## Files changed
- added: `src/barrett/evaluation/late_fusion.py`, `scripts/14_run_lgd2_late_fusion.py`, `tests/test_late_fusion.py`, `docs/implementation_execution_report_20260713.md`.
- modified: `src/barrett/evaluation/io.py`, `src/barrett/evaluation/tables.py`, `scripts/02_recompute_patient_detection_metrics.py`, `scripts/04_make_main_results_table.py`, `docs/final_results_manifest.csv`, `docs/final_results_manifest.md`, `docs/lgd2_completion_audit.md`, `PROJECT_STATE.md`, `README.md`, and regenerated `reports/thesis_ch1/` metric/comparison/interpretation files.
- renamed (outer, untracked): `current_updare.md` → `current_update.md`.

## Remaining work
- LGD2+ CNV region/gene interpretation (BLOCKED; needs a compute run, not lightweight).
- Model-internal fusion attribution (beyond probability comparisons).
- Composite clinician-facing multimodal case figures.
- Clean final tile/magnification LGD2+ comparison table.
- Foundation-combo `patient_id` join validation; clinical-augmentation scope decision.

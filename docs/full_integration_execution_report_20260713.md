# Full LGD2+ Fusion Integration Report

## Outcome
- complete (CNV region/gene interpretation remains BLOCKED by design; cross-fitted thresholds deferred and documented)
- starting branch/commit: `main` @ `edb5d31`
- implementation branch: `chapter1-fusion-integration-hardening`
- implementation commit(s): recorded at push (see outer `current_update.md` for final hash)
- push/merge status: see Git section

## Review findings resolved
| finding | change | test | status |
|---|---|---|---|
| 1 merge_oof silent inner-join | exact one_to_one merge per image model; fail on unmatched keys with examples; row-count equality | test_unmatched_cnv/image_keys_rejected | resolved |
| 2 CLI can overwrite canonical outputs | fail if dest exists; `--overwrite` opt-in; atomic temp+rename; run_metadata.json | test_atomic_write_in_system_temp_and_overwrite_guard | resolved |
| 3 image models mixed in one stacker | group by (condition,rep,image_model,fold); merge/compute per model | test_no_image_model_mixing_in_meta_training | resolved |
| 4 dup/leak/label warn-but-continue | script 02 fails closed (SKIP) via io helpers | test_late_fusion_method_reason_*, test_master_agreement_*, test_fold_integrity_* | resolved |
| 5 manifest marks completed work MISSING | histology SUPPLEMENTARY, fusion SUPPLEMENTARY, late-fusion metrics filled | manifest uniqueness/schema | resolved |
| 6 contradictory interpretation docs | interpretation summary rewritten to current-state; histology summary regenerated (8 cases) | consistency scan | resolved |
| 7 fold-purity not independently proven | monkeypatch spy proves held-out fold absent from training | test_fold_purity_holds_out_test_fold | resolved |
| 8 no paired delta CIs vs CNV-only | paired_comparison.py + script 15 (shared-index bootstrap) | test_paired_* | resolved |
| 9 ablation not packaged | script 16 + patient-level ablation table | (validated by run; identical sample sets) | resolved |

## Late-fusion pairing validation
| encoder | image model | CNV rows | image rows | matched rows | unmatched | duplicates | patients | folds | status |
|---|---|---|---|---|---|---|---|---|---|
| uni2 | abmil | 903 | 903 | 903 | 0 | 0 | 155 | 5 | OK |
| virchow2 | abmil | 903 | 903 | 903 | 0 | 0 | 155 | 5 | OK |
| gigapath | set_transformer_lite | 903 | 903 | 903 | 0 | 0 | 155 | 5 | OK |

(Canonical external late-fusion outputs were NOT rerun; migrated code validated by toy tests. The hardened merge enforces one_to_one pairing, so these counts are checked at ingestion.)

## External write safety
- Overwrite behaviour: `run_late_fusion` raises `FileExistsError` if `cv_predictions_late_fusion.csv` exists unless `overwrite=True`.
- Atomic-write behaviour: writes `*.tmp` then `os.replace`; also emits `run_metadata.json` (args, input paths+sizes, counts, seed, schema, fold diagnostics, timestamp).
- Canonical outputs untouched: no `--overwrite` used; `data/lgd2_late_fusion_20260713/{uni2,virchow2,gigapath}` unchanged.
- Output dir inside the clean repo (including `tmp`/`test`) is always rejected; tests use a system temp dir.

## Metric integrity
- Master join and label checks: script 02 fails closed on missing patient IDs, y_true-vs-master label disagreement, and prediction-vs-master patient-id disagreement (`master_agreement_reason`).
- Duplicate/fold-leakage behaviour: duplicate `(condition,rep,fold,fusion_method,sample_id)` late-fusion rows, a missing declared method, differing method sample sets, patients in multiple folds, or a fold count != 5 all SKIP the result group (no metrics from invalid rows).
- Cohort counts: enforced 155/55/100 (all-samples) and 150/50/100 (early); sample rows 903. All 16 families satisfy them (0 violations, 0 SKIP/WARN beyond expected INFO).
- Regression vs `edb5d31`: max abs diff = 0.00e+00 across all existing patient-level rows and all comparison-table slots; no rows dropped; late-fusion metrics unchanged.

## Manifest and documentation
- Rows/statuses changed: `lgd2_histology_interpretability` MISSING→SUPPLEMENTARY (8 selected cases, paths+summary populated); `lgd2_fusion_help_hurt_fail` MISSING→SUPPLEMENTARY; 3 `lgd2_late_fusion_*` metrics_existing/missing updated (patient-level + paired), `needs_patient_aggregation=yes` preserved.
- Stale summaries corrected: `lgd2_interpretation_summary.md` rewritten to current-state; `lgd2_histology_interpretation_summary.csv/.md/_warnings.md` regenerated (script 09 path-resolution fix) to show 8 completed cases.
- Consistency scan: canonical README/PROJECT_STATE/manifest/summaries free of active "histology missing / not run / late_fusion unavailable / full patient clinical metrics missing" claims.

## Paired model differences: all samples
| contrast | delta AUPRC (95% CI) | delta AUC (95% CI) | delta Brier (95% CI) | n |
|---|---|---|---|---|
| image_uni2_abmil - cnv_only (prespec) | +0.119 (-0.010, +0.234) | +0.079 (-0.003, +0.166) | +0.017 (-0.025, +0.059) | 155 |
| early_fusion_uni2 - cnv_only (prespec) | +0.189 (+0.066, +0.294) | +0.130 (+0.058, +0.211) | -0.051 (-0.084, -0.018) | 155 |
| intermediate(best) - cnv_only (selected) | +0.178 (+0.051, +0.288) | +0.110 (+0.030, +0.191) | +0.000 (-0.043, +0.046) | 155 |
| late_fusion_uni2_mean - cnv_only (prespec) | +0.120 (+0.016, +0.216) | +0.088 (+0.023, +0.158) | -0.020 (-0.040, -0.001) | 155 |
| late_fusion(best) - cnv_only (selected) | +0.136 (+0.024, +0.241) | +0.099 (+0.030, +0.173) | -0.021 (-0.041, -0.002) | 155 |
| early_fusion_uni2 - image_uni2_abmil (prespec) | +0.070 (-0.004, +0.144) | +0.051 (+0.006, +0.099) | -0.068 (-0.095, -0.040) | 155 |
| early_fusion_uni2 - late_fusion_uni2_mean (prespec) | +0.068 (-0.000, +0.137) | +0.042 (+0.004, +0.085) | -0.031 (-0.051, -0.010) | 155 |

## Paired model differences: early prediction only
| contrast | delta AUPRC (95% CI) | delta AUC (95% CI) | delta Brier (95% CI) | n |
|---|---|---|---|---|
| image_uni2_abmil - cnv_only (prespec) | +0.153 (+0.006, +0.280) | +0.128 (+0.014, +0.243) | +0.018 (-0.027, +0.063) | 150 |
| early_fusion_uni2 - cnv_only (prespec) | +0.211 (+0.073, +0.328) | +0.191 (+0.101, +0.290) | -0.047 (-0.082, -0.013) | 150 |
| intermediate(best) - cnv_only (selected) | +0.157 (+0.016, +0.276) | +0.137 (+0.033, +0.243) | +0.008 (-0.037, +0.054) | 150 |
| late_fusion_uni2_mean - cnv_only (prespec) | +0.137 (+0.019, +0.240) | +0.137 (+0.053, +0.228) | -0.022 (-0.045, -0.001) | 150 |
| late_fusion(best) - cnv_only (selected) | +0.127 (+0.003, +0.245) | +0.118 (+0.024, +0.215) | -0.017 (-0.039, +0.004) | 150 |
| early_fusion_uni2 - image_uni2_abmil (prespec) | +0.058 (-0.040, +0.152) | +0.063 (+0.003, +0.127) | -0.065 (-0.095, -0.036) | 150 |
| early_fusion_uni2 - late_fusion_uni2_mean (prespec) | +0.075 (-0.014, +0.157) | +0.054 (+0.004, +0.106) | -0.025 (-0.046, -0.002) | 150 |

## Modality ablation
- Files found: per-sample OOF predictions for baseline/shuffle_image/shuffle_cnv/shuffle_both under `.../campaign_lgd2_h200_patient_signal_lgd2_20260319/patchselect/uni2_signal/`. Patient-level comparison valid (identical 903-sample/155-patient sets across conditions).
- Reporting level: patient_max, clean metric helpers.
- Baseline/shuffle (e.g. `early_mean_mlp` AUPRC): baseline 0.845 → shuffle_image 0.791 → shuffle_cnv 0.825 → shuffle_both 0.449. Image shuffling (direct histology test) degrades all models; shuffling both collapses toward chance.
- Blocker: none. Described as supporting evidence, not causal proof.

## Scientific conclusion
- Adding histopathology to CNV improved internal out-of-fold patient-level discrimination for next-biopsy LGD2+ progression in the matched cohort: early-fusion UNI2 vs CNV-only and late-fusion UNI2 (mean) vs CNV-only both have delta AUPRC and AUC 95% CIs excluding zero, in both analysis sets.
- Image-only vs CNV-only crosses zero for delta AUPRC in the all-samples set (borderline; excludes zero in early-prediction), so image-only superiority is not robustly established.
- Sensitivity/specificity trade-off: `stack_logit` raises specificity at the cost of sensitivity vs `mean`; `mean` gives the better AUPRC/AUC.
- Endpoint wording: LGD2+ neoplastic progression, NOT cancer/OAC prediction.
- Cannot be claimed: external validity; causal modality attribution; strict known-lead-time performance; superiority where CIs cross zero (e.g. early-fusion over late-fusion mean).

## Tests and data safety
- pytest: 82 passed (58 prior + hardening + paired; erin env).
- py_compile: OK on all changed/new Python.
- regression checks: 0.00e+00 vs `edb5d31`.
- no-data guard: OK (allowlist extended for ablation + paired CSVs in `.gitignore` and `assert_no_data_tracked.sh`).
- heavy outputs external: only small summary CSVs/MDs tracked; predictions/matrices/WSI remain external.

## Files changed
- added: `src/barrett/evaluation/paired_comparison.py`, `scripts/15_make_lgd2_paired_model_comparisons.py`, `scripts/16_make_lgd2_modality_ablation_table.py`, `tests/test_paired_comparison.py`, `reports/thesis_ch1/lgd2_paired_model_differences_*.csv/.md`, `lgd2_paired_model_difference_warnings.md`, `lgd2_modality_ablation_*.csv/.md`, `lgd2_timing_and_operating_point_limitations.md`, `docs/full_integration_execution_report_20260713.md`.
- modified: `src/barrett/evaluation/late_fusion.py`, `src/barrett/evaluation/io.py`, `scripts/02`, `scripts/04`, `scripts/09`, `scripts/14`, `scripts/assert_no_data_tracked.sh`, `.gitignore`, `docs/final_results_manifest.csv/.md`, `reports/thesis_ch1/lgd2_interpretation_summary.md`, `lgd2_results_interpretation.md`, `lgd2_histology_interpretation_summary.csv/.md/_warnings.md`, `tests/test_late_fusion.py`.
- removed/renamed: none in the clean repo.

## Remaining limitations
- External validation: not performed (internal 5-fold CV only).
- Strict known-lead-time cohort: not available; current analysis is "at-event excluded" (missing-timing rows retained).
- Cross-fitted thresholds: not implemented; fixed operating points are post-hoc. Documented as remaining work.
- CNV biological interpretation (region/gene): BLOCKED (needs an external compute run; no persisted estimator/importance).
- Model-internal fusion attribution: missing.

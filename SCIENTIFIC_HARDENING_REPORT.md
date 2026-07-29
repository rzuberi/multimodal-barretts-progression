# Scientific Hardening Report — Barrett's multimodal progression (Chapter 1)

- **Branch:** `chapter1-scientific-hardening` (off `origin/main` @ ef3a73c). Additive; the frozen Chapter-1 release is not modified.
- **Output root:** `analysis/chapter1_scientific_hardening_20260727/` (cluster; row-level/sensitive outputs stay here, outside Git).
- **Evaluation invariant:** leakage-safe, patient-disjoint 5-fold reusing the frozen `patient_splits.csv`/`row_to_fold.csv`; patient-level metrics after patient-max; paired patient-level CIs.
- **Scope note:** external validation is explicitly deferred (no digitised external cohort on cluster).
- **Progress:** Phases 0–6 COMPLETE. Phase 6 (Virchow2 encoder sensitivity) is a clean NEGATIVE result — UNI2 remains the reported backbone.

Tags: **[V]** verified from code/data this session · **[I]** inferred · **[U]** unknown.

---

## Phase 0 — Primary task contract  ✅ COMPLETE (gate passed)

### 0.1 Endpoint verification — **PASS, 0 discrepancies**
Independently reconstructed `NextBiopsyProgression_LGD2plus` from source columns (`NextBiopsyLabel`, `LGDStreakSoFar`) using the locked rule in `src/barrett/labels/lgd2.py`, and compared to the frozen stored endpoint on all 707 evaluated rows.
- **Result: 0 / 707 discrepancies** (stored 107 pos / 600 neg == derived 107 / 600). **The frozen Chapter-1 endpoint is verified; downstream modelling proceeds.**
- Exact Boolean: `positive <=> NextBiopsyLabel>=3 OR (NextBiopsyLabel==2 AND LGDStreakSoFar>=1)`. A next LGD counts only when it completes a **second consecutive** LGD.
- **Temporal integrity [V]:** 707/707 rows have the next biopsy strictly later; **0 same-day events**, 0 rows relying on the DaysToNextBiopsy-only fallback. The 172 same-day rows present in the canonical master are all removed by the strict pre-event filter — this **resolves the prior [U] same-day-event flag**.
- Deliverables: `primary_endpoint_contract.md`; row-level `primary_endpoint_recomputed.csv` + `primary_endpoint_discrepancies.csv` (0 rows) written to the cluster output root (kept out of Git).

### 0.2 Index-cohort terminology — **correction required to prior wording**
- Index-grade composition (Verified): **NDBE 553 rows/137 pt (9.6% pos), indefinite 67/27 (19.4%), LGD 87/38 (47.1%)**; HGD/IMC/OAC = 0 at index.
- **"Dysplasia-free" and "before dysplasia is visible" are INACCURATE** — the cohort includes 87 LGD (dysplastic) index rows.
- **Correct terminology:** *"pre-high-grade surveillance cohort (non-dysplastic, indefinite, or low-grade at index; HGD/IMC/OAC excluded)."*
- Recommend reporting NDBE+indefinite (early-detection claim), LGD (risk-stratification-of-LGD claim), and full-cohort strata separately. Deliverable: `terminology_ruling.md`.

### 0.3 Grade provenance — **reproducibility gap identified [HIGH]**
- Grade columns (`CurrentGradeInt/Norm`, `NextBiopsyLabel`, `LGDStreakSoFar`, `MaxPathologySoFar`, `max_pathology`) are **read but never constructed** in the repo. The worst-grade collapse + streak computation happen **upstream, in the external master-CSV derivation, which is NOT version-controlled** in this repo.
- Worst-grade collapse is per-timepoint; **0/356 timepoints show within-timepoint grade variation** (already collapsed upstream). Raw pre-collapse per-biopsy grades are **[U] not recoverable from the frozen release**.
- The endpoint *rule* is versioned (`lgd2.py`); the *inputs* to it are not. Deliverable: `grade_provenance.md` (+ flow diagram).

### 0.4 Feature-availability audit — **gate for Phase 1 [V]**
- **Prediction-time-SAFE clinical features (7, matching `feature_availability_audit.csv`):** `CurrentGradeInt`, `CurrentGradeNorm` (the index-grade stratum), `LGDStreakSoFar`, `MaxPathologySoFar`, `BiopsyIndex`, `DaysSincePreviousBiopsy` (+is-first flag/impute; 296 nulls = first biopsies), `IsFirstBiopsy`.
- **AMBIGUOUS (excluded pending provenance):** `max_pathology` (0-5 range exceeds the past+current `MaxPathologySoFar` 0-2 → may include global/future grades).
- **LEAKY (must not be features):** `BiopsiesTotalForPatient`, `IsLastBiopsy`, `MonthsBeforeLastBiopsy`, `DaysFromFirstBiopsyToEvent`, `DaysFromCurrentToEvent`, `EventDate/Type`, `NextBiopsyLabel/Date`, `DaysToNextBiopsy`.
- Deliverable: `feature_availability_audit.csv`.

**Phase 0 gate: PASSED** — endpoint reproduces exactly, temporal definition clean, no leakage in the safe feature set. Proceeding to Phase 1 with the 7 safe clinical features.

---

## Phase 1 — Clinical and simple statistical baselines  ✅ COMPLETE

**Method:** leakage-safe nested models on the frozen 5-fold patient-disjoint splits. Scaling, imputation (days-since-previous → training-fold median) and fitting occur on training folds only; predictions are out-of-fold; metrics are patient-level (patient-max). Combined models use **cross-fitted stacking** — to score fold *f*, the meta-logistic is fit on the OOF rows of the other 4 folds only, so no patient's own base prediction trains its meta-model. Safe clinical features (Phase 0.4): index grade (one-hot), LGD streak, MaxPathologySoFar, biopsy index, days-since-previous-biopsy, is-first-biopsy.

### 1.1 / 1.2 Model comparison table (patient-level, n=150 / 50 positive)
| Model | AUPRC | ROC AUC | Brier |
|---|---|---|---|
| prevalence | 0.333 | 0.500 | 0.255 |
| grade_only | 0.490 | 0.666 | 0.226 |
| history_only | 0.493 | 0.711 | 0.239 |
| grade_plus_history | 0.495 | 0.720 | 0.235 |
| clinical_tree | 0.497 | 0.677 | 0.236 |
| clinical (=grade+history) | 0.495 | 0.720 | 0.235 |
| cnv | 0.538 | 0.663 | 0.216 |
| image | 0.557 | 0.731 | 0.245 |
| CNV+image (cross-fit re-stack) | 0.562 | 0.746 | 0.245 |
| CNV+image (frozen late_mean, reference) | 0.630 | 0.774 | 0.184 |
| clinical_cnv | 0.528 | 0.740 | 0.244 |
| clinical_image | 0.554 | 0.778 | 0.228 |
| clinical_cnv_image | 0.576 | 0.801 | 0.222 |


### Key paired comparisons (patient-level bootstrap, 5000 resamples)
| Comparison | ΔAUPRC [95% CI] | ΔROC [95% CI] | ΔBrier [95% CI] |
|---|---|---|---|
| clinical_cnv_image − clinical_cnv | +0.048 (-0.0248, 0.1237) | +0.061 (-0.0011, 0.1227) | +0.021 (-0.0022, 0.0452) |
| clinical − cnv | -0.043 (-0.1703, 0.1115) | +0.057 (-0.0526, 0.1711) | -0.019 (-0.0775, 0.0362) |
| clinical − image | -0.062 (-0.201, 0.0839) | -0.011 (-0.1265, 0.1076) | +0.010 (-0.0334, 0.054) |
| clinical − cnv_image | -0.067 (-0.1952, 0.0788) | -0.025 (-0.1399, 0.0908) | +0.009 (-0.0276, 0.0459) |
| cnv_image − cnv | +0.024 (-0.0929, 0.1589) | +0.083 (-0.0272, 0.1937) | -0.029 (-0.0858, 0.0256) |
| cnv_image − image | +0.005 (-0.0615, 0.0617) | +0.014 (-0.0249, 0.053) | +0.001 (-0.0169, 0.0198) |
| clinical_cnv − clinical | +0.033 (-0.0099, 0.0797) | +0.020 (-0.0195, 0.0612) | -0.009 (-0.0242, 0.0073) |
| clinical_image − clinical | +0.058 (-0.0231, 0.1452) | +0.058 (-0.0101, 0.1292) | +0.007 (-0.0199, 0.0346) |
| clinical_cnv_image − cnv_image | +0.014 (-0.0556, 0.0987) | +0.055 (-0.0057, 0.1189) | +0.022 (0.001, 0.0417) |
| cnv_image_latemean_frozen − cnv | +0.091 (-0.0303, 0.2253) | +0.111 (0.0014, 0.2205) | +0.032 (0.0027, 0.0604) |


### Verified findings
- **The clinical baseline is strong.** Grade+history logistic reaches **AUPRC 0.495 / ROC 0.720 / Brier 0.235** — essentially matching CNV-only (0.538/0.663) and approaching image-only (0.557/0.731). *A simple, prediction-time-safe clinical model is competitive with each single modality.* This is the previously-missing comparison and it materially qualifies the multimodal story.
- **PRIMARY comparison — does histology add beyond clinical+genomics?** `clinical+CNV+image` vs `clinical+CNV`: **ΔAUPRC +0.048 [−0.025, +0.124]**, ΔROC +0.061 [−0.001, +0.123], ΔBrier +0.021 [−0.002, +0.045]. **All three CIs include (or touch) zero — the added value of histopathology beyond clinical+CNV is NOT conclusive.** Point estimates favour adding image, but underpowered.
- **Adding clinical information helps discrimination and calibration.** `clinical+CNV+image` has the **highest ROC of any model (0.801)** — above the frozen late-mean fusion (0.774) — and `clinical+CNV+image vs CNV+image` improves Brier with a CI excluding zero (+0.022 [+0.001, +0.042]).
- **Clinical vs each modality:** clinical is statistically indistinguishable from CNV and from image on AUPRC (CIs wide, cross zero). No modality conclusively beats the clinical baseline on the primary metric at this sample size.
- **Fusion-choice note [I]:** a fresh cross-fit logistic re-stack of CNV+image (AUPRC 0.562) underperforms the pre-tuned frozen late-mean fusion (0.630). The frozen late-mean remains the pre-specified best CNV+image model; the re-stack is used only to keep the clinical-decomposition internally consistent. Comparisons that need the *best* fusion use the frozen late-mean.

### Deliverables
- `clinical_baseline_oof.csv`, `clinical_multimodal_oof.csv` (row-level, cluster output root, out of Git).
- `clinical_baseline_metrics.csv`, `clinical_multimodal_comparisons.csv`.
- This section serves as `CLINICAL_BASELINE_REPORT.md` content (also written standalone).

**Phase 1 gate: the clinical baseline is competitive and the primary "histology-adds-value" test is inconclusive at n=150. This does NOT invalidate downstream work — it sharpens the claim. Proceeding to Phase 2 (calibration + decision curves).**

---

## Phase 2 — Calibration & clinical utility  ✅ COMPLETE

**Method:** patient-level out-of-fold predictions (patient-max). Calibration slope/intercept from logistic recalibration of the logit; ECE with 10 bins; decision-curve net benefit `TP/n − FP/n·(p/(1−p))`; operating points at the threshold giving ≥90% sensitivity with maximal specificity.

### 2.1 Discrimination + calibration
| Model | AUPRC | ROC | Brier | Cal. slope | Cal. intercept | ECE |
|---|---|---|---|---|---|---|
| clinical | 0.495 | 0.720 | 0.235 | 0.55 | -0.86 | 0.206 |
| cnv | 0.538 | 0.663 | 0.216 | 1.23 | +0.73 | 0.095 |
| image | 0.557 | 0.731 | 0.245 | 0.62 | -0.99 | 0.215 |
| cnv_image_fusion | 0.630 | 0.774 | 0.184 | 1.78 | +0.10 | 0.075 |
| clinical_cnv | 0.528 | 0.740 | 0.244 | 0.91 | -1.07 | 0.230 |
| clinical_image | 0.554 | 0.778 | 0.228 | 0.69 | -1.06 | 0.225 |
| clinical_cnv_image | 0.576 | 0.801 | 0.223 | 0.72 | -1.11 | 0.229 |


### 2.3 Operating points at ≥90% sensitivity (patient-level)
| Model | Threshold | Sens | Spec | PPV | NPV |
|---|---|---|---|---|---|
| clinical | 0.282 | 0.92 | 0.28 | 0.390 | 0.875 |
| cnv | 0.144 | 0.92 | 0.15 | 0.351 | 0.789 |
| image | 0.318 | 0.90 | 0.31 | 0.395 | 0.861 |
| cnv_image_fusion | 0.289 | 0.90 | 0.42 | 0.437 | 0.894 |
| clinical_cnv | 0.419 | 0.92 | 0.40 | 0.434 | 0.909 |
| clinical_image | 0.480 | 0.90 | 0.60 | 0.529 | 0.923 |
| clinical_cnv_image | 0.538 | 0.90 | 0.66 | 0.570 | 0.930 |


### Verified findings
- **Calibration is modality-dependent.** The frozen CNV+image fusion (slope **1.78**, ECE **0.075**) and CNV-only (slope 1.23, ECE 0.095) are well-calibrated. The clinical-only, clinical+image and clinical+CNV+image models are **over-confident** (slopes 0.55–0.72, negative intercepts, ECE 0.21–0.23); clinical+CNV has a near-ideal slope (0.91) but still a high ECE (0.23), so its miscalibration is intercept/bin-shape rather than slope.
  - **[I] Confound flagged:** the frozen fusion carries **per-fold Platt calibration**; the quick cross-fit clinical stacks do **not**. Part of the calibration gap is this missing step, not intrinsic. Discrimination and operating-point specificity are unaffected; a fair calibration comparison needs per-fold Platt on the stacks (Phase 4 refinement).
- **Decision-curve analysis:** the frozen CNV+image fusion has the **highest net benefit across most of the clinically relevant range (~0.15–0.45)**; `clinical+CNV+image` is competitive in the 0.25–0.45 band. All models beat treat-all/treat-none between ~0.15 and ~0.45.
- **Operating points show a clean, monotonic clinical-utility gain:** at 90% sensitivity, specificity rises **0.28 (clinical) → 0.42 (CNV+image fusion) → 0.66 (clinical+CNV+image)**, PPV 0.39 → 0.44 → **0.57**, NPV 0.88 → 0.89 → **0.93**. Adding clinical context to the multimodal model roughly halves the false-positive rate at fixed sensitivity — the most tangible clinical result here.

### Deliverables
`calibration_curves.png/.pdf`, `decision_curves.png/.pdf`, `calibration_metrics.csv`, `decision_curve_results.csv`, `clinical_operating_points.csv`.

**Phase 2 gate: PASSED.** Main caveat (uncalibrated stacks) recorded for Phase 4.

---

## Phase 3 — Matching, provenance, endpoint & temporal robustness  ✅ COMPLETE

All cuts reuse the frozen OOF predictions (no retraining); the anchor contrast is the Chapter-1 primary delta **late-mean fusion − CNV-only**, patient-level (patient-max), paired bootstrap 2000 resamples. **Prevalence is reported for every subset — AUPRC is not compared across subsets of different prevalence.**

### 3.1 Image-record matching sensitivity
| analysis | n_rows | n_pat | n_pos | prevalence | cnv_only_auprc | image_only_auprc | late_mean_auprc | clinical_auprc | latemean_vs_cnv_dAUPRC | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full_cohort | 707 | 150 | 50 | 0.1513 | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 |
| exact_only | 532 | 111 | 24 | 0.0959 | 0.2819 | 0.417 | 0.4581 | 0.4327 | 0.1762 | 0.0071 | 0.3413 |
| exact_plus_formatting | 565 | 118 | 28 | 0.1097 | 0.3011 | 0.42 | 0.4509 | 0.4195 | 0.1499 | -0.0155 | 0.3019 |
| exclude_patient_fallback | 578 | 121 | 30 | 0.1107 | 0.3456 | 0.3958 | 0.4439 | 0.4365 | 0.0983 | -0.0442 | 0.2565 |
| only_patient_fallback | 129 | 40 | 20 | 0.3333 | 0.8148 | 0.9095 | 0.9195 | 0.7718 | 0.1047 | -0.0062 | 0.2427 |
| only_dot_dash_swap | 31 | 9 | 3 | 0.3226 | 0.4444 | 0.4444 | 0.4444 | 0.4583 | 0.0 | -0.3333 | 0.2667 |
| only_none | 8 | 2 | 1 | 0.125 | 1.0 | 0.5 | 0.5 | 0.5 | nan | nan | nan |

**Finding — the multimodal benefit is NOT a matching artifact; it is cleaner on exact matches.** On **exact-match-only** (532 rows, prevalence 9.6%) the paired ΔAUPRC **rises to +0.176 [+0.007, +0.341], CI excludes zero** (vs +0.091 [−0.031, +0.219] on the full cohort). The high absolute AUPRC on the full cohort is partly propped up by the **patient-fallback** subset (129 rows, prevalence 33%, late-mean AUPRC 0.92) — a higher-base-rate, easier stratum. Excluding those fuzzy matches lowers absolute numbers but preserves the paired benefit.

### 3.2 Grade-provenance sensitivity — benefit STRENGTHENS with cleaner labels
| analysis | n_rows | n_pat | n_pos | prevalence | cnv_only_auprc | image_only_auprc | late_mean_auprc | clinical_auprc | latemean_vs_cnv_dAUPRC | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full_cohort | 707 | 150 | 50 | 0.1513 | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 |
| scraped_confirmed_only | 547 | 112 | 28 | 0.1133 | 0.3053 | 0.4364 | 0.4659 | 0.4224 | 0.1606 | 0.0115 | 0.3179 |
| exclude_master_fallback | 552 | 113 | 29 | 0.1141 | 0.3053 | 0.4314 | 0.4572 | 0.4395 | 0.1518 | 0.0058 | 0.3081 |

On **scraped-confirmed grades only** ΔAUPRC +0.161 [+0.012, +0.318] and **excluding master-label fallback** +0.152 [+0.006, +0.308] — **both CIs exclude zero**. The multimodal effect is not driven by weakly-sourced labels.

### 3.3 Cleaner-endpoint sensitivity — benefit ATTENUATES at higher grade
| analysis | n_rows | n_pat | n_pos | prevalence | cnv_only_auprc | image_only_auprc | late_mean_auprc | clinical_auprc | latemean_vs_cnv_dAUPRC | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LGD2plus_primary | 707 | 150 | 50 | 0.1513 | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 |
| LGD3plus_rescored | 707 | 150 | 36 | 0.1132 | 0.5 | 0.456 | 0.549 | 0.2975 | 0.049 | -0.087 | 0.1963 |
| highrisk_ge3_rescored | 707 | 150 | 36 | 0.1132 | 0.5 | 0.456 | 0.549 | 0.2975 | 0.049 | -0.087 | 0.1963 |

Re-scoring the frozen LGD2+-trained models against the **LGD3+ / high-risk (≥HGD next biopsy)** endpoint (identical here: 36 positive patients) gives ΔAUPRC +0.049 [−0.087, +0.196], crossing zero. The benefit is **largest for the LGD2+ definition and attenuates for the stricter endpoint** — an honest limitation (also, this is transfer scoring, not retraining on the new label).

### 3.4 Temporal sensitivity — robust
| analysis | n_rows | n_pat | n_pos | prevalence | cnv_only_auprc | image_only_auprc | late_mean_auprc | clinical_auprc | latemean_vs_cnv_dAUPRC | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full_cohort | 707 | 150 | 50 | 0.1513 | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 |
| exclude_same_day | 707 | 150 | 50 | 0.1513 | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 |
| min_horizon_30d | 701 | 150 | 50 | 0.1526 | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 |
| min_horizon_90d | 676 | 149 | 48 | 0.1538 | 0.5135 | 0.5324 | 0.5983 | 0.4652 | 0.0848 | -0.0389 | 0.225 |

Zero same-day events (confirmed Phase 0). Imposing a 30-day or 90-day minimum prediction horizon removes ≤31 rows and barely moves the delta (+0.085 [−0.039, +0.225] at 90d). No temporal-leakage inflation.

### 3.5 Aggregation sensitivity — ranking stable
| analysis | cnv_only_auprc | image_only_auprc | late_mean_auprc | clinical_auprc | latemean_vs_cnv_dAUPRC | ci_lo | ci_hi | crosses0 |
|---|---|---|---|---|---|---|---|---|
| patient_max | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 | yes |
| patient_mean | 0.6306 | 0.6278 | 0.7006 | 0.6834 | 0.0700 | -0.0800 | 0.2285 | yes |
| most_recent | 0.5484 | 0.5783 | 0.6593 | 0.5985 | 0.1109 | -0.0432 | 0.2616 | yes |
| first_eligible | 0.1732 | 0.2363 | 0.2265 | 0.3219 | 0.0532 | -0.0898 | 0.2294 | yes |
| biopsy_then_patient_max | 0.5385 | 0.557 | 0.6296 | 0.4952 | 0.0912 | -0.0307 | 0.2192 | yes |

Each ΔAUPRC is computed **under its own aggregation scheme** (paired bootstrap re-aggregates both models the same way). All five give a positive fusion>CNV delta — patient-max +0.091, patient-mean +0.070, most-recent +0.111, first-eligible +0.053, biopsy-then-max +0.091 — every CI crossing zero, so the ordering is preserved across aggregation choices though none is individually conclusive. biopsy-then-max equals patient-max exactly (one slide per biopsy makes max-then-max collapse to patient-max). **First-eligible collapses to 16 positive patients** (many progressors' event is not at their first eligible biopsy) — underpowered, not a valid primary. No aggregation is promoted to primary; patient-max stays the pre-specified method.

### 3.6 Fold & patient influence — the main fragility
| fold | n_pat | n_pos | late_mean_auprc | cnv_auprc | d_auprc |
|---|---|---|---|---|---|
| 1.0 | 30.0 | 10.0 | 0.5029 | 0.6152 | -0.1123 |
| 2.0 | 30.0 | 10.0 | 0.8483 | 0.4288 | 0.4195 |
| 3.0 | 30.0 | 10.0 | 0.6949 | 0.6384 | 0.0565 |
| 4.0 | 30.0 | 10.0 | 0.8249 | 0.7677 | 0.0572 |
| 5.0 | 30.0 | 10.0 | 0.7732 | 0.619 | 0.1542 |

**The benefit is fold-heterogeneous: ΔAUPRC ranges from −0.11 (fold 1) to +0.42 (fold 2).** Fold 1 actually reverses. This is the single biggest internal-validity caveat and reflects the small per-fold positive count (10 progressors/fold).
- **Patient-level influence is reassuring:** leave-one-patient-out on the full ΔAUPRC gives a max single-patient influence of **0.023** on a base of 0.091 (top-5 |influence| ≈ 0.10 combined). No individual patient drives the result — the fragility is fold-level (distributional), not one or two patients. 82 patients push the delta positive, 65 negative.

### Verified summary
| Robustness cut | ΔAUPRC | CI excludes 0? | Verdict |
|---|---|---|---|
| Full cohort (primary) | +0.091 | no | benefit, inconclusive |
| Exact match only | +0.176 | **yes** | **strengthens** |
| Exclude patient-fallback | +0.098 | no | holds |
| Scraped-confirmed grade only | +0.161 | **yes** | **strengthens** |
| Exclude master-label fallback | +0.152 | **yes** | **strengthens** |
| LGD3+/high-risk endpoint | +0.049 | no | attenuates |
| Min horizon 90d | +0.085 | no | holds |
| Aggregation variants | +0.05–0.11 | no | stable |
| Per-fold | −0.11 to +0.42 | — | **fold-fragile** |

**Interpretation [I]:** the multimodal (late-mean fusion) benefit over CNV-only is **directionally consistent and often significant on the cleaner subsets** (exact matches, confirmed grades), which is the opposite of what a data-artifact would produce. The two genuine caveats are (a) it attenuates at the stricter LGD3+ endpoint and (b) it is fold-heterogeneous, being carried disproportionately by fold 2. Neither invalidates the finding but both bound how strongly it can be claimed at n=150.

### Deliverables
`matching_sensitivity.csv`, `grade_provenance_sensitivity.csv`, `endpoint_sensitivity.csv`, `temporal_sensitivity.csv`, `aggregation_sensitivity.csv`, `fold_stability.csv`, `patient_influence_summary.csv`, `robustness_forest.png/.pdf`. Row-level `patient_influence_full.csv` kept on the cluster.

**Phase 3 gate: PASSED — no cut invalidates the result; fold-heterogeneity and endpoint-attenuation recorded as bounding caveats.**

---

## Phase 4 — Systematic error analysis  ✅ COMPLETE

**Method:** patient-level (patient-max) OOF predictions. Binary decisions use a **leakage-safe per-fold threshold** = the 90th percentile of *other-fold* negative predictions (a spec≈0.90 proxy that never sees the test fold). Categories are pre-specified from the (fusion-correct, cnv-correct, image-correct) triple — no hand-picking of cases.

### Error taxonomy (n=150; 50 progressors)
| Category | n |
|---|---|
| Correct progressor (fusion) | 18 |
| Fusion-harm missed progressor (a modality was right, fusion wrong) | 10 |
| Missed progressor (all modalities wrong) | 22 |
| Correct non-progressor | 88 |
| Fusion-harm false positive | 9 |
| Persistent false positive (all wrong) | 3 |

### Modality agreement & the central mechanistic finding
- Modalities agree on **71%** of patients (106/150).
- **When they agree**, fusion is accurate (0.76). **When they disagree** (44 patients), fusion accuracy falls to **0.57**.
- **Late-mean fusion averages away a correct unimodal signal on conflict.** On the 44 disagreement cases, at least one single modality was correct in every case (oracle upper bound 1.00 — this is definitional, an *achievable* modality-selector would be lower), yet mean-fusion recovers only 0.57. Fusion support breakdown: 81 all-agree, 21 image-carried, 4 CNV-carried, 44 fusion-wrong. **This is the strongest mechanistic motivation for a learned gating/attention fusion** (deferred by scope), and explains why the AUPRC benefit is modest: mean-fusion wins on the easy concordant cases and loses ground on conflicts.
- Strong-confident unimodal signal lost by fusion: **3** patients.

### False negatives are distant, not imminent (reassuring)
- Missed progressors (32) have a **longer** median time-to-event (**729 d**) than caught progressors (18; 548 d). The model catches imminent progression and misses distant progression — clinically sensible, and argues against a short-horizon-leakage explanation of the positive signal.

### False positives concentrate in NDBE
- Of the false positives, index-grade distribution: {'NDBE': 7, 'LGD': 3, 'ID': 2} — mostly non-dysplastic Barrett's flagged as high-risk that did not progress in-window.

### Error category by index grade
index_grade  correct_nonprogressor  correct_progressor  fusion_harm_false_positive  fusion_harm_missed_progressor  missed_progressor_all  persistent_false_positive
         ID                      5                   3                           2                              1                      4                          0
        LGD                      5                   7                           1                              4                      8                          2
       NDBE                     78                   8                           6                              5                     10                          1

### Deliverables
`error_analysis_summary.csv`, `error_by_index_grade.csv`, `modality_disagreement_analysis.csv`, `error_analysis_summary.png/.pdf`. Row-level `patient_error_taxonomy.csv` (patient ids) kept on the cluster.

**Phase 4 gate: complete.** Key exploratory finding: mean-fusion's ceiling is set by its behaviour on modality-disagreement cases — a concrete, pre-registered motivation for learned fusion once sample size permits.

---

## Phase 5 — Killcoyne multimodal feasibility  ✅ COMPLETE (counts only, no GPU)

**Linkage** (keyed on `BiopsyID_real` = pathology-block PSID `ps##.#####`): Killcoyne discovery = 345 distinct PSIDs; 329 map to the local master; **242 fall in the strict-eligible multimodal cohort**, belonging to **69 of the 150 multimodal patients** — and that 69-patient set is **entirely a subset of the 150** (`subset_of_150 = True`).

**Modality availability on the 454-row / 69-patient overlap:** CNV 454/454, H&E 454/454, and UNI2 / GigaPath / Virchow2 embeddings 454/454 each — full multimodal data present. Local LGD2+ outcome on the overlap: 54 positive rows / **27 positive patients**. Grade mix NDBE 333 / LGD 69 / ID 52; biopsies/patient median 6, max 19.

**The decisive finding: this is NOT independent validation.** The 69 overlap patients are a strict subset of the local training cohort. Evaluating the frozen models on them reuses patients the base models saw → within-cohort benchmark, not external validation (spec rule #11). The paper's endpoint is CNV-only (no histology), so a like-for-like multimodal comparison to Killcoyne is impossible regardless, and 27 positives make a fresh LOPO retraining statistically fragile.

**Recommendation — Option 3 (defined internal use), NOT a validation campaign:**
1. Use the overlap only as a **labelled internal benchmark / sensitivity subset**, clearly marked "within-cohort, not external validation."
2. Keep **CNV-only Killcoyne LOPO (0.78–0.80)** as the paper-comparison anchor, with the documented ~0.07–0.09 gap to the paper's 0.87 (QC/preprocessing) reconciled before any paper claim.
3. **Defer external validation** to a genuinely independent digitised cohort (spec defers this).

**Deliverables:** `killcoyne_multimodal_overlap_summary.md`, `killcoyne_lopo_feasibility.md`, `killcoyne_protocol_comparison.md`, `killcoyne_multimodal_overlap_counts.csv`, `killcoyne_multimodal_overlap_summary.json`.

**Phase 5 gate: complete — do not launch a multimodal LOPO GPU campaign; the overlap is a subset, not an external cohort.**

---

## Phase 6 — Limited Virchow2 encoder sensitivity  ✅ COMPLETE (negative result)

**Gate:** all 707 Virchow2 embeddings verified (feat_dim 2560, tile counts 64–256, 0 bad, frozen splits reused, leakage-safe). late_mean derivation reproduces the frozen UNI2 anchor exactly (0.6296/0.7742/0.1842).

Ran the primary LGD2+ task with Virchow2 for image_only, intermediate_fusion, and derived late_mean (cnv_only reused, backbone-independent). Same ABMIL/protocol/splits; patient-level, paired bootstrap 2000.

| model | n_pat | n_pos | auprc | roc | brier | auprc_lo | auprc_hi | roc_lo | roc_hi |
|---|---|---|---|---|---|---|---|---|---|
| cnv_only(shared) | 150 | 50 | 0.5385 | 0.663 | 0.216 | 0.41 | 0.6742 | 0.5711 | 0.7581 |
| uni2_image_only | 150 | 50 | 0.557 | 0.7312 | 0.2453 | 0.4326 | 0.7125 | 0.6421 | 0.8155 |
| virchow2_image_only | 150 | 50 | 0.4823 | 0.6658 | 0.2499 | 0.3685 | 0.6409 | 0.5741 | 0.7574 |
| uni2_late_mean | 150 | 50 | 0.6296 | 0.7742 | 0.1842 | 0.4969 | 0.7697 | 0.6938 | 0.8466 |
| virchow2_late_mean | 150 | 50 | 0.5582 | 0.7106 | 0.1951 | 0.4308 | 0.7035 | 0.6207 | 0.7946 |
| uni2_intermediate_fusion | 150 | 50 | 0.5675 | 0.7414 | 0.2242 | 0.4362 | 0.7051 | 0.6567 | 0.8153 |
| virchow2_intermediate_fusion | 150 | 50 | 0.488 | 0.6614 | 0.2737 | 0.3688 | 0.6337 | 0.5696 | 0.7506 |

**Verdict:** Virchow2 is slightly WORSE than UNI2 on every family and metric (image_only ΔAUPRC −0.075/ΔROC −0.065; late_mean −0.071/−0.064; intermediate −0.079/−0.080; ROC deltas significant). Calibration also worse (Virchow2 image/intermediate slopes 0.32–0.35). **Per the pre-specified rule, Virchow2 is NOT expanded to other endpoints; UNI2 remains the reported backbone.** Clean negative encoder-sensitivity result — the multimodal finding is not specific to one foundation model, and a larger/newer encoder does not help at n=150. See `VIRCHOW2_SENSITIVITY_REPORT.md`.

**Phase 6 gate: complete.**

---

## Phase 6 extension - Multi-encoder investigation  (COMPLETE, negative result)

Tested three pathology foundation encoders (UNI2, GigaPath, Virchow2) individually and combined (mean-ensemble + fold-pure logistic stacking), primary LGD2+ endpoint. GigaPath is the best single image encoder (AUPRC 0.609 > UNI2 0.557 > Virchow2 0.482), and the learned stacker down-weights Virchow2 - so encoders do carry different signal. But **no combination beats the reported UNI2 late-mean (0.630)**: the 3-encoder learned stack overfits (0.535, significantly worse than headline, delta -0.095 CI [-0.172,-0.009]); GigaPath late-mean ties (0.624, delta -0.006 crosses 0); cnv+mean(uni2,giga) gives the best point estimate (0.635) but within noise. UNI2 remains the reported backbone; GigaPath an acceptable tie. See MULTI_ENCODER_INVESTIGATION.md.

---

## Exploratory - Image label-noise / tissue-sampling investigation  (COMPLETE)

Asked whether low image scores on progressor patients are model error or benign-slide sampling. Image score rises with the imaged biopsy's own grade (NDBE 0.34 / ID 0.50 / LGD 0.52 - the model reads the slide). Of 70 image-missed positives, 51% have a **benign** current biopsy and 63% of all positives have current grade below the patient max: the lesion is elsewhere, so a low score is correct for the sampled tissue. Attention on 5 such cases lands on real epithelium, not artefacts - **the pattern is tissue sampling + patient-level labelling, not artefact error.** CNV scores these image-unwinnable cases above baseline (0.212 vs 0.172), a structural argument for multimodal fusion. See IMAGE_LABEL_NOISE_INVESTIGATION.md.

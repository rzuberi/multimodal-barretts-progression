# Scientific Hardening Report — Barrett's multimodal progression (Chapter 1)

- **Branch:** `chapter1-scientific-hardening` (off `origin/main` @ ef3a73c). Additive; the frozen Chapter-1 release is not modified.
- **Output root:** `analysis/chapter1_scientific_hardening_20260727/` (cluster; row-level/sensitive outputs stay here, outside Git).
- **Evaluation invariant:** leakage-safe, patient-disjoint 5-fold reusing the frozen `patient_splits.csv`/`row_to_fold.csv`; patient-level metrics after patient-max; paired patient-level CIs.
- **Scope note:** external validation is explicitly deferred (no digitised external cohort on cluster).

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

**Phase 0 gate: PASSED** — endpoint reproduces exactly, temporal definition clean, no leakage in the safe feature set. Proceeding to Phase 1 with the 8 safe clinical features.

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
- **Calibration is modality-dependent.** The frozen CNV+image fusion (slope **1.78**, ECE **0.075**) and CNV-only (slope 1.23, ECE 0.095) are well-calibrated. The clinical and clinical-stacked models are **over-confident** (slopes 0.55–0.72, negative intercepts, ECE 0.21–0.23).
  - **[I] Confound flagged:** the frozen fusion carries **per-fold Platt calibration**; the quick cross-fit clinical stacks do **not**. Part of the calibration gap is this missing step, not intrinsic. Discrimination and operating-point specificity are unaffected; a fair calibration comparison needs per-fold Platt on the stacks (Phase 4 refinement).
- **Decision-curve analysis:** the frozen CNV+image fusion has the **highest net benefit across most of the clinically relevant range (~0.15–0.45)**; `clinical+CNV+image` is competitive in the 0.25–0.45 band. All models beat treat-all/treat-none between ~0.15 and ~0.45.
- **Operating points show a clean, monotonic clinical-utility gain:** at 90% sensitivity, specificity rises **0.28 (clinical) → 0.42 (CNV+image fusion) → 0.66 (clinical+CNV+image)**, PPV 0.39 → 0.44 → **0.57**, NPV 0.88 → 0.89 → **0.93**. Adding clinical context to the multimodal model roughly halves the false-positive rate at fixed sensitivity — the most tangible clinical result here.

### Deliverables
`calibration_curves.png/.pdf`, `decision_curves.png/.pdf`, `calibration_metrics.csv`, `decision_curve_results.csv`, `clinical_operating_points.csv`.

**Phase 2 gate: PASSED.** Main caveat (uncalibrated stacks) recorded for Phase 4.

# Clinical Baseline Report (Phase 1)

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

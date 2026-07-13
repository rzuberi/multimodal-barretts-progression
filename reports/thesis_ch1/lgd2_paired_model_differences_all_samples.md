# LGD2+ Paired Patient-Level Model Differences - all_samples

Endpoint: `NextBiopsyProgression_LGD2plus`. Patient-level `patient_max`, shared-index bootstrap.
Delta = (model_a - model_b). AUPRC/AUC: positive favours a. Brier: NEGATIVE favours a (lower is better).
CIs are percentile 95%. Sign-prob is a two-sided bootstrap sign probability, not a frequentist p-value.

| contrast | type | n (pos/neg) | dAUPRC (95% CI) | dAUC (95% CI) | dBrier (95% CI) | valid frac |
|---|---|---|---|---|---|---|
| image_uni2_abmil - cnv_only | prespecified | 155 (55/100) | +0.119 (-0.010, +0.234) | +0.079 (-0.003, +0.166) | +0.017 (-0.025, +0.059) | 1.00 |
| early_fusion_uni2 - cnv_only | prespecified | 155 (55/100) | +0.189 (+0.066, +0.294) | +0.130 (+0.058, +0.211) | -0.051 (-0.084, -0.018) | 1.00 |
| intermediate_fusion(best) - cnv_only | model_selected | 155 (55/100) | +0.178 (+0.051, +0.288) | +0.110 (+0.030, +0.191) | +0.000 (-0.043, +0.046) | 1.00 |
| late_fusion_uni2_mean - cnv_only | prespecified | 155 (55/100) | +0.120 (+0.016, +0.216) | +0.088 (+0.023, +0.158) | -0.020 (-0.040, -0.001) | 1.00 |
| late_fusion(best) - cnv_only | model_selected | 155 (55/100) | +0.136 (+0.024, +0.241) | +0.099 (+0.030, +0.173) | -0.021 (-0.041, -0.002) | 1.00 |
| early_fusion_uni2 - image_uni2_abmil | prespecified | 155 (55/100) | +0.070 (-0.004, +0.144) | +0.051 (+0.006, +0.099) | -0.068 (-0.095, -0.040) | 1.00 |
| early_fusion_uni2 - late_fusion_uni2_mean | prespecified | 155 (55/100) | +0.068 (-0.000, +0.137) | +0.042 (+0.004, +0.085) | -0.031 (-0.051, -0.010) | 1.00 |

Model-selected contrasts (best-of) are optimistic; interpret their CIs with that caveat.
Where a delta CI crosses zero, do not claim superiority.

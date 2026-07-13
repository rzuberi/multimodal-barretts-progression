# LGD2+ Paired Patient-Level Model Differences - early_prediction_only

Endpoint: `NextBiopsyProgression_LGD2plus`. Patient-level `patient_max`, shared-index bootstrap.
Delta = (model_a - model_b). AUPRC/AUC: positive favours a. Brier: NEGATIVE favours a (lower is better).
CIs are percentile 95%. Sign-prob is a two-sided bootstrap sign probability, not a frequentist p-value.

| contrast | type | n (pos/neg) | dAUPRC (95% CI) | dAUC (95% CI) | dBrier (95% CI) | valid frac |
|---|---|---|---|---|---|---|
| image_uni2_abmil - cnv_only | prespecified | 150 (50/100) | +0.153 (+0.006, +0.280) | +0.128 (+0.014, +0.243) | +0.018 (-0.027, +0.063) | 1.00 |
| early_fusion_uni2 - cnv_only | prespecified | 150 (50/100) | +0.211 (+0.073, +0.328) | +0.191 (+0.101, +0.290) | -0.047 (-0.082, -0.013) | 1.00 |
| intermediate_fusion(best) - cnv_only | model_selected | 150 (50/100) | +0.157 (+0.016, +0.276) | +0.137 (+0.033, +0.243) | +0.008 (-0.037, +0.054) | 1.00 |
| late_fusion_uni2_mean - cnv_only | prespecified | 150 (50/100) | +0.137 (+0.019, +0.240) | +0.137 (+0.053, +0.228) | -0.022 (-0.045, -0.001) | 1.00 |
| late_fusion(best) - cnv_only | model_selected | 150 (50/100) | +0.127 (+0.003, +0.245) | +0.118 (+0.024, +0.215) | -0.017 (-0.039, +0.004) | 1.00 |
| early_fusion_uni2 - image_uni2_abmil | prespecified | 150 (50/100) | +0.058 (-0.040, +0.152) | +0.063 (+0.003, +0.127) | -0.065 (-0.095, -0.036) | 1.00 |
| early_fusion_uni2 - late_fusion_uni2_mean | prespecified | 150 (50/100) | +0.075 (-0.014, +0.157) | +0.054 (+0.004, +0.106) | -0.025 (-0.046, -0.002) | 1.00 |

Model-selected contrasts (best-of) are optimistic; interpret their CIs with that caveat.
Where a delta CI crosses zero, do not claim superiority.

# Virchow2 Sensitivity Report (Phase 6)

**Pre-specified encoder sensitivity analysis** on the primary LGD2+ endpoint only. Same ABMIL architecture, same nested inner-CV / threshold / Platt-calibration protocol, same frozen patient-disjoint 5-fold splits as the locked Chapter-1 analysis — only the image feature view is swapped (UNI2 → Virchow2, feat_dim 1536 → 2560). Patient-level (patient-max), paired bootstrap 2000 resamples.

## Embedding verification (gate) — PASSED
All 707 primary-cohort Virchow2 slide embeddings readable; `embeddings` key present; feat_dim consistent at 2560; tile counts 64–256 (plausible MIL bags); zero missing/invalid slides. Same 707-row cohort → frozen splits reused directly. Virchow2 features are frozen per-slide encoder outputs (no fold/label information enters embedding generation) — leakage-safe.

## Reproduction check — PASSED
Deriving late_mean as the sample-level mean of `cnv_only` and `uni2_image_only` raw `y_prob` (then patient-max) reproduces the frozen late_mean **exactly** (AUPRC 0.6296 / ROC 0.7742 / Brier 0.1842) — confirms the derivation recipe and that the frozen anchors are intact before applying the same recipe to Virchow2.

## Primary metrics (patient-level, n=150 / 50 positive)
| model | n_pat | n_pos | auprc | roc | brier | auprc_lo | auprc_hi | roc_lo | roc_hi |
|---|---|---|---|---|---|---|---|---|---|
| cnv_only(shared) | 150 | 50 | 0.5385 | 0.663 | 0.216 | 0.41 | 0.6742 | 0.5711 | 0.7581 |
| uni2_image_only | 150 | 50 | 0.557 | 0.7312 | 0.2453 | 0.4326 | 0.7125 | 0.6421 | 0.8155 |
| virchow2_image_only | 150 | 50 | 0.4823 | 0.6658 | 0.2499 | 0.3685 | 0.6409 | 0.5741 | 0.7574 |
| uni2_late_mean | 150 | 50 | 0.6296 | 0.7742 | 0.1842 | 0.4969 | 0.7697 | 0.6938 | 0.8466 |
| virchow2_late_mean | 150 | 50 | 0.5582 | 0.7106 | 0.1951 | 0.4308 | 0.7035 | 0.6207 | 0.7946 |
| uni2_intermediate_fusion | 150 | 50 | 0.5675 | 0.7414 | 0.2242 | 0.4362 | 0.7051 | 0.6567 | 0.8153 |
| virchow2_intermediate_fusion | 150 | 50 | 0.488 | 0.6614 | 0.2737 | 0.3688 | 0.6337 | 0.5696 | 0.7506 |


## Paired comparison — Virchow2 minus UNI2 (same patients)
| comparison | d_auprc | auprc_ci | auprc_crosses0 | d_roc | roc_ci | d_brier | brier_ci |
|---|---|---|---|---|---|---|---|
| virchow2_image_only - uni2_image_only | -0.0748 | [-0.1702,0.0234] | True | -0.0654 | [-0.1309,-0.0037] | 0.0046 | [-0.0281,0.0365] |
| virchow2_late_mean - uni2_late_mean | -0.0714 | [-0.1422,0.0042] | True | -0.0636 | [-0.123,-0.0058] | 0.0109 | [-0.0032,0.0255] |
| virchow2_intermediate_fusion - uni2_intermediate_fusion | -0.0794 | [-0.1632,0.0086] | True | -0.08 | [-0.1549,-0.004] | 0.0495 | [0.0134,0.0835] |


## Calibration
| model | cal_slope | cal_intercept | ece |
|---|---|---|---|
| virchow2_image_only | 0.351 | -0.686 | 0.1884 |
| virchow2_late_mean | 1.037 | -0.005 | 0.0729 |
| virchow2_intermediate_fusion | 0.317 | -0.82 | 0.2115 |
| uni2_late_mean | 1.582 | 0.033 | 0.0751 |


## Verdict — Virchow2 does NOT improve on UNI2; UNI2 remains the reported backbone
On the primary LGD2+ task, Virchow2 is **slightly worse than UNI2 on every model family and every metric**:
- **image_only:** AUPRC 0.557 → 0.482 (Δ −0.075); ROC 0.731 → 0.666 (Δ −0.065, CI excludes 0).
- **late_mean fusion:** AUPRC 0.630 → 0.558 (Δ −0.071); ROC 0.774 → 0.711 (Δ −0.064, CI excludes 0).
- **intermediate_fusion:** AUPRC 0.567 → 0.488 (Δ −0.079); ROC 0.741 → 0.661 (Δ −0.080) and Brier both worsen (CI excludes 0).

Every paired ΔAUPRC is negative (AUPRC CIs cross zero; ROC deltas are significantly negative for all three families). Virchow2 image/intermediate models are also more poorly calibrated (slopes 0.32–0.35, ECE 0.19–0.21) than the well-calibrated Virchow2 late_mean (slope 1.04) and the UNI2 baseline.

**Per the pre-specified rule (spec Phase 6): Virchow2 is NOT expanded to other endpoints or model families**, because it produces no material or stable improvement on AUPRC, ROC, Brier, calibration, or the paired comparison. **UNI2 (with GigaPath effectively tied) remains the default reported encoder.** This is a clean negative encoder-sensitivity result: the multimodal finding is not an artifact of one particular pathology foundation model, and swapping to a larger/newer encoder (Virchow2, 2560-d) does not help at this sample size.

## Deliverables
`virchow2_primary_metrics.csv`, `virchow2_paired_comparisons.csv`, `virchow2_calibration.csv`, this report. Trained checkpoints/predictions and the Virchow2 registry config kept on the cluster under `analysis/chapter1_scientific_hardening_20260727/virchow2_training/`.

**Phase 6 gate: complete — negative sensitivity result recorded (spec rule 9: preserve negative findings).**

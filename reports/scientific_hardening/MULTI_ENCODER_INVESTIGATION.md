# Multi-Encoder Investigation (Phase 6 extension)

**Question (reviewer-anticipating):** UNI2 and Virchow2 were each tested alone (Phase 6). Do *other* foundation encoders help, and does *combining* encoders recover complementary signal (one encoder strong where another is weak)?

**Setup:** three frozen pathology foundation encoders — UNI2 (1536-d), GigaPath (1536-d), Virchow2 (2560-d) — each producing per-slide MIL bags fed to the same frozen ABMIL image model, same nested-CV / patient-disjoint splits / raw-`y_prob` patient-max protocol. GigaPath image-only was trained here (5-fold GPU) to match; UNI2 and Virchow2 reused. All combinations evaluated patient-level, paired bootstrap 2000. late_mean derivation validated against the frozen UNI2 anchor (reproduces 0.6296 exactly).

## Single encoders + combinations (patient-level, n=150 / 50 pos)
| model | n_pat | n_pos | auprc | roc | brier | auprc_lo | auprc_hi | roc_lo | roc_hi |
|---|---|---|---|---|---|---|---|---|---|
| cnv_only | 150 | 50 | 0.5385 | 0.663 | 0.216 | 0.41 | 0.6742 | 0.5711 | 0.7581 |
| uni2_image | 150 | 50 | 0.557 | 0.7312 | 0.2453 | 0.4326 | 0.7125 | 0.6421 | 0.8155 |
| virchow2_image | 150 | 50 | 0.4823 | 0.6658 | 0.2499 | 0.3685 | 0.6409 | 0.5741 | 0.7574 |
| gigapath_image | 150 | 50 | 0.6093 | 0.7332 | 0.2319 | 0.4686 | 0.7424 | 0.643 | 0.8185 |
| img_mean3(ensemble) | 150 | 50 | 0.5606 | 0.725 | 0.2235 | 0.43 | 0.7123 | 0.6333 | 0.8104 |
| img_stack3(logistic) | 150 | 50 | 0.5351 | 0.7248 | 0.2062 | 0.4089 | 0.6817 | 0.6326 | 0.8064 |
| img_stack3+cnv | 150 | 50 | 0.5519 | 0.7378 | 0.2038 | 0.4232 | 0.6978 | 0.6491 | 0.8164 |
| uni2_late_mean(headline) | 150 | 50 | 0.6296 | 0.7742 | 0.1842 | 0.4969 | 0.7697 | 0.6938 | 0.8466 |


## GigaPath and 2-encoder late-mean vs the headline
| model | n_pat | n_pos | auprc | roc | brier | auprc_lo | auprc_hi | roc_lo | roc_hi |
|---|---|---|---|---|---|---|---|---|---|
| cnv_only | 150 | 50 | 0.5385 | 0.663 | 0.216 | 0.41 | 0.6742 | 0.5711 | 0.7581 |
| uni2_late_mean(headline) | 150 | 50 | 0.6296 | 0.7742 | 0.1842 | 0.4969 | 0.7697 | 0.6938 | 0.8466 |
| gigapath_late_mean | 150 | 50 | 0.6238 | 0.77 | 0.1798 | 0.4884 | 0.7579 | 0.6881 | 0.8422 |
| cnv+mean(uni2,giga) | 150 | 50 | 0.6354 | 0.7764 | 0.1806 | 0.5042 | 0.7722 | 0.6942 | 0.8509 |
| virchow2_late_mean | 150 | 50 | 0.5582 | 0.7106 | 0.1951 | 0.4308 | 0.7035 | 0.6207 | 0.7946 |


## Paired comparisons
| comparison | d_auprc | auprc_ci | auprc_crosses0 | d_roc | roc_ci | roc_crosses0 |
|---|---|---|---|---|---|---|
| img_stack3 - uni2_image | -0.0219 | [-0.1213,0.069] | True | -0.0064 | [-0.0648,0.0473] | True |
| img_stack3 - uni2_late_mean(headline) | -0.0945 | [-0.1721,-0.0092] | False | -0.0494 | [-0.1063,0.0045] | True |
| img_stack3+cnv - uni2_late_mean(headline) | -0.0777 | [-0.1496,0.0011] | True | -0.0364 | [-0.0929,0.0174] | True |
| img_mean3 - uni2_image | 0.0036 | [-0.0756,0.0788] | True | -0.0062 | [-0.0467,0.0322] | True |


| comparison | d_auprc | auprc_ci | auprc_crosses0 | d_roc | roc_ci | roc_crosses0 | d_brier | brier_ci |
|---|---|---|---|---|---|---|---|---|
| gigapath_late_mean - uni2_late_mean(headline) | -0.0058 | [-0.0751,0.0674] | True | -0.0042 | [-0.0615,0.0489] | True | -0.0043 | [-0.0167,0.0097] |
| gigapath_late_mean - cnv_only | 0.0854 | [-0.0323,0.2169] | True | 0.107 | [-0.0073,0.2176] | True | -0.0361 | [-0.066,-0.0052] |
| cnv+mean(uni2,giga) - uni2_late_mean(headline) | 0.0058 | [-0.0397,0.0569] | True | 0.0022 | [-0.0318,0.0345] | True | -0.0036 | [-0.0107,0.0039] |


## Learned stacker weights (standardized logistic coef per fold, image encoders)
| fold | uni2 | virchow2 | gigapath |
|---|---|---|---|
| 0 | 0.137 | 0.017 | 0.905 |
| 1 | 0.506 | -0.322 | 0.73 |
| 2 | 0.231 | -0.23 | 0.987 |
| 3 | 0.5 | -0.221 | 0.654 |
| 4 | 0.61 | -0.09 | 0.377 |
| mean | 0.397 | -0.169 | 0.731 |


## Findings

1. **GigaPath is the strongest single image encoder** (AUPRC 0.609 vs UNI2 0.557, Virchow2 0.482) — the intuition that encoders differ is real, and the learned stacker confirms it: it weights GigaPath (+0.73) and UNI2 (+0.40) up and Virchow2 (-0.17) down.
2. **Combining encoders does NOT beat the single-encoder-plus-CNV headline.** The 3-encoder learned stack overfits at n=150 (AUPRC 0.535 - below GigaPath alone) and is significantly worse than the headline (delta -0.095, CI [-0.172, -0.009], excludes 0). The 3-encoder mean-ensemble only ties UNI2 image.
3. **Swapping UNI2->GigaPath in the CNV+image late-mean is a tie, not a gain** (0.624 vs 0.630; delta -0.006, CI crosses 0). Fusing CNV with the mean of UNI2+GigaPath gives the single best point estimate tested (AUPRC 0.635) but the gain over 0.630 is within noise (delta +0.006, CI [-0.040, +0.057]).

## Verdict
No encoder choice or combination improves on the reported **UNI2 late-mean fusion (0.630)** beyond noise. This closes the "did you try other encoders / combining them" question: three encoders were tested individually and combined (mean-ensemble and fold-pure learned stacking); at this sample size the simple CNV + single-encoder late-mean remains best, and learned multi-encoder fusion overfits. **UNI2 remains the reported backbone; GigaPath is an acceptable tie.**

Artifacts: `multiencoder_metrics.csv`, `multiencoder_paired.csv`, `multiencoder_stacker_weights.csv`, `gigapath_latemean_metrics.csv`, `gigapath_latemean_paired.csv`, `multiencoder_comparison.png`.

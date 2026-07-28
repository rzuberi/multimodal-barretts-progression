# Robustness Report (Phase 3)

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
